"""
Phase 13 Unit Tests: Monte Carlo Wealth & Goal Simulator.

Tests:
1. Exact deterministic reproducibility with fixed random seed (seed=42).
2. Zero-volatility collapse (sigma=0 produces identical deterministic compounding across all paths).
3. Monotonic percentile ordering (p5 <= p25 <= p50 <= p75 <= p95).
4. Goal achievement probability calculation correctness.
5. Input validation bounds (rejection of simulation counts > 5000 or < 100).
"""

from decimal import Decimal
import pytest
from pydantic import ValidationError

from app.monte_carlo import run_monte_carlo_simulation
from app.simulation_schemas import MonteCarloRequest


class TestMonteCarloEngine:
    """Rigorous tests for the stochastic Monte Carlo wealth simulator."""

    def test_reproducibility_with_seed(self):
        """Two independent runs with the same seed yield identical median terminal wealth."""
        req1 = MonteCarloRequest(
            initial_value=Decimal("100000.00"),
            monthly_contribution=Decimal("5000.00"),
            horizon_months=60,
            num_simulations=500,
            expected_annual_return_pct=Decimal("12.00"),
            annual_volatility_pct=Decimal("15.00"),
            seed=42,
        )
        req2 = MonteCarloRequest(
            initial_value=Decimal("100000.00"),
            monthly_contribution=Decimal("5000.00"),
            horizon_months=60,
            num_simulations=500,
            expected_annual_return_pct=Decimal("12.00"),
            annual_volatility_pct=Decimal("15.00"),
            seed=42,
        )

        res1 = run_monte_carlo_simulation(req1)
        res2 = run_monte_carlo_simulation(req2)

        assert res1.terminal_wealth.median == res2.terminal_wealth.median
        assert res1.terminal_wealth.p5 == res2.terminal_wealth.p5
        assert res1.terminal_wealth.p95 == res2.terminal_wealth.p95
        assert res1.terminal_wealth.mean == res2.terminal_wealth.mean

    def test_zero_volatility_edge_case(self):
        """When volatility is 0.0%, all simulation paths collapse to the exact same deterministic value."""
        req = MonteCarloRequest(
            initial_value=Decimal("100000.00"),
            monthly_contribution=Decimal("0.00"),
            horizon_months=12,
            num_simulations=200,
            expected_annual_return_pct=Decimal("10.00"),
            annual_volatility_pct=Decimal("0.00"),
            seed=123,
        )

        res = run_monte_carlo_simulation(req)

        # Standard deviation across paths must be 0.0
        assert res.terminal_wealth.std_dev == Decimal("0.00")
        # p5, p50, and p95 must all be identical
        assert res.terminal_wealth.p5 == res.terminal_wealth.median
        assert res.terminal_wealth.p95 == res.terminal_wealth.median
        assert res.terminal_wealth.min == res.terminal_wealth.max

    def test_monotonic_percentiles(self):
        """Percentile slices must satisfy p5 <= p25 <= p50 <= p75 <= p95 at every milestone."""
        req = MonteCarloRequest(
            initial_value=Decimal("50000.00"),
            monthly_contribution=Decimal("2000.00"),
            horizon_months=36,
            num_simulations=500,
            expected_annual_return_pct=Decimal("11.00"),
            annual_volatility_pct=Decimal("16.00"),
            seed=7,
        )

        res = run_monte_carlo_simulation(req)

        for pt in res.percentile_trajectory:
            assert pt.p5 <= pt.p25
            assert pt.p25 <= pt.p50
            assert pt.p50 <= pt.p75
            assert pt.p75 <= pt.p95

    def test_goal_probability_bounds(self):
        """Target set extremely high yields 0% probability; target set at 0 yields 100%."""
        # Unrealistic target: 100 Crore in 1 year with 10k initial
        req_high = MonteCarloRequest(
            initial_value=Decimal("10000.00"),
            horizon_months=12,
            target_amount=Decimal("1000000000.00"),
            num_simulations=200,
            seed=42,
        )
        res_high = run_monte_carlo_simulation(req_high)
        assert res_high.goal_success_probability_pct == Decimal("0.00")

        # Easily achievable target: 1 Rupee in 1 year with 100k initial
        req_low = MonteCarloRequest(
            initial_value=Decimal("100000.00"),
            horizon_months=12,
            target_amount=Decimal("1.00"),
            num_simulations=200,
            seed=42,
        )
        res_low = run_monte_carlo_simulation(req_low)
        assert res_low.goal_success_probability_pct == Decimal("100.00")

    def test_computational_bounds_validation(self):
        """Simulation counts exceeding 5,000 or below 100 fail Pydantic validation."""
        with pytest.raises(ValidationError):
            MonteCarloRequest(num_simulations=10000)

        with pytest.raises(ValidationError):
            MonteCarloRequest(num_simulations=50)
