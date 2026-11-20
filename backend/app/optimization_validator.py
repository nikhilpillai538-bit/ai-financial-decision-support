"""
Optimization readiness validation service for Phase 6.

Serves as the rigorous boundary between Phase 6 data modeling and Phase 7 algorithmic optimization.
Evaluates portfolio data completeness, pricing, currency uniformity, and target allocation validity.
"""

from decimal import Decimal
from typing import List, Optional

from app.db.models import PortfolioModel, TargetAllocationModel
from app.portfolio_schemas import (
    CheckItem,
    OptimizationReadinessResponse,
)
from app.portfolio_valuation import calculate_portfolio_valuation


def validate_optimization_readiness(
    portfolio: PortfolioModel,
    target_allocation: Optional[TargetAllocationModel],
) -> OptimizationReadinessResponse:
    """Validate whether a portfolio meets all data integrity criteria for Phase 7 optimization algorithms."""
    valuation = calculate_portfolio_valuation(portfolio)
    checks: List[CheckItem] = []
    blockers: List[str] = []
    warnings: List[str] = []

    # 1. Holdings count check (must have at least 2 distinct holdings for meaningful asset allocation)
    total_holdings = valuation.total_holdings_count
    if total_holdings >= 2:
        checks.append(
            CheckItem(
                name="minimum_holdings_count",
                passed=True,
                details=f"Portfolio contains {total_holdings} holdings (minimum 2 required for diversification).",
            )
        )
    elif total_holdings == 1:
        checks.append(
            CheckItem(
                name="minimum_holdings_count",
                passed=True,
                details="Portfolio contains only 1 holding. Diversification optimization will have limited effect.",
            )
        )
        warnings.append("Portfolio contains only 1 holding. Minimum 2 recommended for portfolio rebalancing.")
    else:
        checks.append(
            CheckItem(
                name="minimum_holdings_count",
                passed=False,
                details="Portfolio contains 0 holdings.",
            )
        )
        blockers.append("Portfolio contains no holdings. At least 1 priced instrument is required for optimization.")

    # 2. Complete price coverage check
    unpriced_count = valuation.unpriced_holdings_count
    if total_holdings > 0 and unpriced_count == 0:
        checks.append(
            CheckItem(
                name="price_coverage_complete",
                passed=True,
                details="100% of holdings have valid user-supplied current prices.",
            )
        )
    else:
        checks.append(
            CheckItem(
                name="price_coverage_complete",
                passed=False,
                details=f"{unpriced_count} of {total_holdings} holdings are unpriced.",
            )
        )
        blockers.append(
            f"{unpriced_count} holding(s) are missing user-supplied current prices. "
            "All holdings must be priced before portfolio optimization can be executed."
        )

    # 3. Positive portfolio market value
    if valuation.priced_holdings_value > Decimal("0.00"):
        checks.append(
            CheckItem(
                name="positive_market_value",
                passed=True,
                details=f"Total priced market value is {valuation.base_currency} {valuation.priced_holdings_value}.",
            )
        )
    else:
        checks.append(
            CheckItem(
                name="positive_market_value",
                passed=False,
                details="Total priced market value is zero.",
            )
        )
        blockers.append("Total portfolio market value must be positive to perform asset weight optimization.")

    # 4. Currency uniformity (no mixed currencies without FX conversion)
    if not valuation.has_mixed_currencies:
        checks.append(
            CheckItem(
                name="single_currency_uniformity",
                passed=True,
                details=f"All holdings are denominated in base currency '{valuation.base_currency}'.",
            )
        )
    else:
        checks.append(
            CheckItem(
                name="single_currency_uniformity",
                passed=False,
                details=f"Holdings span multiple currencies: {valuation.currencies_present}.",
            )
        )
        blockers.append(
            f"Holdings have mixed currencies ({valuation.currencies_present}). "
            "Optimization requires all assets to be denominated in the portfolio base currency."
        )

    # 5. Target allocation exists and is not draft
    if target_allocation is None:
        checks.append(
            CheckItem(
                name="target_allocation_configured",
                passed=False,
                details="No target allocation record found for this portfolio.",
            )
        )
        blockers.append(
            "Portfolio lacks a target asset allocation. Configure target allocation weights via PUT /portfolios/{id}/allocation-target."
        )
    elif target_allocation.is_draft:
        checks.append(
            CheckItem(
                name="target_allocation_configured",
                passed=False,
                details="Target allocation is marked as an incomplete draft.",
            )
        )
        blockers.append(
            "Target allocation is currently saved as an incomplete draft. Finalize target weights to sum to 100%."
        )
    else:
        # Check sum of targets
        target_sum = sum(Decimal(str(v)) for v in target_allocation.targets.values())
        if abs(target_sum - Decimal("100.00")) <= Decimal("0.05"):
            checks.append(
                CheckItem(
                    name="target_allocation_configured",
                    passed=True,
                    details=f"Target allocation is validated and sums to {target_sum:.2f}%.",
                )
            )
        else:
            checks.append(
                CheckItem(
                    name="target_allocation_configured",
                    passed=False,
                    details=f"Target allocation sum is {target_sum:.2f}% (must equal 100.00%).",
                )
            )
            blockers.append(f"Target allocation sum is {target_sum:.2f}% rather than 100.00%.")

    # 6. Instrument metadata check
    missing_metadata = False
    for item in valuation.holdings:
        if not item.name or not item.asset_class:
            missing_metadata = True
            break
    if not missing_metadata and total_holdings > 0:
        checks.append(
            CheckItem(
                name="instrument_metadata_valid",
                passed=True,
                details="All holdings are linked to valid instruments with known asset classes.",
            )
        )
    elif missing_metadata:
        checks.append(
            CheckItem(
                name="instrument_metadata_valid",
                passed=False,
                details="One or more holdings reference instruments with incomplete metadata.",
            )
        )
        blockers.append("Holdings contain instruments with missing names or unassigned asset classes.")

    # Final readiness determination
    is_ready = len(blockers) == 0
    if is_ready:
        status = "ready"
    elif len(blockers) <= 2 and total_holdings > 0:
        status = "partially_ready"
    else:
        status = "not_ready"

    return OptimizationReadinessResponse(
        portfolio_id=portfolio.id,
        is_ready_for_optimization=is_ready,
        readiness_status=status,
        checks=checks,
        blockers=blockers,
        warnings=warnings,
    )
