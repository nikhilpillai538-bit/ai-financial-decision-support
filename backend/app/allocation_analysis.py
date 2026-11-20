"""
Deterministic asset allocation analysis engine for Phase 6.

Compares current asset-class allocation weights with the user's target allocation.
Computes percentage-point variances, identifies overweight and underweight classes,
and flags data completeness issues.
"""

from decimal import Decimal
from typing import Dict, List, Optional, Set

from app.db.models import PortfolioModel, TargetAllocationModel
from app.portfolio_schemas import (
    AllocationAnalysisResponse,
    AssetClassComparison,
    quantize_decimal,
)
from app.portfolio_valuation import calculate_portfolio_valuation


def calculate_allocation_analysis(
    portfolio: PortfolioModel,
    target_allocation: Optional[TargetAllocationModel],
) -> AllocationAnalysisResponse:
    """Analyze variance between current holdings allocation and configured target allocation."""
    valuation = calculate_portfolio_valuation(portfolio)

    current_weights: Dict[str, Decimal] = {}
    current_market_values: Dict[str, Decimal] = {}
    for item in valuation.asset_class_breakdown:
        current_weights[item.asset_class] = item.allocation_percentage
        current_market_values[item.asset_class] = item.market_value

    has_target = target_allocation is not None
    is_draft = target_allocation.is_draft if target_allocation else False
    target_weights: Dict[str, Decimal] = {}

    warnings: List[str] = list(valuation.warnings)

    if not has_target:
        warnings.append("No target allocation has been set for this portfolio. Variance comparison is unavailable.")
    elif is_draft:
        warnings.append("The target allocation is marked as an incomplete draft. Comparison results are provisional.")
        target_weights = {k: Decimal(str(v)) for k, v in target_allocation.targets.items()}
    else:
        target_weights = {k: Decimal(str(v)) for k, v in target_allocation.targets.items()}

    all_classes: Set[str] = set(current_weights.keys()).union(target_weights.keys())

    comparisons: List[AssetClassComparison] = []
    overweight_classes: List[str] = []
    underweight_classes: List[str] = []
    unspecified_target_classes: List[str] = []
    missing_holding_classes: List[str] = []

    has_priced_assets = valuation.priced_holdings_value > Decimal("0")

    for ac in sorted(all_classes):
        curr_mv = current_market_values.get(ac, Decimal("0.00"))
        curr_pct = current_weights.get(ac, Decimal("0.00"))
        tgt_pct = target_weights.get(ac)

        if not has_priced_assets:
            status = "no_holdings"
            diff = None
        elif tgt_pct is None:
            diff = None
            status = "unspecified_target"
            unspecified_target_classes.append(ac)
        else:
            diff = quantize_decimal(curr_pct - tgt_pct, 2)
            if curr_mv == Decimal("0.00") and tgt_pct > Decimal("0.00"):
                missing_holding_classes.append(ac)

            if diff > Decimal("0.05"):
                status = "overweight"
                overweight_classes.append(ac)
            elif diff < Decimal("-0.05"):
                status = "underweight"
                underweight_classes.append(ac)
            else:
                status = "on_target"

        comparisons.append(
            AssetClassComparison(
                asset_class=ac,
                current_market_value=curr_mv,
                current_percentage=curr_pct,
                target_percentage=tgt_pct,
                difference_percentage_points=diff,
                status=status,
            )
        )

    is_reliable = (
        has_target
        and not is_draft
        and valuation.valuation_coverage_percentage == Decimal("100.00")
        and has_priced_assets
        and not valuation.has_mixed_currencies
    )

    if not is_reliable and has_target:
        if valuation.valuation_coverage_percentage < Decimal("100.00"):
            warnings.append(
                f"Valuation coverage is {valuation.valuation_coverage_percentage}%. "
                "Unpriced holdings cause the allocation analysis to be partial."
            )
        if valuation.has_mixed_currencies:
            warnings.append(
                "Holdings in non-base currencies prevent an exact consolidated allocation comparison."
            )

    return AllocationAnalysisResponse(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        base_currency=valuation.base_currency,
        has_target_allocation=has_target,
        is_target_draft=is_draft,
        valuation_coverage_percentage=valuation.valuation_coverage_percentage,
        comparisons=comparisons,
        overweight_classes=overweight_classes,
        underweight_classes=underweight_classes,
        unspecified_target_classes=unspecified_target_classes,
        missing_holding_classes=missing_holding_classes,
        is_analysis_reliable=is_reliable,
        warnings=warnings,
    )
