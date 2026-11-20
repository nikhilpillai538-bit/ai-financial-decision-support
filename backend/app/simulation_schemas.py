"""
Pydantic Schemas for Phase 13:
- Portfolio Stress Testing
- Historical Portfolio Backtesting
- Monte Carlo Wealth & Goal Simulation
- Investment-Goal Multi-Scenario Comparison
"""

from datetime import date as DateType, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.portfolio_schemas import quantize_decimal


# ---------------------------------------------------------------------------
# Helper: Quantization
# ---------------------------------------------------------------------------

def _q2(v: Optional[Decimal]) -> Optional[Decimal]:
    if v is None:
        return None
    return quantize_decimal(v, places=2)


def _q4(v: Optional[Decimal]) -> Optional[Decimal]:
    if v is None:
        return None
    return quantize_decimal(v, places=4)


# ---------------------------------------------------------------------------
# 1. Stress Testing Schemas
# ---------------------------------------------------------------------------

class CustomShock(BaseModel):
    """Specific shock percentage to apply to an asset class or individual symbol."""

    asset_class: Optional[str] = Field(
        None,
        description="Asset class target: 'equity', 'fixed_income', 'cash', 'alternatives', 'commodities', etc.",
    )
    symbol: Optional[str] = Field(
        None,
        description="Individual ticker target (e.g. 'RELIANCE.NS', 'AAPL', 'INFY.NS').",
    )
    shock_percentage: Decimal = Field(
        ...,
        ge=-100.0,
        le=500.0,
        description="Shock percentage in % (e.g. -25.0 for a 25% drop).",
    )


class CustomHoldingInput(BaseModel):
    """Optional manual holding for ad-hoc unpersisted stress testing."""

    symbol: str = Field(..., min_length=1, max_length=50)
    asset_class: str = Field(default="equity")
    current_value: Decimal = Field(..., gt=0)


class StressTestRequest(BaseModel):
    """Request payload for running a deterministic portfolio stress test."""

    portfolio_id: Optional[str] = Field(
        None,
        description="Optional ID of saved portfolio to stress-test.",
    )
    custom_holdings: Optional[List[CustomHoldingInput]] = Field(
        None,
        description="Optional list of custom holdings if testing without a saved portfolio.",
    )
    scenario: str = Field(
        default="equity_market_crash",
        description="Predefined scenario identifier ('equity_market_crash', 'bond_market_decline', 'stagflation_shock', 'tech_sector_rout', 'covid_liquidity_shock', 'custom').",
    )
    custom_shocks: Optional[List[CustomShock]] = Field(
        None,
        description="List of custom shocks when scenario='custom' or to override presets.",
    )
    name: Optional[str] = Field(
        None,
        description="Optional user label for this stress test run.",
    )


class HoldingShockResult(BaseModel):
    """Stress test outcome for a single asset holding."""

    symbol: str
    asset_name: str
    asset_class: str
    baseline_value: Decimal
    shock_percentage: Decimal
    stressed_value: Decimal
    absolute_change: Decimal
    contribution_to_loss_pct: Decimal


class AssetClassShockResult(BaseModel):
    """Stress test outcome aggregate for an asset class."""

    asset_class: str
    baseline_value: Decimal
    baseline_weight_pct: Decimal
    shock_percentage: Decimal
    stressed_value: Decimal
    stressed_weight_pct: Decimal
    absolute_change: Decimal
    contribution_to_loss_pct: Decimal


class StressTestResponse(BaseModel):
    """Comprehensive response for a portfolio stress test."""

    scenario_name: str
    description: str
    baseline_portfolio_value: Decimal
    stressed_portfolio_value: Decimal
    absolute_change: Decimal
    percentage_change: Decimal
    holdings_breakdown: List[HoldingShockResult]
    asset_class_breakdown: List[AssetClassShockResult]
    warnings: List[str] = []
    assumptions: List[str] = []
    disclaimers: List[str] = []


# ---------------------------------------------------------------------------
# 2. Historical Portfolio Backtesting Schemas
# ---------------------------------------------------------------------------

class BacktestRequest(BaseModel):
    """Request payload for historical portfolio backtesting."""

    portfolio_id: Optional[str] = Field(
        None,
        description="Optional ID of saved portfolio to backtest using its current holdings.",
    )
    symbols: Optional[List[str]] = Field(
        None,
        description="List of asset symbols if backtesting a custom asset set.",
    )
    weights: Optional[Dict[str, Decimal]] = Field(
        None,
        description="Optional target allocation weights {symbol: weight} where sum(weights) == 1.0.",
    )
    initial_value: Decimal = Field(
        default=Decimal("100000.00"),
        gt=0,
        description="Initial capital at start date.",
    )
    start_date: Optional[DateType] = Field(
        None,
        description="Backtest start date (YYYY-MM-DD). If omitted, earliest common date is used.",
    )
    end_date: Optional[DateType] = Field(
        None,
        description="Backtest end date (YYYY-MM-DD). If omitted, latest common date is used.",
    )
    rebalance_frequency: str = Field(
        default="monthly",
        description="Rebalancing schedule: 'none', 'monthly', 'quarterly', 'annual', 'drift_5pct'.",
    )
    fee_bps: Decimal = Field(
        default=Decimal("10.0"),
        ge=0,
        le=1000.0,
        description="Transaction cost per turnover in basis points (10 bps = 0.10%).",
    )
    benchmark_symbol: Optional[str] = Field(
        None,
        description="Optional benchmark ticker present in dataset for comparative tracking.",
    )
    risk_free_rate_pct: Decimal = Field(
        default=Decimal("6.0"),
        ge=0,
        le=50.0,
        description="Annual risk-free rate percentage for Sharpe ratio calculation (e.g. 6.0 for 6%).",
    )

    @field_validator("rebalance_frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        s = v.strip().lower()
        if s not in {"none", "monthly", "quarterly", "annual", "drift_5pct"}:
            raise ValueError("rebalance_frequency must be one of: 'none', 'monthly', 'quarterly', 'annual', 'drift_5pct'.")
        return s


class BacktestEquityPoint(BaseModel):
    """A single observation along the backtest equity curve."""

    date: str
    portfolio_value: Decimal
    portfolio_return_pct: Decimal
    benchmark_value: Optional[Decimal] = None
    benchmark_return_pct: Optional[Decimal] = None
    drawdown_pct: Decimal


class RebalanceEventItem(BaseModel):
    """Log entry for an executed periodic portfolio rebalancing."""

    date: str
    portfolio_value_pre: Decimal
    turnover_value: Decimal
    transaction_cost: Decimal
    pre_weights: Dict[str, Decimal]
    post_weights: Dict[str, Decimal]


class BacktestBenchmarkSummary(BaseModel):
    """Summary comparative performance metrics for the benchmark."""

    symbol: str
    final_value: Decimal
    cumulative_return_pct: Decimal
    annualized_return_cagr_pct: Decimal
    annualized_volatility_pct: Decimal
    sharpe_ratio: Decimal
    max_drawdown_pct: Decimal


class BacktestResponse(BaseModel):
    """Comprehensive outcome of historical portfolio backtest."""

    symbols: List[str]
    start_date: str
    end_date: str
    trading_days: int
    initial_value: Decimal
    final_value: Decimal
    cumulative_return_pct: Decimal
    annualized_return_cagr_pct: Decimal
    annualized_volatility_pct: Decimal
    sharpe_ratio: Decimal
    max_drawdown_pct: Decimal
    calmar_ratio: Decimal
    total_transaction_costs: Decimal
    rebalance_count: int
    benchmark_summary: Optional[BacktestBenchmarkSummary] = None
    equity_curve: List[BacktestEquityPoint]
    rebalance_events: List[RebalanceEventItem] = []
    warnings: List[str] = []
    assumptions: List[str] = []
    disclaimers: List[str] = []


# ---------------------------------------------------------------------------
# 3. Monte Carlo Simulation Schemas
# ---------------------------------------------------------------------------

class MonteCarloRequest(BaseModel):
    """Request payload for stochastic Monte Carlo wealth projection."""

    portfolio_id: Optional[str] = Field(
        None,
        description="Optional ID of saved portfolio to derive expected return and volatility.",
    )
    initial_value: Decimal = Field(
        default=Decimal("100000.00"),
        gt=0,
        description="Starting portfolio capital at t=0.",
    )
    monthly_contribution: Decimal = Field(
        default=Decimal("0.00"),
        ge=0,
        description="Planned monthly contribution (SIP) deposit.",
    )
    horizon_months: int = Field(
        default=120,
        ge=1,
        le=360,
        description="Simulation horizon in months (1 to 360 months / 30 years).",
    )
    num_simulations: int = Field(
        default=1000,
        ge=100,
        le=5000,
        description="Number of stochastic simulation trajectories (bounded 100 to 5000).",
    )
    expected_annual_return_pct: Optional[Decimal] = Field(
        None,
        ge=-50.0,
        le=100.0,
        description="Expected annualized portfolio drift return in % (e.g. 12.0 for 12%). If omitted, derived from portfolio holdings or default.",
    )
    annual_volatility_pct: Optional[Decimal] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Expected annualized portfolio volatility in % (e.g. 15.0 for 15%). If omitted, derived from historical asset matrix or default.",
    )
    target_amount: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Target wealth milestone to evaluate goal achievement probability.",
    )
    seed: Optional[int] = Field(
        None,
        description="Optional integer random seed for exact deterministic reproducibility.",
    )


class MonteCarloPercentilePoint(BaseModel):
    """Trajectory fan chart slice at a given monthly milestone."""

    month: int
    year: float
    p5: Decimal
    p25: Decimal
    p50: Decimal
    p75: Decimal
    p95: Decimal
    sample_paths: List[Decimal] = []


class TerminalWealthStats(BaseModel):
    """Summary distribution of terminal wealth across all simulated paths."""

    mean: Decimal
    median: Decimal
    std_dev: Decimal
    p5: Decimal
    p25: Decimal
    p75: Decimal
    p95: Decimal
    min: Decimal
    max: Decimal


class MonteCarloResponse(BaseModel):
    """Response payload for Monte Carlo wealth and goal simulation."""

    initial_value: Decimal
    monthly_contribution: Decimal
    horizon_months: int
    num_simulations: int
    annual_return_assumed_pct: Decimal
    annual_volatility_assumed_pct: Decimal
    target_amount: Optional[Decimal] = None
    goal_success_probability_pct: Optional[Decimal] = None
    terminal_wealth: TerminalWealthStats
    percentile_trajectory: List[MonteCarloPercentilePoint]
    warnings: List[str] = []
    assumptions: List[str] = []
    disclaimers: List[str] = []


# ---------------------------------------------------------------------------
# 4. Investment-Goal Scenario Comparison Schemas
# ---------------------------------------------------------------------------

class GoalScenarioOption(BaseModel):
    """Hypothetical parameter variation for comparison against a baseline goal."""

    name: str = Field(..., min_length=1, max_length=80, description="Label for this scenario.")
    monthly_contribution: Optional[Decimal] = Field(None, ge=0)
    horizon_months: Optional[int] = Field(None, ge=1, le=600)
    target_date: Optional[DateType] = None
    expected_annual_return_pct: Optional[Decimal] = Field(None, ge=-50.0, le=100.0)
    initial_amount: Optional[Decimal] = Field(None, ge=0)


class ScenarioComparisonItem(BaseModel):
    """Evaluated metric summary for one scenario variant."""

    name: str
    monthly_contribution: Decimal
    horizon_months: int
    target_date: str
    expected_annual_return_pct: Decimal
    deterministic_projected_value: Decimal
    deterministic_gap: Decimal
    deterministic_required_sip: Decimal
    mc_median_projected_value: Decimal
    mc_p5_downside_value: Decimal
    mc_p95_upside_value: Decimal
    mc_goal_success_probability_pct: Decimal
    contribution_delta_from_baseline: Decimal
    success_probability_delta_pct: Decimal


class GoalScenarioComparisonRequest(BaseModel):
    """Request payload to compare multiple what-if scenario variations."""

    goal_id: Optional[str] = Field(
        None,
        description="Optional ID of existing persisted investment goal to baseline from.",
    )
    baseline_target_amount: Optional[Decimal] = Field(None, gt=0)
    baseline_current_amount: Optional[Decimal] = Field(None, ge=0)
    baseline_monthly_contribution: Optional[Decimal] = Field(None, ge=0)
    baseline_target_date: Optional[DateType] = None
    baseline_annual_return_pct: Optional[Decimal] = Field(None, ge=-50.0, le=100.0)
    scenarios: List[GoalScenarioOption] = Field(
        ...,
        min_length=1,
        max_length=6,
        description="1 to 6 scenario variations to compare.",
    )
    num_simulations: int = Field(default=1000, ge=100, le=2500)
    seed: Optional[int] = Field(default=42)


class GoalScenarioComparisonResponse(BaseModel):
    """Outcome comparison across baseline and hypothetical goal configurations."""

    goal_id: Optional[str] = None
    goal_name: str
    target_amount: Decimal
    baseline: ScenarioComparisonItem
    compared_scenarios: List[ScenarioComparisonItem]
    insights: List[str] = []
    assumptions: List[str] = []
    disclaimers: List[str] = []
