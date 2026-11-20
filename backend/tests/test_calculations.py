"""
Tests for app/calculations.py — the deterministic financial calculation module.

All monetary values in test cases use Python's ``Decimal`` type to ensure
precision is preserved throughout the assertion chain.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.calculations import calculate_financial_summary
from app.schemas import FinancialSummaryResponse, Transaction, TransactionType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_transaction(
    amount: str | Decimal,
    transaction_type: TransactionType,
    description: str = "Test transaction",
    category: str = "test",
    txn_date: str = "2024-01-01",
) -> Transaction:
    """Create a validated Transaction for use in tests."""
    return Transaction(
        date=txn_date,
        description=description,
        amount=Decimal(str(amount)),
        transaction_type=transaction_type,
        category=category,
    )


def _income(amount: str | Decimal, **kwargs) -> Transaction:
    return _make_transaction(amount, TransactionType.income, **kwargs)


def _expense(amount: str | Decimal, **kwargs) -> Transaction:
    return _make_transaction(amount, TransactionType.expense, **kwargs)


# ---------------------------------------------------------------------------
# Empty list
# ---------------------------------------------------------------------------


class TestEmptyTransactionList:
    def test_returns_financial_summary_response(self):
        result = calculate_financial_summary([])
        assert isinstance(result, FinancialSummaryResponse)

    def test_total_income_is_zero(self):
        result = calculate_financial_summary([])
        assert result.total_income == "0.00"

    def test_total_expenses_is_zero(self):
        result = calculate_financial_summary([])
        assert result.total_expenses == "0.00"

    def test_net_cash_flow_is_zero(self):
        result = calculate_financial_summary([])
        assert result.net_cash_flow == "0.00"

    def test_transaction_count_is_zero(self):
        result = calculate_financial_summary([])
        assert result.transaction_count == 0


# ---------------------------------------------------------------------------
# Income-only transactions
# ---------------------------------------------------------------------------


class TestIncomeOnly:
    def test_single_income_transaction(self):
        txns = [_income("1000.00")]
        result = calculate_financial_summary(txns)
        assert result.total_income == "1000.00"
        assert result.total_expenses == "0.00"
        assert result.net_cash_flow == "1000.00"
        assert result.transaction_count == 1

    def test_multiple_income_transactions_summed_correctly(self):
        txns = [_income("1500.00"), _income("2500.00"), _income("75.50")]
        result = calculate_financial_summary(txns)
        assert result.total_income == "4075.50"
        assert result.total_expenses == "0.00"
        assert result.net_cash_flow == "4075.50"
        assert result.transaction_count == 3

    def test_income_with_many_decimal_places_rounded(self):
        # Decimal("0.005") rounds up to 0.01 under ROUND_HALF_UP
        txns = [_income("0.005")]
        result = calculate_financial_summary(txns)
        assert result.total_income == "0.01"


# ---------------------------------------------------------------------------
# Expense-only transactions
# ---------------------------------------------------------------------------


class TestExpenseOnly:
    def test_single_expense_transaction(self):
        txns = [_expense("500.00")]
        result = calculate_financial_summary(txns)
        assert result.total_income == "0.00"
        assert result.total_expenses == "500.00"
        assert result.net_cash_flow == "-500.00"
        assert result.transaction_count == 1

    def test_multiple_expense_transactions_summed_correctly(self):
        txns = [_expense("200.00"), _expense("300.50"), _expense("49.50")]
        result = calculate_financial_summary(txns)
        assert result.total_expenses == "550.00"
        assert result.net_cash_flow == "-550.00"
        assert result.transaction_count == 3


# ---------------------------------------------------------------------------
# Mixed income and expense transactions
# ---------------------------------------------------------------------------


class TestMixedTransactions:
    def test_net_cash_flow_positive(self):
        txns = [_income("3000.00"), _expense("1200.00")]
        result = calculate_financial_summary(txns)
        assert result.total_income == "3000.00"
        assert result.total_expenses == "1200.00"
        assert result.net_cash_flow == "1800.00"
        assert result.transaction_count == 2

    def test_net_cash_flow_negative(self):
        txns = [_income("500.00"), _expense("900.00")]
        result = calculate_financial_summary(txns)
        assert result.net_cash_flow == "-400.00"

    def test_net_cash_flow_zero(self):
        txns = [_income("750.00"), _expense("750.00")]
        result = calculate_financial_summary(txns)
        assert result.net_cash_flow == "0.00"

    def test_multiple_mixed_with_decimals(self):
        txns = [
            _income("1000.75"),
            _income("234.50"),
            _expense("88.25"),
            _expense("346.00"),
        ]
        result = calculate_financial_summary(txns)
        assert result.total_income == "1235.25"
        assert result.total_expenses == "434.25"
        assert result.net_cash_flow == "801.00"
        assert result.transaction_count == 4

    def test_large_number_of_transactions(self):
        # 100 income of 1.11 → 111.00; 50 expenses of 2.22 → 111.00 → net 0.00
        txns = [_income("1.11")] * 100 + [_expense("2.22")] * 50
        result = calculate_financial_summary(txns)
        assert result.total_income == "111.00"
        assert result.total_expenses == "111.00"
        assert result.net_cash_flow == "0.00"
        assert result.transaction_count == 150


# ---------------------------------------------------------------------------
# Decimal precision
# ---------------------------------------------------------------------------


class TestDecimalPrecision:
    def test_sum_of_many_small_decimals(self):
        # 3 × 0.10 = 0.30  (floating-point 0.1 + 0.1 + 0.1 ≠ 0.3)
        txns = [_income("0.10"), _income("0.10"), _income("0.10")]
        result = calculate_financial_summary(txns)
        assert result.total_income == "0.30"

    def test_amounts_passed_as_decimal_objects(self):
        txns = [
            Transaction(
                date=date(2024, 3, 1),
                description="Direct Decimal",
                amount=Decimal("999.99"),
                transaction_type=TransactionType.income,
            )
        ]
        result = calculate_financial_summary(txns)
        assert result.total_income == "999.99"


# ---------------------------------------------------------------------------
# Schema validation (Pydantic-level — not API layer)
# ---------------------------------------------------------------------------


class TestSchemaValidation:
    def test_negative_amount_rejected(self):
        with pytest.raises(Exception):  # pydantic ValidationError
            Transaction(
                date="2024-01-01",
                description="Bad transaction",
                amount=Decimal("-100.00"),
                transaction_type=TransactionType.expense,
            )

    def test_zero_amount_rejected(self):
        with pytest.raises(Exception):
            Transaction(
                date="2024-01-01",
                description="Zero amount",
                amount=Decimal("0"),
                transaction_type=TransactionType.income,
            )

    def test_empty_description_rejected(self):
        with pytest.raises(Exception):
            Transaction(
                date="2024-01-01",
                description="   ",
                amount=Decimal("10.00"),
                transaction_type=TransactionType.income,
            )

    def test_invalid_transaction_type_rejected(self):
        with pytest.raises(Exception):
            Transaction(
                date="2024-01-01",
                description="Test",
                amount=Decimal("10.00"),
                transaction_type="refund",  # type: ignore[arg-type]
            )

    def test_invalid_date_format_rejected(self):
        with pytest.raises(Exception):
            Transaction(
                date="not-a-date",  # type: ignore[arg-type]
                description="Test",
                amount=Decimal("10.00"),
                transaction_type=TransactionType.income,
            )

    def test_category_defaults_to_uncategorized(self):
        txn = Transaction(
            date="2024-01-01",
            description="No category",
            amount=Decimal("10.00"),
            transaction_type=TransactionType.income,
        )
        assert txn.category == "uncategorized"
