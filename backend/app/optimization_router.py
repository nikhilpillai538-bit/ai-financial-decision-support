"""
FastAPI router for Phase 7: Modern Portfolio Theory (MPT), Risk Analysis,
Historical Market Data Ingestion, and Explainable Portfolio Optimization.
"""

from decimal import Decimal
import io
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.models import UserModel
from app.db.repositories.portfolio_repo import SQLPortfolioRepository
from app.db.session import get_db
from app.historical_data import (
    parse_historical_prices_csv,
    prepare_market_data_matrix,
)
from app.market_fetcher import (
    CURATED_PRESETS,
    fetch_live_quotes,
    fetch_yahoo_historical_data,
)
from app.optimization_schemas import (
    HistoricalPriceImportResponse,
    HistoricalPriceResponse,
    HistoricalPriceRow,
    MarketPresetItem,
    MarketQuoteItem,
    MarketQuotesRequest,
    MarketQuotesResponse,
    OptimizationRequest,
    OptimizationRunSummary,
    PortfolioMarketSyncHoldingItem,
    PortfolioMarketSyncResponse,
    PortfolioOptimizationResponse,
    YahooFetchHistoricalRequest,
    YahooFetchHistoricalResponse,
)
from app.portfolio_optimization import run_mpt_optimization
from app.portfolio_router import get_portfolio_repo

optimization_router = APIRouter(tags=["Portfolio Optimization & Risk Analysis"])


# ---------------------------------------------------------------------------
# Historical Price Data Endpoints
# ---------------------------------------------------------------------------

@optimization_router.post(
    "/market-data/historical-prices/import-csv",
    response_model=HistoricalPriceImportResponse,
    summary="Upload and ingest a historical asset price CSV dataset",
)
@optimization_router.post(
    "/market-data/upload-csv",
    response_model=HistoricalPriceImportResponse,
    include_in_schema=False,
)
async def import_market_data_csv(
    file: UploadFile = File(..., description="CSV file containing date, symbol, adjusted_close"),
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> HistoricalPriceImportResponse:
    MAX_CSV_BYTES = 10 * 1024 * 1024  # 10 MB limit
    content = await file.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="The uploaded CSV exceeds the maximum allowed size of 10 MB.",
        )
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file must be UTF-8 encoded.",
        )

    valid_rows, errors = parse_historical_prices_csv(text)
    if not valid_rows and errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV validation failed: {'; '.join(errors[:5])}",
        )

    imported, skipped = repo.save_historical_prices(valid_rows)
    updated_symbols = sorted(list(set(r.symbol for r in valid_rows)))

    return HistoricalPriceImportResponse(
        filename=file.filename,
        total_rows=len(valid_rows) + len(errors),
        imported=imported,
        skipped_duplicates=skipped,
        rejected=len(errors),
        symbols_updated=updated_symbols,
        errors=errors[:20],
    )


@optimization_router.post(
    "/portfolios/{portfolio_id}/historical-prices/import-csv",
    response_model=HistoricalPriceImportResponse,
    summary="Upload historical price CSV dataset for a specific portfolio",
)
async def import_portfolio_historical_prices(
    portfolio_id: str,
    file: UploadFile = File(..., description="CSV file containing historical prices"),
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> HistoricalPriceImportResponse:
    portfolio = repo.get_portfolio(portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )

    MAX_CSV_BYTES = 10 * 1024 * 1024  # 10 MB limit
    content = await file.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="The uploaded CSV exceeds the maximum allowed size of 10 MB.",
        )
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file must be UTF-8 encoded.",
        )

    valid_rows, errors = parse_historical_prices_csv(text)
    if not valid_rows and errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"CSV validation failed: {'; '.join(errors[:5])}",
        )

    imported, skipped = repo.save_historical_prices(valid_rows)
    portfolio_symbols = {
        h.asset.symbol.upper() for h in portfolio.holdings if h.asset and h.asset.symbol
    }
    updated_portfolio_symbols = sorted(
        list(set(r.symbol for r in valid_rows if r.symbol in portfolio_symbols))
    )

    return HistoricalPriceImportResponse(
        filename=file.filename,
        total_rows=len(valid_rows) + len(errors),
        imported=imported,
        skipped_duplicates=skipped,
        rejected=len(errors),
        symbols_updated=updated_portfolio_symbols,
        errors=errors[:20],
    )


@optimization_router.get(
    "/market-data/historical-prices/{symbol}",
    response_model=List[HistoricalPriceResponse],
    summary="Retrieve stored historical prices for a ticker symbol",
)
def get_symbol_prices(
    symbol: str,
    limit: int = Query(252, ge=1, le=2520, description="Max observations to return"),
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> List[HistoricalPriceResponse]:
    prices = repo.get_historical_prices(symbols=[symbol])
    return [HistoricalPriceResponse.model_validate(p) for p in prices[-limit:]]


# ---------------------------------------------------------------------------
# Yahoo Finance Auto-Fetch & Live Market Quotes
# ---------------------------------------------------------------------------

@optimization_router.get(
    "/market-data/summary",
    summary="Summary of stored market data and available ticker observations",
)
def get_market_data_summary(
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_db),
):
    from sqlalchemy import func, select
    from app.db.models import HistoricalPriceModel

    stmt = select(
        HistoricalPriceModel.symbol,
        func.count(HistoricalPriceModel.id),
        func.min(HistoricalPriceModel.date),
        func.max(HistoricalPriceModel.date),
    ).group_by(HistoricalPriceModel.symbol)

    results = session.execute(stmt).all()
    symbols = [r[0] for r in results]
    total_points = sum(r[1] for r in results)
    min_date = min((r[2] for r in results if r[2]), default=None)
    max_date = max((r[3] for r in results if r[3]), default=None)

    return {
        "symbols_count": len(symbols),
        "data_points_count": total_points,
        "date_range_start": min_date.isoformat() if min_date else None,
        "date_range_end": max_date.isoformat() if max_date else None,
        "available_symbols": sorted(symbols),
    }


@optimization_router.get(
    "/market-data/presets",
    response_model=List[MarketPresetItem],
    summary="Get curated stock market ticker group presets (India & Global)",
)
def get_market_presets() -> List[MarketPresetItem]:
    return [MarketPresetItem(**p) for p in CURATED_PRESETS]


@optimization_router.post(
    "/market-data/yfinance/fetch-historical",
    response_model=YahooFetchHistoricalResponse,
    summary="Auto-fetch and ingest historical prices from Yahoo Finance",
)
def fetch_historical_from_yahoo(
    payload: YahooFetchHistoricalRequest,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> YahooFetchHistoricalResponse:
    if payload.portfolio_id:
        portfolio = repo.get_portfolio(payload.portfolio_id, user_id=current_user.id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio '{payload.portfolio_id}' not found.",
            )

    price_rows, succ, fail = fetch_yahoo_historical_data(
        symbols=payload.symbols,
        period=payload.period,
    )

    imported = 0
    skipped = 0
    start_date = None
    end_date = None

    if price_rows:
        imported, skipped = repo.save_historical_prices(price_rows, source="yfinance")
        start_date = min(r.date for r in price_rows)
        end_date = max(r.date for r in price_rows)

    msg = f"Successfully fetched {len(succ)} symbol(s) ({imported} new observations imported, {skipped} existing skipped)."
    if fail:
        msg += f" Could not fetch {len(fail)} symbol(s): {', '.join(fail)}."

    return YahooFetchHistoricalResponse(
        symbols_requested=payload.symbols,
        symbols_successful=succ,
        symbols_failed=fail,
        imported_rows=imported,
        skipped_rows=skipped,
        period=payload.period,
        date_range_start=start_date,
        date_range_end=end_date,
        message=msg,
    )


@optimization_router.post(
    "/market-data/quotes",
    response_model=MarketQuotesResponse,
    summary="Retrieve live market quotes for stock symbols from Yahoo Finance",
)
def get_market_quotes(
    payload: MarketQuotesRequest,
    current_user: UserModel = Depends(get_current_user),
) -> MarketQuotesResponse:
    quotes_raw = fetch_live_quotes(payload.symbols)
    quote_items = {
        sym: MarketQuoteItem(
            symbol=q["symbol"],
            last_price=q["last_price"],
            currency=q["currency"],
            previous_close=q.get("previous_close"),
            change=q.get("change"),
            change_percent=q.get("change_percent"),
            fetched_at=q["fetched_at"],
        )
        for sym, q in quotes_raw.items()
    }
    return MarketQuotesResponse(quotes=quote_items, count=len(quote_items))


@optimization_router.post(
    "/portfolios/{portfolio_id}/sync-market-prices",
    response_model=PortfolioMarketSyncResponse,
    summary="Sync all portfolio holdings to current live Yahoo Finance prices",
)
def sync_portfolio_live_prices(
    portfolio_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> PortfolioMarketSyncResponse:
    portfolio = repo.get_portfolio(portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )

    # Collect holdings that have a symbol
    symbol_holdings = [
        h for h in portfolio.holdings if h.asset and h.asset.symbol and h.asset.symbol.strip()
    ]
    if not symbol_holdings:
        return PortfolioMarketSyncResponse(
            portfolio_id=portfolio_id,
            synced_count=0,
            failed_count=0,
            updated_holdings=[],
            message="No holdings with ticker symbols found in this portfolio.",
        )

    symbols = list({h.asset.symbol.strip().upper() for h in symbol_holdings})
    quotes = fetch_live_quotes(symbols)

    updated_items = []
    synced = 0
    failed = 0

    now_utc = datetime.now(timezone.utc)

    for h in symbol_holdings:
        sym = h.asset.symbol.strip().upper()
        if sym in quotes:
            q = quotes[sym]
            new_price = q["last_price"]
            old_price = h.current_price
            repo.update_holding(
                holding_id=h.id,
                portfolio_id=portfolio_id,
                user_id=current_user.id,
                current_price=new_price,
                price_as_of=now_utc,
            )
            updated_items.append(
                PortfolioMarketSyncHoldingItem(
                    holding_id=h.id,
                    symbol=sym,
                    asset_name=h.asset.name,
                    old_price=old_price,
                    new_price=new_price,
                    currency=q.get("currency", h.asset.currency or "INR"),
                )
            )
            synced += 1
        else:
            failed += 1

    msg = f"Synced {synced} holding(s) with live market prices."
    if failed > 0:
        msg += f" {failed} holding(s) could not be updated (symbol not found on market)."

    return PortfolioMarketSyncResponse(
        portfolio_id=portfolio_id,
        synced_count=synced,
        failed_count=failed,
        updated_holdings=updated_items,
        message=msg,
    )


# ---------------------------------------------------------------------------
# Portfolio Optimization Endpoint
# ---------------------------------------------------------------------------

@optimization_router.post(
    "/portfolios/{portfolio_id}/optimize",
    response_model=PortfolioOptimizationResponse,
    summary="Execute Modern Portfolio Theory (MPT) optimization and rebalancing analysis",
)
def optimize_portfolio(
    portfolio_id: str,
    payload: OptimizationRequest,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> PortfolioOptimizationResponse:
    portfolio = repo.get_portfolio(portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )

    # Validate that portfolio has holdings with symbols
    holdings = portfolio.holdings or []
    if len(holdings) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Portfolio has {len(holdings)} holdings. MPT optimization requires at least 2 distinct instruments.",
        )

    symbols = []
    for h in holdings:
        if not h.asset or not h.asset.symbol:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Holding '{h.id}' is linked to an asset without a ticker symbol. All assets must have symbols for historical return matching.",
            )
        symbols.append(h.asset.symbol.upper())

    # De-duplicate while preserving order
    unique_symbols = list(dict.fromkeys(symbols))
    if len(unique_symbols) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Portfolio must contain at least 2 distinct asset symbols.",
        )

    # Resolve price records: from inline CSV or from database
    if payload.csv_content:
        price_rows, errors = parse_historical_prices_csv(payload.csv_content)
        if not price_rows:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Could not parse inline CSV price content: {'; '.join(errors[:3])}",
            )
    else:
        db_records = repo.get_historical_prices(symbols=unique_symbols)
        if not db_records:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"No historical price data found for portfolio symbols {unique_symbols}. "
                    "Upload historical prices first via POST /portfolios/{id}/historical-prices/import-csv "
                    "or include 'csv_content' in the optimization request."
                ),
            )
        price_rows = [
            HistoricalPriceRow(
                date=r.date,
                symbol=r.symbol,
                adjusted_close=r.adjusted_close,
            )
            for r in db_records
        ]

    # Build market data returns matrix
    try:
        market_data = prepare_market_data_matrix(
            price_records=price_rows,
            required_symbols=unique_symbols,
            min_observations=payload.min_observations,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # Retrieve target allocation if available
    target_alloc = repo.get_target_allocation(portfolio_id, user_id=current_user.id)

    # Execute MPT Optimization
    response = run_mpt_optimization(
        portfolio=portfolio,
        target_allocation=target_alloc,
        market_data=market_data,
        request=payload,
    )

    # Persist audit record
    try:
        run_record = repo.save_optimization_run(
            portfolio_id=portfolio.id,
            user_id=current_user.id,
            strategy=response.strategy,
            risk_free_rate=response.risk_free_rate,
            expected_return=response.expected_return,
            expected_volatility=response.expected_volatility,
            sharpe_ratio=response.sharpe_ratio,
            weights={a.symbol: str(a.optimal_weight) for a in response.allocations},
            metadata_info={
                "observation_count": response.observation_count,
                "start_date": str(response.start_date),
                "end_date": str(response.end_date),
                "methodology": response.methodology,
                "warnings": response.warnings,
            },
        )
        response.run_id = run_record.id
    except Exception:
        # Non-critical for response
        pass

    return response


@optimization_router.get(
    "/portfolios/{portfolio_id}/optimization-history",
    response_model=List[OptimizationRunSummary],
    summary="List past optimization runs for a portfolio",
)
def list_portfolio_optimization_history(
    portfolio_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> List[OptimizationRunSummary]:
    portfolio = repo.get_portfolio(portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )

    runs = repo.list_optimization_runs(portfolio_id, user_id=current_user.id)
    return [
        OptimizationRunSummary(
            id=r.id,
            portfolio_id=r.portfolio_id,
            strategy=r.strategy,
            risk_free_rate=r.risk_free_rate,
            expected_return=r.expected_return,
            expected_volatility=r.expected_volatility,
            sharpe_ratio=r.sharpe_ratio,
            weights={k: Decimal(str(v)) for k, v in r.weights.items()},
            created_at=r.created_at,
        )
        for r in runs
    ]
