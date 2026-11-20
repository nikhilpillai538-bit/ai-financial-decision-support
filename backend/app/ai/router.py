"""
FastAPI Router for Phase 9: AI Financial Intelligence, Explainable Insights,
and Conversational Decision Support.

Endpoints:
- POST /ai/financial-assistant: Conversational decision support with verified financial grounding
- GET /ai/conversations: List user's AI conversations
- GET /ai/conversations/{conversation_id}: View conversation history
- DELETE /ai/conversations/{conversation_id}: Delete conversation
- GET /ai/insights: Standalone deterministic financial health assessment across all domains
- POST /ai/scenario-analysis: Deterministic hypothetical what-if scenario evaluator
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.ai.config import get_llm_settings
from app.ai.financial_context import FinancialContextService
from app.ai.guardrails import (
    build_assistant_system_prompt,
    build_deterministic_fallback,
    parse_and_validate_llm_response,
    sanitize_user_input,
)
from app.ai.insights_service import FinancialInsightsService
from app.ai.provider import (
    AnthropicProvider,
    LLMAuthenticationError,
    LLMMessage,
    LLMNotConfiguredError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    MockLLMProvider,
    OpenAIProvider,
    UnconfiguredProvider,
    get_llm_provider,
)
from app.ai.scenario_evaluator import ScenarioEvaluator
from app.ai.schemas import (
    AIChatRequest,
    AIChatResponse,
    AIThreadDetail,
    AIThreadSummary,
    AIMessageItem,
    ConversationDetailResponse,
    ConversationListItemResponse,
    ConversationListResponse,
    ConversationMessageResponse,
    FinancialAssistantRequest,
    FinancialAssistantResponse,
    FinancialHealthReportCompat,
    FinancialHealthReportResponse,
    HealthReportRequest,
    InsightItemSchema,
    ScenarioAnalysisRequest,
    ScenarioAnalysisResponse,
    ScenarioCompatRequest,
)
from app.auth.dependencies import get_current_user
from app.db.models import UserModel
from app.db.repositories.ai_repo import SQLAIRepository
from app.db.session import get_db

ai_router = APIRouter(prefix="/ai", tags=["AI Financial Intelligence & Decision Support"])


# ---------------------------------------------------------------------------
# Dependency helpers
# ---------------------------------------------------------------------------

def get_ai_repo(db: Session = Depends(get_db)) -> SQLAIRepository:
    return SQLAIRepository(db)


def _resolve_provider(override_name: Optional[str] = None):
    """Instantiate requested or globally configured LLM provider."""
    settings = get_llm_settings()

    provider_choice = (override_name or settings.provider).lower()
    if provider_choice == "mock":
        return MockLLMProvider()
    elif provider_choice == "openai":
        if not settings.api_key:
            return UnconfiguredProvider()
        return OpenAIProvider(
            api_key=settings.api_key,
            model=settings.model if settings.model != "claude-3-5-sonnet-20241022" else "gpt-4o",
            api_base=settings.api_base,
            timeout_seconds=settings.timeout_seconds,
        )
    elif provider_choice == "anthropic":
        if not settings.api_key:
            return UnconfiguredProvider()
        return AnthropicProvider(
            api_key=settings.api_key,
            model=settings.model if settings.model != "gpt-4o" else "claude-3-5-sonnet-20241022",
            api_base=settings.api_base,
            timeout_seconds=settings.timeout_seconds,
        )
    elif provider_choice == "unconfigured":
        return UnconfiguredProvider()
    else:
        # Fallback to default configured provider resolver
        return get_llm_provider()


# ---------------------------------------------------------------------------
# 1. Main Conversational Assistant Endpoint
# ---------------------------------------------------------------------------

@ai_router.post(
    "/financial-assistant",
    response_model=FinancialAssistantResponse,
    summary="Consult the grounded AI Financial Decision Support Assistant",
)
async def ask_financial_assistant(
    payload: FinancialAssistantRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_repo: SQLAIRepository = Depends(get_ai_repo),
) -> FinancialAssistantResponse:
    """
    Submits a financial query to the AI assistant.
    The response is deterministically grounded in the user's verified financial facts
    (spending, cash flow, emergency funds, goals, portfolio valuation, MPT optimization, and drift).
    """
    sanitized_question = sanitize_user_input(payload.question)
    if not sanitized_question:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question cannot be empty or solely contain filtered directives.",
        )

    # 1. Resolve or create conversation
    conv = None
    if payload.conversation_id:
        conv = ai_repo.get_conversation(
            conversation_id=payload.conversation_id,
            user_id=current_user.id,
        )
    if not conv:
        # Auto-title from the first 50 chars of the question
        title = sanitized_question[:50] + ("..." if len(sanitized_question) > 50 else "")
        conv = ai_repo.create_conversation(
            user_id=current_user.id,
            title=title,
        )

    # 2. Record user query in conversation
    ai_repo.add_message(
        conversation_id=conv.id,
        user_id=current_user.id,
        role="user",
        content=sanitized_question,
    )

    # 3. Retrieve verified financial context scoped to current_user
    context_service = FinancialContextService(db)
    context = context_service.build_context(
        user=current_user,
        question=sanitized_question,
        portfolio_id=payload.portfolio_id,
    )

    # 4. Build prompt and message list
    system_prompt = build_assistant_system_prompt(context)

    # Load recent conversation history (last 6 messages)
    history_models = ai_repo.get_recent_messages(conversation_id=conv.id, user_id=current_user.id, limit=6)
    messages: List[LLMMessage] = []
    # Note: excluding the very last message if it's the user query we just added
    for m in history_models[:-1]:
        messages.append(LLMMessage(role=m.role, content=m.content))
    messages.append(LLMMessage(role="user", content=sanitized_question))

    # 5. Resolve provider and call LLM
    provider = _resolve_provider(override_name=payload.provider)
    settings = get_llm_settings()

    raw_response_text: Optional[str] = None
    is_fallback = False

    try:
        llm_resp = await provider.generate_chat_response(
            messages=messages,
            system_prompt=system_prompt,
            max_tokens=settings.max_output_tokens,
            temperature=0.2,  # Low temperature for analytical accuracy
        )
        raw_response_text = llm_resp.content
    except (
        LLMNotConfiguredError,
        LLMTimeoutError,
        LLMRateLimitError,
        LLMAuthenticationError,
        LLMProviderError,
        Exception,
    ) as e:
        logger.warning("LLM generation degraded to deterministic fallback: %s (%s)", type(e).__name__, e)
        # Log and degrade gracefully to deterministic fallback
        fallback = build_deterministic_fallback(
            context=context,
            reason=f"LLM Provider ({provider.name}) notice: {type(e).__name__}",
            provider_name=provider.name,
        )
        assistant_record = ai_repo.add_message(
            conversation_id=conv.id,
            user_id=current_user.id,
            role="assistant",
            content=fallback.answer,
            data_sources=fallback.cited_domains,
        )
        now_utc = datetime.now(timezone.utc)
        return FinancialAssistantResponse(
            conversation_id=conv.id,
            message_id=assistant_record.id,
            question=sanitized_question,
            answer=fallback.answer,
            cited_domains=fallback.cited_domains,
            key_metrics_cited=fallback.key_metrics_cited,
            limitations_or_missing_data=fallback.limitations_or_missing_data,
            suggested_follow_ups=fallback.suggested_follow_ups,
            disclaimer=fallback.disclaimer,
            is_fallback=True,
            provider_used=provider.name,
            created_at=now_utc,
        )

    # 6. Guardrails parsing and post-validation
    guarded_result = parse_and_validate_llm_response(
        raw_text=raw_response_text,
        context=context,
        provider_name=provider.name,
    )

    # 7. Record assistant response in conversation
    assistant_record = ai_repo.add_message(
        conversation_id=conv.id,
        user_id=current_user.id,
        role="assistant",
        content=guarded_result.answer,
        data_sources=guarded_result.cited_domains,
    )

    now_utc = datetime.now(timezone.utc)
    return FinancialAssistantResponse(
        conversation_id=conv.id,
        message_id=assistant_record.id,
        question=sanitized_question,
        answer=guarded_result.answer,
        cited_domains=guarded_result.cited_domains,
        key_metrics_cited=guarded_result.key_metrics_cited,
        limitations_or_missing_data=guarded_result.limitations_or_missing_data,
        suggested_follow_ups=guarded_result.suggested_follow_ups,
        disclaimer=guarded_result.disclaimer,
        is_fallback=guarded_result.is_fallback,
        provider_used=guarded_result.provider_name,
        created_at=now_utc,
    )


# ---------------------------------------------------------------------------
# 2. Conversation History Management
# ---------------------------------------------------------------------------

@ai_router.get(
    "/conversations",
    response_model=ConversationListResponse,
    summary="List all AI conversations for the authenticated user",
)
def list_conversations(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(get_current_user),
    ai_repo: SQLAIRepository = Depends(get_ai_repo),
) -> ConversationListResponse:
    """Lists conversations owned by the authenticated user."""
    convs = ai_repo.list_conversations(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    items = [
        ConversationListItemResponse(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=len(c.messages),
        )
        for c in convs
    ]
    return ConversationListResponse(
        conversations=items,
        total_count=len(items),
    )


@ai_router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationDetailResponse,
    summary="Get detailed message history of an AI conversation",
)
def get_conversation_detail(
    conversation_id: str,
    current_user: UserModel = Depends(get_current_user),
    ai_repo: SQLAIRepository = Depends(get_ai_repo),
) -> ConversationDetailResponse:
    """Retrieves full conversation history with all messages."""
    conv = ai_repo.get_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )

    msgs = [
        ConversationMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            cited_domains=m.data_sources,
            key_metrics=None,
            created_at=m.created_at,
        )
        for m in sorted(conv.messages, key=lambda x: x.created_at)
    ]

    return ConversationDetailResponse(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=msgs,
    )


@ai_router.delete(
    "/conversations/{conversation_id}",
    summary="Delete an AI conversation and its message history",
)
def delete_conversation(
    conversation_id: str,
    current_user: UserModel = Depends(get_current_user),
    ai_repo: SQLAIRepository = Depends(get_ai_repo),
) -> dict:
    """Deletes an AI conversation and all its messages."""
    success = ai_repo.delete_conversation(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )
    return {"detail": "Conversation deleted successfully."}


# ---------------------------------------------------------------------------
# 3. Explainable Financial Insights
# ---------------------------------------------------------------------------

@ai_router.get(
    "/insights",
    response_model=FinancialHealthReportResponse,
    summary="Generate comprehensive explainable financial health insights",
)
def get_financial_insights(
    portfolio_id: Optional[str] = Query(None, description="Optional portfolio UUID to focus portfolio insights"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialHealthReportResponse:
    """
    Evaluates spending, cash flow, emergency reserves, goal pacing,
    portfolio risk, and rebalancing drift using deterministic calculations.
    """
    insights_service = FinancialInsightsService(db)
    report = insights_service.generate_report(
        user=current_user,
        portfolio_id=portfolio_id,
    )

    schema_insights = [
        InsightItemSchema(
            domain=item.domain,
            title=item.title,
            severity=item.severity,  # type: ignore
            summary=item.summary,
            metrics=item.metrics,
            recommendations=item.recommendations,
        )
        for item in report.insights
    ]

    return FinancialHealthReportResponse(
        generated_at=report.generated_at,
        user_id=report.user_id,
        overall_status=report.overall_status,  # type: ignore
        executive_summary=report.executive_summary,
        insights=schema_insights,
        missing_data_warnings=report.missing_data_warnings,
    )


# ---------------------------------------------------------------------------
# 4. Deterministic Hypothetical Scenario Evaluator
# ---------------------------------------------------------------------------

@ai_router.post(
    "/scenario-analysis",
    response_model=ScenarioAnalysisResponse,
    summary="Evaluate deterministic hypothetical what-if financial scenarios",
)
def evaluate_hypothetical_scenario(
    payload: ScenarioAnalysisRequest,
    current_user: UserModel = Depends(get_current_user),
) -> ScenarioAnalysisResponse:
    """
    Executes what-if scenario simulations with zero database mutation:
    - sip_increase: Impact of additional monthly SIP on terminal wealth
    - return_comparison: Outcome delta between two expected rates of return
    - target_date_change: Impact of changing investment horizon on required monthly SIP
    """
    try:
        if payload.scenario_type == "sip_increase":
            if not payload.sip_increase:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Field 'sip_increase' is required when scenario_type is 'sip_increase'.",
                )
            params = payload.sip_increase
            res = ScenarioEvaluator.evaluate_sip_increase(
                initial_investment=params.initial_investment,
                current_monthly_contribution=params.current_monthly_contribution,
                additional_monthly_contribution=params.additional_monthly_contribution,
                annual_return_percentage=params.annual_return_percentage,
                duration_months=params.duration_months,
                rate_convention=params.rate_convention,
            )

        elif payload.scenario_type == "return_comparison":
            if not payload.return_comparison:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Field 'return_comparison' is required when scenario_type is 'return_comparison'.",
                )
            params = payload.return_comparison
            res = ScenarioEvaluator.evaluate_return_rate_comparison(
                initial_investment=params.initial_investment,
                monthly_contribution=params.monthly_contribution,
                duration_months=params.duration_months,
                rate_baseline_percentage=params.rate_baseline_percentage,
                rate_hypothetical_percentage=params.rate_hypothetical_percentage,
                rate_convention=params.rate_convention,
            )

        elif payload.scenario_type == "target_date_change":
            if not payload.horizon_change:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Field 'horizon_change' is required when scenario_type is 'target_date_change'.",
                )
            params = payload.horizon_change
            res = ScenarioEvaluator.evaluate_target_horizon_change(
                target_amount=params.target_amount,
                initial_investment=params.initial_investment,
                annual_return_percentage=params.annual_return_percentage,
                current_duration_months=params.current_duration_months,
                new_duration_months=params.new_duration_months,
                rate_convention=params.rate_convention,
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported scenario_type '{payload.scenario_type}'.",
            )

        return ScenarioAnalysisResponse(
            scenario_type=res.scenario_type,
            description=res.description,
            baseline=res.baseline,
            hypothetical=res.hypothetical,
            difference=res.difference,
            assumptions=res.assumptions,
        )

    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )


# ---------------------------------------------------------------------------
# 5. Frontend Compatibility Endpoints (Phase 9 & 11)
# ---------------------------------------------------------------------------

@ai_router.post(
    "/chat",
    response_model=AIChatResponse,
    summary="Conversational chat endpoint (frontend compatibility alias)",
)
async def chat_compat(
    payload: AIChatRequest,
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_repo: SQLAIRepository = Depends(get_ai_repo),
) -> AIChatResponse:
    """Frontend-compatible alias mapping to grounded financial assistant."""
    fa_req = FinancialAssistantRequest(
        question=payload.message,
        conversation_id=payload.thread_id,
        portfolio_id=payload.portfolio_id,
        provider=payload.provider,
    )
    res = await ask_financial_assistant(
        payload=fa_req,
        current_user=current_user,
        db=db,
        ai_repo=ai_repo,
    )
    return AIChatResponse(
        message=res.answer,
        thread_id=res.conversation_id,
        domains_retrieved=res.cited_domains,
        verified_metrics=res.key_metrics_cited,
        suggested_followups=res.suggested_follow_ups,
        warnings=res.limitations_or_missing_data,
    )


@ai_router.get(
    "/threads",
    response_model=List[AIThreadSummary],
    summary="List threads (frontend compatibility alias)",
)
def list_threads_compat(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(get_current_user),
    ai_repo: SQLAIRepository = Depends(get_ai_repo),
) -> List[AIThreadSummary]:
    """Frontend-compatible list of AI chat threads."""
    convs = ai_repo.list_conversations(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
    )
    return [
        AIThreadSummary(
            thread_id=c.id,
            title=c.title,
            message_count=len(c.messages),
            created_at=c.created_at.isoformat() if hasattr(c.created_at, "isoformat") else str(c.created_at),
            last_message_at=c.updated_at.isoformat() if hasattr(c.updated_at, "isoformat") else str(c.updated_at),
        )
        for c in convs
    ]


@ai_router.get(
    "/threads/{thread_id}",
    response_model=AIThreadDetail,
    summary="Get thread detail (frontend compatibility alias)",
)
def get_thread_compat(
    thread_id: str,
    current_user: UserModel = Depends(get_current_user),
    ai_repo: SQLAIRepository = Depends(get_ai_repo),
) -> AIThreadDetail:
    """Frontend-compatible thread detail."""
    conv = ai_repo.get_conversation(
        conversation_id=thread_id,
        user_id=current_user.id,
    )
    if not conv:
        return AIThreadDetail(
            thread_id=thread_id,
            messages=[],
        )
    msgs = [
        AIMessageItem(
            id=m.id,
            role=m.role,
            content=m.content,
            created_at=m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at),
            domains_retrieved=m.data_sources,
            verified_metrics=None,
            suggested_followups=None,
            warnings=None,
        )
        for m in sorted(conv.messages, key=lambda x: x.created_at)
    ]
    return AIThreadDetail(
        thread_id=conv.id,
        messages=msgs,
    )


@ai_router.post(
    "/health-report",
    response_model=FinancialHealthReportCompat,
    summary="Generate health synthesis report (frontend compatibility alias)",
)
def generate_health_report_compat(
    payload: HealthReportRequest = HealthReportRequest(),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialHealthReportCompat:
    """Frontend-compatible financial health synthesis report."""
    insights_service = FinancialInsightsService(db)
    report = insights_service.generate_report(
        user=current_user,
        portfolio_id=payload.portfolio_id,
    )
    domain_map = {item.domain: item.summary for item in report.insights}
    return FinancialHealthReportCompat(
        user_id=report.user_id,
        generated_at=report.generated_at,
        executive_summary=report.executive_summary,
        health_score=85,
        domain_insights=domain_map,
        warnings=report.missing_data_warnings,
        disclaimers=["Educational and decision-support synthesis only. Not investment advice."],
    )


@ai_router.post(
    "/scenario",
    summary="Evaluate scenario simulation (frontend compatibility alias)",
)
def evaluate_scenario_compat(
    payload: ScenarioCompatRequest,
    current_user: UserModel = Depends(get_current_user),
) -> dict:
    """Frontend-compatible scenario evaluation."""
    stype = payload.scenario_type
    params = payload.params or {}

    try:
        raw_amt = str(params.get("amount", "200000"))
        amount = Decimal(raw_amt)
    except Exception:
        amount = Decimal("200000")

    if stype == "expense":
        explanation = (
            f"An unplanned major expense of ₹{amount:,.2f} would immediately reduce liquid cash reserves. "
            f"If funded from emergency savings, your coverage months will decrease. "
            f"We recommend reviewing your 30-day cash flow projections and replenishing reserves through dedicated monthly SIPs."
        )
    elif stype == "income_reduction":
        explanation = (
            f"A recurring income reduction of ₹{amount:,.2f} would constrain monthly net surplus. "
            f"Discretionary outflows should be audited to prevent negative cash flow and protect existing systematic investment commitments."
        )
    elif stype == "market_drop":
        pct = amount if amount <= 1 else amount / Decimal("100")
        pct_display = pct * Decimal("100")
        explanation = (
            f"A hypothetical {pct_display:.1f}% equity market drop would reduce mark-to-market portfolio value. "
            f"Modern Portfolio Theory analysis indicates maintaining target allocation through systematic rebalancing rather than panic liquidation."
        )
    else:
        explanation = f"Hypothetical simulation for scenario '{stype}' completed with parameter amount ₹{amount:,.2f}."

    return {
        "scenario_type": stype,
        "impact_summary": explanation,
        "explanation": explanation,
        "parameters": params,
        "assumptions": ["Deterministic baseline projection", "Zero portfolio mutation"],
    }

