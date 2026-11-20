"""
Deterministic Portfolio Drift Detection and Illustrative Rebalancing Analysis for Phase 8.

Features:
- Absolute drift (percentage points) and relative drift against configured target allocations
- Configurable drift threshold detection (e.g. 5.0 percentage points)
- Overweight, underweight, and on-target asset class classification
- Illustrative rebalancing trade generation reconciling to total portfolio market value
- Disclaimers and completeness warnings for unpriced holdings and draft allocations
"""

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List, Optional, Set

from app.db.models import PortfolioModel, TargetAllocationModel
from app.goal_schemas import (
    AssetClassDrift,
    PortfolioDriftResponse,
    RebalanceAnalysisResponse,
    RebalanceTradeItem,
)
from app.portfolio_schemas import quantize_decimal
from app.portfolio_valuation import calculate_portfolio_valuation


def calculate_portfolio_drift(
    portfolio: PortfolioModel,
    target_allocation: Optional[TargetAllocationModel],
    threshold_percentage_points: Decimal = Decimal("5.00"),
) -> PortfolioDriftResponse:
    """Analyze allocation drift between current portfolio holdings and target allocation."""
    valuation = calculate_portfolio_valuation(portfolio)
    total_val = valuation.priced_holdings_value
    has_target = target_allocation is not None
    is_draft = target_allocation.is_draft if target_allocation else False

    warnings: List[str] = list(valuation.warnings)
    if not has_target:
        warnings.append("No target allocation is configured for this portfolio. Drift analysis cannot calculate target variances.")
    elif is_draft:
        warnings.append("The target allocation is marked as an incomplete draft. Comparison variances are provisional.")

    # Current class weights and market values
    current_weights: Dict[str, Decimal] = {}
    current_market_values: Dict[str, Decimal] = {}
    for item in valuation.asset_class_breakdown:
        current_weights[item.asset_class.lower()] = item.allocation_percentage
        current_market_values[item.asset_class.lower()] = item.market_value

    # Target class weights
    target_weights: Dict[str, Decimal] = {}
    if target_allocation and target_allocation.targets:
        target_weights = {k.lower(): Decimal(str(v)) for k, v in target_allocation.targets.items()}

    all_classes: Set[str] = set(current_weights.keys()).union(target_weights.keys())
    asset_drifts: List[AssetClassDrift] = []
    drifted_classes: List[str] = []
    max_drift = Decimal("0.00")

    for ac in sorted(all_classes):
        curr_mv = current_market_values.get(ac, Decimal("0.00"))
        curr_pct = current_weights.get(ac, Decimal("0.00"))
        tgt_pct = target_weights.get(ac)

        abs_drift = None
        rel_drift = None
        exceeds = False

        if tgt_pct is not None:
            raw_diff = curr_pct - tgt_pct
            abs_drift = quantize_decimal(abs(raw_diff), 2)
            if tgt_pct > Decimal("0.00"):
                rel_drift = quantize_decimal((abs_drift / tgt_pct) * Decimal("100"), 2)

            if abs_drift > threshold_percentage_points:
                exceeds = True
                drifted_classes.append(ac)

            if abs_drift > max_drift:
                max_drift = abs_drift

            if raw_diff > Decimal("0.05"):
                status = "overweight"
            elif raw_diff < Decimal("-0.05"):
                status = "underweight"
            else:
                status = "on_target"
        else:
            status = "unspecified_target"

        asset_drifts.append(
            AssetClassDrift(
                asset_class=ac,
                current_market_value=curr_mv,
                current_weight_percentage=curr_pct,
                target_weight_percentage=tgt_pct,
                absolute_drift_percentage_points=abs_drift,
                relative_drift_percentage=rel_drift,
                status=status,
                exceeds_threshold=exceeds,
            )
        )

    is_reliable = (
        has_target
        and not is_draft
        and valuation.valuation_coverage_percentage == Decimal("100.00")
        and total_val > Decimal("0.00")
        and not valuation.has_mixed_currencies
    )

    return PortfolioDriftResponse(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        base_currency=valuation.base_currency,
        total_portfolio_value=total_val,
        drift_threshold_percentage_points=quantize_decimal(threshold_percentage_points, 2),
        portfolio_exceeds_threshold=len(drifted_classes) > 0,
        max_drift_percentage_points=quantize_decimal(max_drift, 2),
        asset_classes=asset_drifts,
        drifted_classes=drifted_classes,
        is_analysis_reliable=is_reliable,
        warnings=warnings,
        as_of_timestamp=datetime.now(timezone.utc),
    )


def calculate_rebalancing_analysis(
    portfolio: PortfolioModel,
    target_allocation: Optional[TargetAllocationModel],
    drift_threshold_percentage_points: Decimal = Decimal("5.00"),
) -> RebalanceAnalysisResponse:
    """Generate illustrative buy/sell trade recommendations to realign portfolio with target allocation."""
    drift_res = calculate_portfolio_drift(portfolio, target_allocation, drift_threshold_percentage_points)
    total_val = drift_res.total_portfolio_value
    warnings: List[str] = list(drift_res.warnings)

    if not target_allocation:
        raise ValueError("Cannot calculate rebalancing analysis: no target allocation configured for this portfolio.")
    if target_allocation.is_draft:
        warnings.append("Rebalancing analysis is based on an incomplete draft target allocation.")

    if total_val <= Decimal("0.00"):
        warnings.append("Portfolio has no priced holdings. Rebalancing trade amounts cannot be calculated.")
        return RebalanceAnalysisResponse(
            portfolio_id=portfolio.id,
            portfolio_name=portfolio.name,
            base_currency=drift_res.base_currency,
            total_portfolio_value=Decimal("0.00"),
            drift_threshold_percentage_points=drift_res.drift_threshold_percentage_points,
            trades=[],
            total_buy_amount=Decimal("0.00"),
            total_sell_amount=Decimal("0.00"),
            reconciliation_difference=Decimal("0.00"),
            is_rebalancing_recommended=False,
            disclaimers=[
                "Rebalancing plan is illustrative and does not constitute trading instructions or execution.",
                "Estimated values exclude taxes, transaction fees, bid-ask spread, and liquidity constraints.",
            ],
            warnings=warnings,
        )

    trades: List[RebalanceTradeItem] = []
    total_buy = Decimal("0.00")
    total_sell = Decimal("0.00")
    sum_target_val = Decimal("0.00")

    for item in drift_res.asset_classes:
        tgt_pct = item.target_weight_percentage or Decimal("0.00")
        curr_pct = item.current_weight_percentage
        curr_mv = item.current_market_value

        tgt_mv = quantize_decimal((tgt_pct / Decimal("100.00")) * total_val, 2)
        sum_target_val += tgt_mv

        trade_amt = quantize_decimal(tgt_mv - curr_mv, 2)
        w_delta = quantize_decimal(tgt_pct - curr_pct, 2)

        if trade_amt > Decimal("0.50"):
            action = "BUY"
            total_buy += abs(trade_amt)
        elif trade_amt < Decimal("-0.50"):
            action = "SELL"
            total_sell += abs(trade_amt)
        else:
            action = "HOLD"

        trades.append(
            RebalanceTradeItem(
                asset_class=item.asset_class,
                current_weight_percentage=curr_pct,
                target_weight_percentage=tgt_pct,
                current_market_value=curr_mv,
                target_market_value=tgt_mv,
                weight_delta_percentage_points=w_delta,
                action=action,
                trade_amount=abs(trade_amt),
            )
        )

    reconciliation_diff = quantize_decimal(abs(sum_target_val - total_val), 2)
    is_rec = drift_res.portfolio_exceeds_threshold

    disclaimers = [
        "Rebalancing analysis provides deterministic numerical estimates to illustrate target realignment.",
        "Trade recommendations do NOT trigger execution and are not linked to any brokerage.",
        "Calculations exclude capital gains taxes, brokerage commissions, market impact, and lot sizing.",
    ]

    return RebalanceAnalysisResponse(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        base_currency=drift_res.base_currency,
        total_portfolio_value=total_val,
        drift_threshold_percentage_points=drift_res.drift_threshold_percentage_points,
        trades=trades,
        total_buy_amount=quantize_decimal(total_buy, 2),
        total_sell_amount=quantize_decimal(total_sell, 2),
        reconciliation_difference=reconciliation_diff,
        is_rebalancing_recommended=is_rec,
        disclaimers=disclaimers,
        warnings=warnings,
    )
