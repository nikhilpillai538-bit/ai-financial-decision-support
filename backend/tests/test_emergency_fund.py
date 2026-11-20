"""
Unit tests for app/emergency_fund.py — emergency fund calculation module.

All tests use pure Python inputs (no HTTP, no repository) so they exercise
the calculation logic in complete isolation.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.emergency_fund import (
    DEFAULT_ESSENTIAL_CATEGORIES,
    _MIN_RELIABLE_MONTHS,
    calculate_emergency_fund_analysis,
)
from app.schemas import StoredTransaction, TransactionSource, TransactionType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _txn(
    amount: str,
    txn_type: TransactionType,
    category: str,
    txn_date: str,
    description: str = "Test transaction",
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


def _expense(amount: str, category: str, txn_date: str) -> StoredTransaction:
    return _txn(amount, TransactionType.expense, category, txn_date)


def _income(amount: str, txn_date: str) -> StoredTransaction:
    return _txn(amount, TransactionType.income, "salary", txn_date)


# ---------------------------------------------------------------------------
# Empty / no-transaction cases
# ---------------------------------------------------------------------------


class TestNoTransactions:
    def test_no_transactions_returns_zero_averages(self):
        result = calculate_emergency_fund_analysis([], None, DEFAULT_ESSENTIAL_CATEGORIES)
        assert result["average_monthly_essential_expenses"] == "0.00"
        assert result["three_month_target"] == "0.00"
        assert result["six_month_target"] == "0.00"

    def test_no_transactions_produces_warning(self):
        result = calculate_emergency_fund_analysis([], None, DEFAULT_ESSENTIAL_CATEGORIES)
        assert any("No transaction history" in w for w in result["warnings"])

    def test_no_transactions_zero_months_analyzed(self):
        result = calculate_emergency_fund_analysis([], None, DEFAULT_ESSENTIAL_CATEGORIES)
        assert result["complete_months_analyzed"] == 0

    def test_no_transactions_balance_status_unknown(self):
        result = calculate_emergency_fund_analysis([], None, DEFAULT_ESSENTIAL_CATEGORIES)
        assert result["balance_status"] == "unknown"


# ---------------------------------------------------------------------------
# Three-month and six-month targets
# ---------------------------------------------------------------------------


class TestTargetCalculations:
    def _make_transactions(self):
        """Three months of data: Jan, Feb, Mar 2024 — ₹20,000 each month."""
        return [
            _expense("20000.00", "rent", "2024-01-15"),
            _expense("20000.00", "rent", "2024-02-15"),
            _expense("20000.00", "rent", "2024-03-15"),
        ]

    def test_three_month_target_correct(self):
        txns = self._make_transactions()
        result = calculate_emergency_fund_analysis(txns, None, ["rent"])
        assert result["average_monthly_essential_expenses"] == "20000.00"
        assert result["three_month_target"] == "60000.00"

    def test_six_month_target_correct(self):
        txns = self._make_transactions()
        result = calculate_emergency_fund_analysis(txns, None, ["rent"])
        assert result["six_month_target"] == "120000.00"

    def test_mixed_months_averaged_correctly(self):
        """Jan: ₹15,000  |  Feb: ₹25,000  → avg = ₹20,000."""
        txns = [
            _expense("15000.00", "rent", "2024-01-10"),
            _expense("25000.00", "rent", "2024-02-10"),
        ]
        result = calculate_emergency_fund_analysis(txns, None, ["rent"])
        assert result["average_monthly_essential_expenses"] == "20000.00"

    def test_decimal_arithmetic_is_precise(self):
        """Three months of ₹333.33 each — Decimal sum should be exactly ₹333.33."""
        txns = [
            _expense("333.33", "groceries", "2024-01-05"),
            _expense("333.33", "groceries", "2024-02-05"),
            _expense("333.33", "groceries", "2024-03-05"),
        ]
        result = calculate_emergency_fund_analysis(txns, None, ["groceries"])
        assert result["average_monthly_essential_expenses"] == "333.33"
        # Three-month target: 333.33 * 3 = 999.99
        assert result["three_month_target"] == "999.99"


# ---------------------------------------------------------------------------
# Essential vs non-essential distinction
# ---------------------------------------------------------------------------


class TestEssentialVsNonEssential:
    def test_non_essential_expenses_excluded_from_average(self):
        txns = [
            _expense("20000.00", "rent", "2024-01-15"),        # essential
            _expense("5000.00", "entertainment", "2024-01-20"),  # NOT essential
        ]
        result = calculate_emergency_fund_analysis(txns, None, ["rent"])
        assert result["average_monthly_essential_expenses"] == "20000.00"

    def test_income_transactions_excluded(self):
        txns = [
            _income("50000.00", "2024-01-01"),
            _expense("20000.00", "rent", "2024-01-15"),
        ]
        result = calculate_emergency_fund_analysis(txns, None, ["rent"])
        assert result["average_monthly_essential_expenses"] == "20000.00"

    def test_custom_essential_categories(self):
        txns = [
            _expense("3000.00", "education", "2024-01-10"),
            _expense("5000.00", "shopping", "2024-01-20"),
        ]
        # education is custom-essential; shopping is not
        result = calculate_emergency_fund_analysis(
            txns, None, ["rent", "education"]
        )
        assert result["average_monthly_essential_expenses"] == "3000.00"

    def test_category_matching_is_case_insensitive(self):
        txns = [_expense("8000.00", "Utilities", "2024-01-05")]
        result = calculate_emergency_fund_analysis(txns, None, ["utilities"])
        assert result["average_monthly_essential_expenses"] == "8000.00"


# ---------------------------------------------------------------------------
# Missing balance handling
# ---------------------------------------------------------------------------


class TestMissingBalance:
    def _base_txns(self):
        return [
            _expense("20000.00", "rent", "2024-01-15"),
            _expense("20000.00", "rent", "2024-02-15"),
            _expense("20000.00", "rent", "2024-03-15"),
        ]

    def test_balance_status_unknown_when_not_supplied(self):
        result = calculate_emergency_fund_analysis(
            self._base_txns(), None, ["rent"]
        )
        assert result["balance_status"] == "unknown"

    def test_shortfall_none_when_balance_not_supplied(self):
        result = calculate_emergency_fund_analysis(
            self._base_txns(), None, ["rent"]
        )
        assert result["shortfall_three_month"] is None
        assert result["shortfall_six_month"] is None

    def test_months_coverage_none_when_balance_not_supplied(self):
        result = calculate_emergency_fund_analysis(
            self._base_txns(), None, ["rent"]
        )
        assert result["months_of_coverage"] is None

    def test_warning_emitted_when_balance_not_supplied(self):
        result = calculate_emergency_fund_analysis(
            self._base_txns(), None, ["rent"]
        )
        assert any("not been provided" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Known balance — shortfall and coverage
# ---------------------------------------------------------------------------


class TestKnownBalance:
    def _base_txns(self):
        return [
            _expense("20000.00", "rent", "2024-01-15"),
            _expense("20000.00", "rent", "2024-02-15"),
            _expense("20000.00", "rent", "2024-03-15"),
        ]

    def test_balance_status_known(self):
        result = calculate_emergency_fund_analysis(
            self._base_txns(), Decimal("50000.00"), ["rent"]
        )
        assert result["balance_status"] == "known"

    def test_shortfall_three_month_correct(self):
        # avg = 20000, 3-month target = 60000, balance = 50000 → shortfall = 10000
        result = calculate_emergency_fund_analysis(
            self._base_txns(), Decimal("50000.00"), ["rent"]
        )
        assert result["shortfall_three_month"] == "10000.00"

    def test_shortfall_six_month_correct(self):
        # 6-month target = 120000, balance = 50000 → shortfall = 70000
        result = calculate_emergency_fund_analysis(
            self._base_txns(), Decimal("50000.00"), ["rent"]
        )
        assert result["shortfall_six_month"] == "70000.00"

    def test_shortfall_zero_when_balance_exceeds_target(self):
        result = calculate_emergency_fund_analysis(
            self._base_txns(), Decimal("200000.00"), ["rent"]
        )
        assert result["shortfall_three_month"] == "0.00"
        assert result["shortfall_six_month"] == "0.00"

    def test_months_of_coverage_correct(self):
        # balance = 40000, avg monthly = 20000 → coverage = 2.00 months
        result = calculate_emergency_fund_analysis(
            self._base_txns(), Decimal("40000.00"), ["rent"]
        )
        assert result["months_of_coverage"] == "2.00"

    def test_balance_displayed_in_response(self):
        result = calculate_emergency_fund_analysis(
            self._base_txns(), Decimal("75000.00"), ["rent"]
        )
        assert result["emergency_fund_balance"] == "75000.00"


# ---------------------------------------------------------------------------
# Insufficient history
# ---------------------------------------------------------------------------


class TestInsufficientHistory:
    def test_one_month_produces_warning(self):
        txns = [_expense("20000.00", "rent", "2024-01-15")]
        result = calculate_emergency_fund_analysis(txns, None, ["rent"])
        assert any("1 calendar month" in w for w in result["warnings"])

    def test_two_months_produces_warning(self):
        txns = [
            _expense("20000.00", "rent", "2024-01-15"),
            _expense("20000.00", "rent", "2024-02-15"),
        ]
        result = calculate_emergency_fund_analysis(txns, None, ["rent"])
        assert any("2 calendar month" in w for w in result["warnings"])

    def test_three_months_no_reliability_warning(self):
        txns = [
            _expense("20000.00", "rent", "2024-01-15"),
            _expense("20000.00", "rent", "2024-02-15"),
            _expense("20000.00", "rent", "2024-03-15"),
        ]
        result = calculate_emergency_fund_analysis(txns, None, ["rent"])
        # No "insufficient history" warning should appear for ≥ MIN_RELIABLE_MONTHS
        assert not any("calendar month" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# No essential expenses — no division-by-zero
# ---------------------------------------------------------------------------


class TestNoEssentialExpenses:
    def test_no_essential_expenses_returns_zero_average(self):
        txns = [
            _expense("5000.00", "entertainment", "2024-01-10"),
            _expense("2000.00", "dining", "2024-02-15"),
        ]
        result = calculate_emergency_fund_analysis(
            txns, Decimal("30000.00"), ["rent"]
        )
        assert result["average_monthly_essential_expenses"] == "0.00"
        assert result["three_month_target"] == "0.00"
        assert result["six_month_target"] == "0.00"

    def test_no_essential_expenses_months_coverage_none(self):
        txns = [_expense("5000.00", "entertainment", "2024-01-10")]
        result = calculate_emergency_fund_analysis(
            txns, Decimal("30000.00"), ["rent"]
        )
        assert result["months_of_coverage"] is None

    def test_no_essential_expenses_produces_warning(self):
        txns = [_expense("5000.00", "entertainment", "2024-01-10")]
        result = calculate_emergency_fund_analysis(
            txns, None, ["rent"]
        )
        assert any("essential categories" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Analysis window
# ---------------------------------------------------------------------------


class TestAnalysisWindow:
    def test_window_limits_months_analyzed(self):
        """12 months of history but window=3 → only 3 months in denominator."""
        txns = [
            _expense("10000.00", "rent", f"2024-{m:02d}-15")
            for m in range(1, 13)
        ]
        result = calculate_emergency_fund_analysis(txns, None, ["rent"], analysis_window_months=3)
        assert result["complete_months_analyzed"] == 3
        # Only Oct, Nov, Dec (last 3 of 2024-01..12) are used
        assert result["average_monthly_essential_expenses"] == "10000.00"

    def test_window_larger_than_history_uses_all(self):
        txns = [_expense("15000.00", "rent", "2024-01-10")]
        result = calculate_emergency_fund_analysis(txns, None, ["rent"], analysis_window_months=24)
        assert result["complete_months_analyzed"] == 1

    def test_currency_is_inr(self):
        result = calculate_emergency_fund_analysis([], None, DEFAULT_ESSENTIAL_CATEGORIES)
        assert result["currency"] == "INR"

    def test_assumptions_list_is_non_empty(self):
        result = calculate_emergency_fund_analysis([], None, DEFAULT_ESSENTIAL_CATEGORIES)
        assert len(result["assumptions"]) > 0
