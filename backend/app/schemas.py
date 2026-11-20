"""
Pydantic schemas for the AI Financial Decision Support System.

Defines validated request and response models for the transactions API.
All monetary amounts are represented as strings in the JSON layer and
converted to Decimal internally to preserve precision.

Phase 2 additions
-----------------
- ``StoredTransaction`` — persisted record with ``id`` and ``source``.
- ``CreateTransactionRequest`` — request body for ``POST /transactions``.
- ``TransactionFilters`` — query-parameter filter bundle.
- ``DeleteResponse`` — success envelope for DELETE.
- ``CSVImportReport`` — detailed result of a CSV import operation.
- ``RowError`` — single-row error detail within an import report.
"""

# Import `date` under an alias to avoid the Pydantic v2 name-shadowing issue
# where a field named `date` would shadow the `datetime.date` type inside the
# class body, making the annotation unevaluable.
from datetime import date as ISODate
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Shared enumerations
# ---------------------------------------------------------------------------


class TransactionType(str, Enum):
    """Allowed transaction types."""

    income = "income"
    expense = "expense"


class TransactionSource(str, Enum):
    """Origin of a transaction record."""

    manual = "manual"
    csv_import = "csv_import"


# ---------------------------------------------------------------------------
# Phase 1 — core transaction schema (unchanged, kept for backward compat)
# ---------------------------------------------------------------------------


class Transaction(BaseModel):
    """A single financial transaction submitted by the client (Phase 1 shape)."""

    date: ISODate = Field(..., description="Transaction date in ISO 8601 format (YYYY-MM-DD).")
    description: str = Field(..., description="Non-empty human-readable description of the transaction.")
    amount: Decimal = Field(..., description="Positive monetary amount for this transaction.")
    transaction_type: TransactionType = Field(
        ..., description="Whether this is an 'income' or 'expense' transaction."
    )
    category: str = Field(
        default="uncategorized",
        description="Optional category label; defaults to 'uncategorized'.",
    )

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, value: str) -> str:
        """Reject blank or whitespace-only descriptions."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("description must not be empty or whitespace.")
        return stripped

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        """Reject zero and negative amounts."""
        if value <= Decimal("0"):
            raise ValueError("amount must be greater than zero.")
        return value

    @field_validator("category")
    @classmethod
    def category_defaults_to_uncategorized(cls, value: str) -> str:
        """Strip whitespace; keep the default if value is empty after stripping."""
        stripped = value.strip()
        return stripped if stripped else "uncategorized"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "date": "2024-01-15",
                    "description": "Monthly salary",
                    "amount": "5000.00",
                    "transaction_type": "income",
                    "category": "salary",
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# Phase 1 — summary request / response (unchanged)
# ---------------------------------------------------------------------------


class TransactionSummaryRequest(BaseModel):
    """Request body for the POST /transactions/summary endpoint."""

    transactions: List[Transaction] = Field(
        default_factory=list,
        description="List of transactions to summarise. An empty list returns zero totals.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "transactions": [
                        {
                            "date": "2024-01-15",
                            "description": "Monthly salary",
                            "amount": "5000.00",
                            "transaction_type": "income",
                            "category": "salary",
                        },
                        {
                            "date": "2024-01-20",
                            "description": "Rent payment",
                            "amount": "1200.00",
                            "transaction_type": "expense",
                            "category": "housing",
                        },
                    ]
                }
            ]
        }
    }


class FinancialSummaryResponse(BaseModel):
    """Financial summary returned by POST /transactions/summary."""

    total_income: str = Field(
        ..., description="Sum of all income transactions as a string (2 decimal places)."
    )
    total_expenses: str = Field(
        ..., description="Sum of all expense transactions as a string (2 decimal places)."
    )
    net_cash_flow: str = Field(
        ..., description="total_income − total_expenses as a string (2 decimal places)."
    )
    transaction_count: int = Field(
        ..., description="Total number of transactions processed.", ge=0
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_income": "5000.00",
                    "total_expenses": "1200.00",
                    "net_cash_flow": "3800.00",
                    "transaction_count": 2,
                }
            ]
        }
    }


class HealthResponse(BaseModel):
    """Response returned by GET /health."""

    status: str = Field("ok", description="Overall health state")
    project: str = Field("AI Financial Decision Support System")
    database: Optional[str] = Field("connected", description="Database connectivity state")
    ai_provider: Optional[str] = Field(None, description="Active AI provider")
    version: Optional[str] = Field("12.0.0", description="System version")


# ===========================================================================
# Phase 3 — Emergency Fund schemas
# ===========================================================================

#: Default essential expense categories used for emergency-fund analysis.
#: Defined here (not in emergency_fund.py) to avoid circular imports:
#: emergency_fund.py imports from schemas.py.
DEFAULT_ESSENTIAL_CATEGORIES: List[str] = [
    "rent",
    "groceries",
    "utilities",
    "healthcare",
    "transport",
]


class EmergencyFundConfig(BaseModel):
    """Request/response body for PUT /financial-profile/emergency-fund.

    The user supplies their explicitly known emergency fund balance.
    If the balance is unknown, omit the field rather than guessing.
    """

    emergency_fund_balance: Optional[Decimal] = Field(
        default=None,
        description=(
            "Emergency fund balance in INR explicitly known to the user. "
            "Omit or set to null if unknown — the system will not assume zero."
        ),
    )
    essential_categories: List[str] = Field(
        default_factory=lambda: list(DEFAULT_ESSENTIAL_CATEGORIES),
        description=(
            "Expense categories treated as essential for the analysis. "
            "Must match the category labels used in your transactions."
        ),
    )
    analysis_window_months: int = Field(
        default=12,
        ge=1,
        le=60,
        description="Number of most-recent calendar months to include in the average.",
    )

    @field_validator("emergency_fund_balance")
    @classmethod
    def balance_must_not_be_negative(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        """A negative emergency fund balance is not meaningful."""
        if v is not None and v < Decimal("0"):
            raise ValueError(
                "emergency_fund_balance cannot be negative. "
                "Provide your actual savings balance or omit the field."
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "emergency_fund_balance": "150000.00",
                    "essential_categories": [
                        "rent", "groceries", "utilities", "healthcare", "transport"
                    ],
                    "analysis_window_months": 12,
                }
            ]
        }
    }


class EmergencyFundAnalysisResponse(BaseModel):
    """Structured emergency fund analysis result."""

    currency: str = Field(..., description="Display currency (INR).")
    analysis_window_months_requested: int = Field(
        ..., description="Number of months requested for the analysis window."
    )
    complete_months_analyzed: int = Field(
        ..., description="Distinct calendar months actually found in the transaction history."
    )
    essential_categories_used: List[str] = Field(
        ..., description="Expense categories counted as essential."
    )
    essential_expense_transaction_count: int = Field(
        ..., description="Number of essential expense transactions in the analysis window."
    )
    average_monthly_essential_expenses: str = Field(
        ..., description="Average monthly essential expenses (INR, 2 d.p.)."
    )
    three_month_target: str = Field(
        ..., description="Recommended 3-month emergency fund target (INR, 2 d.p.)."
    )
    six_month_target: str = Field(
        ..., description="Recommended 6-month emergency fund target (INR, 2 d.p.)."
    )
    emergency_fund_balance: Optional[str] = Field(
        default=None,
        description="User-supplied emergency fund balance (INR, 2 d.p.), or null if unknown.",
    )
    balance_status: str = Field(
        ..., description="'known' when balance was supplied, 'unknown' otherwise."
    )
    shortfall_three_month: Optional[str] = Field(
        default=None,
        description="Amount still needed to reach the 3-month target, or null if balance unknown.",
    )
    shortfall_six_month: Optional[str] = Field(
        default=None,
        description="Amount still needed to reach the 6-month target, or null if balance unknown.",
    )
    months_of_coverage: Optional[str] = Field(
        default=None,
        description=(
            "How many months of essential expenses the current balance covers, "
            "or null if balance unknown or average expenses are zero."
        ),
    )
    warnings: List[str] = Field(default_factory=list, description="Data-quality warnings.")
    assumptions: List[str] = Field(default_factory=list, description="Documented calculation assumptions.")


# ===========================================================================
# Phase 3 — Cash-flow forecast schemas
# ===========================================================================


class FutureTransaction(BaseModel):
    """A single user-confirmed future income or expense transaction."""

    date: ISODate = Field(..., description="Date the transaction will occur (YYYY-MM-DD).")
    description: str = Field(..., description="Transaction description.")
    amount: Decimal = Field(..., description="Positive transaction amount in INR.")
    transaction_type: TransactionType = Field(..., description="'income' or 'expense'.")

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= Decimal("0"):
            raise ValueError("amount must be greater than zero.")
        return v

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("description must not be empty.")
        return v.strip()


class CashFlowForecastRequest(BaseModel):
    """Request body for POST /financial-analysis/cash-flow-forecast."""

    current_balance: Decimal = Field(
        ...,
        description=(
            "Your current cash balance in INR. Required. "
            "The system cannot infer this from transaction history."
        ),
    )
    forecast_start_date: Optional[ISODate] = Field(
        default=None,
        description="First day of the 30-day window. Defaults to today.",
    )
    min_cash_buffer: Optional[Decimal] = Field(
        default=None,
        description=(
            "Days where projected balance falls below this amount (but remains ≥ 0) "
            "are flagged as low-cash days. Defaults to 0."
        ),
    )
    confirmed_future_transactions: List[FutureTransaction] = Field(
        default_factory=list,
        description="Known future income or expenses to incorporate into the forecast.",
    )
    observation_window_months: int = Field(
        default=6,
        ge=1,
        le=60,
        description="Number of recent calendar months of history to use.",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "current_balance": "250000.00",
                    "forecast_start_date": "2026-11-01",
                    "min_cash_buffer": "50000.00",
                    "confirmed_future_transactions": [
                        {
                            "date": "2026-11-01",
                            "description": "Monthly salary",
                            "amount": "45000.00",
                            "transaction_type": "income",
                        }
                    ],
                    "observation_window_months": 6,
                }
            ]
        }
    }


class DailyForecast(BaseModel):
    """Projected cash-flow figures for a single day."""

    date: str = Field(..., description="ISO date string (YYYY-MM-DD).")
    projected_income: str = Field(..., description="Expected income on this day (INR, 2 d.p.).")
    projected_expenses: str = Field(..., description="Expected expenses on this day (INR, 2 d.p.).")
    net_daily_flow: str = Field(..., description="projected_income − projected_expenses.")
    closing_balance: str = Field(..., description="Projected end-of-day balance.")
    is_low_cash: bool = Field(..., description="True when balance < min_cash_buffer (and ≥ 0).")
    is_negative_balance: bool = Field(..., description="True when projected balance < 0.")


class DetectedRecurringInfo(BaseModel):
    """Summary of one detected recurring transaction pattern."""

    description: str
    transaction_type: str
    typical_day_of_month: int
    typical_amount: str
    months_observed: int


class CashFlowForecastResponse(BaseModel):
    """Full 30-day cash-flow forecast result."""

    forecast_start_date: str
    forecast_end_date: str
    opening_balance: str
    projected_closing_balance: str
    total_projected_income: str
    total_projected_expenses: str
    net_projected_cash_flow: str
    low_cash_dates: List[str]
    negative_balance_dates: List[str]
    daily_forecasts: List[DailyForecast]
    detected_recurring_transactions: List[DetectedRecurringInfo]
    months_of_history_used: int
    methodology: str
    assumptions: List[str]
    warnings: List[str]


# ---------------------------------------------------------------------------
# Phase 2 — stored transaction (has id + source)
# ---------------------------------------------------------------------------


class StoredTransaction(BaseModel):
    """A transaction record as persisted in the repository.

    Extends the base transaction with a server-assigned ``id`` and an
    optional ``source`` tag indicating how the record was created.
    """

    id: str = Field(..., description="Unique transaction identifier (UUID).")
    date: ISODate = Field(..., description="Transaction date in ISO 8601 format (YYYY-MM-DD).")
    description: str = Field(..., description="Non-empty human-readable description.")
    amount: Decimal = Field(..., description="Positive monetary amount.")
    transaction_type: TransactionType = Field(..., description="'income' or 'expense'.")
    category: str = Field(default="uncategorized", description="Category label.")
    source: TransactionSource = Field(
        default=TransactionSource.manual,
        description="Origin of the record: 'manual' or 'csv_import'.",
    )

    model_config = {}  # Decimal amounts are serialised to str by the repository layer.


# ---------------------------------------------------------------------------
# Phase 2 — create transaction request
# ---------------------------------------------------------------------------


class CreateTransactionRequest(BaseModel):
    """Request body for POST /transactions."""

    date: ISODate = Field(..., description="Transaction date (YYYY-MM-DD).")
    description: str = Field(..., description="Non-empty transaction description.")
    amount: Decimal = Field(..., description="Positive monetary amount.")
    transaction_type: TransactionType = Field(..., description="'income' or 'expense'.")
    category: Optional[str] = Field(
        default=None,
        description="Category. If omitted or 'uncategorized', auto-categorization is applied.",
    )
    source: TransactionSource = Field(
        default=TransactionSource.manual,
        description="Record origin.",
    )

    @field_validator("description")
    @classmethod
    def description_must_not_be_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("description must not be empty or whitespace.")
        return stripped

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, value: Decimal) -> Decimal:
        if value <= Decimal("0"):
            raise ValueError("amount must be greater than zero.")
        return value

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "date": "2026-10-20",
                    "description": "Monthly salary",
                    "amount": "45000.00",
                    "transaction_type": "income",
                    "category": "salary",
                    "source": "manual",
                }
            ]
        }
    }


# ---------------------------------------------------------------------------
# Phase 2 — delete response
# ---------------------------------------------------------------------------


class DeleteResponse(BaseModel):
    """Returned by DELETE /transactions/{id}."""

    message: str
    transaction_id: str


# ---------------------------------------------------------------------------
# Phase 2 — CSV import report
# ---------------------------------------------------------------------------


class RowError(BaseModel):
    """Details of a single rejected row during CSV import."""

    row: int = Field(..., description="1-based row number in the CSV (header = row 0).")
    reason: str = Field(..., description="Human-readable rejection reason.")
    raw_data: Optional[dict] = Field(default=None, description="The raw row data, if available.")


class CSVImportReport(BaseModel):
    """Full report returned after a CSV import attempt.

    Policy
    ------
    Valid rows are imported even when other rows are invalid ('partial
    import' policy).  The response always states clearly how many rows were
    imported, duplicated, and rejected.

    Duplicate-detection strategy
    ----------------------------
    A row is considered a duplicate if an existing stored transaction
    (or another row in the same batch) has the same combination of
    ``date``, ``description`` (case-insensitive, stripped), ``amount``
    (normalised to 2 d.p.), and ``transaction_type``.

    **Limitation**: two genuinely different transactions on the same day
    for the same amount and description cannot be distinguished by this
    strategy.  Duplicates are flagged as *suspected* duplicates, not
    confirmed ones.
    """

    filename: str = Field(..., description="Name of the uploaded file.")
    total_rows: int = Field(..., description="Total data rows in the file (excluding header).")
    imported: int = Field(..., description="Number of rows successfully imported.")
    duplicates_skipped: int = Field(..., description="Rows skipped as suspected duplicates.")
    rejected: int = Field(..., description="Rows rejected due to validation errors.")
    errors: List[RowError] = Field(default_factory=list, description="Per-row error details.")
    imported_ids: List[str] = Field(default_factory=list, description="IDs of newly created records.")
