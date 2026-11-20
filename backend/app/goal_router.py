"""
FastAPI router for Phase 8:
- Forward SIP Calculator (/calculators/sip)
- Reverse SIP Calculator (/calculators/reverse-sip)
- Goal Projections & Required Contributions (/investment-goals/{goal_id}/projection)
- Standalone Goal Planner (/investment-goals/plan)
- Portfolio Drift Detection (/portfolios/{portfolio_id}/drift)
- Illustrative Rebalancing Analysis (/portfolios/{portfolio_id}/rebalancing-analysis)
- Risk-Aware Investment Glide Path (/investment-goals/{goal_id}/glide-path, /calculators/glide-path)
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.dependencies import get_current_user
from app.db.models import PortfolioModel, UserModel
from app.db.repositories.portfolio_repo import SQLPortfolioRepository
from app.glide_path import generate_glide_path
from app.goal_planning import calculate_goal_projection, calculate_standalone_goal_plan
from app.goal_schemas import (
    GlidePathRequest,
    GlidePathResponse,
    GoalProjectionRequest,
    GoalProjectionResponse,
    PortfolioDriftResponse,
    RebalanceAnalysisResponse,
    ReverseSIPRequest,
    ReverseSIPResponse,
    SIPCalculationRequest,
    SIPCalculationResponse,
    StandaloneGoalPlanRequest,
)
from app.portfolio_drift import (
    calculate_portfolio_drift,
    calculate_rebalancing_analysis,
)
from app.portfolio_router import get_portfolio_repo
from app.portfolio_valuation import calculate_portfolio_valuation
from app.sip_calculator import calculate_forward_sip, calculate_reverse_sip

goal_router = APIRouter(tags=["Goal Planning, SIP Calculators & Portfolio Drift"])


# ---------------------------------------------------------------------------
# SIP Calculator Endpoints
# ---------------------------------------------------------------------------

@goal_router.post(
    "/calculators/sip",
    response_model=SIPCalculationResponse,
    summary="Calculate forward SIP future value and schedule",
)
def forward_sip_calculator(
    payload: SIPCalculationRequest,
    current_user: UserModel = Depends(get_current_user),
) -> SIPCalculationResponse:
    try:
        return calculate_forward_sip(payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@goal_router.post(
    "/calculators/reverse-sip",
    response_model=ReverseSIPResponse,
    summary="Calculate required monthly contribution to reach target future value",
)
def reverse_sip_calculator(
    payload: ReverseSIPRequest,
    current_user: UserModel = Depends(get_current_user),
) -> ReverseSIPResponse:
    try:
        return calculate_reverse_sip(payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# Goal Planning & Projection Endpoints
# ---------------------------------------------------------------------------

@goal_router.post(
    "/investment-goals/{goal_id}/projection",
    response_model=GoalProjectionResponse,
    summary="Project future value, progress, and required monthly SIP for a saved goal",
)
def project_saved_goal(
    goal_id: str,
    payload: GoalProjectionRequest,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> GoalProjectionResponse:
    goal = repo.get_goal(goal_id, user_id=current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment goal '{goal_id}' not found.",
        )

    linked_portfolio: Optional[PortfolioModel] = None
    if goal.portfolio_id:
        linked_portfolio = repo.get_portfolio(goal.portfolio_id, user_id=current_user.id)

    try:
        return calculate_goal_projection(goal, payload, portfolio=linked_portfolio)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@goal_router.post(
    "/investment-goals/plan",
    response_model=GoalProjectionResponse,
    summary="Ad-hoc goal projection and required SIP calculation without saving",
)
def plan_ad_hoc_goal(
    payload: StandaloneGoalPlanRequest,
    current_user: UserModel = Depends(get_current_user),
) -> GoalProjectionResponse:
    try:
        return calculate_standalone_goal_plan(payload)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# Portfolio Drift & Rebalancing Analysis Endpoints
# ---------------------------------------------------------------------------

@goal_router.get(
    "/portfolios/{portfolio_id}/drift",
    response_model=PortfolioDriftResponse,
    summary="Analyze portfolio asset allocation drift against target allocation",
)
def get_portfolio_drift(
    portfolio_id: str,
    threshold_percentage_points: Decimal = Query(
        Decimal("5.00"),
        ge=Decimal("0.10"),
        le=Decimal("50.00"),
        description="Drift alert threshold in percentage points.",
    ),
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> PortfolioDriftResponse:
    portfolio = repo.get_portfolio(portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )

    target_alloc = repo.get_target_allocation(portfolio_id, user_id=current_user.id)
    return calculate_portfolio_drift(
        portfolio=portfolio,
        target_allocation=target_alloc,
        threshold_percentage_points=threshold_percentage_points,
    )


@goal_router.post(
    "/portfolios/{portfolio_id}/rebalancing-analysis",
    response_model=RebalanceAnalysisResponse,
    summary="Generate illustrative rebalancing buy/sell trade amounts to match target allocation",
)
def get_portfolio_rebalancing(
    portfolio_id: str,
    threshold_percentage_points: Decimal = Query(
        Decimal("5.00"),
        ge=Decimal("0.10"),
        le=Decimal("50.00"),
        description="Rebalancing recommendation threshold.",
    ),
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> RebalanceAnalysisResponse:
    portfolio = repo.get_portfolio(portfolio_id, user_id=current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio '{portfolio_id}' not found.",
        )

    target_alloc = repo.get_target_allocation(portfolio_id, user_id=current_user.id)
    if not target_alloc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot calculate rebalancing analysis: no target allocation configured for this portfolio.",
        )

    try:
        return calculate_rebalancing_analysis(
            portfolio=portfolio,
            target_allocation=target_alloc,
            drift_threshold_percentage_points=threshold_percentage_points,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------------------------
# Risk-Aware Investment Glide Path Endpoints
# ---------------------------------------------------------------------------

@goal_router.post(
    "/investment-goals/{goal_id}/glide-path",
    response_model=GlidePathResponse,
    summary="Generate a risk-aware investment glide path for a saved goal",
)
def generate_goal_glide_path(
    goal_id: str,
    payload: GlidePathRequest,
    current_user: UserModel = Depends(get_current_user),
    repo: SQLPortfolioRepository = Depends(get_portfolio_repo),
) -> GlidePathResponse:
    goal = repo.get_goal(goal_id, user_id=current_user.id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investment goal '{goal_id}' not found.",
        )

    start_date = payload.start_date or datetime.now(timezone.utc).date()
    target_date = payload.target_date or goal.target_date

    # If starting allocation not provided, but portfolio is linked, pre-fill from portfolio current allocation
    start_alloc = payload.starting_allocation
    if not start_alloc and goal.portfolio_id:
        portfolio = repo.get_portfolio(goal.portfolio_id, user_id=current_user.id)
        if portfolio:
            val = calculate_portfolio_valuation(portfolio)
            if val.priced_holdings_value > Decimal("0.00") and val.asset_class_breakdown:
                start_alloc = {
                    item.asset_class: item.allocation_percentage for item in val.asset_class_breakdown
                }

    req_copy = payload.model_copy(update={"starting_allocation": start_alloc})

    try:
        return generate_glide_path(
            start_date=start_date,
            target_date=target_date,
            request=req_copy,
            goal_id=goal.id,
            goal_name=goal.name,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@goal_router.post(
    "/calculators/glide-path",
    response_model=GlidePathResponse,
    summary="Generate an ad-hoc risk-aware investment glide path",
)
def generate_standalone_glide_path(
    payload: GlidePathRequest,
    current_user: UserModel = Depends(get_current_user),
) -> GlidePathResponse:
    start_date = payload.start_date or datetime.now(timezone.utc).date()
    if not payload.target_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_date is required for standalone glide path calculation.",
        )

    try:
        return generate_glide_path(
            start_date=start_date,
            target_date=payload.target_date,
            request=payload,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
