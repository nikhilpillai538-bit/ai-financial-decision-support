"""
Pydantic schemas for Phase 8:
- Forward SIP Calculator
- Reverse SIP Calculator
- Goal-Based Investment Planning & Projections
- Portfolio Drift Detection & Rebalancing Analysis
- Risk-Aware Investment Glide Paths
"""

from datetime import date as DateType, datetime
from decimal import Decimal
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.portfolio_schemas import quantize_decimal


# ---------------------------------------------------------------------------
# Forward & Reverse SIP Schemas
# ---------------------------------------------------------------------------

class SIPScheduleItem(BaseModel):
    """Breakdown for a single period (year or month) of an investment projection."""

    period: int = Field(..., description="Period index (1, 2, ...).")
    period_label: str = Field(..., description="Human-readable label, e.g. 'Year 1' or 'Month 12'.")
    opening_balance: Decimal = Field(..., description="Balance at the beginning of the period.")
    contributions: Decimal = Field(..., description="Contributions deposited during the period.")
    growth_earned: Decimal = Field(..., description="Compound interest/growth earned during the period.")
    closing_balance: Decimal = Field(..., description="Balance at the end of the period.")
    total_contributed_to_date: Decimal = Field(..., description="Cumulative principal invested to date.")


class SIPCalculationRequest(BaseModel):
    """Request payload for Forward SIP projection."""

    initial_investment: Decimal = Field(default=Decimal("0.00"), ge=0, description="Initial lump-sum at t=0.")
    monthly_contribution: Decimal = Field(..., ge=0, description="Recurring monthly contribution.")
    annual_return_percentage: Decimal = Field(..., ge=-100.0, le=1000.0, description="Expected annual return rate in % (e.g. 12.0 for 12%).")
    duration_months: int = Field(..., gt=0, le=600, description="Investment duration in months (1 to 600).")
    rate_convention: str = Field(default="effective", description="'effective' ((1+R)^(1/12)-1) or 'nominal' (R/12).")
    annual_step_up_percentage: Optional[Decimal] = Field(default=None, ge=0, le=100.0, description="Optional annual percentage increase in monthly contribution.")
    include_schedule: bool = Field(default=True, description="Whether to include period-by-period schedule.")

    @field_validator("rate_convention")
    @classmethod
    def validate_convention(cls, v: str) -> str:
        s = v.strip().lower()
        if s not in {"effective", "nominal"}:
            raise ValueError("rate_convention must be either 'effective' or 'nominal'.")
        return s

    @field_validator("initial_investment", "monthly_contribution")
    @classmethod
    def quantize_money(cls, v: Decimal) -> Decimal:
        return quantize_decimal(v, places=2)


class SIPCalculationResponse(BaseModel):
    """Response payload for Forward SIP projection."""

    initial_investment: Decimal
    monthly_contribution: Decimal
    annual_return_percentage: Decimal
    duration_months: int
    rate_convention: str
    projected_future_value: Decimal
    total_contributions: Decimal
    total_invested: Decimal
    estimated_wealth_gain: Decimal
    annual_step_up_percentage: Optional[Decimal] = None
    schedule: List[SIPScheduleItem] = []
    assumptions: List[str] = []
    disclaimers: List[str] = []


class ReverseSIPRequest(BaseModel):
    """Request payload for Reverse SIP target solver."""

    target_amount: Decimal = Field(..., gt=0, description="Target future corpus required.")
    initial_investment: Decimal = Field(default=Decimal("0.00"), ge=0, description="Existing initial corpus at t=0.")
    annual_return_percentage: Decimal = Field(..., ge=0.0, le=1000.0, description="Expected annual return rate in % (e.g. 12.0 for 12%).")
    duration_months: int = Field(..., gt=0, le=600, description="Duration in months to reach the goal.")
    rate_convention: str = Field(default="effective", description="'effective' or 'nominal'.")
    include_schedule: bool = Field(default=True, description="Whether to include period-by-period schedule.")

    @field_validator("rate_convention")
    @classmethod
    def validate_convention(cls, v: str) -> str:
        s = v.strip().lower()
        if s not in {"effective", "nominal"}:
            raise ValueError("rate_convention must be either 'effective' or 'nominal'.")
        return s

    @field_validator("target_amount", "initial_investment")
    @classmethod
    def quantize_money(cls, v: Decimal) -> Decimal:
        return quantize_decimal(v, places=2)


class ReverseSIPResponse(BaseModel):
    """Response payload for Reverse SIP target solver."""

    target_amount: Decimal
    initial_investment: Decimal
    annual_return_percentage: Decimal
    duration_months: int
    rate_convention: str
    required_monthly_contribution: Decimal
    projected_future_value: Decimal
    total_contributions: Decimal
    total_invested: Decimal
    estimated_wealth_gain: Decimal
    is_target_already_covered: bool
    schedule: List[SIPScheduleItem] = []
    explanation: str
    assumptions: List[str] = []
    disclaimers: List[str] = []


# ---------------------------------------------------------------------------
# Goal Planning & Projection Schemas
# ---------------------------------------------------------------------------

class GoalProjectionRequest(BaseModel):
    """Request payload to project an existing investment goal with optional overrides."""

    expected_annual_return: Optional[Decimal] = Field(None, ge=-1.0, le=10.0, description="Expected annual return rate (e.g. 0.12 for 12%). Overrides stored goal return.")
    monthly_contribution: Optional[Decimal] = Field(None, ge=0, description="Planned monthly contribution. Overrides stored goal contribution.")
    current_amount: Optional[Decimal] = Field(None, ge=0, description="Current amount invested. Overrides linked portfolio valuation or stored amount.")
    target_date: Optional[DateType] = Field(None, description="Optional override for target date.")
    rate_convention: str = Field(default="effective", description="'effective' or 'nominal'.")
    as_of_date: Optional[DateType] = Field(None, description="As-of evaluation date (defaults to today).")

    @field_validator("rate_convention")
    @classmethod
    def validate_convention(cls, v: str) -> str:
        s = v.strip().lower()
        if s not in {"effective", "nominal"}:
            raise ValueError("rate_convention must be either 'effective' or 'nominal'.")
        return s


class StandaloneGoalPlanRequest(BaseModel):
    """Request payload for standalone goal planning without requiring an existing DB goal."""

    goal_name: str = Field(..., min_length=1, max_length=100)
    target_amount: Decimal = Field(..., gt=0)
    target_date: DateType = Field(...)
    current_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    expected_annual_return: Decimal = Field(default=Decimal("0.1000"), ge=-1.0, le=10.0)
    planned_monthly_contribution: Decimal = Field(default=Decimal("0.00"), ge=0)
    rate_convention: str = Field(default="effective")
    as_of_date: Optional[DateType] = None

    @field_validator("rate_convention")
    @classmethod
    def validate_convention(cls, v: str) -> str:
        s = v.strip().lower()
        if s not in {"effective", "nominal"}:
            raise ValueError("rate_convention must be either 'effective' or 'nominal'.")
        return s


class GoalProjectionResponse(BaseModel):
    """Comprehensive goal progress, projection, gap analysis, and recommendations."""

    goal_id: Optional[str] = None
    goal_name: str
    target_amount: Decimal
    current_amount: Decimal
    progress_percentage: Decimal
    remaining_amount: Decimal
    target_date: DateType
    as_of_date: DateType
    remaining_months: int
    expected_annual_return: Decimal
    rate_convention: str
    planned_monthly_contribution: Decimal
    projected_future_value: Decimal
    shortfall_or_surplus: Decimal
    is_on_track: bool
    required_monthly_contribution: Decimal
    contribution_difference: Decimal
    status_assessment: str  # "on_track", "ahead", "behind", "expired"
    schedule: List[SIPScheduleItem] = []
    assumptions: List[str] = []
    warnings: List[str] = []


# ---------------------------------------------------------------------------
# Portfolio Drift Detection & Rebalancing Schemas
# ---------------------------------------------------------------------------

class AssetClassDrift(BaseModel):
    """Allocation drift details for a single asset class."""

    asset_class: str
    current_market_value: Decimal
    current_weight_percentage: Decimal
    target_weight_percentage: Optional[Decimal] = None
    absolute_drift_percentage_points: Optional[Decimal] = None
    relative_drift_percentage: Optional[Decimal] = None
    status: str  # "on_target", "overweight", "underweight", "unspecified_target"
    exceeds_threshold: bool = False


class PortfolioDriftResponse(BaseModel):
    """Response payload for portfolio drift analysis."""

    portfolio_id: str
    portfolio_name: str
    base_currency: str
    total_portfolio_value: Decimal
    drift_threshold_percentage_points: Decimal
    portfolio_exceeds_threshold: bool
    max_drift_percentage_points: Decimal
    asset_classes: List[AssetClassDrift]
    drifted_classes: List[str]
    is_analysis_reliable: bool
    warnings: List[str] = []
    as_of_timestamp: datetime


class RebalanceTradeItem(BaseModel):
    """Illustrative trade recommendation to rebalance an asset class to target weight."""

    asset_class: str
    current_weight_percentage: Decimal
    target_weight_percentage: Decimal
    current_market_value: Decimal
    target_market_value: Decimal
    weight_delta_percentage_points: Decimal
    action: str  # "BUY", "SELL", "HOLD"
    trade_amount: Decimal


class RebalanceAnalysisResponse(BaseModel):
    """Response payload for illustrative portfolio rebalancing analysis."""

    portfolio_id: str
    portfolio_name: str
    base_currency: str
    total_portfolio_value: Decimal
    drift_threshold_percentage_points: Decimal
    trades: List[RebalanceTradeItem]
    total_buy_amount: Decimal
    total_sell_amount: Decimal
    reconciliation_difference: Decimal
    is_rebalancing_recommended: bool
    disclaimers: List[str] = []
    warnings: List[str] = []


# ---------------------------------------------------------------------------
# Risk-Aware Investment Glide Path Schemas
# ---------------------------------------------------------------------------

class GlidePathRequest(BaseModel):
    """Request payload to generate a risk-aware investment glide path."""

    target_date: Optional[DateType] = Field(None, description="Target milestone completion date.")
    start_date: Optional[DateType] = Field(None, description="Starting evaluation date (defaults to today).")
    starting_allocation: Optional[Dict[str, Decimal]] = Field(None, description="Starting asset class weights (sum to 100%).")
    ending_allocation: Optional[Dict[str, Decimal]] = Field(None, description="Ending target asset class weights (sum to 100%).")
    interval_months: int = Field(default=12, ge=1, le=60, description="Checkpoint interval in months (e.g. 12 for annual).")
    risk_profile: Optional[str] = Field(default="moderate", description="'conservative', 'moderate', or 'aggressive'.")

    @field_validator("risk_profile")
    @classmethod
    def validate_risk(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip().lower()
            if s not in {"conservative", "moderate", "aggressive"}:
                raise ValueError("risk_profile must be 'conservative', 'moderate', or 'aggressive'.")
            return s
        return "moderate"


class GlidePathCheckpoint(BaseModel):
    """A single milestone checkpoint along the investment glide path."""

    checkpoint_index: int
    checkpoint_date: DateType
    years_remaining: Decimal
    months_remaining: int
    allocation_weights: Dict[str, Decimal]
    risk_level: str  # "aggressive", "moderate", "conservative"
    commentary: str


class GlidePathResponse(BaseModel):
    """Response payload for risk-aware investment glide path."""

    goal_id: Optional[str] = None
    goal_name: Optional[str] = None
    start_date: DateType
    target_date: DateType
    total_horizon_years: Decimal
    interval_months: int
    starting_allocation: Dict[str, Decimal]
    ending_allocation: Dict[str, Decimal]
    checkpoints: List[GlidePathCheckpoint]
    assumptions: List[str] = []
    warnings: List[str] = []
