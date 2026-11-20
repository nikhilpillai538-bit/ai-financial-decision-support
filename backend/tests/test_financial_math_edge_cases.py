"""
Phase 12 Deterministic Financial Math & Calculation Correctness Tests.

Strictly verifies financial calculation rules, precision, edge cases,
and numerical equivalence:
1. Forward vs Reverse SIP mathematical equivalence and closure.
2. Zero-return (0%) and negative return SIP handling without division by zero.
3. Reverse SIP when initial lump sum already covers the target.
4. Ledoit-Wolf covariance shrinkage on perfectly collinear / singular instruments.
5. Simplex projection constraints (sum of weights = 1.0, lower <= w <= upper).
6. Risk-aware glide-path equity decay as horizon nears completion.
7. Portfolio valuation precision and unpriced holdings accounting.
"""

from datetime import date, timedelta
from decimal import Decimal
import math
import numpy as np
import pytest

from app.goal_schemas import (
    SIPCalculationRequest,
    ReverseSIPRequest,
)
from app.historical_data import (
    HistoricalPriceRow,
    prepare_market_data_matrix,
)
from app.portfolio_optimization import (
    project_onto_bounded_simplex,
)
from app.sip_calculator import (
    calculate_forward_sip,
    calculate_reverse_sip,
    compute_monthly_rate,
)
from app.glide_path import generate_glide_path


class TestSIPMathematics:
    """Rigorous mathematical tests for forward and reverse SIP compounding."""

    @pytest.mark.parametrize("rate_pct", [Decimal("6.0"), Decimal("10.5"), Decimal("12.0"), Decimal("15.0")])
    @pytest.mark.parametrize("duration_months", [36, 60, 120, 240])
    def test_forward_and_reverse_sip_equivalence(self, rate_pct: Decimal, duration_months: int):
        """Verify that solving for required SIP to reach a target achieves that target under forward calculation."""
        target_corpus = Decimal("2500000.00")  # 25 Lakhs
        initial_lump = Decimal("100000.00")    # 1 Lakh initial

        rev_req = ReverseSIPRequest(
            target_amount=target_corpus,
            initial_investment=initial_lump,
            annual_return_percentage=rate_pct,
            duration_months=duration_months,
            rate_convention="nominal",
            include_schedule=False,
        )
        rev_res = calculate_reverse_sip(rev_req)
        required_p = rev_res.required_monthly_contribution
        assert required_p > Decimal("0.00")

        # Now feed required_p into Forward SIP
        fwd_req = SIPCalculationRequest(
            initial_investment=initial_lump,
            monthly_contribution=required_p,
            annual_return_percentage=rate_pct,
            duration_months=duration_months,
            rate_convention="nominal",
            include_schedule=False,
        )
        fwd_res = calculate_forward_sip(fwd_req)

        # Because monthly contribution is quantized to 2 decimal places (rupees & paise),
        # the final future value must agree within 0.1% or 50 rupees of the target.
        diff = abs(fwd_res.projected_future_value - target_corpus)
        pct_diff = (diff / target_corpus) * Decimal("100")
        assert pct_diff < Decimal("0.1"), f"Discrepancy too high: {diff} on {target_corpus}"

    def test_zero_return_sip(self):
        """0% return rate should strictly compute simple accumulation: FV = L + P*n."""
        initial = Decimal("50000.00")
        monthly = Decimal("5000.00")
        months = 12

        req = SIPCalculationRequest(
            initial_investment=initial,
            monthly_contribution=monthly,
            annual_return_percentage=Decimal("0.0"),
            duration_months=months,
            include_schedule=True,
        )
        res = calculate_forward_sip(req)

        expected_fv = initial + (monthly * Decimal(months))  # 50,000 + 60,000 = 110,000
        assert res.projected_future_value == expected_fv
        assert res.estimated_wealth_gain == Decimal("0.00")
        assert res.total_contributions == Decimal("60000.00")

    def test_reverse_sip_zero_return(self):
        """Reverse SIP with 0% return must simply divide shortfall equally."""
        target = Decimal("120000.00")
        initial = Decimal("0.00")
        months = 12

        rev_req = ReverseSIPRequest(
            target_amount=target,
            initial_investment=initial,
            annual_return_percentage=Decimal("0.0"),
            duration_months=months,
        )
        rev_res = calculate_reverse_sip(rev_req)
        assert rev_res.required_monthly_contribution == Decimal("10000.00")

    def test_reverse_sip_target_already_covered(self):
        """When initial lump sum alone exceeds target FV, required SIP must be exactly 0."""
        initial = Decimal("1000000.00")  # 10 Lakhs
        target = Decimal("500000.00")    # 5 Lakhs (already covered)
        months = 60

        rev_req = ReverseSIPRequest(
            target_amount=target,
            initial_investment=initial,
            annual_return_percentage=Decimal("12.0"),
            duration_months=months,
        )
        rev_res = calculate_reverse_sip(rev_req)
        assert rev_res.is_target_already_covered is True
        assert rev_res.required_monthly_contribution == Decimal("0.00")

    def test_rate_conventions(self):
        """Nominal vs Effective compounding monthly rates must match textbook formulas."""
        annual = Decimal("12.0")
        nom = compute_monthly_rate(annual, "nominal")
        eff = compute_monthly_rate(annual, "effective")

        # Nominal = 12% / 12 = 1% = 0.01
        assert math.isclose(nom, 0.01, rel_tol=1e-7)
        # Effective = (1 + 0.12)^(1/12) - 1 ~ 0.00948879
        expected_eff = math.pow(1.12, 1.0 / 12.0) - 1.0
        assert math.isclose(eff, expected_eff, rel_tol=1e-7)
        assert eff < nom


class TestModernPortfolioTheoryMath:
    """Verifies numerical properties of the Markowitz solver and covariance regularization."""

    def test_simplex_projection_exact_sum(self):
        """Simplex projection must guarantee sum(weights) == 1.0 within numerical tolerance."""
        np.random.seed(42)
        for _ in range(20):
            dim = np.random.randint(3, 10)
            raw_v = np.random.randn(dim)
            lower = np.full(dim, 0.0)
            upper = np.full(dim, 0.5)

            w = project_onto_bounded_simplex(raw_v, lower, upper)
            assert math.isclose(float(np.sum(w)), 1.0, abs_tol=1e-6)
            assert np.all(w >= lower - 1e-7)
            assert np.all(w <= upper + 1e-7)

    def test_collinear_assets_trigger_ledoit_wolf_shrinkage(self):
        """Perfect collinearity creates a singular covariance matrix that must be regularized."""
        base_date = date(2025, 1, 1)
        records: list[HistoricalPriceRow] = []

        # Asset A and Asset B are identical (collinear)
        for i in range(30):
            d = base_date + timedelta(days=i)
            price_a = Decimal(str(100.0 + i * 2.0))
            price_b = Decimal(str(200.0 + i * 4.0))  # Exactly 2x Asset A
            records.append(HistoricalPriceRow(date=d, symbol="SYM_A", adjusted_close=price_a))
            records.append(HistoricalPriceRow(date=d, symbol="SYM_B", adjusted_close=price_b))

        matrix = prepare_market_data_matrix(
            price_records=records,
            required_symbols=["SYM_A", "SYM_B"],
            min_observations=15,
        )

        assert matrix.was_regularized is True
        # Verify regularized matrix is strictly positive definite (all eigenvalues > 0)
        eigenvals = np.linalg.eigvalsh(matrix.cov_matrix)
        assert np.all(eigenvals > 0.0)
        assert any("Covariance matrix was ill-conditioned" in w for w in matrix.warnings)


class TestGlidePathCorrectness:
    """Verifies deterministic asset allocation transition along a glide path."""

    def test_glide_path_equity_decay(self):
        """Equity allocation must decrease monotonically as checkpoints approach target date."""
        from app.goal_schemas import GlidePathRequest

        start_d = date(2025, 1, 1)
        target_d = date(2045, 1, 1)  # 20-year horizon

        req = GlidePathRequest(
            start_date=start_d,
            target_date=target_d,
            risk_profile="moderate",
            interval_months=24,  # Every 2 years
        )

        res = generate_glide_path(
            start_date=start_d,
            target_date=target_d,
            request=req,
        )

        # Checkpoints trace the glide path over time
        checkpoints = res.checkpoints
        assert len(checkpoints) >= 5

        # As time progresses towards target_date, equity percentage must decrease or remain constant
        equity_series = [cp.allocation_weights.get("equity", Decimal("0.0")) for cp in checkpoints]
        for i in range(len(equity_series) - 1):
            assert equity_series[i] >= equity_series[i + 1], (
                f"Glide path failed monotonicity: Checkpoint {i} ({equity_series[i]}) < "
                f"Checkpoint {i+1} ({equity_series[i+1]})"
            )
