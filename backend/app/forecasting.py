"""
30-day cash-flow forecasting module.

Produces a day-by-day projection of cash balances over the next 30 days
using a simple, fully deterministic methodology.

Methodology (in order of application)
--------------------------------------
1. Filter the transaction history to an explicit observation window
   (default: the most recent 6 distinct calendar months).
2. Detect recurring transactions: a transaction group is considered monthly-
   recurring only when it appears in **two or more distinct calendar months**
   with the same normalised description and transaction type.
3. Compute average monthly income and expenses from the observation window.
4. Subtract the recurring portion from the average so that recurring items
   are projected explicitly on their expected day, while non-recurring items
   are spread evenly across the 30-day window.
5. For each forecast day:
   a. Add user-confirmed future income.
   b. Subtract user-confirmed future expenses.
   c. Add any detected recurring income due on that calendar day
      (skipped if the user has already confirmed a transaction with the
      same normalised description + type).
   d. Subtract any detected recurring expense due on that calendar day
      (same skip logic).
   e. Add the daily share of non-recurring average income (monthly ÷ 30).
   f. Subtract the daily share of non-recurring average expenses (monthly ÷ 30).
   g. Update the running closing balance.

Limitations
-----------
- Recurring detection is conservative: two occurrences required.
  A one-time transaction is never projected as recurring.
- Typical day of month is clamped to 28 to remain valid in every month
  (e.g., salary on the 31st is approximated as the 28th).
- Historical patterns may not repeat.  Forecasts are estimates, not
  financial guarantees.
- The system cannot infer the user's actual bank balance from transactions.
  ``current_balance`` is always a required user input.
"""

import statistics
from collections import defaultdict
from datetime import date as ISODate
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, List, Optional, Tuple

from app.schemas import StoredTransaction, TransactionType

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FORECAST_DAYS: int = 30
"""Number of days in the forecast horizon."""

_MIN_MONTHS_FOR_RECURRING: int = 2
"""Minimum number of distinct calendar months a transaction must appear in
before it is treated as a monthly recurring transaction."""

_MIN_RELIABLE_HISTORY_MONTHS: int = 2
"""Minimum months of history considered sufficient for confident forecasting."""

_SAFE_MAX_DAY: int = 28
"""Recurring transactions whose median day exceeds this value are clamped
here so the projected date is valid in every calendar month (Feb–Dec)."""

_TWO_PLACES = Decimal("0.01")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fmt(value: Decimal) -> str:
    return str(value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP))


def _year_month(d: ISODate) -> Tuple[int, int]:
    return (d.year, d.month)


def _normalize(description: str) -> str:
    """Case-fold and strip a description for comparison."""
    return description.strip().lower()


# ---------------------------------------------------------------------------
# Recurring transaction detection
# ---------------------------------------------------------------------------


class _RecurringTransaction:
    """Represents a detected monthly-recurring transaction pattern."""

    __slots__ = (
        "normalized_description",
        "transaction_type",
        "typical_day_of_month",
        "typical_amount",
        "months_observed",
    )

    def __init__(
        self,
        normalized_description: str,
        transaction_type: TransactionType,
        typical_day_of_month: int,
        typical_amount: Decimal,
        months_observed: int,
    ) -> None:
        self.normalized_description = normalized_description
        self.transaction_type = transaction_type
        self.typical_day_of_month = typical_day_of_month
        self.typical_amount = typical_amount
        self.months_observed = months_observed

    @property
    def key(self) -> Tuple[str, TransactionType]:
        """Fingerprint used to deduplicate against user-confirmed future transactions."""
        return (self.normalized_description, self.transaction_type)


def detect_recurring(
    transactions: List[StoredTransaction],
) -> List[_RecurringTransaction]:
    """Identify monthly-recurring transaction patterns in historical data.

    A pattern is recognised only when the **same normalised description and
    transaction type** appears in at least ``_MIN_MONTHS_FOR_RECURRING``
    distinct calendar months.  Single-month purchases are never labelled
    recurring.

    Args:
        transactions: Historical stored transactions.

    Returns:
        A list of :class:`_RecurringTransaction` objects, one per detected
        pattern.
    """
    # Group occurrences by (normalised description, transaction_type)
    groups: Dict[Tuple[str, TransactionType], List[dict]] = defaultdict(list)
    for txn in transactions:
        key = (_normalize(txn.description), txn.transaction_type)
        groups[key].append(
            {
                "ym": _year_month(txn.date),
                "day": txn.date.day,
                "amount": Decimal(str(txn.amount)),
            }
        )

    result: List[_RecurringTransaction] = []
    for (norm_desc, txn_type), occurrences in groups.items():
        distinct_months = {o["ym"] for o in occurrences}
        if len(distinct_months) < _MIN_MONTHS_FOR_RECURRING:
            continue  # One-time transaction — skip

        days = [o["day"] for o in occurrences]
        amounts = sorted(o["amount"] for o in occurrences)

        # Use median day (robust against one-off date shifts) clamped to safe max
        typical_day = min(int(statistics.median(days)), _SAFE_MAX_DAY)
        # Use median amount (robust against one-off unusual payments)
        typical_amount = amounts[len(amounts) // 2]

        result.append(
            _RecurringTransaction(
                normalized_description=norm_desc,
                transaction_type=txn_type,
                typical_day_of_month=typical_day,
                typical_amount=typical_amount,
                months_observed=len(distinct_months),
            )
        )

    return result


# ---------------------------------------------------------------------------
# Forecast generation
# ---------------------------------------------------------------------------


def generate_cash_flow_forecast(
    transactions: List[StoredTransaction],
    current_balance: Decimal,
    forecast_start_date: ISODate,
    min_cash_buffer: Decimal = Decimal("0"),
    confirmed_future_transactions: Optional[List] = None,
    observation_window_months: int = 6,
) -> dict:
    """Generate a deterministic 30-day cash-flow forecast.

    This function is decoupled from FastAPI for testability.

    Args:
        transactions: All stored transactions from the repository.
        current_balance: The user's current cash balance (required; the
            system never guesses this from transaction history).
        forecast_start_date: The first day of the 30-day forecast window.
        min_cash_buffer: Days where the projected balance falls below this
            threshold (but remains non-negative) are flagged as low-cash
            days.  Defaults to zero.
        confirmed_future_transactions: A list of
            :class:`~app.schemas.FutureTransaction` objects representing
            income or expenses the user knows will occur.  These are
            incorporated as-is.
        observation_window_months: How many recent calendar months of
            history to use.  Older months are excluded.

    Returns:
        A plain ``dict`` that maps directly to
        :class:`~app.schemas.CashFlowForecastResponse` fields.
    """
    if confirmed_future_transactions is None:
        confirmed_future_transactions = []

    warnings: List[str] = []
    assumptions: List[str] = [
        f"Observation window: the most recent {observation_window_months} distinct "
        "calendar month(s) of transaction history (or all available if fewer).",
        (
            f"Recurring patterns require ≥ {_MIN_MONTHS_FOR_RECURRING} distinct calendar "
            "months with the same description and transaction type."
        ),
        (
            "Recurring transactions are projected on their typical day of month "
            f"(clamped to day {_SAFE_MAX_DAY} to be valid in all months)."
        ),
        "Non-recurring historical income and expenses are spread evenly across 30 days.",
        "User-confirmed future transactions are included at their stated amounts and dates.",
        (
            "If a confirmed future transaction shares a description + type with a "
            "detected recurring transaction, the recurring item is NOT projected again "
            "on that day to avoid double-counting."
        ),
        "Forecasts are probabilistic estimates. Actual cash flows will differ.",
        "All amounts are in INR.",
    ]

    forecast_end_date = forecast_start_date + timedelta(days=FORECAST_DAYS - 1)

    # -----------------------------------------------------------------------
    # Step 1 — filter to observation window
    # -----------------------------------------------------------------------
    all_months = sorted({_year_month(t.date) for t in transactions})

    if len(all_months) > observation_window_months:
        window_set = set(all_months[-observation_window_months:])
    else:
        window_set = set(all_months)

    history = [t for t in transactions if _year_month(t.date) in window_set]
    months_used = len(window_set)

    # -----------------------------------------------------------------------
    # Step 2 — data-quality warnings
    # -----------------------------------------------------------------------
    if months_used == 0:
        warnings.append(
            "No transaction history available. "
            "Forecast is based entirely on user-confirmed future transactions. "
            "Average daily values are zero."
        )
    elif months_used < _MIN_RELIABLE_HISTORY_MONTHS:
        warnings.append(
            f"Only {months_used} month(s) of transaction history available "
            f"(minimum {_MIN_RELIABLE_HISTORY_MONTHS} recommended). "
            "Forecast accuracy is limited."
        )

    # -----------------------------------------------------------------------
    # Step 3 — detect recurring patterns
    # -----------------------------------------------------------------------
    recurring_list = detect_recurring(history) if history else []

    if not recurring_list and months_used >= _MIN_RELIABLE_HISTORY_MONTHS:
        warnings.append(
            "No recurring transaction patterns detected. "
            "Forecast uses only average daily values and confirmed future transactions."
        )

    # -----------------------------------------------------------------------
    # Step 4 — compute average monthly totals
    # -----------------------------------------------------------------------
    if months_used > 0:
        months_d = Decimal(str(months_used))
        avg_monthly_income = (
            sum(Decimal(str(t.amount)) for t in history
                if t.transaction_type == TransactionType.income)
            / months_d
        )
        avg_monthly_expense = (
            sum(Decimal(str(t.amount)) for t in history
                if t.transaction_type == TransactionType.expense)
            / months_d
        )
    else:
        avg_monthly_income = Decimal("0")
        avg_monthly_expense = Decimal("0")

    # -----------------------------------------------------------------------
    # Step 5 — subtract recurring contribution from the average
    # (prevents double-counting when recurring is also in the baseline)
    # -----------------------------------------------------------------------
    recurring_monthly_income = sum(
        r.typical_amount for r in recurring_list
        if r.transaction_type == TransactionType.income
    )
    recurring_monthly_expense = sum(
        r.typical_amount for r in recurring_list
        if r.transaction_type == TransactionType.expense
    )

    non_recurring_income = max(Decimal("0"), avg_monthly_income - recurring_monthly_income)
    non_recurring_expense = max(Decimal("0"), avg_monthly_expense - recurring_monthly_expense)
    daily_avg_income = non_recurring_income / Decimal("30")
    daily_avg_expense = non_recurring_expense / Decimal("30")

    # -----------------------------------------------------------------------
    # Step 6 — build confirmed-transaction lookup structures
    # -----------------------------------------------------------------------
    confirmed_by_date: Dict[ISODate, list] = defaultdict(list)
    for ft in confirmed_future_transactions:
        confirmed_by_date[ft.date].append(ft)

    # Fingerprints used to skip recurring on days where user has confirmed the same item
    confirmed_fingerprints: set = {
        (_normalize(ft.description), ft.transaction_type)
        for ft in confirmed_future_transactions
    }

    # -----------------------------------------------------------------------
    # Step 7 — day-by-day projection
    # -----------------------------------------------------------------------
    balance = current_balance
    daily_forecasts: List[dict] = []
    total_proj_income = Decimal("0")
    total_proj_expense = Decimal("0")
    low_cash_dates: List[str] = []
    negative_balance_dates: List[str] = []

    for offset in range(FORECAST_DAYS):
        forecast_date = forecast_start_date + timedelta(days=offset)
        day_income = Decimal("0")
        day_expense = Decimal("0")

        # 7a — user-confirmed transactions for this day
        for ft in confirmed_by_date.get(forecast_date, []):
            amt = Decimal(str(ft.amount))
            if ft.transaction_type == TransactionType.income:
                day_income += amt
            else:
                day_expense += amt

        # 7b — detected recurring (skip if user already confirmed same fingerprint)
        for r in recurring_list:
            if r.typical_day_of_month == forecast_date.day:
                if r.key not in confirmed_fingerprints:
                    if r.transaction_type == TransactionType.income:
                        day_income += r.typical_amount
                    else:
                        day_expense += r.typical_amount

        # 7c — non-recurring daily spread
        day_income += daily_avg_income
        day_expense += daily_avg_expense

        net = day_income - day_expense
        balance += net

        is_negative = balance < Decimal("0")
        is_low = (not is_negative) and (balance < min_cash_buffer)

        if is_negative:
            negative_balance_dates.append(forecast_date.isoformat())
        if is_low:
            low_cash_dates.append(forecast_date.isoformat())

        total_proj_income += day_income
        total_proj_expense += day_expense

        daily_forecasts.append({
            "date": forecast_date.isoformat(),
            "projected_income": _fmt(day_income),
            "projected_expenses": _fmt(day_expense),
            "net_daily_flow": _fmt(net),
            "closing_balance": _fmt(balance),
            "is_low_cash": is_low,
            "is_negative_balance": is_negative,
        })

    # -----------------------------------------------------------------------
    # Return payload
    # -----------------------------------------------------------------------
    return {
        "forecast_start_date": forecast_start_date.isoformat(),
        "forecast_end_date": forecast_end_date.isoformat(),
        "opening_balance": _fmt(current_balance),
        "projected_closing_balance": _fmt(balance),
        "total_projected_income": _fmt(total_proj_income),
        "total_projected_expenses": _fmt(total_proj_expense),
        "net_projected_cash_flow": _fmt(total_proj_income - total_proj_expense),
        "low_cash_dates": low_cash_dates,
        "negative_balance_dates": negative_balance_dates,
        "daily_forecasts": daily_forecasts,
        "detected_recurring_transactions": [
            {
                "description": r.normalized_description,
                "transaction_type": r.transaction_type.value,
                "typical_day_of_month": r.typical_day_of_month,
                "typical_amount": _fmt(r.typical_amount),
                "months_observed": r.months_observed,
            }
            for r in recurring_list
        ],
        "months_of_history_used": months_used,
        "methodology": (
            "1. History filtered to observation window. "
            "2. Recurring patterns detected (≥2 distinct months, same description+type). "
            "3. Average monthly income/expenses computed; recurring portion subtracted. "
            "4. Each forecast day: confirmed transactions + projected recurring "
            "(if not already confirmed) + daily share of non-recurring average."
        ),
        "assumptions": assumptions,
        "warnings": warnings,
    }
