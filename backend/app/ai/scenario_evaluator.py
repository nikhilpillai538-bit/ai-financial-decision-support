"""
Deterministic Hypothetical Scenario Evaluator for Phase 9.

Processes "what-if" financial questions using the existing deterministic calculators.
Zero Database Mutation: What-if scenarios are strictly transient analytical comparisons
and never alter the user's persisted records.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

from app.goal_schemas import ReverseSIPRequest, SIPCalculationRequest
from app.portfolio_schemas import quantize_decimal
from app.sip_calculator import calculate_forward_sip, calculate_reverse_sip


@dataclass
class ScenarioEvaluationResult:
    scenario_type: str
    description: str
    baseline: Dict[str, Any]
    hypothetical: Dict[str, Any]
    difference: Dict[str, Any]
    assumptions: List[str]


class ScenarioEvaluator:
    """Evaluates hypothetical financial scenarios using deterministic engine modules."""

    @staticmethod
    def evaluate_sip_increase(
        initial_investment: Decimal,
        current_monthly_contribution: Decimal,
        additional_monthly_contribution: Decimal,
        annual_return_percentage: Decimal,
        duration_months: int,
        rate_convention: str = "effective",
    ) -> ScenarioEvaluationResult:
        """Compare current monthly SIP against an increased monthly SIP contribution."""
        if additional_monthly_contribution <= Decimal("0.00"):
            raise ValueError("Additional monthly contribution must be greater than zero.")

        # Baseline projection
        base_req = SIPCalculationRequest(
            initial_investment=initial_investment,
            monthly_contribution=current_monthly_contribution,
            annual_return_percentage=annual_return_percentage,
            duration_months=duration_months,
            rate_convention=rate_convention,
            include_schedule=False,
        )
        base_res = calculate_forward_sip(base_req)

        # Hypothetical projection
        hypo_monthly = current_monthly_contribution + additional_monthly_contribution
        hypo_req = SIPCalculationRequest(
            initial_investment=initial_investment,
            monthly_contribution=hypo_monthly,
            annual_return_percentage=annual_return_percentage,
            duration_months=duration_months,
            rate_convention=rate_convention,
            include_schedule=False,
        )
        hypo_res = calculate_forward_sip(hypo_req)

        delta_fv = quantize_decimal(hypo_res.projected_future_value - base_res.projected_future_value, 2)
        delta_contrib = quantize_decimal(hypo_res.total_contributions - base_res.total_contributions, 2)
        delta_gain = quantize_decimal(hypo_res.estimated_wealth_gain - base_res.estimated_wealth_gain, 2)

        return ScenarioEvaluationResult(
            scenario_type="sip_increase",
            description=(
                f"Impact of contributing an additional {additional_monthly_contribution:,.2f} per month "
                f"over {duration_months} months at an assumed {annual_return_percentage:.2f}% annual return."
            ),
            baseline={
                "monthly_contribution": str(current_monthly_contribution),
                "total_invested": str(base_res.total_invested),
                "projected_future_value": str(base_res.projected_future_value),
                "estimated_wealth_gain": str(base_res.estimated_wealth_gain),
            },
            hypothetical={
                "monthly_contribution": str(hypo_monthly),
                "total_invested": str(hypo_res.total_invested),
                "projected_future_value": str(hypo_res.projected_future_value),
                "estimated_wealth_gain": str(hypo_res.estimated_wealth_gain),
            },
            difference={
                "additional_monthly_contribution": str(additional_monthly_contribution),
                "additional_capital_invested": str(delta_contrib),
                "additional_future_value": str(delta_fv),
                "additional_wealth_gain": str(delta_gain),
            },
            assumptions=[
                "Calculations assume end-of-month contributions (ordinary annuity).",
                f"Rate convention: {rate_convention}.",
                "Hypothetical simulation does NOT modify your stored goal or portfolio records.",
            ],
        )

    @staticmethod
    def evaluate_return_rate_comparison(
        initial_investment: Decimal,
        monthly_contribution: Decimal,
        duration_months: int,
        rate_baseline_percentage: Decimal,
        rate_hypothetical_percentage: Decimal,
        rate_convention: str = "effective",
    ) -> ScenarioEvaluationResult:
        """Compare investment outcome between two distinct annual return rates."""
        base_req = SIPCalculationRequest(
            initial_investment=initial_investment,
            monthly_contribution=monthly_contribution,
            annual_return_percentage=rate_baseline_percentage,
            duration_months=duration_months,
            rate_convention=rate_convention,
            include_schedule=False,
        )
        base_res = calculate_forward_sip(base_req)

        hypo_req = SIPCalculationRequest(
            initial_investment=initial_investment,
            monthly_contribution=monthly_contribution,
            annual_return_percentage=rate_hypothetical_percentage,
            duration_months=duration_months,
            rate_convention=rate_convention,
            include_schedule=False,
        )
        hypo_res = calculate_forward_sip(hypo_req)

        delta_fv = quantize_decimal(hypo_res.projected_future_value - base_res.projected_future_value, 2)
        delta_gain = quantize_decimal(hypo_res.estimated_wealth_gain - base_res.estimated_wealth_gain, 2)

        return ScenarioEvaluationResult(
            scenario_type="return_comparison",
            description=(
                f"Comparing {rate_baseline_percentage:.2f}% annual return vs {rate_hypothetical_percentage:.2f}% "
                f"annual return over {duration_months} months."
            ),
            baseline={
                "annual_return_percentage": str(rate_baseline_percentage),
                "projected_future_value": str(base_res.projected_future_value),
                "estimated_wealth_gain": str(base_res.estimated_wealth_gain),
            },
            hypothetical={
                "annual_return_percentage": str(rate_hypothetical_percentage),
                "projected_future_value": str(hypo_res.projected_future_value),
                "estimated_wealth_gain": str(hypo_res.estimated_wealth_gain),
            },
            difference={
                "annual_return_percentage_difference": str(rate_hypothetical_percentage - rate_baseline_percentage),
                "future_value_difference": str(delta_fv),
                "wealth_gain_difference": str(delta_gain),
            },
            assumptions=[
                "Calculations assume smooth compound growth without intermittent volatility.",
                "Hypothetical simulation does NOT alter existing account records.",
            ],
        )

    @staticmethod
    def evaluate_target_horizon_change(
        target_amount: Decimal,
        initial_investment: Decimal,
        annual_return_percentage: Decimal,
        current_duration_months: int,
        new_duration_months: int,
        rate_convention: str = "effective",
    ) -> ScenarioEvaluationResult:
        """Evaluate how extending or reducing investment horizon alters required monthly SIP."""
        if new_duration_months <= 0:
            raise ValueError("New duration in months must be greater than zero.")

        base_res = calculate_reverse_sip(
            ReverseSIPRequest(
                target_amount=target_amount,
                initial_investment=initial_investment,
                annual_return_percentage=annual_return_percentage,
                duration_months=current_duration_months,
                rate_convention=rate_convention,
                include_schedule=False,
            )
        )
        hypo_res = calculate_reverse_sip(
            ReverseSIPRequest(
                target_amount=target_amount,
                initial_investment=initial_investment,
                annual_return_percentage=annual_return_percentage,
                duration_months=new_duration_months,
                rate_convention=rate_convention,
                include_schedule=False,
            )
        )

        sip_diff = quantize_decimal(hypo_res.required_monthly_contribution - base_res.required_monthly_contribution, 2)
        total_inv_diff = quantize_decimal(hypo_res.total_invested - base_res.total_invested, 2)

        return ScenarioEvaluationResult(
            scenario_type="target_date_change",
            description=(
                f"Impact of changing goal investment horizon from {current_duration_months} months "
                f"to {new_duration_months} months for a target of {target_amount:,.2f}."
            ),
            baseline={
                "duration_months": current_duration_months,
                "required_monthly_contribution": str(base_res.required_monthly_contribution),
                "total_invested": str(base_res.total_invested),
            },
            hypothetical={
                "duration_months": new_duration_months,
                "required_monthly_contribution": str(hypo_res.required_monthly_contribution),
                "total_invested": str(hypo_res.total_invested),
            },
            difference={
                "months_difference": new_duration_months - current_duration_months,
                "monthly_contribution_difference": str(sip_diff),
                "total_invested_difference": str(total_inv_diff),
            },
            assumptions=[
                "Calculated using deterministic reverse ordinary annuity solver.",
                "Target corpus remains constant while compounding duration changes.",
            ],
        )
