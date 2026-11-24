"""
Pydantic schemas for Phase 6: Investment Portfolio Management, Asset Allocation,
Holdings Management, Goals, Deterministic Valuation, and Optimization Readiness.
"""

from datetime import date as DateType, datetime
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.models import AssetClass


def quantize_decimal(value: Decimal, places: int = 2) -> Decimal:
    """Round a Decimal to specified decimal places using ROUND_HALF_UP."""
    exp = Decimal(10) ** -places
    return value.quantize(exp, rounding=ROUND_HALF_UP)


# ---------------------------------------------------------------------------
# Asset Instrument Schemas
# ---------------------------------------------------------------------------

class AssetCreate(BaseModel):
    """Schema for creating a new asset instrument."""

    name: str = Field(..., min_length=1, max_length=255, description="Asset or instrument name.")
    asset_class: AssetClass = Field(..., description="Controlled asset category.")
    symbol: Optional[str] = Field(None, max_length=50, description="Ticker or exchange symbol.")
    currency: str = Field(default="INR", min_length=3, max_length=10, description="Currency code (e.g. INR, USD).")
    instrument_type: Optional[str] = Field(None, max_length=50, description="Sub-classification.")

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Asset name cannot be blank.")
        return s

    @field_validator("currency")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("symbol")
    @classmethod
    def validate_symbol_clean(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip().upper()
            return s if s else None
        return None


class AssetUpdate(BaseModel):
    """Schema for updating an existing user-created asset."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    asset_class: Optional[AssetClass] = None
    symbol: Optional[str] = Field(None, max_length=50)
    currency: Optional[str] = Field(None, min_length=3, max_length=10)
    instrument_type: Optional[str] = Field(None, max_length=50)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip()
            if not s:
                raise ValueError("Asset name cannot be blank.")
            return s
        return None

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper() if v is not None else None


class AssetResponse(BaseModel):
    """Schema for asset instrument response."""

    id: str
    user_id: Optional[str] = None
    symbol: Optional[str] = None
    name: str
    asset_class: str
    currency: str
    instrument_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Portfolio Schemas
# ---------------------------------------------------------------------------

class PortfolioCreate(BaseModel):
    """Schema for creating a new portfolio."""

    name: str = Field(..., min_length=1, max_length=100, description="Portfolio name.")
    description: Optional[str] = Field(None, description="Optional description.")
    base_currency: str = Field(default="INR", min_length=3, max_length=10, description="Base currency code.")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Portfolio name cannot be blank.")
        return s

    @field_validator("base_currency")
    @classmethod
    def validate_base_currency(cls, v: str) -> str:
        return v.strip().upper()


class PortfolioUpdate(BaseModel):
    """Schema for updating a portfolio."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    base_currency: Optional[str] = Field(None, min_length=3, max_length=10)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip()
            if not s:
                raise ValueError("Portfolio name cannot be blank.")
            return s
        return None

    @field_validator("base_currency")
    @classmethod
    def validate_base_currency(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().upper() if v is not None else None


class HoldingResponse(BaseModel):
    """Schema for a holding response with instrument context."""

    id: str
    portfolio_id: str
    asset_id: str
    asset_symbol: Optional[str] = None
    asset_name: str
    asset_class: str
    currency: str
    quantity: Decimal
    average_purchase_price: Decimal
    current_price: Optional[Decimal] = None
    price_as_of: Optional[datetime] = None
    cost_basis: Decimal
    market_value: Optional[Decimal] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PortfolioResponse(BaseModel):
    """Schema for portfolio response."""

    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    base_currency: str
    holding_count: int = 0
    holdings: Optional[List[HoldingResponse]] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Target Allocation Schemas
# ---------------------------------------------------------------------------

VALID_ASSET_CLASSES = {e.value for e in AssetClass}


class TargetAllocationSetRequest(BaseModel):
    """Schema for setting target asset allocation percentages."""

    targets: Dict[str, Decimal] = Field(
        ...,
        description="Map of asset_class to target percentage (e.g. {'equity': 60.0, 'debt': 25.0, 'gold': 10.0, 'cash': 5.0})."
    )
    is_draft: bool = Field(default=False, description="Set to true if allocation is an incomplete draft.")
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_targets(self) -> "TargetAllocationSetRequest":
        if not self.targets:
            raise ValueError("Target allocation must include at least one asset class.")

        clean_targets: Dict[str, Decimal] = {}
        total = Decimal("0.00")

        for key, val in self.targets.items():
            norm_key = key.strip().lower()
            if norm_key not in VALID_ASSET_CLASSES:
                raise ValueError(
                    f"Invalid asset class '{key}'. Supported classes are: {sorted(list(VALID_ASSET_CLASSES))}"
                )
            if val < Decimal("0") or val > Decimal("100"):
                raise ValueError(f"Allocation percentage for '{key}' must be between 0 and 100. Received: {val}")
            
            clean_val = quantize_decimal(Decimal(str(val)), places=2)
            clean_targets[norm_key] = clean_val
            total += clean_val

        self.targets = clean_targets

        # If not draft, total must equal 100% within 0.05% rounding tolerance
        if not self.is_draft:
            diff = abs(total - Decimal("100.00"))
            if diff > Decimal("0.05"):
                raise ValueError(
                    f"Target allocation percentages must sum to 100.00%. Current sum is {total:.2f}%. "
                    "Set is_draft=True to save an incomplete allocation draft."
                )

        return self


class TargetAllocationResponse(BaseModel):
    """Schema for target allocation response."""

    id: str
    portfolio_id: str
    user_id: str
    targets: Dict[str, Decimal]
    is_draft: bool
    total_target_percentage: Decimal
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Investment Goal Schemas
# ---------------------------------------------------------------------------

class InvestmentGoalCreate(BaseModel):
    """Schema for creating an investment goal."""

    name: str = Field(..., min_length=1, max_length=100, description="Goal name.")
    target_amount: Decimal = Field(..., gt=0, description="Target monetary amount (must be > 0).")
    target_date: DateType = Field(..., description="Target milestone completion date (YYYY-MM-DD).")
    portfolio_id: Optional[str] = Field(None, description="Optional portfolio ID linked to this goal.")
    priority: str = Field(default="medium", description="Goal priority: low, medium, or high.")
    status: str = Field(default="in_progress", description="Goal status: in_progress, achieved, paused, behind, on_track.")
    current_amount: Optional[Decimal] = Field(None, ge=0, description="Optional manually recorded current saved amount.")
    initial_lump_sum: Optional[Decimal] = Field(None, ge=0, description="Optional initial lump sum invested.")
    expected_annual_return: Optional[Decimal] = Field(None, ge=-1.0, le=10.0, description="User-supplied expected annual return rate (e.g. 0.12 for 12%).")
    monthly_contribution: Optional[Decimal] = Field(None, ge=0, description="Optional planned monthly contribution.")
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Goal name cannot be blank.")
        return s

    @field_validator("target_amount")
    @classmethod
    def quantize_amount(cls, v: Decimal) -> Decimal:
        return quantize_decimal(v, places=2)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        s = v.strip().lower()
        if s not in {"low", "medium", "high"}:
            raise ValueError("Priority must be one of: 'low', 'medium', 'high'.")
        return s

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        s = v.strip().lower()
        valid = {"in_progress", "achieved", "paused", "behind", "on_track"}
        if s not in valid:
            raise ValueError(f"Status must be one of: {sorted(list(valid))}")
        return s


class InvestmentGoalUpdate(BaseModel):
    """Schema for updating an investment goal."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    target_amount: Optional[Decimal] = Field(None, gt=0)
    target_date: Optional[DateType] = None
    portfolio_id: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    current_amount: Optional[Decimal] = Field(None, ge=0)
    initial_lump_sum: Optional[Decimal] = Field(None, ge=0)
    expected_annual_return: Optional[Decimal] = Field(None, ge=-1.0, le=10.0)
    monthly_contribution: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip()
            if not s:
                raise ValueError("Goal name cannot be blank.")
            return s
        return None

    @field_validator("target_amount")
    @classmethod
    def quantize_amount(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            return quantize_decimal(v, places=2)
        return None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip().lower()
            if s not in {"low", "medium", "high"}:
                raise ValueError("Priority must be one of: 'low', 'medium', 'high'.")
            return s
        return None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip().lower()
            valid = {"in_progress", "achieved", "paused", "behind", "on_track"}
            if s not in valid:
                raise ValueError(f"Status must be one of: {sorted(list(valid))}")
            return s
        return None


class InvestmentGoalResponse(BaseModel):
    """Schema for investment goal with progress calculations."""

    id: str
    user_id: str
    portfolio_id: Optional[str] = None
    name: str
    target_amount: Decimal
    target_date: DateType
    priority: str
    status: str = "in_progress"
    current_amount: Optional[Decimal] = None
    initial_lump_sum: Optional[Decimal] = None
    expected_annual_return: Optional[Decimal] = None
    monthly_contribution: Optional[Decimal] = None
    notes: Optional[str] = None
    current_portfolio_value: Optional[Decimal] = None
    progress_percentage: Optional[Decimal] = None
    remaining_amount: Optional[Decimal] = None
    days_remaining: Optional[int] = None
    warnings: List[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Valuation Schemas
# ---------------------------------------------------------------------------

class AssetClassValuation(BaseModel):
    """Asset class valuation aggregate."""

    asset_class: str
    market_value: Decimal
    allocation_percentage: Decimal
    holdings_count: int


class HoldingValuationItem(BaseModel):
    """Holding item with calculated values."""

    holding_id: str
    asset_id: str
    symbol: Optional[str] = None
    name: str
    asset_class: str
    currency: str
    quantity: Decimal
    average_purchase_price: Decimal
    current_price: Optional[Decimal] = None
    cost_basis: Decimal
    market_value: Optional[Decimal] = None
    unrealized_gain_loss: Optional[Decimal] = None
    unrealized_gain_loss_percentage: Optional[Decimal] = None
    is_priced: bool


class PortfolioValuationResponse(BaseModel):
    """Full deterministic portfolio valuation response."""

    portfolio_id: str
    portfolio_name: str
    base_currency: str
    valuation_as_of: datetime
    priced_holdings_value: Decimal
    cost_basis_priced: Decimal
    cost_basis_all: Decimal
    unrealized_gain_loss: Optional[Decimal] = None
    unrealized_gain_loss_percentage: Optional[Decimal] = None
    asset_class_breakdown: List[AssetClassValuation]
    holdings: List[HoldingValuationItem]
    total_holdings_count: int
    priced_holdings_count: int
    unpriced_holdings_count: int
    valuation_coverage_percentage: Decimal
    has_mixed_currencies: bool
    currencies_present: List[str]
    assumptions: List[str]
    warnings: List[str]


# ---------------------------------------------------------------------------
# Allocation Analysis Schemas
# ---------------------------------------------------------------------------

class AssetClassComparison(BaseModel):
    """Comparison for one asset class against target allocation."""

    asset_class: str
    current_market_value: Decimal
    current_percentage: Decimal
    target_percentage: Optional[Decimal] = None
    difference_percentage_points: Optional[Decimal] = None
    status: str = Field(..., description="'on_target', 'overweight', 'underweight', 'unspecified_target', 'no_holdings'.")


class AllocationAnalysisResponse(BaseModel):
    """Deterministic asset allocation analysis report."""

    portfolio_id: str
    portfolio_name: str
    base_currency: str
    has_target_allocation: bool
    is_target_draft: bool
    valuation_coverage_percentage: Decimal
    comparisons: List[AssetClassComparison]
    overweight_classes: List[str]
    underweight_classes: List[str]
    unspecified_target_classes: List[str]
    missing_holding_classes: List[str]
    is_analysis_reliable: bool
    warnings: List[str]


# ---------------------------------------------------------------------------
# Phase 7 Optimization Readiness Schemas
# ---------------------------------------------------------------------------

class CheckItem(BaseModel):
    """Individual readiness verification check."""

    name: str
    passed: bool
    details: str


class OptimizationReadinessResponse(BaseModel):
    """Pre-optimization readiness validation report for Phase 7."""

    portfolio_id: str
    is_ready_for_optimization: bool
    readiness_status: str = Field(..., description="'ready', 'partially_ready', 'not_ready'.")
    checks: List[CheckItem]
    blockers: List[str]
    warnings: List[str]
