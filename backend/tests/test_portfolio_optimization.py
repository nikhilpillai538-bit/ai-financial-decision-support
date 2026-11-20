"""
Unit tests for Phase 7 Modern Portfolio Theory (MPT) Optimization Engine.

Tests mathematical correctness of:
- Bounded simplex projection algorithm.
- Portfolio return, volatility, and Sharpe calculations.
- Global Minimum Volatility solver (including analytical 2-asset comparison).
- Maximum Sharpe Ratio solver (including tangency fallback when returns <= rf).
- Target-Return constrained solver (feasible and infeasible targets).
- Asset weight bounds enforcement (uniform and per-asset).
- Efficient frontier curve tracing.
- High-level rebalancing action generation, valuation mapping, and asset class summaries.
"""

from datetime import date
from decimal import Decimal
import numpy as np
import pytest

from app.db.models import AssetModel, PortfolioHoldingModel, PortfolioModel, TargetAllocationModel
from app.historical_data import MarketDataMatrix
from app.optimization_schemas import (
    AssetWeightBound,
    OptimizationRequest,
    OptimizationStrategy,
)
from app.portfolio_optimization import (
    optimize_max_sharpe,
    optimize_min_volatility,
    optimize_target_return,
    portfolio_performance,
    project_onto_bounded_simplex,
    run_mpt_optimization,
    trace_efficient_frontier,
)


class TestSimplexProjection:
    """Tests for exact projection onto the bounded probability simplex."""

    def test_basic_projection_sums_to_one(self):
        v = np.array([0.5, 0.8, -0.2, 0.1])
        lower = np.zeros(4)
        upper = np.ones(4)
        w = project_onto_bounded_simplex(v, lower, upper)

        assert pytest.approx(float(np.sum(w)), abs=1e-6) == 1.0
        assert np.all(w >= lower - 1e-7)
        assert np.all(w <= upper + 1e-7)

    def test_uniform_bounds_enforcement(self):
        v = np.array([0.9, 0.05, 0.05])
        lower = np.full(3, 0.10)
        upper = np.full(3, 0.50)
        w = project_onto_bounded_simplex(v, lower, upper)

        assert pytest.approx(float(np.sum(w)), abs=1e-6) == 1.0
        assert np.all(w >= 0.10 - 1e-6)
        assert np.all(w <= 0.50 + 1e-6)

    def test_asymmetric_bounds(self):
        v = np.array([0.5, 0.5])
        lower = np.array([0.20, 0.30])
        upper = np.array([0.40, 0.80])
        w = project_onto_bounded_simplex(v, lower, upper)

        assert pytest.approx(float(np.sum(w)), abs=1e-6) == 1.0
        assert 0.20 <= w[0] <= 0.40 + 1e-6
        assert 0.30 <= w[1] <= 0.80 + 1e-6


class TestPortfolioPerformance:
    """Tests for portfolio performance metrics."""

    def test_performance_calculation(self):
        mean_returns = np.array([0.10, 0.20])
        # Diagonal cov matrix: asset 1 var 0.04 (vol 0.20), asset 2 var 0.09 (vol 0.30)
        cov_matrix = np.array([
            [0.04, 0.00],
            [0.00, 0.09],
        ])
        weights = np.array([0.5, 0.5])
        rf = 0.02

        ret, vol, sharpe = portfolio_performance(weights, mean_returns, cov_matrix, rf)

        # Expected return: 0.5*0.10 + 0.5*0.20 = 0.15
        assert pytest.approx(ret, rel=1e-4) == 0.15
        # Expected variance: 0.25*0.04 + 0.25*0.09 = 0.01 + 0.0225 = 0.0325 -> vol = sqrt(0.0325) ~ 0.180277
        assert pytest.approx(vol, rel=1e-4) == np.sqrt(0.0325)
        # Expected Sharpe: (0.15 - 0.02) / sqrt(0.0325) ~ 0.13 / 0.180277 ~ 0.7211
        assert pytest.approx(sharpe, rel=1e-3) == (0.15 - 0.02) / np.sqrt(0.0325)


class TestOptimizationSolvers:
    """Tests for Markowitz optimization algorithms."""

    def test_min_volatility_matches_analytical_two_asset(self):
        """For two uncorrelated assets, w1* = sigma2^2 / (sigma1^2 + sigma2^2)."""
        var1 = 0.04  # vol 20%
        var2 = 0.16  # vol 40%
        cov_matrix = np.array([
            [var1, 0.0],
            [0.0, var2],
        ])
        lower = np.zeros(2)
        upper = np.ones(2)

        w = optimize_min_volatility(cov_matrix, lower, upper)

        expected_w1 = var2 / (var1 + var2)  # 0.16 / 0.20 = 0.80
        expected_w2 = var1 / (var1 + var2)  # 0.04 / 0.20 = 0.20

        assert pytest.approx(w[0], abs=1e-2) == expected_w1
        assert pytest.approx(w[1], abs=1e-2) == expected_w2
        assert pytest.approx(float(np.sum(w)), abs=1e-6) == 1.0

    def test_min_volatility_respects_custom_upper_bounds(self):
        """Even if asset 1 has lower volatility, if capped at 50%, w1 must not exceed 50%."""
        cov_matrix = np.array([
            [0.01, 0.00],
            [0.00, 0.10],
        ])
        lower = np.zeros(2)
        upper = np.array([0.50, 1.00])  # Asset 1 capped at 50%

        w = optimize_min_volatility(cov_matrix, lower, upper)
        assert w[0] <= 0.5001
        assert pytest.approx(w[0], abs=1e-2) == 0.50
        assert pytest.approx(w[1], abs=1e-2) == 0.50

    def test_max_sharpe_finds_higher_sharpe_than_min_vol(self):
        """Tangency portfolio should attain higher Sharpe ratio than min-vol portfolio."""
        mean_returns = np.array([0.06, 0.18])
        cov_matrix = np.array([
            [0.02, 0.005],
            [0.005, 0.08],
        ])
        rf = 0.03
        lower = np.zeros(2)
        upper = np.ones(2)

        w_min = optimize_min_volatility(cov_matrix, lower, upper)
        _, _, sharpe_min = portfolio_performance(w_min, mean_returns, cov_matrix, rf)

        w_sharpe, valid, reason = optimize_max_sharpe(mean_returns, cov_matrix, rf, lower, upper)
        _, _, sharpe_max = portfolio_performance(w_sharpe, mean_returns, cov_matrix, rf)

        assert valid is True
        assert reason is None
        assert sharpe_max >= sharpe_min - 1e-4

    def test_max_sharpe_fallback_when_returns_below_risk_free(self):
        """When all assets return less than rf, tangency portfolio falls back to min volatility."""
        mean_returns = np.array([0.01, 0.02])
        cov_matrix = np.array([
            [0.04, 0.00],
            [0.00, 0.09],
        ])
        rf = 0.05  # rf > all asset returns
        lower = np.zeros(2)
        upper = np.ones(2)

        w, valid, reason = optimize_max_sharpe(mean_returns, cov_matrix, rf, lower, upper)
        w_min = optimize_min_volatility(cov_matrix, lower, upper)

        assert valid is False
        assert reason is not None
        assert "less than or equal to the risk-free rate" in reason
        assert np.allclose(w, w_min, atol=1e-3)

    def test_target_return_optimization_feasible(self):
        mean_returns = np.array([0.05, 0.15])
        cov_matrix = np.array([
            [0.01, 0.00],
            [0.00, 0.04],
        ])
        target_ret = 0.10
        lower = np.zeros(2)
        upper = np.ones(2)

        w, valid, reason = optimize_target_return(mean_returns, cov_matrix, target_ret, lower, upper)
        ret, _, _ = portfolio_performance(w, mean_returns, cov_matrix, 0.02)

        assert valid is True
        assert ret >= target_ret - 1e-3

    def test_target_return_optimization_infeasible_allocates_to_max(self):
        mean_returns = np.array([0.05, 0.12])
        cov_matrix = np.array([
            [0.01, 0.00],
            [0.00, 0.04],
        ])
        target_ret = 0.25  # Infeasible, max return is 0.12
        lower = np.zeros(2)
        upper = np.ones(2)

        w, valid, reason = optimize_target_return(mean_returns, cov_matrix, target_ret, lower, upper)
        assert valid is False
        assert "exceeds the maximum individual asset" in reason
        # Should allocate 100% to asset 2 (highest return)
        assert pytest.approx(w[1], abs=1e-3) == 1.0


class TestEfficientFrontier:
    """Tests for efficient frontier tracing."""

    def test_frontier_generates_ordered_points(self):
        mean_returns = np.array([0.06, 0.12, 0.18])
        cov_matrix = np.array([
            [0.01, 0.002, 0.001],
            [0.002, 0.04, 0.005],
            [0.001, 0.005, 0.09],
        ])
        symbols = ["BOND", "EQUITY", "CRYPTO"]
        rf = 0.03
        lower = np.zeros(3)
        upper = np.ones(3)

        points = trace_efficient_frontier(mean_returns, cov_matrix, rf, symbols, lower, upper, n_points=10)

        assert len(points) == 10
        # Frontier points should have weights summing to 1.0
        for pt in points:
            sum_w = sum(pt.weights.values())
            assert pytest.approx(float(sum_w), abs=0.01) == 1.0
        
        # Volatilities should be sorted in ascending order
        vols = [float(p.expected_volatility) for p in points]
        assert vols == sorted(vols)


class TestHighLevelOptimizationRunner:
    """Tests for run_mpt_optimization orchestrator."""

    def _build_dummy_portfolio(self):
        asset1 = AssetModel(
            id="asset-1",
            symbol="AAPL",
            name="Apple Inc",
            asset_class="equity",
            currency="USD",
        )
        asset2 = AssetModel(
            id="asset-2",
            symbol="BND",
            name="Total Bond Market",
            asset_class="fixed_income",
            currency="USD",
        )
        holding1 = PortfolioHoldingModel(
            id="h-1",
            portfolio_id="port-1",
            asset_id="asset-1",
            quantity=Decimal("100"),
            average_purchase_price=Decimal("150.00"),
            current_price=Decimal("200.00"),  # Value: 20,000 (80%)
            asset=asset1,
        )
        holding2 = PortfolioHoldingModel(
            id="h-2",
            portfolio_id="port-1",
            asset_id="asset-2",
            quantity=Decimal("50"),
            average_purchase_price=Decimal("100.00"),
            current_price=Decimal("100.00"),  # Value: 5,000 (20%)
            asset=asset2,
        )
        portfolio = PortfolioModel(
            id="port-1",
            user_id="user-1",
            name="Test Growth Portfolio",
            base_currency="USD",
            holdings=[holding1, holding2],
        )
        return portfolio

    def test_run_mpt_optimization_rebalancing_generation(self):
        portfolio = self._build_dummy_portfolio()
        # AAPL: high return, high vol. BND: low return, low vol.
        mean_returns = np.array([0.15, 0.04])
        cov_matrix = np.array([
            [0.04, 0.00],
            [0.00, 0.005],
        ])
        market_data = MarketDataMatrix(
            symbols=["AAPL", "BND"],
            mean_returns=mean_returns,
            cov_matrix=cov_matrix,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1),
            observation_count=250,
            was_regularized=False,
            warnings=[],
        )

        # Min volatility strategy should shift weights towards BND (currently only 20%)
        req = OptimizationRequest(
            strategy=OptimizationStrategy.MIN_VOLATILITY,
            risk_free_rate=Decimal("0.02"),
            include_efficient_frontier=True,
        )

        response = run_mpt_optimization(
            portfolio=portfolio,
            target_allocation=None,
            market_data=market_data,
            request=req,
            run_id="run-123",
        )

        assert response.portfolio_id == "port-1"
        assert response.total_portfolio_value == Decimal("25000.00")
        assert len(response.allocations) == 2
        assert len(response.efficient_frontier) > 0

        # Check holding rebalancing
        bnd_alloc = next(a for a in response.allocations if a.symbol == "BND")
        aapl_alloc = next(a for a in response.allocations if a.symbol == "AAPL")

        # BND optimal weight should be high (lower vol), so current 20% -> optimal > 20% -> BUY
        assert bnd_alloc.optimal_weight > bnd_alloc.current_weight
        assert bnd_alloc.action == "BUY"
        assert bnd_alloc.trade_amount > Decimal("0")

        # AAPL optimal weight should be lower than current 80% -> SELL
        assert aapl_alloc.optimal_weight < aapl_alloc.current_weight
        assert aapl_alloc.action == "SELL"

        # Asset class summary should aggregate correctly
        eq_class = next(c for c in response.asset_class_summary if c.asset_class == "equity")
        fi_class = next(c for c in response.asset_class_summary if c.asset_class == "fixed_income")
        assert eq_class.current_weight == aapl_alloc.current_weight
        assert fi_class.current_weight == bnd_alloc.current_weight

    def test_run_mpt_with_target_allocation_comparison(self):
        portfolio = self._build_dummy_portfolio()
        mean_returns = np.array([0.15, 0.04])
        cov_matrix = np.array([
            [0.04, 0.00],
            [0.00, 0.005],
        ])
        market_data = MarketDataMatrix(
            symbols=["AAPL", "BND"],
            mean_returns=mean_returns,
            cov_matrix=cov_matrix,
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1),
            observation_count=250,
            was_regularized=False,
            warnings=[],
        )

        target_alloc = TargetAllocationModel(
            portfolio_id="port-1",
            is_draft=False,
            targets={"equity": Decimal("60.00"), "fixed_income": Decimal("40.00")},
        )

        req = OptimizationRequest(strategy=OptimizationStrategy.MIN_VOLATILITY)
        response = run_mpt_optimization(
            portfolio=portfolio,
            target_allocation=target_alloc,
            market_data=market_data,
            request=req,
        )

        eq_class = next(c for c in response.asset_class_summary if c.asset_class == "equity")
        assert eq_class.target_allocation_weight == Decimal("0.6000")
