"""
Deterministic Goal-Based Investment Planning and Projections for Phase 8.

Calculates:
- Current goal progress and remaining capital
- Remaining horizon in months
- Projected future value from current holdings and planned monthly contributions
- Shortfall or surplus at target milestone date
- Required monthly contribution (Reverse SIP) to bridge any gap
- Planned vs required contribution gap analysis
- Seamless integration with linked Phase 6 portfolio holdings and valuations
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from app.db.models import InvestmentGoalModel, PortfolioModel
from app.goal_schemas import (
    GoalProjectionRequest,
    GoalProjectionResponse,
    ReverseSIPRequest,
    SIPCalculationRequest,
    StandaloneGoalPlanRequest,
)
from app.portfolio_schemas import quantize_decimal
from app.portfolio_valuation import calculate_portfolio_valuation
from app.sip_calculator import calculate_forward_sip, calculate_reverse_sip


def _compute_remaining_months(target_date: date, as_of_date: date) -> int:
    """Compute integer remaining investment months between as_of_date and target_date."""
    days = (target_date - as_of_date).days
    if days <= 0:
        return 0
    # Average calendar days per month convention: 365.25 / 12 = 30.4375
    months = round(days / 30.4375)
    return max(1, months)


def calculate_goal_projection(
    goal: InvestmentGoalModel,
    request: GoalProjectionRequest,
    portfolio: Optional[PortfolioModel] = None,
) -> GoalProjectionResponse:
    """Project future value and required contributions for a persisted investment goal."""
    as_of = request.as_of_date or datetime.now(timezone.utc).date()
    target_dt = request.target_date or goal.target_date
    warnings: List[str] = []

    # 1. Resolve current invested amount
    current_amt: Decimal = Decimal("0.00")
    if request.current_amount is not None:
        current_amt = request.current_amount
    elif goal.current_amount is not None:
        current_amt = goal.current_amount
    elif portfolio is not None:
        val = calculate_portfolio_valuation(portfolio)
        current_amt = val.priced_holdings_value
        if val.unpriced_holdings_count > 0:
            warnings.append(
                f"Linked portfolio has {val.unpriced_holdings_count} unpriced holding(s); "
                "current investment progress is based strictly on priced holdings."
            )
        if val.has_mixed_currencies:
            warnings.append("Linked portfolio has multi-currency holdings. Foreign exchange variance is not modeled.")

    current_amt = quantize_decimal(max(Decimal("0.00"), current_amt), 2)
    target_amt = quantize_decimal(goal.target_amount, 2)

    # 2. Progress and Remaining Capital
    if target_amt > Decimal("0.00"):
        progress_pct = quantize_decimal((current_amt / target_amt) * Decimal("100"), 2)
    else:
        progress_pct = Decimal("0.00")
    remaining_amt = quantize_decimal(max(Decimal("0.00"), target_amt - current_amt), 2)

    # 3. Time Horizon
    remaining_months = _compute_remaining_months(target_dt, as_of)
    is_expired = (target_dt - as_of).days <= 0

    # 4. Return and Contribution Assumptions
    exp_annual_ret = (
        request.expected_annual_return
        if request.expected_annual_return is not None
        else (goal.expected_annual_return if goal.expected_annual_return is not None else Decimal("0.1000"))
    )
    planned_contrib = (
        request.monthly_contribution
        if request.monthly_contribution is not None
        else (goal.monthly_contribution if goal.monthly_contribution is not None else Decimal("0.00"))
    )
    planned_contrib = quantize_decimal(planned_contrib, 2)
    annual_return_pct = quantize_decimal(exp_annual_ret * Decimal("100"), 2)

    # 5. Handle Expired Goals
    if is_expired:
        warnings.append(f"Target completion date ({target_dt.isoformat()}) has already passed or is today.")
        shortfall_val = current_amt - target_amt
        is_on_track = shortfall_val >= Decimal("0.00")
        status_assessment = "achieved" if is_on_track else "expired"

        return GoalProjectionResponse(
            goal_id=goal.id,
            goal_name=goal.name,
            target_amount=target_amt,
            current_amount=current_amt,
            progress_percentage=progress_pct,
            remaining_amount=remaining_amt,
            target_date=target_dt,
            as_of_date=as_of,
            remaining_months=0,
            expected_annual_return=exp_annual_ret,
            rate_convention=request.rate_convention,
            planned_monthly_contribution=planned_contrib,
            projected_future_value=current_amt,
            shortfall_or_surplus=quantize_decimal(shortfall_val, 2),
            is_on_track=is_on_track,
            required_monthly_contribution=Decimal("0.00"),
            contribution_difference=planned_contrib,
            status_assessment=status_assessment,
            schedule=[],
            assumptions=["Target date is in the past; no forward compounding applied."],
            warnings=warnings,
        )

    # 6. Execute Forward SIP Projection
    fwd_req = SIPCalculationRequest(
        initial_investment=current_amt,
        monthly_contribution=planned_contrib,
        annual_return_percentage=annual_return_pct,
        duration_months=remaining_months,
        rate_convention=request.rate_convention,
        include_schedule=True,
    )
    fwd_res = calculate_forward_sip(fwd_req)
    proj_fv = fwd_res.projected_future_value
    shortfall_surplus = quantize_decimal(proj_fv - target_amt, 2)
    is_on_track = shortfall_surplus >= Decimal("0.00")

    # 7. Execute Reverse SIP Calculation
    rev_req = ReverseSIPRequest(
        target_amount=target_amt,
        initial_investment=current_amt,
        annual_return_percentage=annual_return_pct,
        duration_months=remaining_months,
        rate_convention=request.rate_convention,
        include_schedule=False,
    )
    rev_res = calculate_reverse_sip(rev_req)
    req_monthly = rev_res.required_monthly_contribution
    contrib_diff = quantize_decimal(planned_contrib - req_monthly, 2)

    # 8. Status Assessment
    if shortfall_surplus >= (target_amt * Decimal("0.05")):
        status_assessment = "ahead"
    elif is_on_track:
        status_assessment = "on_track"
    else:
        status_assessment = "behind"

    assumptions = [
        f"Annual return assumption: {annual_return_pct}% ({request.rate_convention} compounding).",
        f"Investment horizon: {remaining_months} months remaining (from {as_of.isoformat()} to {target_dt.isoformat()}).",
        "Monthly contributions are deposited at the end of each calendar month.",
        "Calculations exclude taxes, inflation, fund management fees, and transaction charges.",
    ]

    return GoalProjectionResponse(
        goal_id=goal.id,
        goal_name=goal.name,
        target_amount=target_amt,
        current_amount=current_amt,
        progress_percentage=progress_pct,
        remaining_amount=remaining_amt,
        target_date=target_dt,
        as_of_date=as_of,
        remaining_months=remaining_months,
        expected_annual_return=exp_annual_ret,
        rate_convention=request.rate_convention,
        planned_monthly_contribution=planned_contrib,
        projected_future_value=proj_fv,
        shortfall_or_surplus=shortfall_surplus,
        is_on_track=is_on_track,
        required_monthly_contribution=req_monthly,
        contribution_difference=contrib_diff,
        status_assessment=status_assessment,
        schedule=fwd_res.schedule,
        assumptions=assumptions,
        warnings=warnings,
    )


def calculate_standalone_goal_plan(request: StandaloneGoalPlanRequest) -> GoalProjectionResponse:
    """Calculate goal projection and SIP requirements for an ad-hoc goal specification."""
    dummy_goal = InvestmentGoalModel(
        id="standalone-plan",
        user_id="anonymous",
        name=request.goal_name,
        target_amount=request.target_amount,
        target_date=request.target_date,
        priority="medium",
        current_amount=request.current_amount,
        expected_annual_return=request.expected_annual_return,
        monthly_contribution=request.planned_monthly_contribution,
    )
    proj_req = GoalProjectionRequest(
        expected_annual_return=request.expected_annual_return,
        monthly_contribution=request.planned_monthly_contribution,
        current_amount=request.current_amount,
        target_date=request.target_date,
        rate_convention=request.rate_convention,
        as_of_date=request.as_of_date,
    )
    res = calculate_goal_projection(dummy_goal, proj_req, portfolio=None)
    res.goal_id = None
    return res
