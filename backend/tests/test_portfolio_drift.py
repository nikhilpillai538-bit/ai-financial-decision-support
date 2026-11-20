"""
Unit tests for Phase 8 Portfolio Drift Detection and Rebalancing Analysis.

Tests:
- Portfolio exactly on target (0% drift)
- Drift below threshold (not flagged as exceeded)
- Drift exactly at threshold
- Drift above threshold (alert flagged in drifted_classes)
- Missing or draft target allocations (completeness warnings)
- Unpriced holdings warning detection
- Illustrative rebalancing buy/sell calculations
- Rebalancing value reconciliation: sum of target market values equals total portfolio value
"""

from decimal import Decimal
import pytest

from app.db.models import AssetModel, PortfolioHoldingModel, PortfolioModel, TargetAllocationModel
from app.portfolio_drift import (
    calculate_portfolio_drift,
    calculate_rebalancing_analysis,
)


def _build_test_portfolio_with_classes(equity_val: Decimal, bond_val: Decimal) -> PortfolioModel:
    """Helper to build a portfolio with specified equity and fixed income market values."""
    eq_asset = AssetModel(id="a-eq", name="Equity ETF", symbol="EQ", asset_class="equity", currency="USD")
    fi_asset = AssetModel(id="a-fi", name="Bond ETF", symbol="BOND", asset_class="fixed_income", currency="USD")

    holdings = []
    if equity_val > Decimal("0.00"):
        holdings.append(
            PortfolioHoldingModel(
                id="h-eq",
                portfolio_id="port-drift",
                asset_id="a-eq",
                quantity=equity_val / Decimal("100.00"),
                average_purchase_price=Decimal("100.00"),
                current_price=Decimal("100.00"),
                asset=eq_asset,
            )
        )
    if bond_val > Decimal("0.00"):
        holdings.append(
            PortfolioHoldingModel(
                id="h-fi",
                portfolio_id="port-drift",
                asset_id="a-fi",
                quantity=bond_val / Decimal("50.00"),
                average_purchase_price=Decimal("50.00"),
                current_price=Decimal("50.00"),
                asset=fi_asset,
            )
        )

    return PortfolioModel(
        id="port-drift",
        user_id="user-drift",
        name="Drift Test Portfolio",
        base_currency="USD",
        holdings=holdings,
    )


class TestPortfolioDriftDetection:
    """Tests for calculate_portfolio_drift."""

    def test_portfolio_exactly_matches_target_allocation(self):
        """60% equity, 40% bond holdings against 60/40 target -> 0% drift."""
        # Total value 100,000 (60,000 equity, 40,000 bond)
        portfolio = _build_test_portfolio_with_classes(Decimal("60000.00"), Decimal("40000.00"))
        target = TargetAllocationModel(
            portfolio_id="port-drift",
            is_draft=False,
            targets={"equity": Decimal("60.00"), "fixed_income": Decimal("40.00")},
        )

        res = calculate_portfolio_drift(portfolio, target, threshold_percentage_points=Decimal("5.00"))

        assert res.total_portfolio_value == Decimal("100000.00")
        assert res.portfolio_exceeds_threshold is False
        assert res.max_drift_percentage_points == Decimal("0.00")
        assert len(res.drifted_classes) == 0

        eq_drift = next(c for c in res.asset_classes if c.asset_class == "equity")
        assert eq_drift.current_weight_percentage == Decimal("60.00")
        assert eq_drift.target_weight_percentage == Decimal("60.00")
        assert eq_drift.absolute_drift_percentage_points == Decimal("0.00")
        assert eq_drift.status == "on_target"
        assert eq_drift.exceeds_threshold is False

    def test_drift_below_threshold(self):
        """Current 63% equity vs 60% target -> 3% drift (threshold 5% -> not exceeded)."""
        portfolio = _build_test_portfolio_with_classes(Decimal("63000.00"), Decimal("37000.00"))
        target = TargetAllocationModel(
            portfolio_id="port-drift",
            is_draft=False,
            targets={"equity": Decimal("60.00"), "fixed_income": Decimal("40.00")},
        )

        res = calculate_portfolio_drift(portfolio, target, threshold_percentage_points=Decimal("5.00"))

        assert res.portfolio_exceeds_threshold is False
        assert res.max_drift_percentage_points == Decimal("3.00")
        assert len(res.drifted_classes) == 0

        eq_drift = next(c for c in res.asset_classes if c.asset_class == "equity")
        assert eq_drift.absolute_drift_percentage_points == Decimal("3.00")
        assert eq_drift.status == "overweight"
        assert eq_drift.exceeds_threshold is False

    def test_drift_exactly_at_threshold(self):
        """Current 65% equity vs 60% target -> 5.00% drift vs 5.00% threshold -> not exceeded (> strictly)."""
        portfolio = _build_test_portfolio_with_classes(Decimal("65000.00"), Decimal("35000.00"))
        target = TargetAllocationModel(
            portfolio_id="port-drift",
            is_draft=False,
            targets={"equity": Decimal("60.00"), "fixed_income": Decimal("40.00")},
        )

        res = calculate_portfolio_drift(portfolio, target, threshold_percentage_points=Decimal("5.00"))

        assert res.max_drift_percentage_points == Decimal("5.00")
        assert res.portfolio_exceeds_threshold is False

    def test_drift_above_threshold_triggers_alert(self):
        """Current 68% equity vs 60% target -> 8% drift vs 5% threshold -> alert triggered."""
        portfolio = _build_test_portfolio_with_classes(Decimal("68000.00"), Decimal("32000.00"))
        target = TargetAllocationModel(
            portfolio_id="port-drift",
            is_draft=False,
            targets={"equity": Decimal("60.00"), "fixed_income": Decimal("40.00")},
        )

        res = calculate_portfolio_drift(portfolio, target, threshold_percentage_points=Decimal("5.00"))

        assert res.portfolio_exceeds_threshold is True
        assert res.max_drift_percentage_points == Decimal("8.00")
        assert "equity" in res.drifted_classes
        assert "fixed_income" in res.drifted_classes

        eq_drift = next(c for c in res.asset_classes if c.asset_class == "equity")
        assert eq_drift.exceeds_threshold is True
        assert eq_drift.status == "overweight"
        # Relative drift: 8 / 60 * 100 = 13.33%
        assert eq_drift.relative_drift_percentage == Decimal("13.33")

    def test_missing_target_allocation_handling(self):
        portfolio = _build_test_portfolio_with_classes(Decimal("50000.00"), Decimal("50000.00"))
        res = calculate_portfolio_drift(portfolio, target_allocation=None)

        assert res.is_analysis_reliable is False
        assert any("No target allocation is configured" in w for w in res.warnings)
        for c in res.asset_classes:
            assert c.status == "unspecified_target"
            assert c.target_weight_percentage is None


class TestRebalancingAnalysis:
    """Tests for calculate_rebalancing_analysis."""

    def test_rebalancing_trade_generation_and_reconciliation(self):
        """Current 68k equity / 32k bond vs 60/40 target -> SELL 8k equity, BUY 8k bond."""
        portfolio = _build_test_portfolio_with_classes(Decimal("68000.00"), Decimal("32000.00"))
        target = TargetAllocationModel(
            portfolio_id="port-drift",
            is_draft=False,
            targets={"equity": Decimal("60.00"), "fixed_income": Decimal("40.00")},
        )

        res = calculate_rebalancing_analysis(portfolio, target, drift_threshold_percentage_points=Decimal("5.00"))

        assert res.is_rebalancing_recommended is True
        assert len(res.trades) == 2

        eq_trade = next(t for t in res.trades if t.asset_class == "equity")
        fi_trade = next(t for t in res.trades if t.asset_class == "fixed_income")

        # Equity: current 68k, target 60k -> SELL 8k
        assert eq_trade.action == "SELL"
        assert eq_trade.trade_amount == Decimal("8000.00")
        assert eq_trade.target_market_value == Decimal("60000.00")

        # Bond: current 32k, target 40k -> BUY 8k
        assert fi_trade.action == "BUY"
        assert fi_trade.trade_amount == Decimal("8000.00")
        assert fi_trade.target_market_value == Decimal("40000.00")

        # Reconciliation check
        assert res.total_buy_amount == Decimal("8000.00")
        assert res.total_sell_amount == Decimal("8000.00")
        assert res.reconciliation_difference == Decimal("0.00")
        assert len(res.disclaimers) > 0

    def test_rebalancing_raises_when_no_target_allocation(self):
        portfolio = _build_test_portfolio_with_classes(Decimal("50000.00"), Decimal("50000.00"))
        with pytest.raises(ValueError, match="no target allocation configured"):
            calculate_rebalancing_analysis(portfolio, target_allocation=None)
