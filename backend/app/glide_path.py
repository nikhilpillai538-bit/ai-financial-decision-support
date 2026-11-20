"""
Deterministic Risk-Aware Investment Glide Path Service for Phase 8.

Generates milestone checkpoints that gradually de-risk asset allocation
from starting weights to capital preservation ending weights as the investment
goal deadline approaches.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set

from app.db.models import AssetClass
from app.goal_schemas import (
    GlidePathCheckpoint,
    GlidePathRequest,
    GlidePathResponse,
)
from app.portfolio_schemas import quantize_decimal

CLASS_ALIASES = {
    "fixed_income": "debt",
    "bonds": "debt",
    "bond": "debt",
    "gold": "commodities_gold",
    "commodities": "commodities_gold",
}

# Standard risk-profile defaults if user does not supply custom starting/ending weights
DEFAULT_STARTING_ALLOCATIONS = {
    "aggressive": {"equity": Decimal("85.00"), "debt": Decimal("10.00"), "cash": Decimal("5.00")},
    "moderate": {"equity": Decimal("70.00"), "debt": Decimal("25.00"), "cash": Decimal("5.00")},
    "conservative": {"equity": Decimal("50.00"), "debt": Decimal("40.00"), "cash": Decimal("10.00")},
}

DEFAULT_ENDING_ALLOCATIONS = {
    "aggressive": {"equity": Decimal("30.00"), "debt": Decimal("55.00"), "cash": Decimal("15.00")},
    "moderate": {"equity": Decimal("20.00"), "debt": Decimal("60.00"), "cash": Decimal("20.00")},
    "conservative": {"equity": Decimal("10.00"), "debt": Decimal("60.00"), "cash": Decimal("30.00")},
}

VALID_ASSET_CLASSES = {c.value for c in AssetClass}


def normalize_class_name(ac: str) -> str:
    s = ac.strip().lower()
    return CLASS_ALIASES.get(s, s)


def _validate_allocation(alloc: Dict[str, Decimal], name: str):
    """Validate that weights are nonnegative, classes are valid, and sum to 100%."""
    total = Decimal("0.00")
    for ac, w in alloc.items():
        if w < Decimal("0.00"):
            raise ValueError(f"Weight for '{ac}' in {name} cannot be negative ({w}%).")
        if ac not in VALID_ASSET_CLASSES:
            raise ValueError(f"Invalid asset class '{ac}' in {name}. Must be one of {sorted(list(VALID_ASSET_CLASSES))}.")
        total += w

    if abs(total - Decimal("100.00")) > Decimal("0.50"):
        raise ValueError(f"{name} weights must sum to 100.00% (currently sums to {total}%).")
        total += w

    if abs(total - Decimal("100.00")) > Decimal("0.50"):
        raise ValueError(f"{name} weights must sum to 100.00% (currently sums to {total}%).")


def generate_glide_path(
    start_date: date,
    target_date: date,
    request: GlidePathRequest,
    goal_id: Optional[str] = None,
    goal_name: Optional[str] = None,
) -> GlidePathResponse:
    """Generate deterministic milestone checkpoints transitioning from starting to ending allocation."""
    total_days = (target_date - start_date).days
    if total_days <= 0:
        raise ValueError(f"Target completion date ({target_date.isoformat()}) must be after start date ({start_date.isoformat()}).")

    risk_prof = request.risk_profile or "moderate"
    start_alloc = request.starting_allocation or DEFAULT_STARTING_ALLOCATIONS.get(risk_prof, DEFAULT_STARTING_ALLOCATIONS["moderate"])
    end_alloc = request.ending_allocation or DEFAULT_ENDING_ALLOCATIONS.get(risk_prof, DEFAULT_ENDING_ALLOCATIONS["moderate"])

    # Clean and normalize dictionaries
    start_alloc = {normalize_class_name(k): quantize_decimal(Decimal(str(v)), 2) for k, v in start_alloc.items()}
    end_alloc = {normalize_class_name(k): quantize_decimal(Decimal(str(v)), 2) for k, v in end_alloc.items()}

    _validate_allocation(start_alloc, "Starting allocation")
    _validate_allocation(end_alloc, "Ending allocation")

    # Union of all asset classes
    all_classes = sorted(list(set(start_alloc.keys()).union(end_alloc.keys())))
    for ac in all_classes:
        start_alloc.setdefault(ac, Decimal("0.00"))
        end_alloc.setdefault(ac, Decimal("0.00"))

    interval_m = request.interval_months
    total_years = quantize_decimal(Decimal(str(total_days)) / Decimal("365.25"), 2)

    # Determine checkpoint dates
    checkpoint_dates: List[date] = [start_date]
    cur_date = start_date
    while True:
        # Step forward interval_m months (approx 30.4375 days * interval)
        step_days = int(round(interval_m * 30.4375))
        next_date = cur_date + timedelta(days=step_days)
        if next_date >= target_date:
            break
        checkpoint_dates.append(next_date)
        cur_date = next_date

    if checkpoint_dates[-1] != target_date:
        checkpoint_dates.append(target_date)

    checkpoints: List[GlidePathCheckpoint] = []
    n_pts = len(checkpoint_dates)

    for idx, cp_date in enumerate(checkpoint_dates):
        if n_pts == 1 or total_days == 0:
            alpha = 0.0
        else:
            elapsed_days = (cp_date - start_date).days
            alpha = min(1.0, max(0.0, float(elapsed_days) / float(total_days)))

        days_rem = max(0, (target_date - cp_date).days)
        years_rem = quantize_decimal(Decimal(str(days_rem)) / Decimal("365.25"), 2)
        months_rem = max(0, int(round(days_rem / 30.4375)))

        # Linear interpolation between start and end weights
        raw_weights: Dict[str, float] = {}
        for ac in all_classes:
            w_s = float(start_alloc[ac])
            w_e = float(end_alloc[ac])
            raw_weights[ac] = (1.0 - alpha) * w_s + alpha * w_e

        # Normalize and quantize weights so they sum exactly to 100.00%
        sum_raw = sum(raw_weights.values())
        norm_weights = {ac: (w / sum_raw) * 100.0 for ac, w in raw_weights.items()}

        quantized_weights: Dict[str, Decimal] = {
            ac: quantize_decimal(Decimal(str(w)), 2) for ac, w in norm_weights.items()
        }
        # Correct residual cent rounding on largest weight
        q_sum = sum(quantized_weights.values())
        diff = Decimal("100.00") - q_sum
        if diff != Decimal("0.00"):
            max_ac = max(quantized_weights.keys(), key=lambda k: quantized_weights[k])
            quantized_weights[max_ac] = quantize_decimal(quantized_weights[max_ac] + diff, 2)

        # Risk level determination based on equity proportion
        eq_weight = quantized_weights.get("equity", Decimal("0.00"))
        fi_weight = quantized_weights.get("fixed_income", Decimal("0.00"))
        cash_weight = quantized_weights.get("cash", Decimal("0.00"))

        if eq_weight >= Decimal("60.00"):
            risk_level = "aggressive"
        elif eq_weight >= Decimal("35.00"):
            risk_level = "moderate"
        else:
            risk_level = "conservative"

        # Explainable commentary
        if idx == 0:
            commentary = f"Initial accumulation stage: High growth orientation with {eq_weight}% equity."
        elif idx == n_pts - 1:
            commentary = (
                f"Goal milestone horizon reached: Capital preservation priority with {fi_weight}% fixed income "
                f"and {cash_weight}% cash to mitigate sequence-of-returns risk."
            )
        else:
            commentary = (
                f"De-risking transition at {months_rem} months to goal: Equity reduced to {eq_weight}% and "
                f"defensive assets increased to {fi_weight + cash_weight}%."
            )

        checkpoints.append(
            GlidePathCheckpoint(
                checkpoint_index=idx,
                checkpoint_date=cp_date,
                years_remaining=years_rem,
                months_remaining=months_rem,
                allocation_weights=quantized_weights,
                risk_level=risk_level,
                commentary=commentary,
            )
        )

    assumptions = [
        "Asset weights transition monotonically from starting allocation to ending allocation.",
        f"Allocation checkpoints are calculated at approximately {interval_m}-month intervals.",
        "Rebalancing at milestone checkpoints assumes zero friction, transaction costs, and tax liabilities.",
        "Deterministic model: Actual market fluctuations may require tactical adjustments between milestones.",
    ]

    return GlidePathResponse(
        goal_id=goal_id,
        goal_name=goal_name,
        start_date=start_date,
        target_date=target_date,
        total_horizon_years=total_years,
        interval_months=interval_m,
        starting_allocation=start_alloc,
        ending_allocation=end_alloc,
        checkpoints=checkpoints,
        assumptions=assumptions,
        warnings=[],
    )
