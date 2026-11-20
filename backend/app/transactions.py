"""
Transactions router for the AI Financial Decision Support System.

Phase 1 endpoints (preserved, unchanged behaviour)
---------------------------------------------------
- POST /transactions/summary  — stateless summary from a submitted list

Phase 2 endpoints (new)
-----------------------
- POST   /transactions               — create & persist a transaction
- GET    /transactions               — list stored transactions (filterable)
- GET    /transactions/summary       — summarise stored transactions (filterable)
- GET    /transactions/{id}          — get one stored transaction
- DELETE /transactions/{id}          — delete one stored transaction
- POST   /transactions/import-csv    — import transactions from a CSV upload

All financial calculations are delegated to :mod:`app.calculations`.
Categorization is delegated to :mod:`app.categorization`.
Persistence is delegated to :mod:`app.repository`.
"""

import csv
import io
import uuid
from datetime import date as ISODate
from decimal import Decimal, InvalidOperation
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, get_optional_current_user
from app.calculations import calculate_financial_summary
from app.categorization import categorize
from app.db.models import UserModel
from app.db.repositories.transaction_repo import SQLTransactionRepository
from app.db.session import get_db
from app.repository import TransactionRepository, default_repository
from app.schemas import (
    CSVImportReport,
    CreateTransactionRequest,
    DeleteResponse,
    FinancialSummaryResponse,
    RowError,
    StoredTransaction,
    Transaction,
    TransactionSource,
    TransactionSummaryRequest,
    TransactionType,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CSV_MAX_ROWS = 5_000  # Reject files with more than this many data rows
CSV_REQUIRED_COLUMNS = {"date", "description", "amount", "transaction_type"}

# ---------------------------------------------------------------------------
# Dependency — repository injection
# Defaults to database-backed SQLTransactionRepository when a database session
# is available; falls back to file-based default_repository if invoked directly.
# Tests can override this dependency to inject isolated test repositories.
# ---------------------------------------------------------------------------


def get_repository(db: Any = Depends(get_db)) -> Any:
    """Return the active transaction repository (database-backed or fallback)."""
    if isinstance(db, Session):
        return SQLTransactionRepository(db)
    return default_repository


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _duplicate_key(txn: StoredTransaction) -> tuple:
    """Return the normalised tuple used for duplicate detection."""
    return (
        txn.date.isoformat(),
        txn.description.strip().lower(),
        str(Decimal(str(txn.amount)).quantize(Decimal("0.01"))),
        txn.transaction_type.value,
    )


def _stored_from_request(req: CreateTransactionRequest, txn_id: str) -> StoredTransaction:
    """Build a ``StoredTransaction`` from a validated create-request."""
    resolved_category = categorize(req.description, req.category)
    return StoredTransaction(
        id=txn_id,
        date=req.date,
        description=req.description,
        amount=req.amount,
        transaction_type=req.transaction_type,
        category=resolved_category,
        source=req.source,
    )


# ---------------------------------------------------------------------------
# Phase 1 endpoint (unchanged behaviour — stateless summary)
# ---------------------------------------------------------------------------


@router.post(
    "/summary",
    response_model=FinancialSummaryResponse,
    summary="[Phase 1] Summarise a submitted list of transactions",
    description=(
        "Stateless endpoint: accepts a JSON body with a list of transactions and "
        "returns a financial summary.  Does not read or write stored transactions."
    ),
)
def post_transaction_summary(
    request: TransactionSummaryRequest,
) -> FinancialSummaryResponse:
    """Return a deterministic financial summary for submitted transactions.

    Args:
        request: Validated request body containing a list of transactions.

    Returns:
        :class:`~app.schemas.FinancialSummaryResponse` with aggregate totals.
    """
    return calculate_financial_summary(request.transactions)


# ---------------------------------------------------------------------------
# Phase 2 endpoint A — create a transaction
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=StoredTransaction,
    status_code=status.HTTP_201_CREATED,
    summary="Create and persist a new transaction",
)
def create_transaction(
    request: CreateTransactionRequest,
    current_user: UserModel = Depends(get_current_user),
    repo: Any = Depends(get_repository),
) -> StoredTransaction:
    """Validate, categorize, and persist a single transaction scoped to the current user."""
    txn = _stored_from_request(request, txn_id=str(uuid.uuid4()))
    repo.save(txn, user_id=current_user.id)
    return txn


# ---------------------------------------------------------------------------
# Phase 2 endpoint B — list transactions (with optional filters)
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=List[StoredTransaction],
    summary="List stored transactions",
)
def list_transactions(
    start_date: Optional[ISODate] = Query(default=None, description="Filter: earliest transaction date (YYYY-MM-DD)."),
    end_date: Optional[ISODate] = Query(default=None, description="Filter: latest transaction date (YYYY-MM-DD)."),
    transaction_type: Optional[TransactionType] = Query(default=None, description="Filter: 'income' or 'expense'."),
    category: Optional[str] = Query(default=None, description="Filter: exact category match."),
    current_user: UserModel = Depends(get_current_user),
    repo: Any = Depends(get_repository),
) -> List[StoredTransaction]:
    """Return stored transactions for the authenticated user, optionally filtered."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must not be after end_date.",
        )

    results = repo.all(user_id=current_user.id)

    if start_date:
        results = [t for t in results if t.date >= start_date]
    if end_date:
        results = [t for t in results if t.date <= end_date]
    if transaction_type:
        results = [t for t in results if t.transaction_type == transaction_type]
    if category:
        results = [t for t in results if t.category.lower() == category.lower()]

    return results


# ---------------------------------------------------------------------------
# Phase 2 endpoint F — summary of stored transactions (filterable)
# NOTE: must be registered BEFORE /{transaction_id} to avoid route shadowing.
# ---------------------------------------------------------------------------


@router.get(
    "/stored-summary",
    response_model=FinancialSummaryResponse,
    summary="Summarise stored transactions",
)
@router.get(
    "/summary",
    response_model=FinancialSummaryResponse,
    include_in_schema=False,
)
def get_stored_summary(
    start_date: Optional[ISODate] = Query(default=None, description="Filter: earliest date."),
    end_date: Optional[ISODate] = Query(default=None, description="Filter: latest date."),
    transaction_type: Optional[TransactionType] = Query(default=None, description="Filter by type."),
    category: Optional[str] = Query(default=None, description="Filter by category."),
    current_user: UserModel = Depends(get_current_user),
    repo: Any = Depends(get_repository),
) -> FinancialSummaryResponse:
    """Return a financial summary of stored transactions for the authenticated user."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must not be after end_date.",
        )

    stored = repo.all(user_id=current_user.id)

    if start_date:
        stored = [t for t in stored if t.date >= start_date]
    if end_date:
        stored = [t for t in stored if t.date <= end_date]
    if transaction_type:
        stored = [t for t in stored if t.transaction_type == transaction_type]
    if category:
        stored = [t for t in stored if t.category.lower() == category.lower()]

    # Convert StoredTransaction -> Transaction for the Phase 1 calculator.
    phase1_txns: List[Transaction] = [
        Transaction(
            date=t.date,
            description=t.description,
            amount=t.amount,
            transaction_type=t.transaction_type,
            category=t.category,
        )
        for t in stored
    ]
    return calculate_financial_summary(phase1_txns)


# ---------------------------------------------------------------------------
# Phase 2 endpoint E — import from CSV
# NOTE: must be registered BEFORE /{transaction_id} to avoid route shadowing.
# ---------------------------------------------------------------------------


@router.post(
    "/import-csv",
    response_model=CSVImportReport,
    status_code=status.HTTP_200_OK,
    summary="Import transactions from a CSV file",
)
def import_csv(
    file: UploadFile = File(..., description="CSV file with columns: date, description, amount, transaction_type[, category]"),
    current_user: UserModel = Depends(get_current_user),
    repo: Any = Depends(get_repository),
) -> CSVImportReport:
    """Parse, validate, and import transactions from an uploaded CSV file scoped to current_user."""
    # -- Validate file type ------------------------------------------------
    filename = file.filename or "upload.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only .csv files are accepted.",
        )

    # -- Read raw bytes with size limit (never execute file content) -------
    MAX_CSV_BYTES = 10 * 1024 * 1024  # 10 MB
    raw_bytes = file.file.read(MAX_CSV_BYTES + 1)
    if len(raw_bytes) > MAX_CSV_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="The uploaded CSV exceeds the maximum allowed size of 10 MB.",
        )
    if not raw_bytes.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded.",
        )

    # -- Parse CSV ---------------------------------------------------------
    try:
        reader = csv.DictReader(io.StringIO(text))
        headers = set(reader.fieldnames or [])
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not parse CSV file.",
        )

    missing = CSV_REQUIRED_COLUMNS - {h.strip().lower() for h in headers}
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Missing required CSV columns: {', '.join(sorted(missing))}.",
        )

    # Normalise header names (strip whitespace, lowercase)
    rows = []
    for row in reader:
        rows.append({k.strip().lower(): v for k, v in row.items()})

    if len(rows) == 0:
        return CSVImportReport(
            filename=filename,
            total_rows=0,
            imported=0,
            duplicates_skipped=0,
            rejected=0,
        )

    if len(rows) > CSV_MAX_ROWS:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds the maximum of {CSV_MAX_ROWS} data rows.",
        )

    # -- Build duplicate fingerprint set from existing user records only ---
    existing_fingerprints = {_duplicate_key(t) for t in repo.all(user_id=current_user.id)}

    # -- Process rows -------------------------------------------------------
    errors: List[RowError] = []
    to_import: List[StoredTransaction] = []
    batch_fingerprints: set = set()
    duplicates_skipped = 0

    for row_idx, row in enumerate(rows, start=1):
        raw = dict(row)

        # Validate date
        date_str = row.get("date", "").strip()
        try:
            txn_date = ISODate.fromisoformat(date_str)
        except ValueError:
            errors.append(RowError(row=row_idx, reason=f"Invalid date {date_str!r}. Use YYYY-MM-DD.", raw_data=raw))
            continue

        # Validate description
        description = row.get("description", "").strip()
        if not description:
            errors.append(RowError(row=row_idx, reason="description is empty.", raw_data=raw))
            continue

        # Validate amount
        amount_str = row.get("amount", "").strip()
        try:
            amount = Decimal(amount_str)
        except InvalidOperation:
            errors.append(RowError(row=row_idx, reason=f"Invalid amount {amount_str!r}.", raw_data=raw))
            continue
        if amount <= Decimal("0"):
            errors.append(RowError(row=row_idx, reason=f"Amount must be > 0, got {amount_str!r}.", raw_data=raw))
            continue

        # Validate transaction_type
        type_str = row.get("transaction_type", "").strip().lower()
        try:
            txn_type = TransactionType(type_str)
        except ValueError:
            errors.append(RowError(row=row_idx, reason=f"Invalid transaction_type {type_str!r}. Use 'income' or 'expense'.", raw_data=raw))
            continue

        # Category (optional — auto-categorize if blank)
        supplied_cat = row.get("category", "").strip() or None

        # Build candidate stored transaction
        candidate = StoredTransaction(
            id=str(uuid.uuid4()),
            date=txn_date,
            description=description,
            amount=amount,
            transaction_type=txn_type,
            category=categorize(description, supplied_cat),
            source=TransactionSource.csv_import,
        )

        # Duplicate check
        fp = _duplicate_key(candidate)
        if fp in existing_fingerprints or fp in batch_fingerprints:
            duplicates_skipped += 1
            errors.append(RowError(
                row=row_idx,
                reason=(
                    "Suspected duplicate: a transaction with the same date, description, "
                    "amount, and type already exists. Skipped."
                ),
                raw_data=raw,
            ))
            continue

        batch_fingerprints.add(fp)
        to_import.append(candidate)

    # -- Persist valid rows scoped to user ---------------------------------
    if to_import:
        repo.save_many(to_import, user_id=current_user.id)

    return CSVImportReport(
        filename=filename,
        total_rows=len(rows),
        imported=len(to_import),
        duplicates_skipped=duplicates_skipped,
        rejected=len(errors) - duplicates_skipped,
        errors=errors,
        imported_ids=[t.id for t in to_import],
    )


# ---------------------------------------------------------------------------
# Phase 2 endpoint C — get one transaction
# ---------------------------------------------------------------------------


@router.get(
    "/{transaction_id}",
    response_model=StoredTransaction,
    summary="Get a single stored transaction",
)
def get_transaction(
    transaction_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: Any = Depends(get_repository),
) -> StoredTransaction:
    """Return the transaction with the given ID belonging to current user, or 404."""
    txn = repo.get(transaction_id, user_id=current_user.id)
    if txn is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id!r} not found.",
        )
    return txn


# ---------------------------------------------------------------------------
# Phase 2 endpoint D — delete a transaction
# ---------------------------------------------------------------------------


@router.delete(
    "/{transaction_id}",
    response_model=DeleteResponse,
    summary="Delete a stored transaction",
)
def delete_transaction(
    transaction_id: str,
    current_user: UserModel = Depends(get_current_user),
    repo: Any = Depends(get_repository),
) -> DeleteResponse:
    """Delete the transaction belonging to current user, or return 404."""
    deleted = repo.delete(transaction_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id!r} not found.",
        )
    return DeleteResponse(message="Transaction deleted successfully.", transaction_id=transaction_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id!r} not found.",
        )
    return DeleteResponse(message="Transaction deleted successfully.", transaction_id=transaction_id)
