"""
Unit tests for app/forecasting.py — 30-day cash-flow forecasting module.

All tests use pure Python inputs (no HTTP, no repository) and a fixed
``forecast_start_date`` so that results never depend on the real current date.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.forecasting import (
    FORECAST_DAYS,
    _MIN_MONTHS_FOR_RECURRING,
    detect_recurring,
    generate_cash_flow_forecast,
)
from app.schemas import (
    FutureTransaction,
    StoredTransaction,
    TransactionSource,
    TransactionType,
)

# ---------------------------------------------------------------------------
# Fixed reference dates used in tests
# ---------------------------------------------------------------------------

START = date(2024, 3, 1)  # All forecasts start here to avoid date-dependency


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _stored(
    amount: str,
    txn_type: TransactionType,
    txn_date: str,
    description: str = "Salary",
    category: str = "salary",
) -> StoredTransaction:
    return StoredTransaction(
        id="test-id",
        date=txn_date,
        description=description,
        amount=Decimal(amount),
        transaction_type=txn_type,
        category=category,
        source=TransactionSource.manual,
    )


def _income(amount: str, txn_date: str, description: str = "Salary") -> StoredTransaction:
    return _stored(amount, TransactionType.income, txn_date, description, "salary")


def _expense(amount: str, txn_date: str, description: str = "Rent", category: str = "rent") -> StoredTransaction:
    return _stored(amount, TransactionType.expense, txn_date, description, category)


def _future(amount: str, txn_type: str, txn_date: str, description: str = "Future item") -> FutureTransaction:
    return FutureTransaction(
        date=txn_date,
        description=description,
        amount=Decimal(amount),
        transaction_type=TransactionType(txn_type),
    )


def _forecast(
    transactions,
    balance: str = "0.00",
    start: date = START,
    buffer: str = "0.00",
    confirmed=None,
    window: int = 6,
) -> dict:
    return generate_cash_flow_forecast(
        transactions=transactions,
        current_balance=Decimal(balance),
        forecast_start_date=start,
        min_cash_buffer=Decimal(buffer),
        confirmed_future_transactions=confirmed or [],
        observation_window_months=window,
    )


# ---------------------------------------------------------------------------
# Forecast structure and dates
# ---------------------------------------------------------------------------


class TestForecastStructure:
    def test_exactly_30_daily_forecasts(self):
        result = _forecast([], balance="10000.00")
        assert len(result["daily_forecasts"]) == FORECAST_DAYS

    def test_forecast_start_and_end_dates(self):
        result = _forecast([], balance="0.00", start=date(2024, 3, 1))
        assert result["forecast_start_date"] == "2024-03-01"
        assert result["forecast_end_date"] == "2024-03-30"

    def test_opening_balance_matches_input(self):
        result = _forecast([], balance="12345.67")
        assert result["opening_balance"] == "12345.67"

    def test_forecast_is_reproducible(self):
        txns = [
            _income("50000.00", "2024-01-01"),
            _expense("20000.00", "2024-01-05"),
            _income("50000.00", "2024-02-01"),
            _expense("20000.00", "2024-02-05"),
        ]
        r1 = _forecast(txns, balance="100000.00")
        r2 = _forecast(txns, balance="100000.00")
        assert r1["daily_forecasts"] == r2["daily_forecasts"]

    def test_months_of_history_reported(self):
        txns = [
            _income("50000.00", "2024-01-01"),
            _income("50000.00", "2024-02-01"),
        ]
        result = _forecast(txns, window=6)
        assert result["months_of_history_used"] == 2


# ---------------------------------------------------------------------------
# Empty / no-history cases
# ---------------------------------------------------------------------------


class TestNoHistory:
    def test_no_history_produces_warning(self):
        result = _forecast([], balance="50000.00")
        assert any("No transaction history" in w for w in result["warnings"])

    def test_no_history_income_and_expenses_are_zero(self):
        result = _forecast([], balance="50000.00")
        for day in result["daily_forecasts"]:
            # Without confirmed future txns, daily income from non-recurring baseline is 0
            assert day["projected_income"] == "0.00"
            assert day["projected_expenses"] == "0.00"

    def test_no_history_balance_unchanged_over_30_days(self):
        result = _forecast([], balance="50000.00")
        for day in result["daily_forecasts"]:
            assert day["closing_balance"] == "50000.00"


# ---------------------------------------------------------------------------
# Confirmed future transactions
# ---------------------------------------------------------------------------


class TestConfirmedFutureTransactions:
    def test_confirmed_income_appears_on_correct_day(self):
        confirmed = [_future("10000.00", "income", "2024-03-05", "Bonus")]
        result = _forecast([], balance="0.00", confirmed=confirmed)
        march_5 = result["daily_forecasts"][4]  # day index 4 → March 5
        assert march_5["date"] == "2024-03-05"
        assert Decimal(march_5["projected_income"]) == Decimal("10000.00")

    def test_confirmed_expense_appears_on_correct_day(self):
        confirmed = [_future("5000.00", "expense", "2024-03-10", "Insurance")]
        result = _forecast([], balance="20000.00", confirmed=confirmed)
        march_10 = result["daily_forecasts"][9]
        assert Decimal(march_10["projected_expenses"]) == Decimal("5000.00")

    def test_multiple_confirmed_on_same_day_summed(self):
        confirmed = [
            _future("3000.00", "income", "2024-03-01", "Freelance A"),
            _future("2000.00", "income", "2024-03-01", "Freelance B"),
        ]
        result = _forecast([], balance="0.00", confirmed=confirmed)
        march_1 = result["daily_forecasts"][0]
        assert Decimal(march_1["projected_income"]) == Decimal("5000.00")

    def test_total_projected_income_includes_confirmed(self):
        confirmed = [_future("12000.00", "income", "2024-03-15", "Big payment")]
        result = _forecast([], balance="0.00", confirmed=confirmed)
        assert Decimal(result["total_projected_income"]) == Decimal("12000.00")


# ---------------------------------------------------------------------------
# Recurring transaction detection
# ---------------------------------------------------------------------------


class TestRecurringDetection:
    def test_same_description_two_months_is_recurring(self):
        txns = [
            _income("50000.00", "2024-01-01", description="Monthly salary"),
            _income("50000.00", "2024-02-01", description="Monthly salary"),
        ]
        recurring = detect_recurring(txns)
        assert len(recurring) == 1
        assert recurring[0].normalized_description == "monthly salary"

    def test_one_occurrence_is_not_recurring(self):
        txns = [_expense("5000.00", "2024-01-20", description="One-time repair")]
        recurring = detect_recurring(txns)
        assert len(recurring) == 0

    def test_same_description_same_month_twice_is_not_recurring(self):
        """Two transactions in the SAME month — only 1 distinct month → not recurring."""
        txns = [
            _expense("2000.00", "2024-01-05", description="Canteen"),
            _expense("2000.00", "2024-01-25", description="Canteen"),
        ]
        recurring = detect_recurring(txns)
        assert len(recurring) == 0

    def test_typical_day_clamped_to_28(self):
        """Salary paid on the 31st — typical day must be ≤ 28."""
        txns = [
            _income("50000.00", "2024-01-31", description="Monthly salary"),
            _income("50000.00", "2024-03-31", description="Monthly salary"),
        ]
        recurring = detect_recurring(txns)
        assert recurring[0].typical_day_of_month <= 28

    def test_typical_amount_is_median(self):
        """Three occurrences: 1000, 5000, 2000 → median = 2000."""
        txns = [
            _expense("1000.00", "2024-01-10", description="Water bill"),
            _expense("5000.00", "2024-02-10", description="Water bill"),
            _expense("2000.00", "2024-03-10", description="Water bill"),
        ]
        recurring = detect_recurring(txns)
        assert len(recurring) == 1
        # Sorted: 1000, 2000, 5000 → index 1 → 2000
        assert recurring[0].typical_amount == Decimal("2000.00")

    def test_recurring_projected_on_correct_day(self):
        """Salary detected as recurring on day 1; forecast starts March 1."""
        txns = [
            _income("50000.00", "2024-01-01", description="Salary"),
            _income("50000.00", "2024-02-01", description="Salary"),
        ]
        result = _forecast(txns, balance="0.00", start=date(2024, 3, 1))
        # March 1 → daily_forecasts[0]
        march_1 = result["daily_forecasts"][0]
        assert Decimal(march_1["projected_income"]) >= Decimal("50000.00")

    def test_one_time_purchase_not_projected_as_recurring(self):
        """A one-time purchase in Jan must NOT appear in the March forecast."""
        txns = [
            _expense("15000.00", "2024-01-20", description="Laptop purchase"),
        ]
        result = _forecast(txns, balance="100000.00", start=date(2024, 3, 1))
        # No day in March should show ₹15000 expense solely from this transaction
        # (it won't be detected as recurring)
        recurring = detect_recurring(txns)
        assert len(recurring) == 0

    def test_detected_recurring_in_response(self):
        txns = [
            _income("50000.00", "2024-01-01", description="Salary"),
            _income("50000.00", "2024-02-01", description="Salary"),
        ]
        result = _forecast(txns, balance="0.00")
        assert len(result["detected_recurring_transactions"]) == 1
        rec = result["detected_recurring_transactions"][0]
        assert rec["description"] == "salary"
        assert rec["months_observed"] == 2


# ---------------------------------------------------------------------------
# Deduplication with confirmed future transactions
# ---------------------------------------------------------------------------


class TestRecurringDeduplication:
    def test_confirmed_prevents_recurring_double_count(self):
        """
        Salary is detected as recurring on day 1.
        User also confirms salary on March 1.
        → Only the confirmed amount should appear, not recurring + confirmed.
        """
        txns = [
            _income("45000.00", "2024-01-01", description="Salary"),
            _income("45000.00", "2024-02-01", description="Salary"),
        ]
        confirmed = [_future("50000.00", "income", "2024-03-01", "Salary")]
        result = _forecast(txns, balance="0.00", confirmed=confirmed)
        march_1 = result["daily_forecasts"][0]
        # Confirmed ₹50,000 should appear but NOT also the recurring ₹45,000
        # (plus the daily non-recurring spread)
        # The confirmed amount is ₹50,000; recurring is skipped
        income_on_day_1 = Decimal(march_1["projected_income"])
        # Should NOT be 50000 + 45000 = 95000
        assert income_on_day_1 < Decimal("95000.00")
        assert income_on_day_1 >= Decimal("50000.00")

    def test_unrelated_confirmed_does_not_suppress_recurring(self):
        """
        A confirmed future transaction with a DIFFERENT description must not
        suppress the recurring salary projection.
        """
        txns = [
            _income("45000.00", "2024-01-01", description="Salary"),
            _income("45000.00", "2024-02-01", description="Salary"),
        ]
        confirmed = [_future("10000.00", "income", "2024-03-05", "Bonus")]
        result = _forecast(txns, balance="0.00", confirmed=confirmed)
        # Salary recurring should still appear on day 1
        march_1 = result["daily_forecasts"][0]
        assert Decimal(march_1["projected_income"]) >= Decimal("45000.00")


# ---------------------------------------------------------------------------
# Low-cash and negative-balance detection
# ---------------------------------------------------------------------------


class TestCashBalanceFlags:
    def test_negative_balance_flagged(self):
        """Start at ₹1,000, spend ₹5,000 as a confirmed expense on day 1."""
        confirmed = [_future("5000.00", "expense", "2024-03-01", "Emergency")]
        result = _forecast([], balance="1000.00", confirmed=confirmed)
        assert "2024-03-01" in result["negative_balance_dates"]
        assert result["daily_forecasts"][0]["is_negative_balance"] is True

    def test_low_cash_flagged_above_zero(self):
        """Balance stays at ₹5,000 (> 0) but below buffer ₹10,000 → low cash."""
        result = _forecast([], balance="5000.00", buffer="10000.00")
        # Every day has no income/expense → balance stays at 5,000 < buffer
        assert result["daily_forecasts"][0]["is_low_cash"] is True
        assert "2024-03-01" in result["low_cash_dates"]

    def test_negative_not_also_in_low_cash_dates(self):
        """Negative-balance days must NOT also appear in low_cash_dates."""
        confirmed = [_future("9000.00", "expense", "2024-03-01", "Big bill")]
        result = _forecast([], balance="5000.00", buffer="3000.00", confirmed=confirmed)
        assert "2024-03-01" in result["negative_balance_dates"]
        assert "2024-03-01" not in result["low_cash_dates"]

    def test_positive_balance_no_flags(self):
        result = _forecast([], balance="100000.00", buffer="10000.00")
        # No expenses, no income → balance steady at 100,000 >> buffer
        for day in result["daily_forecasts"]:
            assert day["is_negative_balance"] is False
            assert day["is_low_cash"] is False


# ---------------------------------------------------------------------------
# Observation window
# ---------------------------------------------------------------------------


class TestObservationWindow:
    def test_window_filters_old_history(self):
        """6 months of history, window=2 → only last 2 months used."""
        txns = [_income("10000.00", f"2024-{m:02d}-01") for m in range(1, 7)]
        result = _forecast(txns, balance="0.00", window=2)
        assert result["months_of_history_used"] == 2

    def test_one_month_history_produces_warning(self):
        txns = [_income("50000.00", "2024-01-01")]
        result = _forecast(txns, balance="0.00")
        assert any("1 month" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Net cash-flow totals
# ---------------------------------------------------------------------------


class TestNetCashFlow:
    def test_net_cash_flow_equals_income_minus_expenses(self):
        result = _forecast([], balance="10000.00")
        net = Decimal(result["net_projected_cash_flow"])
        income = Decimal(result["total_projected_income"])
        expenses = Decimal(result["total_projected_expenses"])
        assert net == income - expenses

    def test_projected_closing_balance_equals_opening_plus_net(self):
        result = _forecast([], balance="50000.00")
        expected = Decimal(result["opening_balance"]) + Decimal(result["net_projected_cash_flow"])
        assert Decimal(result["projected_closing_balance"]) == expected
