"""
Deterministic Forward and Reverse SIP Calculators for Phase 8.

Implements exact mathematical compounding:
- Forward SIP ordinary annuity: FV = L*(1+r)^n + P*((1+r)^n - 1)/r
- Zero-return handling: FV = L + P*n
- Reverse SIP target solver: P = (FV - L*(1+r)^n) / [((1+r)^n - 1)/r]
- Annual step-up contribution growth option
- Effective vs Nominal monthly compounding rate conversions
- Comprehensive periodic schedule breakdowns
"""

from decimal import Decimal
from typing import List, Tuple
import math

from app.goal_schemas import (
    SIPCalculationRequest,
    SIPCalculationResponse,
    SIPScheduleItem,
    ReverseSIPRequest,
    ReverseSIPResponse,
)
from app.portfolio_schemas import quantize_decimal


def compute_monthly_rate(annual_rate_percentage: Decimal, convention: str = "effective") -> float:
    """Convert annual return percentage into monthly return rate as a float.

    Effective convention: r_m = (1 + R)^(1/12) - 1.
    Nominal convention: r_m = R / 12.
    """
    r_annual = float(annual_rate_percentage) / 100.0
    if abs(r_annual) < 1e-12:
        return 0.0

    if convention == "nominal":
        return r_annual / 12.0
    else:  # effective
        if r_annual <= -1.0:
            return -1.0
        return math.pow(1.0 + r_annual, 1.0 / 12.0) - 1.0


def calculate_forward_sip(request: SIPCalculationRequest) -> SIPCalculationResponse:
    """Calculate future value of an initial investment and recurring monthly contributions."""
    initial_l = float(request.initial_investment)
    monthly_p = float(request.monthly_contribution)
    n = request.duration_months
    r_m = compute_monthly_rate(request.annual_return_percentage, request.rate_convention)
    step_up_rate = float(request.annual_step_up_percentage or 0.0) / 100.0

    # Build schedule month-by-month for exact simulation with step-up
    balance = initial_l
    cumulative_contributions = 0.0
    schedule_items: List[SIPScheduleItem] = []

    # Track annual aggregates
    year_open = balance
    year_contrib = 0.0
    year_growth = 0.0

    for m in range(1, n + 1):
        year_idx = (m - 1) // 12
        if step_up_rate > 0.0:
            cur_p = monthly_p * math.pow(1.0 + step_up_rate, year_idx)
        else:
            cur_p = monthly_p

        # Compounding on opening balance for month m
        growth = balance * r_m
        balance += growth
        # Monthly contribution deposited at end of month (ordinary annuity)
        balance += cur_p
        cumulative_contributions += cur_p

        year_growth += growth
        year_contrib += cur_p

        # End of year or final month checkpoint
        is_year_end = (m % 12 == 0)
        is_final_month = (m == n)

        if (is_year_end or is_final_month) and request.include_schedule:
            yr_num = year_idx + 1
            if is_year_end:
                label = f"Year {yr_num}"
            else:
                label = f"Month {m} (Partial Yr {yr_num})"

            schedule_items.append(
                SIPScheduleItem(
                    period=yr_num,
                    period_label=label,
                    opening_balance=quantize_decimal(Decimal(str(max(0.0, year_open))), 2),
                    contributions=quantize_decimal(Decimal(str(max(0.0, year_contrib))), 2),
                    growth_earned=quantize_decimal(Decimal(str(year_growth)), 2),
                    closing_balance=quantize_decimal(Decimal(str(max(0.0, balance))), 2),
                    total_contributed_to_date=quantize_decimal(Decimal(str(initial_l + cumulative_contributions)), 2),
                )
            )
            # Reset year trackers
            year_open = balance
            year_contrib = 0.0
            year_growth = 0.0

    total_invested_val = initial_l + cumulative_contributions
    wealth_gain_val = balance - total_invested_val

    assumptions = [
        "Contributions are deposited at the end of each calendar month (ordinary annuity convention).",
        f"Compounding rate convention: '{request.rate_convention}' ({'equivalent effective monthly rate' if request.rate_convention == 'effective' else 'nominal annual divided by 12'}).",
        "Rate of return is assumed constant throughout the investment horizon.",
    ]
    if request.annual_step_up_percentage:
        assumptions.append(f"Monthly contribution increases by {request.annual_step_up_percentage}% every 12 months.")

    disclaimers = [
        "Projections are deterministic mathematical estimates and do not guarantee market returns.",
        "Calculations exclude taxes, inflation, fund management fees, and transaction charges.",
    ]

    return SIPCalculationResponse(
        initial_investment=quantize_decimal(Decimal(str(initial_l)), 2),
        monthly_contribution=quantize_decimal(Decimal(str(monthly_p)), 2),
        annual_return_percentage=quantize_decimal(Decimal(str(request.annual_return_percentage)), 2),
        duration_months=n,
        rate_convention=request.rate_convention,
        projected_future_value=quantize_decimal(Decimal(str(max(0.0, balance))), 2),
        total_contributions=quantize_decimal(Decimal(str(max(0.0, cumulative_contributions))), 2),
        total_invested=quantize_decimal(Decimal(str(max(0.0, total_invested_val))), 2),
        estimated_wealth_gain=quantize_decimal(Decimal(str(wealth_gain_val)), 2),
        annual_step_up_percentage=quantize_decimal(Decimal(str(request.annual_step_up_percentage)), 2) if request.annual_step_up_percentage else None,
        schedule=schedule_items,
        assumptions=assumptions,
        disclaimers=disclaimers,
    )


def calculate_reverse_sip(request: ReverseSIPRequest) -> ReverseSIPResponse:
    """Calculate required monthly contribution to reach target future value from initial investment."""
    fv_target = float(request.target_amount)
    initial_l = float(request.initial_investment)
    n = request.duration_months
    r_m = compute_monthly_rate(request.annual_return_percentage, request.rate_convention)

    # Initial lump sum growth without any SIP
    if r_m == 0.0:
        lump_fv = initial_l
    else:
        lump_fv = initial_l * math.pow(1.0 + r_m, n)

    if lump_fv >= fv_target:
        # Initial investment already achieves or exceeds target
        required_p = 0.0
        is_covered = True
        explanation = (
            f"The initial investment of {initial_l:,.2f} is projected to grow to {lump_fv:,.2f} "
            f"over {n} months at {float(request.annual_return_percentage):.2f}% annual return, "
            f"which meets or exceeds the target amount of {fv_target:,.2f}. No recurring monthly SIP is required."
        )
    else:
        is_covered = False
        deficit = fv_target - lump_fv
        if r_m == 0.0:
            required_p = deficit / float(n)
        else:
            annuity_factor = (math.pow(1.0 + r_m, n) - 1.0) / r_m
            required_p = deficit / annuity_factor

        explanation = (
            f"To accumulate a target corpus of {fv_target:,.2f} over {n} months starting with an initial investment "
            f"of {initial_l:,.2f} at an assumed {float(request.annual_return_percentage):.2f}% annual return, "
            f"a disciplined monthly contribution of {required_p:,.2f} is required."
        )

    # Generate schedule using forward SIP with computed required_p
    fwd_req = SIPCalculationRequest(
        initial_investment=quantize_decimal(Decimal(str(initial_l)), 2),
        monthly_contribution=quantize_decimal(Decimal(str(max(0.0, required_p))), 2),
        annual_return_percentage=request.annual_return_percentage,
        duration_months=n,
        rate_convention=request.rate_convention,
        include_schedule=request.include_schedule,
    )
    fwd_res = calculate_forward_sip(fwd_req)

    assumptions = [
        "Contributions are deposited at the end of each calendar month (ordinary annuity convention).",
        f"Compounding rate convention: '{request.rate_convention}' ({'equivalent effective monthly rate' if request.rate_convention == 'effective' else 'nominal annual divided by 12'}).",
        "Rate of return is assumed constant and realized smoothly across all periods.",
    ]
    disclaimers = [
        "The calculated monthly SIP is a deterministic projection based on the stated return assumption.",
        "Market volatility, investment fees, taxes, and inflation may cause actual future values to vary.",
    ]

    return ReverseSIPResponse(
        target_amount=quantize_decimal(Decimal(str(fv_target)), 2),
        initial_investment=quantize_decimal(Decimal(str(initial_l)), 2),
        annual_return_percentage=quantize_decimal(Decimal(str(request.annual_return_percentage)), 2),
        duration_months=n,
        rate_convention=request.rate_convention,
        required_monthly_contribution=quantize_decimal(Decimal(str(max(0.0, required_p))), 2),
        projected_future_value=fwd_res.projected_future_value,
        total_contributions=fwd_res.total_contributions,
        total_invested=fwd_res.total_invested,
        estimated_wealth_gain=fwd_res.estimated_wealth_gain,
        is_target_already_covered=is_covered,
        schedule=fwd_res.schedule,
        explanation=explanation,
        assumptions=assumptions,
        disclaimers=disclaimers,
    )
