"""
FastAPI Router for Phase 6: Portfolio Management, Assets, Holdings, Goals,
Deterministic Valuation, and Asset Allocation Analysis.

All routes require authentication via `get_current_user` and guarantee strict user data isolation.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.allocation_analysis import calculate_allocation_analysis
from app.auth.dependencies import get_current_user
from app.auth.schemas import MessageResponse
from app.db.models import UserModel
from app.db.repositories.portfolio_repo import SQLPortfolioRepository
from app.db.session import get_db
from app.optimization_validator import validate_optimization_readiness
from app.portfolio_schemas import (
    AllocationAnalysisResponse,
    AssetCreate,
    AssetResponse,
    AssetUpdate,
    HoldingCreate,
    HoldingResponse,
    HoldingUpdate,
    InvestmentGoalCreate,
    InvestmentGoalResponse,
    InvestmentGoalUpdate,
    OptimizationReadinessResponse,
    PortfolioCreate,
    PortfolioResponse,
    PortfolioUpdate,
    PortfolioValuationResponse,
    TargetAllocationResponse,
    TargetAllocationSetRequest,
    quantize_decimal,
)
from app.portfolio_valuation import calculate_portfolio_valuation

portfolio_router = APIRouter(tags=["Portfolio Management"])


def get_portfolio_repo(db: Session = Depends(get_db)) -> SQLPortfolioRepository:
    """Dependency provider for the SQL portfolio repository."""
    return SQLPortfolioRepository(db)


# ---------------------------------------------------------------------------
# Helper: format holding response
# ---------------------------------------------------------------------------

def _to_holding_response(holding) -> HoldingResponse:
    asset = holding.asset
    qty = holding.quantity
    avg_price = holding.average_purchase_price
    cost_basis = quantize_decimal(qty * avg_price, 2)
    market_val = (
        quantize_decimal(qty * holding.current_price, 2)
        if holding.current_price is not None
        else None
    )

    return HoldingResponse(
        id=holding.id,
        portfolio_id=holding.portfolio_id,
        asset_id=holding.asset_id,
        asset_symbol=asset.symbol if asset else None,
        asset_name=asset.name if asset else "Unknown",
        asset_class=asset.asset_class if asset else "other",
        currency=asset.currency if asset else "INR",
        quantity=qty,
        average_purchase_price=avg_price,
        current_price=holding.current_price,
        price_as_of=holding.price_as_of,
        cost_basis=cost_basis,
        market_value=market_val,
        notes=holding.notes,
        created_at=holding.created_at,
        updated_at=holding.updated_at,
    )


# ---------------------------------------------------------------------------
# Helper: format goal response with progress
# ---------------------------------------------------------------------------

def _to_goal_response(goal, repo: SQLPortfolioRepository, user_id: str) -> InvestmentGoalResponse:
    current_val: Optional[Decimal] = None
    progress_pct: Optional[Decimal] = None
    remaining: Optional[Decimal] = None
    warnings: List[str] = []

    today = datetime.now(timezone.utc).date()
    days_rem = (goal.target_date - today).days

    if goal.portfolio_id:
        portfolio = repo.get_portfolio(goal.portfolio_id, user_id)
        if portfolio:
            val = calculate_portfolio_valuation(portfolio)
            if val.priced_holdings_value > Decimal("0.00"):
                current_val = val.priced_holdings_value
                progress_pct = quantize_decimal((current_val / goal.target_amount) * Decimal("100"), 2)
                remaining = quantize_decimal(max(Decimal("0.00"), goal.target_amount - current_val), 2)
            else:
                warnings.append("Linked portfolio has no priced holdings. Valuation progress cannot be determined.")
            if val.unpriced_holdings_count > 0:
                warnings.append(f"Linked portfolio has {val.unpriced_holdings_count} unpriced holding(s).")
        else:
            warnings.append("Linked portfolio could not be retrieved.")
    elif goal.current_amount is not None:
        current_val = goal.current_amount
        progress_pct = quantize_decimal((current_val / goal.target_amount) * Decimal("100"), 2)
        remaining = quantize_decimal(max(Decimal("0.00"), goal.target_amount - current_val), 2)

    return InvestmentGoalResponse(
        id=goal.id,
        user_id=goal.user_id,
        portfolio_id=goal.portfolio_id,
        name=goal.name,
        target_amount=goal.target_amount,
        target_date=goal.target_date,
        priority=goal.priority,
        status=getattr(goal, "status", "in_progress") or "in_progress",
        current_amount=goal.current_amount,
        initial_lump_sum=goal.initial_lump_sum,
        expected_annual_return=goal.expected_annual_return,
        monthly_contribution=goal.monthly_contribution,
        notes=goal.notes,
        current_portfolio_value=current_val,
        progress_percentage=progress_pct,
        remaining_amount=remaining,
        days_remaining=days_rem,
        warnings=warnings,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


# ---------------------------------------------------------------------------
# Portfolio Endpoints
# ---------------------------------------------------------------------------

@portfolio_router.post(
    "/portfolios",
    response_model=PortfolioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new investment portfolio",
)
def create_portfolio(
    payload: PortfolioCreate,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> PortfolioResponse:
    portfolio = repo.create_portfolio(
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        base_currency=payload.base_currency,
    )
    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        name=portfolio.name,
        description=portfolio.description,
        base_currency=portfolio.base_currency,
        holding_count=0,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )


@portfolio_router.get(
    "/portfolios",
    response_model=List[PortfolioResponse],
    summary="List all portfolios for the authenticated user",
)
def list_portfolios(
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> List[PortfolioResponse]:
    portfolios = repo.list_portfolios(user_id=current_user.id)
    return [
        PortfolioResponse(
            id=p.id,
            user_id=p.user_id,
            name=p.name,
            description=p.description,
            base_currency=p.base_currency,
            holding_count=len(p.holdings) if p.holdings else 0,
            created_at=p.created_at,
            updated_at=p.updated_at,
        )
        for p in portfolios
    ]


@portfolio_router.get(
    "/portfolios/{portfolio_id}",
    response_model=PortfolioResponse,
    summary="Get details of a single portfolio",
)
def get_portfolio(
    portfolio_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> PortfolioResponse:
    portfolio = repo.get_portfolio(portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )
    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        name=portfolio.name,
        description=portfolio.description,
        base_currency=portfolio.base_currency,
        holding_count=len(portfolio.holdings) if portfolio.holdings else 0,
        holdings=[_to_holding_response(h) for h in portfolio.holdings] if portfolio.holdings else [],
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )


@portfolio_router.patch(
    "/portfolios/{portfolio_id}",
    response_model=PortfolioResponse,
    summary="Update a portfolio's name, description, or base currency",
)
def update_portfolio(
    portfolio_id: str,
    payload: PortfolioUpdate,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> PortfolioResponse:
    portfolio = repo.update_portfolio(
        portfolio_id=portfolio_id,
        user_id=current_user.id,
        name=payload.name,
        description=payload.description,
        base_currency=payload.base_currency,
    )
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )
    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        name=portfolio.name,
        description=portfolio.description,
        base_currency=portfolio.base_currency,
        holding_count=len(portfolio.holdings) if portfolio.holdings else 0,
        holdings=[_to_holding_response(h) for h in portfolio.holdings] if portfolio.holdings else [],
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
    )


@portfolio_router.delete(
    "/portfolios/{portfolio_id}",
    response_model=MessageResponse,
    summary="Delete a portfolio (with safe deletion protection)",
)
def delete_portfolio(
    portfolio_id: str,
    cascade: bool = Query(
        False,
        description="Set to true to force deletion of portfolio and all associated holdings.",
    ),
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> MessageResponse:
    success, message = repo.delete_portfolio(portfolio_id, user_id=current_user.id, cascade=cascade)
    if not success:
        if "not found" in message.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    return MessageResponse(message=message)


# ---------------------------------------------------------------------------
# Asset Instrument Endpoints
# ---------------------------------------------------------------------------

@portfolio_router.post(
    "/assets",
    response_model=AssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new investment asset instrument",
)
def create_asset(
    payload: AssetCreate,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> AssetResponse:
    asset = repo.create_asset(
        user_id=current_user.id,
        name=payload.name,
        asset_class=payload.asset_class.value,
        symbol=payload.symbol,
        currency=payload.currency,
        instrument_type=payload.instrument_type,
    )
    return AssetResponse.model_validate(asset)


@portfolio_router.get(
    "/assets",
    response_model=List[AssetResponse],
    summary="List accessible instruments (system reference + user-defined)",
)
def list_assets(
    asset_class: Optional[str] = Query(None, description="Filter by asset class"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> List[AssetResponse]:
    assets = repo.list_assets(
        user_id=current_user.id,
        asset_class=asset_class,
        symbol=symbol,
    )
    return [AssetResponse.model_validate(a) for a in assets]


@portfolio_router.get(
    "/assets/{asset_id}",
    response_model=AssetResponse,
    summary="Get details of a single asset instrument",
)
def get_asset(
    asset_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> AssetResponse:
    asset = repo.get_asset(asset_id, user_id=current_user.id)
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset instrument '{asset_id}' not found.",
        )
    return AssetResponse.model_validate(asset)


@portfolio_router.patch(
    "/assets/{asset_id}",
    response_model=AssetResponse,
    summary="Update a user-created asset instrument",
)
def update_asset(
    asset_id: str,
    payload: AssetUpdate,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> AssetResponse:
    asset = repo.update_asset(
        asset_id=asset_id,
        user_id=current_user.id,
        name=payload.name,
        asset_class=payload.asset_class.value if payload.asset_class else None,
        symbol=payload.symbol,
        currency=payload.currency,
        instrument_type=payload.instrument_type,
    )
    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset '{asset_id}' not found or cannot be modified (system assets are read-only).",
        )
    return AssetResponse.model_validate(asset)


# ---------------------------------------------------------------------------
# Holdings Management Endpoints
# ---------------------------------------------------------------------------

@portfolio_router.post(
    "/portfolios/{portfolio_id}/holdings",
    response_model=HoldingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a holding to an investment portfolio",
)
def add_holding(
    portfolio_id: str,
    payload: HoldingCreate,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> HoldingResponse:
    try:
        holding = repo.add_holding(
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            asset_id=payload.asset_id,
            quantity=payload.quantity,
            average_purchase_price=payload.average_purchase_price,
            current_price=payload.current_price,
            price_as_of=payload.price_as_of,
            notes=payload.notes,
        )
    except ValueError as e:
        err_msg = str(e)
        if "not found" in err_msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=err_msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_msg)

    return _to_holding_response(holding)


@portfolio_router.get(
    "/portfolios/{portfolio_id}/holdings",
    response_model=List[HoldingResponse],
    summary="List all holdings in a portfolio",
)
def list_holdings(
    portfolio_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> List[HoldingResponse]:
    portfolio = repo.get_portfolio(portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )
    holdings = repo.list_holdings(portfolio_id, user_id=current_user.id)
    return [_to_holding_response(h) for h in holdings]


@portfolio_router.patch(
    "/portfolios/{portfolio_id}/holdings/{holding_id}",
    response_model=HoldingResponse,
    summary="Update quantity or price of a holding",
)
def update_holding(
    portfolio_id: str,
    holding_id: str,
    payload: HoldingUpdate,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> HoldingResponse:
    holding = repo.update_holding(
        holding_id=holding_id,
        portfolio_id=portfolio_id,
        user_id=current_user.id,
        quantity=payload.quantity,
        average_purchase_price=payload.average_purchase_price,
        current_price=payload.current_price,
        price_as_of=payload.price_as_of,
        notes=payload.notes,
    )
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding '{holding_id}' not found in portfolio '{portfolio_id}'.",
        )
    return _to_holding_response(holding)


@portfolio_router.delete(
    "/portfolios/{portfolio_id}/holdings/{holding_id}",
    response_model=MessageResponse,
    summary="Delete a holding from a portfolio",
)
def delete_holding(
    portfolio_id: str,
    holding_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> MessageResponse:
    success = repo.delete_holding(holding_id, portfolio_id=portfolio_id, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Holding '{holding_id}' not found in portfolio '{portfolio_id}'.",
        )
    return MessageResponse(message="Holding deleted successfully.")


# ---------------------------------------------------------------------------
# Target Allocation Endpoints
# ---------------------------------------------------------------------------

@portfolio_router.put(
    "/portfolios/{portfolio_id}/allocation-target",
    response_model=TargetAllocationResponse,
    summary="Configure target asset allocation percentages for a portfolio",
)
def set_target_allocation(
    portfolio_id: str,
    payload: TargetAllocationSetRequest,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> TargetAllocationResponse:
    try:
        allocation = repo.set_target_allocation(
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            targets=payload.targets,
            is_draft=payload.is_draft,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    total_pct = sum(Decimal(str(v)) for v in allocation.targets.values())
    return TargetAllocationResponse(
        id=allocation.id,
        portfolio_id=allocation.portfolio_id,
        user_id=allocation.user_id,
        targets={k: Decimal(str(v)) for k, v in allocation.targets.items()},
        is_draft=allocation.is_draft,
        total_target_percentage=total_pct,
        notes=allocation.notes,
        created_at=allocation.created_at,
        updated_at=allocation.updated_at,
    )


@portfolio_router.get(
    "/portfolios/{portfolio_id}/allocation-target",
    response_model=TargetAllocationResponse,
    summary="Get target asset allocation for a portfolio",
)
def get_target_allocation(
    portfolio_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> TargetAllocationResponse:
    allocation = repo.get_target_allocation(portfolio_id, user_id=current_user.id)
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No target allocation configured for portfolio '{portfolio_id}'.",
        )

    total_pct = sum(Decimal(str(v)) for v in allocation.targets.values())
    return TargetAllocationResponse(
        id=allocation.id,
        portfolio_id=allocation.portfolio_id,
        user_id=allocation.user_id,
        targets={k: Decimal(str(v)) for k, v in allocation.targets.items()},
        is_draft=allocation.is_draft,
        total_target_percentage=total_pct,
        notes=allocation.notes,
        created_at=allocation.created_at,
        updated_at=allocation.updated_at,
    )


# ---------------------------------------------------------------------------
# Investment Goals Endpoints
# ---------------------------------------------------------------------------

@portfolio_router.post(
    "/investment-goals",
    response_model=InvestmentGoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new investment goal",
)
def create_goal(
    payload: InvestmentGoalCreate,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> InvestmentGoalResponse:
    try:
        goal = repo.create_goal(
            user_id=current_user.id,
            name=payload.name,
            target_amount=payload.target_amount,
            target_date=payload.target_date,
            portfolio_id=payload.portfolio_id,
            priority=payload.priority,
            status=payload.status,
            current_amount=payload.current_amount,
            initial_lump_sum=payload.initial_lump_sum,
            expected_annual_return=payload.expected_annual_return,
            monthly_contribution=payload.monthly_contribution,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _to_goal_response(goal, repo, current_user.id)


@portfolio_router.get(
    "/investment-goals",
    response_model=List[InvestmentGoalResponse],
    summary="List all investment goals for the user",
)
def list_goals(
    portfolio_id: Optional[str] = Query(None, description="Filter by linked portfolio"),
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> List[InvestmentGoalResponse]:
    goals = repo.list_goals(user_id=current_user.id, portfolio_id=portfolio_id)
    return [_to_goal_response(g, repo, current_user.id) for g in goals]


@portfolio_router.get(
    "/investment-goals/{goal_id}",
    response_model=InvestmentGoalResponse,
    summary="Get details and progress for an investment goal",
)
def get_goal(
    goal_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> InvestmentGoalResponse:
    goal = repo.get_goal(goal_id, user_id=current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment goal '{goal_id}' not found.",
        )
    return _to_goal_response(goal, repo, current_user.id)


@portfolio_router.patch(
    "/investment-goals/{goal_id}",
    response_model=InvestmentGoalResponse,
    summary="Update an investment goal",
)
def update_goal(
    goal_id: str,
    payload: InvestmentGoalUpdate,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> InvestmentGoalResponse:
    try:
        goal = repo.update_goal(
            goal_id=goal_id,
            user_id=current_user.id,
            name=payload.name,
            target_amount=payload.target_amount,
            target_date=payload.target_date,
            portfolio_id=payload.portfolio_id,
            priority=payload.priority,
            status=payload.status,
            current_amount=payload.current_amount,
            initial_lump_sum=payload.initial_lump_sum,
            expected_annual_return=payload.expected_annual_return,
            monthly_contribution=payload.monthly_contribution,
            notes=payload.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment goal '{goal_id}' not found.",
        )
    return _to_goal_response(goal, repo, current_user.id)


@portfolio_router.delete(
    "/investment-goals/{goal_id}",
    response_model=MessageResponse,
    summary="Delete an investment goal",
)
def delete_goal(
    goal_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> MessageResponse:
    success = repo.delete_goal(goal_id, user_id=current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment goal '{goal_id}' not found.",
        )
    return MessageResponse(message="Investment goal deleted successfully.")


# ---------------------------------------------------------------------------
# Valuation & Analysis Endpoints
# ---------------------------------------------------------------------------

@portfolio_router.get(
    "/portfolios/{portfolio_id}/valuation",
    response_model=PortfolioValuationResponse,
    summary="Calculate deterministic portfolio valuation and asset-class weights",
)
def get_portfolio_valuation(
    portfolio_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> PortfolioValuationResponse:
    portfolio = repo.get_portfolio(portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )
    return calculate_portfolio_valuation(portfolio)


@portfolio_router.get(
    "/portfolios/{portfolio_id}/allocation-analysis",
    response_model=AllocationAnalysisResponse,
    summary="Analyze current asset allocation against configured target weights",
)
def get_allocation_analysis(
    portfolio_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> AllocationAnalysisResponse:
    portfolio = repo.get_portfolio(portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )
    target_alloc = repo.get_target_allocation(portfolio_id, user_id=current_user.id)
    return calculate_allocation_analysis(portfolio, target_alloc)


@portfolio_router.get(
    "/portfolios/{portfolio_id}/allocation",
    response_model=AllocationAnalysisResponse,
    summary="Alias for /portfolios/{portfolio_id}/allocation-analysis",
)
def get_allocation_alias(
    portfolio_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> AllocationAnalysisResponse:
    return get_allocation_analysis(portfolio_id, current_user, repo)


@portfolio_router.get(
    "/portfolios/{portfolio_id}/optimization-readiness",
    response_model=OptimizationReadinessResponse,
    summary="Check portfolio data completeness for Phase 7 optimization algorithms",
)
def get_optimization_readiness(
    portfolio_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> OptimizationReadinessResponse:
    portfolio = repo.get_portfolio(portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )
    target_alloc = repo.get_target_allocation(portfolio_id, user_id=current_user.id)
    return validate_optimization_readiness(portfolio, target_alloc)
