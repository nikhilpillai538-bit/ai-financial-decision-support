"""
Unit tests for deterministic portfolio valuation calculations.
"""

from decimal import Decimal
import uuid

import pytest

from app.db.models import AssetModel, PortfolioHoldingModel, PortfolioModel
from app.portfolio_valuation import calculate_portfolio_valuation


def _create_mock_portfolio(base_currency: str = "INR") -> PortfolioModel:
    return PortfolioModel(
        id=str(uuid.uuid4()),
        user_id="user-123",
        name="Test Portfolio",
        base_currency=base_currency,
        holdings=[],
    )


def _create_mock_holding(
    portfolio_id: str,
    name: str,
    asset_class: str,
    qty: str,
    avg_price: str,
    current_price: str = None,
    currency: str = "INR",
    symbol: str = None,
) -> PortfolioHoldingModel:
    asset = AssetModel(
        id=str(uuid.uuid4()),
        symbol=symbol,
        name=name,
        asset_class=asset_class,
        currency=currency,
    )
    return PortfolioHoldingModel(
        id=str(uuid.uuid4()),
        portfolio_id=portfolio_id,
        asset_id=asset.id,
        quantity=Decimal(qty),
        average_purchase_price=Decimal(avg_price),
        current_price=Decimal(current_price) if current_price is not None else None,
        asset=asset,
    )


class TestPortfolioValuationEngine:
    """Tests for calculate_portfolio_valuation logic."""

    def test_single_priced_holding(self):
        p = _create_mock_portfolio()
        h1 = _create_mock_holding(
            p.id, "Reliance Industries", "equity", qty="100.00", avg_price="2000.00", current_price="2500.00"
        )
        p.holdings = [h1]

        val = calculate_portfolio_valuation(p)

        assert val.priced_holdings_value == Decimal("250000.00")
        assert val.cost_basis_priced == Decimal("200000.00")
        assert val.cost_basis_all == Decimal("200000.00")
        assert val.unrealized_gain_loss == Decimal("50000.00")
        assert val.unrealized_gain_loss_percentage == Decimal("25.00")
        assert val.total_holdings_count == 1
        assert val.priced_holdings_count == 1
        assert val.unpriced_holdings_count == 0
        assert val.valuation_coverage_percentage == Decimal("100.00")
        assert len(val.asset_class_breakdown) == 1
        assert val.asset_class_breakdown[0].asset_class == "equity"
        assert val.asset_class_breakdown[0].allocation_percentage == Decimal("100.00")

    def test_multiple_holdings_asset_class_breakdown(self):
        p = _create_mock_portfolio()
        # Equity: 10 shares @ current 600 = 6,000
        h_eq = _create_mock_holding(p.id, "Nifty 50 ETF", "equity", "10", "500", "600")
        # Debt: 40 units @ current 100 = 4,000
        h_debt = _create_mock_holding(p.id, "Govt Bond Fund", "debt", "40", "100", "100")
        p.holdings = [h_eq, h_debt]

        val = calculate_portfolio_valuation(p)

        # Total priced = 10,000
        assert val.priced_holdings_value == Decimal("10000.00")
        breakdown = {b.asset_class: b.allocation_percentage for b in val.asset_class_breakdown}
        assert breakdown["equity"] == Decimal("60.00")
        assert breakdown["debt"] == Decimal("40.00")

    def test_unpriced_holding_excluded_from_valuation_denominator(self):
        p = _create_mock_portfolio()
        # Priced: 10 @ 1000 = 10,000
        h1 = _create_mock_holding(p.id, "TCS", "equity", "10", "900", "1000")
        # Unpriced: 5 @ purchase 200, current price None
        h2 = _create_mock_holding(p.id, "Unlisted Startup", "other", "5", "200", None)
        p.holdings = [h1, h2]

        val = calculate_portfolio_valuation(p)

        assert val.priced_holdings_value == Decimal("10000.00")  # h2 not included as 0
        assert val.cost_basis_priced == Decimal("9000.00")
        assert val.cost_basis_all == Decimal("10000.00")  # 9000 + (5*200)
        assert val.priced_holdings_count == 1
        assert val.unpriced_holdings_count == 1
        assert val.valuation_coverage_percentage == Decimal("50.00")
        assert any("unpriced and excluded" in w for w in val.warnings)

    def test_all_unpriced_holdings(self):
        p = _create_mock_portfolio()
        h1 = _create_mock_holding(p.id, "Real Estate Unit", "other", "1", "5000000", None)
        p.holdings = [h1]

        val = calculate_portfolio_valuation(p)

        assert val.priced_holdings_value == Decimal("0.00")
        assert val.priced_holdings_count == 0
        assert val.unpriced_holdings_count == 1
        assert val.valuation_coverage_percentage == Decimal("0.00")
        assert any("market value is unavailable" in w.lower() for w in val.warnings)

    def test_empty_portfolio_valuation(self):
        p = _create_mock_portfolio()
        p.holdings = []

        val = calculate_portfolio_valuation(p)

        assert val.priced_holdings_value == Decimal("0.00")
        assert val.total_holdings_count == 0
        assert val.valuation_coverage_percentage == Decimal("100.00")
        assert any("contains no holdings" in w.lower() for w in val.warnings)

    def test_unrealized_loss_calculation(self):
        p = _create_mock_portfolio()
        # Purchase 100 @ 200 = 20,000. Current 100 @ 150 = 15,000. Loss = -5,000 (-25.00%)
        h = _create_mock_holding(p.id, "Tech Stock", "equity", "100", "200", "150")
        p.holdings = [h]

        val = calculate_portfolio_valuation(p)

        assert val.cost_basis_priced == Decimal("20000.00")
        assert val.priced_holdings_value == Decimal("15000.00")
        assert val.unrealized_gain_loss == Decimal("-5000.00")
        assert val.unrealized_gain_loss_percentage == Decimal("-25.00")

    def test_mixed_currencies_detected_and_flagged(self):
        p = _create_mock_portfolio(base_currency="INR")
        h_inr = _create_mock_holding(p.id, "HDFC Bank", "equity", "10", "1500", "1600", currency="INR")
        h_usd = _create_mock_holding(p.id, "Apple Inc", "equity", "5", "150", "200", currency="USD")
        p.holdings = [h_inr, h_usd]

        val = calculate_portfolio_valuation(p)

        assert val.has_mixed_currencies is True
        assert "INR" in val.currencies_present
        assert "USD" in val.currencies_present
        assert any("mixed currencies" in w.lower() for w in val.warnings)
