"""
FastAPI Router for Phase 13:
- Portfolio Stress Testing (/portfolio/stress-tests, /portfolios/{id}/stress-test)
- Historical Backtesting (/portfolio/backtests, /portfolios/{id}/backtest)
- Stochastic Monte Carlo Simulation (/portfolio/monte-carlo, /portfolios/{id}/monte-carlo)
- Investment-Goal Multi-Scenario Comparison (/goals/{id}/scenario-comparison, /goals/scenario-comparison)
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.backtesting import run_portfolio_backtest
from app.db.models import UserModel
from app.db.repositories.portfolio_repo import SQLPortfolioRepository
from app.monte_carlo import run_monte_carlo_simulation
from app.portfolio_router import get_portfolio_repo
from app.scenario_comparison import compare_goal_scenarios
from app.simulation_schemas import (
    BacktestRequest,
    BacktestResponse,
    GoalScenarioComparisonRequest,
    GoalScenarioComparisonResponse,
    MonteCarloRequest,
    MonteCarloResponse,
    StressTestRequest,
    StressTestResponse,
)
from app.stress_testing import SCENARIO_PRESETS, run_portfolio_stress_test

simulation_router = APIRouter(tags=["Portfolio Stress Testing, Backtesting & Monte Carlo"])


# ---------------------------------------------------------------------------
# 1. Stress Testing Endpoints
# ---------------------------------------------------------------------------

@simulation_router.get(
    "/portfolio/stress-test-presets",
    summary="List predefined macroeconomic crisis shock scenarios",
)
def list_stress_test_presets(
    current_user: UserModel = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return available curated macroeconomic crisis shock presets."""
    return {
        "presets": [
            {
                "id": k,
                "name": v["name"],
                "description": v["description"],
                "asset_class_shocks": {
                    ac: float(shock) for ac, shock in v.get("asset_class_shocks", {}).items()
                },
            }
            for k, v in SCENARIO_PRESETS.items()
        ]
    }


@simulation_router.post(
    "/portfolio/stress-tests",
    response_model=StressTestResponse,
    summary="Run deterministic portfolio stress test (ad-hoc or referenced portfolio)",
)
@simulation_router.post(
    "/portfolios/{portfolio_id}/stress-test",
    response_model=StressTestResponse,
    summary="Run deterministic stress test on a specific saved portfolio",
)
def stress_test_portfolio(
    payload: StressTestRequest,
    portfolio_id: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> StressTestResponse:
    target_pid = portfolio_id or payload.portfolio_id
    portfolio = None

    if target_pid:
        portfolio = repo.get_portfolio(target_pid, user_id=current_user.id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio '{target_pid}' not found or access denied.",
            )

    try:
        return run_portfolio_stress_test(payload, portfolio=portfolio)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# 2. Historical Portfolio Backtesting Endpoints
# ---------------------------------------------------------------------------

@simulation_router.post(
    "/portfolio/backtests",
    response_model=BacktestResponse,
    summary="Run historical portfolio backtest with periodic rebalancing and fees",
)
@simulation_router.post(
    "/portfolios/{portfolio_id}/backtest",
    response_model=BacktestResponse,
    summary="Run historical backtest on a specific saved portfolio",
)
def backtest_portfolio(
    payload: BacktestRequest,
    portfolio_id: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> BacktestResponse:
    target_pid = portfolio_id or payload.portfolio_id
    portfolio = None

    if target_pid:
        portfolio = repo.get_portfolio(target_pid, user_id=current_user.id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio '{target_pid}' not found or access denied.",
            )

    # Determine required symbols
    symbols_to_fetch: List[str] = []
    if payload.weights:
        symbols_to_fetch.extend(payload.weights.keys())
    elif payload.symbols:
        symbols_to_fetch.extend(payload.symbols)
    elif portfolio and portfolio.holdings:
        symbols_to_fetch.extend(
            h.asset.symbol.upper() for h in portfolio.holdings if h.asset and h.asset.symbol
        )

    if payload.benchmark_symbol:
        symbols_to_fetch.append(payload.benchmark_symbol.strip().upper())

    symbols_to_fetch = list(set(s.strip().upper() for s in symbols_to_fetch if s))

    if not symbols_to_fetch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No symbols could be resolved for backtesting. Provide weights, symbols, or portfolio_id.",
        )

    # Retrieve historical price observations from repository
    price_records = repo.get_historical_prices(
        symbols=symbols_to_fetch,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )

    try:
        return run_portfolio_backtest(payload, price_records=price_records, portfolio=portfolio)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# 3. Monte Carlo Simulation Endpoints
# ---------------------------------------------------------------------------

@simulation_router.post(
    "/portfolio/monte-carlo",
    response_model=MonteCarloResponse,
    summary="Execute stochastic Monte Carlo wealth projection and goal probability",
)
@simulation_router.post(
    "/portfolios/{portfolio_id}/monte-carlo",
    response_model=MonteCarloResponse,
    summary="Execute Monte Carlo simulation derived from a specific saved portfolio",
)
def monte_carlo_simulation(
    payload: MonteCarloRequest,
    portfolio_id: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> MonteCarloResponse:
    target_pid = portfolio_id or payload.portfolio_id
    portfolio = None

    if target_pid:
        portfolio = repo.get_portfolio(target_pid, user_id=current_user.id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Portfolio '{target_pid}' not found or access denied.",
            )

    try:
        return run_monte_carlo_simulation(payload, portfolio=portfolio)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# 4. Investment-Goal Scenario Comparison Endpoints
# ---------------------------------------------------------------------------

@simulation_router.post(
    "/goals/{goal_id}/scenario-comparison",
    response_model=GoalScenarioComparisonResponse,
    summary="Compare hypothetical what-if scenarios against a saved investment goal",
)
@simulation_router.post(
    "/investment-goals/{goal_id}/scenario-comparison",
    response_model=GoalScenarioComparisonResponse,
    summary="Compare hypothetical what-if scenarios against a saved investment goal (alias)",
)
@simulation_router.post(
    "/goals/scenario-comparison",
    response_model=GoalScenarioComparisonResponse,
    summary="Compare hypothetical what-if scenarios for a standalone goal",
)
def compare_investment_goal_scenarios(
    payload: GoalScenarioComparisonRequest,
    goal_id: Optional[str] = None,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> GoalScenarioComparisonResponse:
    target_gid = goal_id or payload.goal_id
    goal = None
    portfolio = None

    if target_gid:
        goal = repo.get_goal(target_gid, user_id=current_user.id)
        if not goal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Investment goal '{target_gid}' not found or access denied.",
            )
        if goal.portfolio_id:
            portfolio = repo.get_portfolio(goal.portfolio_id, user_id=current_user.id)

    try:
        return compare_goal_scenarios(payload, goal=goal, portfolio=portfolio)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
