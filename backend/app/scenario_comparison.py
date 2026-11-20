"""
Investment-Goal Multi-Scenario Comparison Engine for Phase 13.

Enables side-by-side evaluation of hypothetical parameters (contribution changes,
horizon extensions, return adjustments) against an investor's baseline goal:
- Reuses Phase 8 deterministic forward & reverse SIP solvers for deterministic benchmarks
- Employs Phase 13 Monte Carlo stochastic simulator for probability of goal success
- Zero Database Mutation: All scenario simulations are transient and strictly read-only
- Generates actionable evidence-grounded recommendations
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from app.db.models import InvestmentGoalModel, PortfolioModel
from app.goal_schemas import ReverseSIPRequest, SIPCalculationRequest
from app.monte_carlo import run_monte_carlo_simulation
from app.portfolio_schemas import quantize_decimal
from app.portfolio_valuation import calculate_portfolio_valuation
from app.simulation_schemas import (
    GoalScenarioComparisonRequest,
    GoalScenarioComparisonResponse,
    GoalScenarioOption,
    MonteCarloRequest,
    ScenarioComparisonItem,
)
from app.sip_calculator import calculate_forward_sip, calculate_reverse_sip


def _compute_months_to_date(target_dt: date, as_of: date) -> int:
    """Compute integer months between as_of date and target_date."""
    days = (target_dt - as_of).days
    if days <= 0:
        return 1
    months = round(days / 30.4375)
    return max(1, months)


def compare_goal_scenarios(
    request: GoalScenarioComparisonRequest,
    goal: Optional[InvestmentGoalModel] = None,
    portfolio: Optional[PortfolioModel] = None,
) -> GoalScenarioComparisonResponse:
    """Evaluate and compare multiple hypothetical goal planning scenarios against a baseline."""
    today = datetime.now(timezone.utc).date()
    assumptions: List[str] = [
        "Deterministic projections use ordinary annuity monthly compounding.",
        "Probabilistic projections use 1,000 Geometric Brownian Motion Monte Carlo trajectories.",
        "Default volatility assumed at 15.0% annualized across equity/blended goal allocations.",
        "Simulations are transient analytical comparisons and do not modify stored goal records.",
    ]
    disclaimers: List[str] = [
        "Scenario projections are illustrative models to support decision-making, not financial guarantees.",
        "Market volatility may cause actual outcomes to diverge from both deterministic and median projected paths.",
    ]

    # 1. Resolve Baseline Parameters
    goal_name = goal.name if goal else "Hypothetical Investment Goal"
    target_amt = (
        request.baseline_target_amount
        if request.baseline_target_amount is not None
        else (goal.target_amount if goal else Decimal("1000000.00"))
    )

    base_initial_amt = Decimal("0.00")
    if request.baseline_current_amount is not None:
        base_initial_amt = request.baseline_current_amount
    elif goal and goal.current_amount is not None:
        base_initial_amt = goal.current_amount
    elif portfolio is not None:
        val = calculate_portfolio_valuation(portfolio)
        base_initial_amt = val.priced_holdings_value

    base_contrib = (
        request.baseline_monthly_contribution
        if request.baseline_monthly_contribution is not None
        else (goal.monthly_contribution if goal and goal.monthly_contribution else Decimal("10000.00"))
    )

    base_target_date = (
        request.baseline_target_date
        if request.baseline_target_date is not None
        else (goal.target_date if goal else date(today.year + 5, 12, 31))
    )

    base_horizon_months = _compute_months_to_date(base_target_date, today)

    base_ret_pct = (
        request.baseline_annual_return_pct
        if request.baseline_annual_return_pct is not None
        else (
            Decimal(str(float(goal.expected_annual_return) * 100.0))
            if goal and goal.expected_annual_return
            else Decimal("12.00")
        )
    )

    # 2. Evaluate a Single Scenario Helper
    def evaluate_variant(
        name: str,
        initial_val: Decimal,
        monthly_c: Decimal,
        horizon_m: int,
        target_dt_str: str,
        annual_r_pct: Decimal,
        target_amount: Decimal,
        baseline_contrib: Decimal,
        baseline_prob: Optional[Decimal] = None,
    ) -> ScenarioComparisonItem:
        # A. Deterministic Forward SIP
        fwd_res = calculate_forward_sip(
            SIPCalculationRequest(
                initial_investment=initial_val,
                monthly_contribution=monthly_c,
                annual_return_percentage=annual_r_pct,
                duration_months=horizon_m,
                rate_convention="effective",
                include_schedule=False,
            )
        )
        det_projected = fwd_res.projected_future_value
        det_gap = det_projected - target_amount

        # B. Deterministic Reverse SIP
        rev_res = calculate_reverse_sip(
            ReverseSIPRequest(
                target_amount=target_amount,
                initial_investment=initial_val,
                annual_return_percentage=annual_r_pct,
                duration_months=horizon_m,
                rate_convention="effective",
                include_schedule=False,
            )
        )
        det_req_sip = rev_res.required_monthly_contribution

        # C. Stochastic Monte Carlo
        mc_res = run_monte_carlo_simulation(
            MonteCarloRequest(
                initial_value=initial_val,
                monthly_contribution=monthly_c,
                horizon_months=horizon_m,
                num_simulations=request.num_simulations,
                expected_annual_return_pct=annual_r_pct,
                annual_volatility_pct=Decimal("15.00"),
                target_amount=target_amount,
                seed=request.seed,
            )
        )
        mc_median = mc_res.terminal_wealth.median
        mc_p5 = mc_res.terminal_wealth.p5
        mc_p95 = mc_res.terminal_wealth.p95
        mc_prob = mc_res.goal_success_probability_pct or Decimal("0.00")

        c_delta = monthly_c - baseline_contrib
        prob_delta = (mc_prob - baseline_prob) if baseline_prob is not None else Decimal("0.00")

        return ScenarioComparisonItem(
            name=name,
            monthly_contribution=quantize_decimal(monthly_c, places=2),
            horizon_months=horizon_m,
            target_date=target_dt_str,
            expected_annual_return_pct=quantize_decimal(annual_r_pct, places=2),
            deterministic_projected_value=quantize_decimal(det_projected, places=2),
            deterministic_gap=quantize_decimal(det_gap, places=2),
            deterministic_required_sip=quantize_decimal(det_req_sip, places=2),
            mc_median_projected_value=quantize_decimal(mc_median, places=2),
            mc_p5_downside_value=quantize_decimal(mc_p5, places=2),
            mc_p95_upside_value=quantize_decimal(mc_p95, places=2),
            mc_goal_success_probability_pct=quantize_decimal(mc_prob, places=2),
            contribution_delta_from_baseline=quantize_decimal(c_delta, places=2),
            success_probability_delta_pct=quantize_decimal(prob_delta, places=2),
        )

    # 3. Evaluate Baseline
    baseline_item = evaluate_variant(
        name="Baseline Plan",
        initial_val=base_initial_amt,
        monthly_c=base_contrib,
        horizon_m=base_horizon_months,
        target_dt_str=str(base_target_date),
        annual_r_pct=base_ret_pct,
        target_amount=target_amt,
        baseline_contrib=base_contrib,
        baseline_prob=None,
    )

    # 4. Evaluate Scenarios
    compared_list: List[ScenarioComparisonItem] = []

    for sc in request.scenarios:
        s_initial = sc.initial_amount if sc.initial_amount is not None else base_initial_amt
        s_contrib = sc.monthly_contribution if sc.monthly_contribution is not None else base_contrib
        s_ret = sc.expected_annual_return_pct if sc.expected_annual_return_pct is not None else base_ret_pct

        if sc.horizon_months is not None:
            s_horizon = sc.horizon_months
            s_target_date_str = f"+{s_horizon} months"
        elif sc.target_date is not None:
            s_horizon = _compute_months_to_date(sc.target_date, today)
            s_target_date_str = str(sc.target_date)
        else:
            s_horizon = base_horizon_months
            s_target_date_str = str(base_target_date)

        item = evaluate_variant(
            name=sc.name,
            initial_val=s_initial,
            monthly_c=s_contrib,
            horizon_m=s_horizon,
            target_dt_str=s_target_date_str,
            annual_r_pct=s_ret,
            target_amount=target_amt,
            baseline_contrib=base_contrib,
            baseline_prob=baseline_item.mc_goal_success_probability_pct,
        )
        compared_list.append(item)

    # 5. Formulate Objective Recommendations
    insights: List[str] = []
    base_prob = baseline_item.mc_goal_success_probability_pct

    if base_prob >= Decimal("85.00"):
        insights.append(
            f"Baseline plan is strongly on track with an estimated {base_prob:.1f}% probability of reaching target ₹{target_amt:,.2f}."
        )
    elif base_prob >= Decimal("65.00"):
        insights.append(
            f"Baseline plan has a moderate {base_prob:.1f}% probability of achieving target ₹{target_amt:,.2f}; market dips may create a shortfall."
        )
    else:
        insights.append(
            f"Baseline plan has a high risk of shortfall ({base_prob:.1f}% probability of success). Adjustment recommended."
        )

    # Identify best scenario that reaches >= 85% probability
    high_prob_scenarios = [s for s in compared_list if s.mc_goal_success_probability_pct >= Decimal("85.00")]
    if high_prob_scenarios:
        # Pick the one with the smallest incremental monthly contribution
        best_s = min(high_prob_scenarios, key=lambda x: x.monthly_contribution)
        insights.append(
            f"Scenario '{best_s.name}' boosts success probability to {best_s.mc_goal_success_probability_pct:.1f}% "
            f"(+{best_s.success_probability_delta_pct:.1f}% improvement) with ₹{best_s.monthly_contribution:,.2f}/mo."
        )
    elif compared_list:
        best_prob_s = max(compared_list, key=lambda x: x.mc_goal_success_probability_pct)
        insights.append(
            f"Scenario '{best_prob_s.name}' offers the highest probability ({best_prob_s.mc_goal_success_probability_pct:.1f}%), "
            f"improving baseline odds by +{best_prob_s.success_probability_delta_pct:.1f}%."
        )

    return GoalScenarioComparisonResponse(
        goal_id=goal.id if goal else None,
        goal_name=goal_name,
        target_amount=quantize_decimal(target_amt, places=2),
        baseline=baseline_item,
        compared_scenarios=compared_list,
        insights=insights,
        assumptions=assumptions,
        disclaimers=disclaimers,
    )
