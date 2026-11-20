"""
Deterministic portfolio valuation engine for Phase 6.

Calculates exact market values, cost basis, unrealized gain/loss,
and asset-class allocation weights using Python Decimal arithmetic.
"""

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Set

from app.db.models import PortfolioHoldingModel, PortfolioModel
from app.portfolio_schemas import (
    AssetClassValuation,
    HoldingValuationItem,
    PortfolioValuationResponse,
    quantize_decimal,
)


def calculate_portfolio_valuation(portfolio: PortfolioModel) -> PortfolioValuationResponse:
    """Calculate deterministic portfolio valuation from stored holdings.

    All monetary arithmetic uses Decimal with ROUND_HALF_UP.
    Unpriced holdings remain explicitly unpriced (never defaulted to 0).
    """
    holdings: List[PortfolioHoldingModel] = portfolio.holdings or []
    base_currency = (portfolio.base_currency or "INR").upper()

    total_holdings_count = len(holdings)
    priced_holdings_count = 0
    unpriced_holdings_count = 0

    priced_holdings_value = Decimal("0.00")
    cost_basis_priced = Decimal("0.00")
    cost_basis_all = Decimal("0.00")

    currencies_present: Set[str] = set()
    asset_class_values: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    asset_class_counts: defaultdict[str, int] = defaultdict(int)

    items: List[HoldingValuationItem] = []
    warnings: List[str] = []
    assumptions: List[str] = [
        "Asset prices are user-supplied and not guaranteed to reflect real-time live market quotes.",
        "Asset allocation percentages are calculated strictly using the total value of priced holdings as the denominator.",
    ]

    for holding in holdings:
        asset = holding.asset
        asset_class = (asset.asset_class if asset else "other").lower()
        asset_currency = ((asset.currency if (asset and asset.currency) else base_currency) or "USD").upper()
        currencies_present.add(asset_currency)

        qty = holding.quantity or Decimal("0")
        purchase_price = holding.average_purchase_price or Decimal("0")
        cost_basis = quantize_decimal(qty * purchase_price, 2)
        cost_basis_all += cost_basis

        is_priced = holding.current_price is not None
        if is_priced:
            priced_holdings_count += 1
            current_price = holding.current_price
            market_val = quantize_decimal(qty * current_price, 2)
            priced_holdings_value += market_val
            cost_basis_priced += cost_basis

            gain_loss = quantize_decimal(market_val - cost_basis, 2)
            if cost_basis > Decimal("0"):
                gain_loss_pct = quantize_decimal(
                    (gain_loss / cost_basis) * Decimal("100"), 2
                )
            else:
                gain_loss_pct = Decimal("0.00")

            asset_class_values[asset_class] += market_val
            asset_class_counts[asset_class] += 1
        else:
            unpriced_holdings_count += 1
            market_val = None
            gain_loss = None
            gain_loss_pct = None

        items.append(
            HoldingValuationItem(
                holding_id=holding.id,
                asset_id=holding.asset_id,
                symbol=asset.symbol if asset else None,
                name=asset.name if asset else "Unknown Instrument",
                asset_class=asset_class,
                currency=asset_currency,
                quantity=qty,
                average_purchase_price=purchase_price,
                current_price=holding.current_price,
                cost_basis=cost_basis,
                market_value=market_val,
                unrealized_gain_loss=gain_loss,
                unrealized_gain_loss_percentage=gain_loss_pct,
                is_priced=is_priced,
            )
        )

    # Coverage percentage
    if total_holdings_count > 0:
        coverage_pct = quantize_decimal(
            (Decimal(priced_holdings_count) / Decimal(total_holdings_count)) * Decimal("100"), 2
        )
    else:
        coverage_pct = Decimal("100.00")

    # Mixed currency detection
    has_mixed = any(c != base_currency for c in currencies_present)
    if has_mixed:
        warnings.append(
            f"Portfolio contains mixed currencies ({sorted(list(currencies_present))}) differing from "
            f"base currency '{base_currency}'. Mixed-currency consolidation without exchange rates is not performed."
        )

    # Missing price warnings
    if unpriced_holdings_count > 0:
        warnings.append(
            f"{unpriced_holdings_count} holding(s) are currently unpriced and excluded from the "
            "market valuation total and allocation percentage calculations."
        )

    if total_holdings_count == 0:
        warnings.append("Portfolio contains no holdings. Valuation and allocation cannot be computed.")
    elif priced_holdings_count == 0:
        warnings.append("None of the holdings in this portfolio have user-supplied prices. Total market value is unavailable.")

    # Total unrealized gain/loss
    if priced_holdings_count > 0:
        total_unrealized_gain_loss = quantize_decimal(priced_holdings_value - cost_basis_priced, 2)
        if cost_basis_priced > Decimal("0"):
            total_unrealized_gain_loss_pct = quantize_decimal(
                (total_unrealized_gain_loss / cost_basis_priced) * Decimal("100"), 2
            )
        else:
            total_unrealized_gain_loss_pct = Decimal("0.00")
    else:
        total_unrealized_gain_loss = None
        total_unrealized_gain_loss_pct = None

    # Asset class breakdown
    breakdown: List[AssetClassValuation] = []
    for ac, val in sorted(asset_class_values.items()):
        if priced_holdings_value > Decimal("0"):
            alloc_pct = quantize_decimal((val / priced_holdings_value) * Decimal("100"), 2)
        else:
            alloc_pct = Decimal("0.00")

        breakdown.append(
            AssetClassValuation(
                asset_class=ac,
                market_value=val,
                allocation_percentage=alloc_pct,
                holdings_count=asset_class_counts[ac],
            )
        )

    return PortfolioValuationResponse(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        base_currency=base_currency,
        valuation_as_of=datetime.now(timezone.utc),
        priced_holdings_value=priced_holdings_value,
        cost_basis_priced=cost_basis_priced,
        cost_basis_all=cost_basis_all,
        unrealized_gain_loss=total_unrealized_gain_loss,
        unrealized_gain_loss_percentage=total_unrealized_gain_loss_pct,
        asset_class_breakdown=breakdown,
        holdings=items,
        total_holdings_count=total_holdings_count,
        priced_holdings_count=priced_holdings_count,
        unpriced_holdings_count=unpriced_holdings_count,
        valuation_coverage_percentage=coverage_pct,
        has_mixed_currencies=has_mixed,
        currencies_present=sorted(list(currencies_present)),
        assumptions=assumptions,
        warnings=warnings,
    )
