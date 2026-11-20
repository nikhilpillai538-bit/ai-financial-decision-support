"""
Unit tests for Phase 8 Forward and Reverse SIP Calculators.

Tests mathematical correctness of:
- Forward SIP ordinary annuity compounding
- Zero return handling: FV = L + P*n
- Positive return handling against known financial annuity formulas
- Step-up contribution growth (annual contribution increases)
- Effective vs Nominal monthly rate conversions
- Reverse SIP target solving
- Target already covered by initial lump sum
- Edge cases: short horizons (1 month), zero contributions, zero initial investment
- Schedule generation and period accounting consistency
"""

from decimal import Decimal
import math
import pytest

from app.goal_schemas import ReverseSIPRequest, SIPCalculationRequest
from app.sip_calculator import (
    calculate_forward_sip,
    calculate_reverse_sip,
    compute_monthly_rate,
)


class TestMonthlyRateConversion:
    """Tests for annual to monthly rate conversion."""

    def test_zero_rate(self):
        assert compute_monthly_rate(Decimal("0.00"), "effective") == 0.0
        assert compute_monthly_rate(Decimal("0.00"), "nominal") == 0.0

    def test_effective_rate_annualizes_exactly(self):
        # With 12% effective annual return, (1 + r_m)^12 must equal 1.12
        r_m = compute_monthly_rate(Decimal("12.00"), "effective")
        assert pytest.approx((1.0 + r_m) ** 12, rel=1e-7) == 1.12

    def test_nominal_rate_is_annual_divided_by_12(self):
        r_m = compute_monthly_rate(Decimal("12.00"), "nominal")
        assert pytest.approx(r_m, rel=1e-7) == 0.01


class TestForwardSIPCalculator:
    """Tests for forward SIP ordinary annuity calculation."""

    def test_zero_return_pure_savings(self):
        """At 0% return, FV = L + P*n."""
        req = SIPCalculationRequest(
            initial_investment=Decimal("10000.00"),
            monthly_contribution=Decimal("5000.00"),
            annual_return_percentage=Decimal("0.00"),
            duration_months=12,
            rate_convention="nominal",
        )
        res = calculate_forward_sip(req)

        # FV = 10,000 + 5,000 * 12 = 70,000
        assert res.projected_future_value == Decimal("70000.00")
        assert res.total_contributions == Decimal("60000.00")
        assert res.total_invested == Decimal("70000.00")
        assert res.estimated_wealth_gain == Decimal("0.00")

    def test_positive_return_matches_annuity_formula(self):
        """Verify FV = L*(1+r)^n + P*((1+r)^n - 1)/r."""
        req = SIPCalculationRequest(
            initial_investment=Decimal("0.00"),
            monthly_contribution=Decimal("10000.00"),
            annual_return_percentage=Decimal("12.00"),
            duration_months=12,
            rate_convention="nominal",  # r_m = 0.01 per month
        )
        res = calculate_forward_sip(req)

        # FV = 10000 * ((1.01^12 - 1) / 0.01) ~ 10000 * 12.682503 = 126,825.03
        r_m = 0.01
        n = 12
        expected_fv = 10000.0 * (((1.0 + r_m) ** n - 1.0) / r_m)

        assert pytest.approx(float(res.projected_future_value), abs=0.50) == expected_fv
        assert res.total_contributions == Decimal("120000.00")
        assert res.estimated_wealth_gain > Decimal("6800.00")

    def test_initial_lump_sum_plus_sip(self):
        """Initial lump sum compounds alongside monthly SIP."""
        req = SIPCalculationRequest(
            initial_investment=Decimal("100000.00"),
            monthly_contribution=Decimal("10000.00"),
            annual_return_percentage=Decimal("12.00"),
            duration_months=12,
            rate_convention="nominal",
        )
        res = calculate_forward_sip(req)

        r_m = 0.01
        n = 12
        lump_fv = 100000.0 * ((1.0 + r_m) ** n)
        sip_fv = 10000.0 * (((1.0 + r_m) ** n - 1.0) / r_m)
        expected_total = lump_fv + sip_fv

        assert pytest.approx(float(res.projected_future_value), abs=1.0) == expected_total
        assert res.total_invested == Decimal("220000.00")

    def test_step_up_contribution_growth(self):
        """10% annual step up in contributions should yield higher corpus than flat SIP."""
        flat_req = SIPCalculationRequest(
            initial_investment=Decimal("0.00"),
            monthly_contribution=Decimal("10000.00"),
            annual_return_percentage=Decimal("10.00"),
            duration_months=24,
        )
        flat_res = calculate_forward_sip(flat_req)

        step_req = SIPCalculationRequest(
            initial_investment=Decimal("0.00"),
            monthly_contribution=Decimal("10000.00"),
            annual_return_percentage=Decimal("10.00"),
            duration_months=24,
            annual_step_up_percentage=Decimal("10.00"),  # Month 13-24 contribution is 11,000
        )
        step_res = calculate_forward_sip(step_req)

        # In year 2, user deposits 11,000/mo instead of 10,000/mo
        assert step_res.total_contributions == Decimal("252000.00")  # 12*10000 + 12*11000
        assert flat_res.total_contributions == Decimal("240000.00")
        assert step_res.projected_future_value > flat_res.projected_future_value

    def test_schedule_breakdown_consistency(self):
        req = SIPCalculationRequest(
            initial_investment=Decimal("50000.00"),
            monthly_contribution=Decimal("5000.00"),
            annual_return_percentage=Decimal("8.00"),
            duration_months=24,
            include_schedule=True,
        )
        res = calculate_forward_sip(req)

        assert len(res.schedule) == 2  # 2 years
        y1 = res.schedule[0]
        y2 = res.schedule[1]

        assert y1.period_label == "Year 1"
        assert y1.opening_balance == Decimal("50000.00")
        assert y2.opening_balance == y1.closing_balance
        assert y2.closing_balance == res.projected_future_value


class TestReverseSIPCalculator:
    """Tests for reverse SIP target solver."""

    def test_reverse_sip_zero_return(self):
        """At 0% return, P = (Target - L) / n."""
        req = ReverseSIPRequest(
            target_amount=Decimal("120000.00"),
            initial_investment=Decimal("0.00"),
            annual_return_percentage=Decimal("0.00"),
            duration_months=12,
            rate_convention="nominal",
        )
        res = calculate_reverse_sip(req)

        # 120,000 / 12 = 10,000
        assert res.required_monthly_contribution == Decimal("10000.00")
        assert res.is_target_already_covered is False
        assert res.projected_future_value == Decimal("120000.00")

    def test_reverse_sip_positive_return_reconciles_forward_sip(self):
        """Passing calculated required SIP back into forward SIP must achieve target amount."""
        target = Decimal("500000.00")
        req = ReverseSIPRequest(
            target_amount=target,
            initial_investment=Decimal("25000.00"),
            annual_return_percentage=Decimal("12.00"),
            duration_months=36,
            rate_convention="nominal",
        )
        res = calculate_reverse_sip(req)

        assert res.required_monthly_contribution > Decimal("0.00")
        assert res.is_target_already_covered is False

        # Verify reconciliation
        fwd_req = SIPCalculationRequest(
            initial_investment=Decimal("25000.00"),
            monthly_contribution=res.required_monthly_contribution,
            annual_return_percentage=Decimal("12.00"),
            duration_months=36,
            rate_convention="nominal",
        )
        fwd_res = calculate_forward_sip(fwd_req)

        # Due to cent quantization, future value should match target within ~50 cents
        assert pytest.approx(float(fwd_res.projected_future_value), abs=1.0) == float(target)

    def test_target_already_covered_by_initial_lump_sum(self):
        """When initial investment already grows to target, required SIP is 0."""
        req = ReverseSIPRequest(
            target_amount=Decimal("100000.00"),
            initial_investment=Decimal("100000.00"),  # Already 100k, with 10% return over 12 months will grow to >100k
            annual_return_percentage=Decimal("10.00"),
            duration_months=12,
        )
        res = calculate_reverse_sip(req)

        assert res.is_target_already_covered is True
        assert res.required_monthly_contribution == Decimal("0.00")
        assert res.projected_future_value >= Decimal("100000.00")
        assert "meets or exceeds the target amount" in res.explanation

    def test_very_short_horizon(self):
        """1-month horizon handles edge case cleanly."""
        req = ReverseSIPRequest(
            target_amount=Decimal("10000.00"),
            initial_investment=Decimal("0.00"),
            annual_return_percentage=Decimal("6.00"),
            duration_months=1,
            rate_convention="nominal",
        )
        res = calculate_reverse_sip(req)
        # In 1 month with contribution at end of month, growth is on 0 opening balance -> P = 10,000
        assert res.required_monthly_contribution == Decimal("10000.00")
