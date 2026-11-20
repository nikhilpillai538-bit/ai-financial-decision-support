"""
Emergency fund analysis module.

Performs deterministic calculations to help users understand whether their
emergency savings can cover essential living expenses.

Key design principles
---------------------
- Only explicitly supplied emergency fund balances are used.  The system
  never infers a cash balance from transaction history.
- Essential expense categories are configurable; defaults are documented.
- All arithmetic uses ``Decimal`` to prevent floating-point rounding errors.
- When data is insufficient the module reports its limitations clearly
  rather than presenting unreliable averages as fact.
- No investment recommendations are made from these calculations alone.

Terminology
-----------
- *Essential expenses*: recurring costs required for basic living
  (rent, groceries, utilities, healthcare, transport, and any
  user-configured additions).
- *Average monthly essential expenses*: total essential expenses in the
  observation window divided by the number of distinct calendar months
  represented in that window.
- *Three-month target*: average monthly essential × 3 (widely cited
  minimum emergency fund recommendation).
- *Six-month target*: average monthly essential × 6 (more conservative
  recommendation).
- *Months of coverage*: emergency_fund_balance ÷ average monthly essential.
"""

from collections import defaultdict
from datetime import date as ISODate
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional, Tuple

from app.schemas import StoredTransaction, TransactionType

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Expense categories treated as essential by default.
#: Import this constant from ``schemas.py`` if you need it in schema
#: validators; it is defined here to keep the logic collocated.
DEFAULT_ESSENTIAL_CATEGORIES: List[str] = [
    "rent",
    "groceries",
    "utilities",
    "healthcare",
    "transport",
]

#: Minimum number of complete months considered sufficient for a reliable
#: monthly average.  Below this threshold a data-quality warning is added.
_MIN_RELIABLE_MONTHS = 3

_TWO_PLACES = Decimal("0.01")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fmt(value: Decimal) -> str:
    """Return a Decimal quantised to two decimal places as a string."""
    return str(value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP))


def _year_month(d: ISODate) -> Tuple[int, int]:
    return (d.year, d.month)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def calculate_emergency_fund_analysis(
    transactions: List[StoredTransaction],
    emergency_fund_balance: Optional[Decimal],
    essential_categories: List[str],
    analysis_window_months: int = 12,
) -> dict:
    """Return a dictionary containing the full emergency fund analysis.

    This function is intentionally decoupled from FastAPI so it can be
    unit-tested and reused without an HTTP context.

    Args:
        transactions: All stored transactions retrieved from the repository.
        emergency_fund_balance: The user's explicitly stated emergency fund
            balance in INR.  Pass ``None`` when unknown — the system will
            report the gap in the response rather than assuming zero.
        essential_categories: Expense category labels to count as essential.
            Matched case-insensitively against ``StoredTransaction.category``.
        analysis_window_months: Maximum number of the most recent complete
            calendar months to include in the average.  Older months are
            excluded.  Defaults to 12.

    Returns:
        A plain ``dict`` that maps directly to
        :class:`~app.schemas.EmergencyFundAnalysisResponse` fields.
    """
    warnings: List[str] = []
    assumptions: List[str] = [
        (
            f"Essential expense categories used: "
            f"{', '.join(sorted(set(c.lower() for c in essential_categories)))}."
        ),
        (
            "Average monthly essential expenses = total essential expenses in the "
            "observation window ÷ number of distinct calendar months in that window."
        ),
        "Only expense transactions are counted; income transactions are excluded.",
        (
            "Months with no essential expense transactions still count toward the "
            "denominator, which prevents overstating the average during low-spend months."
        ),
        (
            "Three-month target = average monthly essential × 3. "
            "Six-month target = average monthly essential × 6."
        ),
    ]

    essential_cats_lower = {c.strip().lower() for c in essential_categories}

    # -----------------------------------------------------------------------
    # Step 1 — determine the observation window
    # -----------------------------------------------------------------------
    all_months_in_history: List[Tuple[int, int]] = sorted(
        {_year_month(t.date) for t in transactions}
    )

    if analysis_window_months and len(all_months_in_history) > analysis_window_months:
        window_months_set = set(all_months_in_history[-analysis_window_months:])
    else:
        window_months_set = set(all_months_in_history)

    complete_months_analyzed = len(window_months_set)

    # -----------------------------------------------------------------------
    # Step 2 — data-quality checks
    # -----------------------------------------------------------------------
    if complete_months_analyzed == 0:
        warnings.append(
            "No transaction history found. "
            "Cannot compute average monthly essential expenses. "
            "Add transactions first."
        )

    elif complete_months_analyzed < _MIN_RELIABLE_MONTHS:
        warnings.append(
            f"Only {complete_months_analyzed} calendar month(s) of transaction "
            f"history found in the analysis window "
            f"(minimum {_MIN_RELIABLE_MONTHS} recommended for a reliable average). "
            "The computed average may not reflect long-term spending patterns."
        )

    # -----------------------------------------------------------------------
    # Step 3 — sum essential expenses inside the window
    # -----------------------------------------------------------------------
    essential_in_window = [
        t for t in transactions
        if t.transaction_type == TransactionType.expense
        and t.category.strip().lower() in essential_cats_lower
        and _year_month(t.date) in window_months_set
    ]

    if not essential_in_window and complete_months_analyzed > 0:
        warnings.append(
            f"No expense transactions found in the essential categories "
            f"({', '.join(sorted(essential_cats_lower))}) "
            f"within the analysis window. "
            "Average monthly essential expenses is zero. "
            "Check that your transactions are categorized correctly."
        )

    total_essential = sum(
        Decimal(str(t.amount)) for t in essential_in_window
    )

    # -----------------------------------------------------------------------
    # Step 4 — average (guard against zero-months denominator)
    # -----------------------------------------------------------------------
    if complete_months_analyzed > 0:
        avg_monthly_essential = total_essential / Decimal(str(complete_months_analyzed))
    else:
        avg_monthly_essential = Decimal("0")

    # -----------------------------------------------------------------------
    # Step 5 — targets
    # -----------------------------------------------------------------------
    three_month_target = avg_monthly_essential * Decimal("3")
    six_month_target = avg_monthly_essential * Decimal("6")

    # -----------------------------------------------------------------------
    # Step 6 — balance-dependent calculations
    # -----------------------------------------------------------------------
    balance_status = "unknown"
    months_of_coverage: Optional[str] = None
    shortfall_three_month: Optional[str] = None
    shortfall_six_month: Optional[str] = None
    balance_str: Optional[str] = None

    if emergency_fund_balance is not None:
        balance_status = "known"
        balance_str = _fmt(emergency_fund_balance)

        shortfall_three_month = _fmt(
            max(Decimal("0"), three_month_target - emergency_fund_balance)
        )
        shortfall_six_month = _fmt(
            max(Decimal("0"), six_month_target - emergency_fund_balance)
        )

        if avg_monthly_essential > Decimal("0"):
            coverage = emergency_fund_balance / avg_monthly_essential
            months_of_coverage = _fmt(coverage)
        else:
            months_of_coverage = None  # Not meaningful when avg expenses are zero
            warnings.append(
                "Months of coverage cannot be calculated because average monthly "
                "essential expenses is zero."
            )
    else:
        warnings.append(
            "Emergency fund balance has not been provided. "
            "Shortfall and months of coverage cannot be calculated. "
            "Use PUT /financial-profile/emergency-fund to set your balance."
        )

    return {
        "currency": "INR",
        "analysis_window_months_requested": analysis_window_months,
        "complete_months_analyzed": complete_months_analyzed,
        "essential_categories_used": sorted(essential_cats_lower),
        "essential_expense_transaction_count": len(essential_in_window),
        "average_monthly_essential_expenses": _fmt(avg_monthly_essential),
        "three_month_target": _fmt(three_month_target),
        "six_month_target": _fmt(six_month_target),
        "emergency_fund_balance": balance_str,
        "balance_status": balance_status,
        "shortfall_three_month": shortfall_three_month,
        "shortfall_six_month": shortfall_six_month,
        "months_of_coverage": months_of_coverage,
        "warnings": warnings,
        "assumptions": assumptions,
    }
