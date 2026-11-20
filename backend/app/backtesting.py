"""
Historical Portfolio Backtesting Engine for Phase 13.

Implements rigorous historical performance replay with:
- Strict prevention of look-ahead bias (only information known at time t is used)
- Configurable periodic rebalancing (none, monthly, quarterly, annual, drift threshold)
- Explicit transaction cost modeling (basis points on rebalance turnover)
- Handling of non-overlapping holidays and data-gap validation
- Comparative tracking against user-selected or equal-weight benchmarks
- Annualized return (CAGR), volatility, max drawdown, Sharpe, and Calmar ratios
"""

from datetime import date as DateType, datetime
from decimal import Decimal
import math
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from app.db.models import HistoricalPriceModel, PortfolioModel
from app.portfolio_schemas import quantize_decimal
from app.simulation_schemas import (
    BacktestBenchmarkSummary,
    BacktestEquityPoint,
    BacktestRequest,
    BacktestResponse,
    RebalanceEventItem,
)


def run_portfolio_backtest(
    request: BacktestRequest,
    price_records: List[HistoricalPriceModel],
    portfolio: Optional[PortfolioModel] = None,
) -> BacktestResponse:
    """Execute a historical portfolio backtest across the provided price records."""
    warnings: List[str] = []
    assumptions: List[str] = [
        "Prices used are adjusted closing prices (accounting for historical splits and standard corporate actions).",
        "Dividends are assumed reinvested on the ex-dividend date as reflected in adjusted close series.",
        "Transactions are executed at close of trading with zero latency or market impact.",
        f"Transaction costs modeled at {float(request.fee_bps):.1f} basis points on turnover.",
        "Taxes (capital gains / STT) are excluded from the backtest simulation.",
    ]
    disclaimers: List[str] = [
        "Historical backtested performance does not guarantee future financial results.",
        "Hypothetical backtests are subject to survivorship and asset selection bias.",
    ]

    if not price_records:
        raise ValueError(
            "No historical price records are available for backtesting. "
            "Please upload or fetch historical price data first."
        )

    # 1. Resolve Symbols & Target Weights
    target_weights: Dict[str, float] = {}

    if request.weights:
        for s, w in request.weights.items():
            sym = s.strip().upper()
            target_weights[sym] = float(w)
    elif portfolio is not None and portfolio.holdings:
        # Derive weights from current portfolio holdings
        total_holdings_val = Decimal("0.00")
        holding_vals: Dict[str, Decimal] = {}
        for h in portfolio.holdings:
            sym = h.asset.symbol.upper() if h.asset else "UNKNOWN"
            price = h.current_price
            if price is not None and price > 0:
                val = h.quantity * price
                holding_vals[sym] = holding_vals.get(sym, Decimal("0.00")) + val
                total_holdings_val += val
            else:
                warnings.append(f"Holding '{sym}' has no price recorded; excluded from backtest target weights.")

        if total_holdings_val <= 0:
            raise ValueError(f"Portfolio '{portfolio.name}' has no priced holdings to determine backtest weights.")

        for sym, val in holding_vals.items():
            target_weights[sym] = float(val / total_holdings_val)

    elif request.symbols:
        clean_syms = [s.strip().upper() for s in request.symbols]
        eq_weight = 1.0 / len(clean_syms) if clean_syms else 0.0
        for s in clean_syms:
            target_weights[s] = eq_weight

    else:
        raise ValueError("Either weights, portfolio_id, or a list of symbols must be provided.")

    if len(target_weights) < 1:
        raise ValueError("At least 1 asset is required for historical backtesting.")

    # Normalize weights to exactly 1.0
    weight_sum = sum(target_weights.values())
    if abs(weight_sum - 1.0) > 1e-3:
        if weight_sum <= 0:
            raise ValueError("Sum of target weights must be greater than zero.")
        for s in target_weights:
            target_weights[s] /= weight_sum
        warnings.append(f"Target weights summed to {weight_sum:.4f}; automatically normalized to 100%.")

    symbols_list = list(target_weights.keys())

    # 2. Build and Align Historical Price DataFrame
    raw_data = [
        {"date": r.date, "symbol": r.symbol.upper(), "price": float(r.adjusted_close)}
        for r in price_records
    ]
    df_raw = pd.DataFrame(raw_data)

    # Check for missing required symbols in dataset
    available_symbols = set(df_raw["symbol"].unique())
    missing_symbols = [s for s in symbols_list if s not in available_symbols]
    if missing_symbols:
        raise ValueError(
            f"Historical price data is missing for required instruments: {missing_symbols}. "
            f"Available symbols in database: {sorted(list(available_symbols))}."
        )

    # Check benchmark availability
    benchmark_sym: Optional[str] = None
    if request.benchmark_symbol:
        b_sym = request.benchmark_symbol.strip().upper()
        if b_sym in available_symbols:
            benchmark_sym = b_sym
        else:
            warnings.append(
                f"Requested benchmark symbol '{b_sym}' not found in historical price database. "
                "Backtest will proceed without comparative benchmark."
            )

    all_needed_symbols = list(set(symbols_list + ([benchmark_sym] if benchmark_sym else [])))
    df_needed = df_raw[df_raw["symbol"].isin(all_needed_symbols)]

    # Filter date range if requested
    if request.start_date:
        df_needed = df_needed[df_needed["date"] >= request.start_date]
    if request.end_date:
        df_needed = df_needed[df_needed["date"] <= request.end_date]

    if df_needed.empty:
        raise ValueError("No historical price observations match the selected date filter.")

    pivoted = df_needed.pivot_table(index="date", columns="symbol", values="price", aggfunc="last")

    # Verify each asset has at least 1 observation in range
    for s in symbols_list:
        if s not in pivoted.columns or pivoted[s].dropna().empty:
            raise ValueError(f"Instrument '{s}' has no price data in the selected backtest date range.")

    # Forward fill gaps up to 1 day for non-overlapping exchange holidays
    pivoted = pivoted.ffill(limit=1).dropna(subset=symbols_list)

    if len(pivoted) < 5:
        raise ValueError(
            f"Backtest dataset has insufficient aligned trading days ({len(pivoted)}). "
            "At least 5 overlapping trading dates are required."
        )

    dates = list(pivoted.index)
    start_dt_str = str(dates[0])
    end_dt_str = str(dates[-1])
    trading_days = len(dates)

    # 3. Simulate Rebalancing and Backtest Over Time
    initial_cap = float(request.initial_value)
    current_portfolio_val = initial_cap
    fee_rate = float(request.fee_bps) / 10000.0

    # Inception: Allocate initial capital
    quantities: Dict[str, float] = {}
    for s in symbols_list:
        p0 = pivoted.loc[dates[0], s]
        quantities[s] = (initial_cap * target_weights[s]) / p0

    equity_curve: List[BacktestEquityPoint] = []
    rebalance_events: List[RebalanceEventItem] = []
    total_fees_paid = 0.0
    peak_val = current_portfolio_val

    # Benchmark tracking initialization
    b_initial_price = pivoted.loc[dates[0], benchmark_sym] if benchmark_sym else None
    benchmark_values: List[float] = []

    # Frequency check variables
    prev_date: Optional[DateType] = None

    rebal_freq = request.rebalance_frequency.strip().lower()

    for idx, dt in enumerate(dates):
        # 1. Compute pre-rebalance asset values on day dt
        asset_values: Dict[str, float] = {}
        for s in symbols_list:
            price = pivoted.loc[dt, s]
            asset_values[s] = quantities[s] * price

        pre_rebal_val = sum(asset_values.values())
        pre_weights = {s: asset_values[s] / pre_rebal_val if pre_rebal_val > 0 else 0.0 for s in symbols_list}

        # 2. Check if rebalancing triggers on date dt (skip t=0)
        trigger_rebalance = False

        if idx > 0 and prev_date is not None:
            if rebal_freq == "monthly" and dt.month != prev_date.month:
                trigger_rebalance = True
            elif rebal_freq == "quarterly" and dt.month != prev_date.month and dt.month in {1, 4, 7, 10}:
                trigger_rebalance = True
            elif rebal_freq == "annual" and dt.year != prev_date.year:
                trigger_rebalance = True
            elif rebal_freq == "drift_5pct":
                max_drift = max(abs(pre_weights[s] - target_weights[s]) for s in symbols_list)
                if max_drift >= 0.05:
                    trigger_rebalance = True

        # 3. Execute Rebalance if triggered
        if trigger_rebalance:
            turnover = 0.0
            for s in symbols_list:
                desired_val = pre_rebal_val * target_weights[s]
                turnover += abs(desired_val - asset_values[s])
            turnover /= 2.0  # Sell volume equals buy volume

            tx_cost = turnover * fee_rate
            total_fees_paid += tx_cost
            post_rebal_val = pre_rebal_val - tx_cost

            # Reallocate quantities to target weights
            for s in symbols_list:
                price = pivoted.loc[dt, s]
                quantities[s] = (post_rebal_val * target_weights[s]) / price

            current_portfolio_val = post_rebal_val

            rebalance_events.append(
                RebalanceEventItem(
                    date=str(dt),
                    portfolio_value_pre=quantize_decimal(Decimal(str(pre_rebal_val)), places=2),
                    turnover_value=quantize_decimal(Decimal(str(turnover)), places=2),
                    transaction_cost=quantize_decimal(Decimal(str(tx_cost)), places=2),
                    pre_weights={s: quantize_decimal(Decimal(str(pre_weights[s] * 100)), places=2) for s in symbols_list},
                    post_weights={s: quantize_decimal(Decimal(str(target_weights[s] * 100)), places=2) for s in symbols_list},
                )
            )
        else:
            current_portfolio_val = pre_rebal_val

        # 4. Drawdown & Returns
        if current_portfolio_val > peak_val:
            peak_val = current_portfolio_val
        drawdown_pct = ((peak_val - current_portfolio_val) / peak_val) * 100.0 if peak_val > 0 else 0.0
        cum_ret_pct = ((current_portfolio_val - initial_cap) / initial_cap) * 100.0

        # Benchmark valuation
        b_val: Optional[Decimal] = None
        b_ret: Optional[Decimal] = None
        if benchmark_sym and b_initial_price and not math.isnan(pivoted.loc[dt, benchmark_sym]):
            cur_b_price = pivoted.loc[dt, benchmark_sym]
            b_val_float = initial_cap * (cur_b_price / b_initial_price)
            benchmark_values.append(b_val_float)
            b_val = quantize_decimal(Decimal(str(b_val_float)), places=2)
            b_ret = quantize_decimal(Decimal(str(((b_val_float - initial_cap) / initial_cap) * 100.0)), places=2)

        equity_curve.append(
            BacktestEquityPoint(
                date=str(dt),
                portfolio_value=quantize_decimal(Decimal(str(current_portfolio_val)), places=2),
                portfolio_return_pct=quantize_decimal(Decimal(str(cum_ret_pct)), places=2),
                benchmark_value=b_val,
                benchmark_return_pct=b_ret,
                drawdown_pct=quantize_decimal(Decimal(str(drawdown_pct)), places=2),
            )
        )

        prev_date = dt

    # 4. Calculate Aggregate Statistics
    final_val = current_portfolio_val
    total_cum_ret_pct = ((final_val - initial_cap) / initial_cap) * 100.0

    # Calendar duration in years
    cal_days = (dates[-1] - dates[0]).days
    cal_years = max(cal_days / 365.25, trading_days / 252.0)

    # CAGR: (V_final / V_initial) ** (1 / years) - 1
    if cal_years >= 0.08:  # At least 1 month
        if final_val > 0:
            cagr = (math.pow(final_val / initial_cap, 1.0 / cal_years) - 1.0) * 100.0
        else:
            cagr = -100.0
    else:
        # Simple annualized return for short periods
        cagr = (total_cum_ret_pct / trading_days) * 252.0

    # Daily returns series
    vals = [float(p.portfolio_value) for p in equity_curve]
    daily_returns = [
        (vals[i] - vals[i - 1]) / vals[i - 1] for i in range(1, len(vals)) if vals[i - 1] > 0
    ]
    if len(daily_returns) > 1:
        daily_std = float(np.std(daily_returns, ddof=1))
        ann_vol_pct = daily_std * math.sqrt(252.0) * 100.0
    else:
        ann_vol_pct = 0.0

    # Max Drawdown
    all_drawdowns = [float(p.drawdown_pct) for p in equity_curve]
    max_dd_pct = max(all_drawdowns) if all_drawdowns else 0.0

    # Sharpe Ratio: (CAGR - Rf) / Annualized Volatility
    rf = float(request.risk_free_rate_pct)
    if ann_vol_pct > 1e-4:
        sharpe = (cagr - rf) / ann_vol_pct
    else:
        sharpe = 0.0

    # Calmar Ratio: CAGR / Max Drawdown
    if max_dd_pct > 1e-4:
        calmar = cagr / max_dd_pct
    else:
        calmar = 0.0

    # Benchmark Summary
    b_summary: Optional[BacktestBenchmarkSummary] = None
    if benchmark_sym and len(benchmark_values) == len(dates):
        b_final = benchmark_values[-1]
        b_cum_ret = ((b_final - initial_cap) / initial_cap) * 100.0
        b_cagr = (
            (math.pow(b_final / initial_cap, 1.0 / cal_years) - 1.0) * 100.0
            if cal_years >= 0.08 and b_final > 0
            else (b_cum_ret / trading_days) * 252.0
        )
        b_daily_rets = [
            (benchmark_values[i] - benchmark_values[i - 1]) / benchmark_values[i - 1]
            for i in range(1, len(benchmark_values))
            if benchmark_values[i - 1] > 0
        ]
        b_vol = float(np.std(b_daily_rets, ddof=1)) * math.sqrt(252.0) * 100.0 if len(b_daily_rets) > 1 else 0.0
        b_peaks = [initial_cap]
        b_dds = [0.0]
        for bv in benchmark_values:
            if bv > b_peaks[-1]:
                b_peaks.append(bv)
            else:
                b_peaks.append(b_peaks[-1])
            b_dds.append(((b_peaks[-1] - bv) / b_peaks[-1]) * 100.0)
        b_max_dd = max(b_dds)
        b_sharpe = (b_cagr - rf) / b_vol if b_vol > 1e-4 else 0.0

        b_summary = BacktestBenchmarkSummary(
            symbol=benchmark_sym,
            final_value=quantize_decimal(Decimal(str(b_final)), places=2),
            cumulative_return_pct=quantize_decimal(Decimal(str(b_cum_ret)), places=2),
            annualized_return_cagr_pct=quantize_decimal(Decimal(str(b_cagr)), places=2),
            annualized_volatility_pct=quantize_decimal(Decimal(str(b_vol)), places=2),
            sharpe_ratio=quantize_decimal(Decimal(str(b_sharpe)), places=2),
            max_drawdown_pct=quantize_decimal(Decimal(str(b_max_dd)), places=2),
        )

    clean_warnings = list(dict.fromkeys(warnings))

    return BacktestResponse(
        symbols=symbols_list,
        start_date=start_dt_str,
        end_date=end_dt_str,
        trading_days=trading_days,
        initial_value=quantize_decimal(Decimal(str(initial_cap)), places=2),
        final_value=quantize_decimal(Decimal(str(final_val)), places=2),
        cumulative_return_pct=quantize_decimal(Decimal(str(total_cum_ret_pct)), places=2),
        annualized_return_cagr_pct=quantize_decimal(Decimal(str(cagr)), places=2),
        annualized_volatility_pct=quantize_decimal(Decimal(str(ann_vol_pct)), places=2),
        sharpe_ratio=quantize_decimal(Decimal(str(sharpe)), places=2),
        max_drawdown_pct=quantize_decimal(Decimal(str(max_dd_pct)), places=2),
        calmar_ratio=quantize_decimal(Decimal(str(calmar)), places=2),
        total_transaction_costs=quantize_decimal(Decimal(str(total_fees_paid)), places=2),
        rebalance_count=len(rebalance_events),
        benchmark_summary=b_summary,
        equity_curve=equity_curve,
        rebalance_events=rebalance_events,
        warnings=clean_warnings,
        assumptions=assumptions,
        disclaimers=disclaimers,
    )
