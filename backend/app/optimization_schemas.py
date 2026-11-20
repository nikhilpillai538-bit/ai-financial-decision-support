"""
Pydantic schemas for Phase 7: Modern Portfolio Theory (MPT), Risk Metrics,
Historical Price Ingestion, and Explainable Portfolio Optimization.
"""

from datetime import date as DateType, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.portfolio_schemas import quantize_decimal


class OptimizationStrategy(str, Enum):
    """Supported Modern Portfolio Theory optimization strategies."""

    MIN_VOLATILITY = "min_volatility"
    MAX_SHARPE = "max_sharpe"
    TARGET_RETURN = "target_return"
    USER_CONSTRAINED = "user_constrained"


# ---------------------------------------------------------------------------
# Historical Price Schemas
# ---------------------------------------------------------------------------

class HistoricalPriceRow(BaseModel):
    """Schema for a single historical price observation."""

    date: DateType = Field(..., description="Trading date (YYYY-MM-DD).")
    symbol: str = Field(..., min_length=1, max_length=50, description="Ticker symbol.")
    adjusted_close: Decimal = Field(..., gt=0, description="Adjusted closing price (> 0).")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        s = v.strip().upper()
        if not s:
            raise ValueError("Symbol cannot be blank.")
        return s

    @field_validator("adjusted_close")
    @classmethod
    def quantize_price(cls, v: Decimal) -> Decimal:
        return quantize_decimal(v, places=4)


class HistoricalPriceResponse(BaseModel):
    """Schema for historical price query responses."""

    symbol: str
    date: DateType
    adjusted_close: Decimal
    source: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HistoricalPriceImportResponse(BaseModel):
    """Report returned after parsing and storing a historical price CSV upload."""

    filename: Optional[str] = None
    total_rows: int
    imported: int
    skipped_duplicates: int
    rejected: int
    symbols_updated: List[str]
    errors: List[str]


# ---------------------------------------------------------------------------
# Portfolio Optimization Request Schemas
# ---------------------------------------------------------------------------

class AssetWeightBound(BaseModel):
    """Upper and lower bounds for an individual asset."""

    min_weight: Decimal = Field(default=Decimal("0.00"), ge=0, le=1)
    max_weight: Decimal = Field(default=Decimal("1.00"), ge=0, le=1)

    @model_validator(mode="after")
    def validate_bounds(self) -> "AssetWeightBound":
        if self.min_weight > self.max_weight:
            raise ValueError(f"min_weight ({self.min_weight}) cannot exceed max_weight ({self.max_weight}).")
        return self


class OptimizationRequest(BaseModel):
    """Request payload for executing Modern Portfolio Theory optimization."""

    strategy: OptimizationStrategy = Field(
        default=OptimizationStrategy.MAX_SHARPE,
        description="Target optimization objective.",
    )
    risk_free_rate: Decimal = Field(
        default=Decimal("0.0600"),
        ge=Decimal("0.0000"),
        le=Decimal("0.5000"),
        description="Annualized risk-free rate (e.g. 0.06 for 6.0% T-Bills).",
    )
    target_return: Optional[Decimal] = Field(
        None,
        ge=Decimal("-0.5000"),
        le=Decimal("2.0000"),
        description="Annualized target return required when using 'target_return' strategy.",
    )
    min_weight: Decimal = Field(
        default=Decimal("0.0000"),
        ge=Decimal("0.0000"),
        le=Decimal("1.0000"),
        description="Global minimum weight per holding (default 0.0, long-only).",
    )
    max_weight: Decimal = Field(
        default=Decimal("1.0000"),
        ge=Decimal("0.0000"),
        le=Decimal("1.0000"),
        description="Global maximum weight per holding (default 1.0 = 100%).",
    )
    asset_bounds: Optional[Dict[str, AssetWeightBound]] = Field(
        None,
        description="Per-asset custom weight constraints mapping symbol to {min_weight, max_weight}.",
    )
    min_observations: int = Field(
        default=20,
        ge=10,
        le=1260,
        description="Minimum aligned historical trading days required (default 20).",
    )
    include_efficient_frontier: bool = Field(
        default=True,
        description="Whether to generate discrete points along the Markowitz efficient frontier.",
    )
    csv_content: Optional[str] = Field(
        None,
        description="Optional inline CSV string with historical prices (date,symbol,adjusted_close).",
    )


# ---------------------------------------------------------------------------
# Portfolio Optimization Response Schemas
# ---------------------------------------------------------------------------

class OptimizedHoldingAllocation(BaseModel):
    """Detailed allocation and rebalancing recommendation for a single holding."""

    asset_id: str
    symbol: str
    name: str
    asset_class: str
    current_weight: Decimal
    optimal_weight: Decimal
    weight_delta: Decimal
    current_value: Decimal
    target_value: Decimal
    action: str = Field(..., description="'BUY', 'SELL', or 'HOLD'.")
    trade_amount: Decimal


class AssetClassOptimizationSummary(BaseModel):
    """Aggregated allocation comparison by asset class."""

    asset_class: str
    current_weight: Decimal
    optimal_weight: Decimal
    target_allocation_weight: Optional[Decimal] = None
    weight_delta: Decimal


class EfficientFrontierPoint(BaseModel):
    """A discrete risk-return tradeoff point on the Markowitz efficient frontier."""

    expected_return: Decimal
    expected_volatility: Decimal
    sharpe_ratio: Decimal
    weights: Dict[str, Decimal]


class PortfolioOptimizationResponse(BaseModel):
    """Comprehensive explainable response for an MPT portfolio optimization run."""

    portfolio_id: str
    portfolio_name: str
    base_currency: str
    strategy: str
    risk_free_rate: Decimal
    expected_return: Decimal
    expected_volatility: Decimal
    sharpe_ratio: Decimal
    current_portfolio_return: Optional[Decimal] = None
    current_portfolio_volatility: Optional[Decimal] = None
    current_portfolio_sharpe: Optional[Decimal] = None
    volatility_reduction_percentage: Optional[Decimal] = None
    sharpe_improvement: Optional[Decimal] = None
    total_portfolio_value: Decimal
    allocations: List[OptimizedHoldingAllocation]
    asset_class_summary: List[AssetClassOptimizationSummary]
    efficient_frontier: List[EfficientFrontierPoint]
    observation_count: int
    start_date: DateType
    end_date: DateType
    methodology: str
    assumptions: List[str]
    warnings: List[str]
    run_id: Optional[str] = None


class OptimizationRunSummary(BaseModel):
    """Historical summary of an optimization execution."""

    id: str
    portfolio_id: str
    strategy: str
    risk_free_rate: Decimal
    expected_return: Decimal
    expected_volatility: Decimal
    sharpe_ratio: Decimal
    weights: Dict[str, Decimal]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Yahoo Finance Auto-Fetch & Live Market Schemas
# ---------------------------------------------------------------------------

class YahooFetchHistoricalRequest(BaseModel):
    """Payload to trigger automatic Yahoo Finance historical price ingestion."""

    symbols: List[str] = Field(..., min_length=1, description="List of stock/ETF symbols (e.g. RELIANCE.NS, TCS.NS, AAPL)")
    period: str = Field(default="1y", description="Time period ('1mo', '3mo', '6mo', '1y', '2y', '5y')")
    portfolio_id: Optional[str] = Field(default=None, description="Optional portfolio ID to associate or validate")


class YahooFetchHistoricalResponse(BaseModel):
    """Response detailing ingested historical prices from Yahoo Finance."""

    symbols_requested: List[str]
    symbols_successful: List[str]
    symbols_failed: List[str]
    imported_rows: int
    skipped_rows: int
    period: str
    date_range_start: Optional[DateType] = None
    date_range_end: Optional[DateType] = None
    message: str


class MarketQuoteItem(BaseModel):
    """Live quote observation for an individual symbol."""

    symbol: str
    last_price: Decimal
    currency: str
    previous_close: Optional[Decimal] = None
    change: Optional[Decimal] = None
    change_percent: Optional[Decimal] = None
    fetched_at: str


class MarketQuotesResponse(BaseModel):
    """Response containing live quotes for multiple symbols."""

    quotes: Dict[str, MarketQuoteItem]
    count: int


class MarketQuotesRequest(BaseModel):
    """Request payload for multiple quotes."""

    symbols: List[str] = Field(..., min_length=1, description="Symbols to retrieve quotes for")


class PortfolioMarketSyncHoldingItem(BaseModel):
    """Individual holding update summary from a live market sync."""

    holding_id: str
    symbol: str
    asset_name: str
    old_price: Optional[Decimal]
    new_price: Decimal
    currency: str


class PortfolioMarketSyncResponse(BaseModel):
    """Response summarizing a portfolio live market price sync."""

    portfolio_id: str
    synced_count: int
    failed_count: int
    updated_holdings: List[PortfolioMarketSyncHoldingItem]
    message: str


class MarketPresetItem(BaseModel):
    """Curated market ticker group preset."""

    id: str
    name: str
    description: str
    symbols: List[str]

