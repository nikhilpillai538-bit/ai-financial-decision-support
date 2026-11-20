"""
Pydantic schemas for Phase 9: AI Financial Intelligence and Decision Support.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Conversational Assistant Schemas
# ---------------------------------------------------------------------------

class FinancialAssistantRequest(BaseModel):
    """User prompt to the conversational financial assistant."""
    question: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Natural-language question or decision-support prompt.",
    )
    conversation_id: Optional[str] = Field(
        None,
        description="UUID of an existing conversation to continue, or None to start a new one.",
    )
    portfolio_id: Optional[str] = Field(
        None,
        description="Optional portfolio UUID to focus portfolio risk and rebalancing queries.",
    )
    provider: Optional[str] = Field(
        None,
        description="Optional provider override ('openai', 'anthropic', 'mock').",
    )


class FinancialAssistantResponse(BaseModel):
    """Guarded and verified answer from the financial assistant."""
    conversation_id: str = Field(..., description="UUID of the active conversation.")
    message_id: str = Field(..., description="UUID of this assistant response message.")
    question: str = Field(..., description="The user's original query.")
    answer: str = Field(..., description="Markdown-formatted grounded answer.")
    cited_domains: List[str] = Field(
        default_factory=list,
        description="Financial domains referenced (e.g. spending, emergency_fund).",
    )
    key_metrics_cited: Dict[str, Any] = Field(
        default_factory=dict,
        description="Exact deterministic metrics cited in the response.",
    )
    limitations_or_missing_data: List[str] = Field(
        default_factory=list,
        description="Missing data points or calculation caveats.",
    )
    suggested_follow_ups: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions for the user.",
    )
    disclaimer: str = Field(
        ...,
        description="Educational and decision-support disclaimer.",
    )
    is_fallback: bool = Field(
        False,
        description="True if generated via deterministic fallback engine.",
    )
    provider_used: str = Field(..., description="Name of LLM provider used.")
    created_at: datetime = Field(..., description="Timestamp of generation.")


# ---------------------------------------------------------------------------
# Conversation History Schemas
# ---------------------------------------------------------------------------

class ConversationMessageResponse(BaseModel):
    """A message in an AI conversation."""
    id: str
    role: str
    content: str
    cited_domains: Optional[List[str]] = None
    key_metrics: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationDetailResponse(BaseModel):
    """A conversation and all its messages."""
    id: str
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ConversationMessageResponse]

    model_config = {"from_attributes": True}


class ConversationListItemResponse(BaseModel):
    """Summary of a user's conversation for list display."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ConversationListResponse(BaseModel):
    """Paginated or listed user conversations."""
    conversations: List[ConversationListItemResponse]
    total_count: int


# ---------------------------------------------------------------------------
# Explainable Insights Schemas
# ---------------------------------------------------------------------------

class InsightItemSchema(BaseModel):
    """Structured insight item for a single financial domain."""
    domain: str
    title: str
    severity: Literal["positive", "info", "warning", "alert"]
    summary: str
    metrics: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)


class FinancialHealthReportResponse(BaseModel):
    """Complete multi-domain financial health assessment."""
    generated_at: str
    user_id: str
    overall_status: Literal["healthy", "attention_needed", "critical", "insufficient_data"]
    executive_summary: str
    insights: List[InsightItemSchema]
    missing_data_warnings: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Hypothetical Scenario Schemas
# ---------------------------------------------------------------------------

class SIPIncreaseScenarioRequest(BaseModel):
    """Parameters for evaluating an increase to monthly SIP."""
    initial_investment: Decimal = Field(default=Decimal("0.00"), ge=0)
    current_monthly_contribution: Decimal = Field(..., gt=0)
    additional_monthly_contribution: Decimal = Field(..., gt=0)
    annual_return_percentage: Decimal = Field(..., ge=0, le=100)
    duration_months: int = Field(..., gt=0, le=600)
    rate_convention: Literal["effective", "nominal"] = "effective"


class ReturnComparisonScenarioRequest(BaseModel):
    """Parameters for comparing two different annual return rates."""
    initial_investment: Decimal = Field(default=Decimal("0.00"), ge=0)
    monthly_contribution: Decimal = Field(..., ge=0)
    duration_months: int = Field(..., gt=0, le=600)
    rate_baseline_percentage: Decimal = Field(..., ge=0, le=100)
    rate_hypothetical_percentage: Decimal = Field(..., ge=0, le=100)
    rate_convention: Literal["effective", "nominal"] = "effective"


class HorizonChangeScenarioRequest(BaseModel):
    """Parameters for evaluating target deadline change on required SIP."""
    target_amount: Decimal = Field(..., gt=0)
    initial_investment: Decimal = Field(default=Decimal("0.00"), ge=0)
    annual_return_percentage: Decimal = Field(..., ge=0, le=100)
    current_duration_months: int = Field(..., gt=0, le=600)
    new_duration_months: int = Field(..., gt=0, le=600)
    rate_convention: Literal["effective", "nominal"] = "effective"


class ScenarioAnalysisRequest(BaseModel):
    """Unified request for evaluating hypothetical financial scenarios."""
    scenario_type: Literal["sip_increase", "return_comparison", "target_date_change"] = Field(
        ...,
        description="Type of deterministic hypothetical scenario to evaluate.",
    )
    sip_increase: Optional[SIPIncreaseScenarioRequest] = None
    return_comparison: Optional[ReturnComparisonScenarioRequest] = None
    horizon_change: Optional[HorizonChangeScenarioRequest] = None


class ScenarioAnalysisResponse(BaseModel):
    """Outcome of a deterministic hypothetical scenario simulation."""
    scenario_type: str
    description: str
    baseline: Dict[str, Any]
    hypothetical: Dict[str, Any]
    difference: Dict[str, Any]
    assumptions: List[str]
    disclaimer: str = (
        "Hypothetical simulation for educational and decision-support purposes only. "
        "Does not mutate user records or guarantee actual market performance."
    )


# ---------------------------------------------------------------------------
# Compatibility Schemas (for frontend /ai/chat, /ai/threads, /ai/health-report, /ai/scenario)
# ---------------------------------------------------------------------------

class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    thread_id: Optional[str] = None
    portfolio_id: Optional[str] = None
    provider: Optional[str] = None


class AIChatResponse(BaseModel):
    message: str
    thread_id: str
    domains_retrieved: List[str] = Field(default_factory=list)
    verified_metrics: Dict[str, Any] = Field(default_factory=dict)
    suggested_followups: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AIThreadSummary(BaseModel):
    thread_id: str
    title: str
    message_count: int
    created_at: str
    last_message_at: str


class AIMessageItem(BaseModel):
    id: str
    role: str
    content: str
    created_at: str
    domains_retrieved: Optional[List[str]] = None
    verified_metrics: Optional[Dict[str, Any]] = None
    suggested_followups: Optional[List[str]] = None
    warnings: Optional[List[str]] = None


class AIThreadDetail(BaseModel):
    thread_id: str
    messages: List[AIMessageItem]


class HealthReportRequest(BaseModel):
    portfolio_id: Optional[str] = None


class FinancialHealthReportCompat(BaseModel):
    user_id: str
    generated_at: str
    executive_summary: str
    health_score: Optional[int] = 85
    domain_insights: Dict[str, str] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    disclaimers: List[str] = Field(default_factory=list)


class ScenarioCompatRequest(BaseModel):
    scenario_type: str
    params: Dict[str, Any] = Field(default_factory=dict)

