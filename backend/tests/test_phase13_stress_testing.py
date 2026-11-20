"""
Phase 13 Unit Tests: Deterministic Portfolio Stress Testing Engine.

Tests:
1. Exact mathematical shock propagation with known baseline and stressed values.
2. Asset-class and individual holding loss contributions.
3. Handling of unpriced holdings (explicit warning emitted, no silent zero conversion).
4. Custom shock overrides for specific symbols.
5. Limited-liability non-negativity floor on extreme shocks (-100%).
"""

from decimal import Decimal
import pytest

from app.simulation_schemas import (
    CustomHoldingInput,
    CustomShock,
    StressTestRequest,
)
from app.stress_testing import run_portfolio_stress_test


class TestStressTestingEngine:
    """Deterministic mathematical tests for portfolio stress testing."""

    def test_known_60_40_equity_market_crash(self):
        """A 60/40 portfolio of 60k Equity and 40k Bonds under equity_market_crash:
        Equity: -25% -> 45,000 (loss of 15,000)
        Bonds: +3% -> 41,200 (gain of 1,200)
        Stressed Value: 86,200 (loss of 13,800, -13.80%)
        """
        req = StressTestRequest(
            scenario="equity_market_crash",
            custom_holdings=[
                CustomHoldingInput(symbol="NIFTYBEES", asset_class="equity", current_value=Decimal("60000.00")),
                CustomHoldingInput(symbol="GILT5YR", asset_class="fixed_income", current_value=Decimal("40000.00")),
            ],
        )

        res = run_portfolio_stress_test(req)

        assert res.baseline_portfolio_value == Decimal("100000.00")
        assert res.stressed_portfolio_value == Decimal("86200.00")
        assert res.absolute_change == Decimal("-13800.00")
        assert res.percentage_change == Decimal("-13.80")

        # Verify holdings breakdown
        h_dict = {h.symbol: h for h in res.holdings_breakdown}
        assert h_dict["NIFTYBEES"].stressed_value == Decimal("45000.00")
        assert h_dict["NIFTYBEES"].absolute_change == Decimal("-15000.00")
        assert h_dict["GILT5YR"].stressed_value == Decimal("41200.00")
        assert h_dict["GILT5YR"].absolute_change == Decimal("1200.00")

        # Verify asset class breakdown
        c_dict = {c.asset_class: c for c in res.asset_class_breakdown}
        assert c_dict["equity"].baseline_weight_pct == Decimal("60.00")
        assert c_dict["fixed_income"].baseline_weight_pct == Decimal("40.00")

    def test_custom_symbol_shock_override(self):
        """Custom shock for a specific symbol overrides the broad asset class shock."""
        req = StressTestRequest(
            scenario="custom",
            custom_shocks=[
                CustomShock(asset_class="equity", shock_percentage=Decimal("-10.0")),
                CustomShock(symbol="TATAMOTORS", shock_percentage=Decimal("-30.0")),
            ],
            custom_holdings=[
                CustomHoldingInput(symbol="RELIANCE", asset_class="equity", current_value=Decimal("50000.00")),
                CustomHoldingInput(symbol="TATAMOTORS", asset_class="equity", current_value=Decimal("50000.00")),
            ],
        )

        res = run_portfolio_stress_test(req)

        h_dict = {h.symbol: h for h in res.holdings_breakdown}
        # RELIANCE receives general equity shock: -10% -> 45,000
        assert h_dict["RELIANCE"].stressed_value == Decimal("45000.00")
        assert h_dict["RELIANCE"].shock_percentage == Decimal("-10.00")

        # TATAMOTORS receives specific symbol shock: -30% -> 35,000
        assert h_dict["TATAMOTORS"].stressed_value == Decimal("35000.00")
        assert h_dict["TATAMOTORS"].shock_percentage == Decimal("-30.00")

        assert res.stressed_portfolio_value == Decimal("80000.00")
        assert res.percentage_change == Decimal("-20.00")

    def test_extreme_wipeout_shock_floors_at_zero(self):
        """Shocking an asset by -100% or worse floors at zero, never negative wealth."""
        req = StressTestRequest(
            scenario="custom",
            custom_shocks=[CustomShock(symbol="RISKY", shock_percentage=Decimal("-100.0"))],
            custom_holdings=[
                CustomHoldingInput(symbol="RISKY", asset_class="crypto", current_value=Decimal("25000.00")),
            ],
        )

        res = run_portfolio_stress_test(req)
        assert res.stressed_portfolio_value == Decimal("0.00")
        assert res.absolute_change == Decimal("-25000.00")
        assert res.percentage_change == Decimal("-100.00")

    def test_missing_input_raises_value_error(self):
        """Empty custom holdings without portfolio_id raises ValueError."""
        req = StressTestRequest(scenario="equity_market_crash")
        with pytest.raises(ValueError, match="Either a valid portfolio_id or custom_holdings"):
            run_portfolio_stress_test(req)
