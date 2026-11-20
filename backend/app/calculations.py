"""
Deterministic financial calculation module.

All monetary arithmetic uses Python's ``Decimal`` type to avoid
floating-point rounding errors.  This module is intentionally
independent of FastAPI so it can be tested and reused in isolation.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import List

from app.schemas import FinancialSummaryResponse, Transaction, TransactionType

# Canonical two-decimal-place quantiser used throughout the module.
_TWO_PLACES = Decimal("0.01")


def _format_decimal(value: Decimal) -> str:
    """Return a Decimal formatted to exactly two decimal places as a string.

    Args:
        value: The Decimal value to format.

    Returns:
        A string like ``"1234.56"`` or ``"-500.00"``.
    """
    return str(value.quantize(_TWO_PLACES, rounding=ROUND_HALF_UP))


def calculate_financial_summary(
    transactions: List[Transaction],
) -> FinancialSummaryResponse:
    """Calculate an aggregate financial summary from a list of transactions.

    Computes:
    - **total_income**: sum of all ``income`` transaction amounts.
    - **total_expenses**: sum of all ``expense`` transaction amounts.
    - **net_cash_flow**: ``total_income − total_expenses``.
    - **transaction_count**: total number of transactions (any type).

    Handles an empty list by returning zero totals and a count of zero.

    Uses ``Decimal`` arithmetic throughout so that monetary values are
    accumulated without floating-point rounding errors.

    Args:
        transactions: A list of validated :class:`~app.schemas.Transaction`
            objects.  May be empty.

    Returns:
        A :class:`~app.schemas.FinancialSummaryResponse` instance with
        string-formatted monetary fields and an integer transaction count.

    Example::

        from decimal import Decimal
        from app.schemas import Transaction, TransactionType
        from app.calculations import calculate_financial_summary

        txns = [
            Transaction(
                date="2024-01-01",
                description="Salary",
                amount=Decimal("3000.00"),
                transaction_type=TransactionType.income,
            ),
            Transaction(
                date="2024-01-05",
                description="Groceries",
                amount=Decimal("150.75"),
                transaction_type=TransactionType.expense,
            ),
        ]
        summary = calculate_financial_summary(txns)
        # summary.total_income   -> "3000.00"
        # summary.total_expenses -> "150.75"
        # summary.net_cash_flow  -> "2849.25"
        # summary.transaction_count -> 2
    """
    total_income: Decimal = Decimal("0")
    total_expenses: Decimal = Decimal("0")

    for txn in transactions:
        # Ensure we operate on a Decimal even if Pydantic already coerced it.
        amount = Decimal(str(txn.amount))
        if txn.transaction_type == TransactionType.income:
            total_income += amount
        else:
            total_expenses += amount

    net_cash_flow: Decimal = total_income - total_expenses

    return FinancialSummaryResponse(
        total_income=_format_decimal(total_income),
        total_expenses=_format_decimal(total_expenses),
        net_cash_flow=_format_decimal(net_cash_flow),
        transaction_count=len(transactions),
    )
