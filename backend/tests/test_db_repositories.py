"""
Unit tests for SQLTransactionRepository and SQLProfileRepository.

Verifies:
- CRUD operations backed by database session.
- ACID transactions (atomic batch saves, rollback on duplicate IDs or integrity errors).
- Exact Decimal handling.
- Efficient SQL filtering.
"""

from datetime import date as ISODate
from decimal import Decimal
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.repositories.profile_repo import SQLProfileRepository
from app.db.repositories.transaction_repo import SQLTransactionRepository
from app.schemas import StoredTransaction, TransactionSource, TransactionType


@pytest.fixture()
def db_session() -> Session:
    """Isolated SQLite database session for repository tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionMaker = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionMaker()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def tx_repo(db_session: Session) -> SQLTransactionRepository:
    return SQLTransactionRepository(db_session)


@pytest.fixture()
def profile_repo(db_session: Session) -> SQLProfileRepository:
    return SQLProfileRepository(db_session)


def _make_txn(
    txn_id: str = None,
    txn_date: str = "2026-10-15",
    desc: str = "Test transaction",
    amount: str = "1000.00",
    txn_type: TransactionType = TransactionType.expense,
    category: str = "groceries",
    source: TransactionSource = TransactionSource.manual,
) -> StoredTransaction:
    return StoredTransaction(
        id=txn_id or str(uuid.uuid4()),
        date=ISODate.fromisoformat(txn_date),
        description=desc,
        amount=Decimal(amount),
        transaction_type=txn_type,
        category=category,
        source=source,
    )


class TestSQLTransactionRepositoryCRUD:
    """Test standard single-record and collection operations."""

    def test_save_and_get(self, tx_repo: SQLTransactionRepository):
        t = _make_txn(amount="45000.75", desc="Salary Credit", txn_type=TransactionType.income)
        saved = tx_repo.save(t)
        assert saved.id == t.id
        assert saved.amount == Decimal("45000.75")

        fetched = tx_repo.get(t.id)
        assert fetched is not None
        assert fetched.id == t.id
        assert fetched.description == "Salary Credit"
        assert fetched.amount == Decimal("45000.75")
        assert fetched.transaction_type == TransactionType.income

    def test_get_nonexistent_returns_none(self, tx_repo: SQLTransactionRepository):
        assert tx_repo.get("does-not-exist") is None

    def test_save_duplicate_id_raises_value_error(self, tx_repo: SQLTransactionRepository):
        t = _make_txn(txn_id="fixed-id-123")
        tx_repo.save(t)

        t_dup = _make_txn(txn_id="fixed-id-123", desc="Another attempt")
        with pytest.raises(ValueError, match="already exists"):
            tx_repo.save(t_dup)

    def test_all_returns_newest_first(self, tx_repo: SQLTransactionRepository):
        t1 = _make_txn(txn_date="2026-10-01", desc="Day 1")
        t2 = _make_txn(txn_date="2026-10-15", desc="Day 15")
        t3 = _make_txn(txn_date="2026-10-10", desc="Day 10")

        tx_repo.save(t1)
        tx_repo.save(t2)
        tx_repo.save(t3)

        results = tx_repo.all()
        assert len(results) == 3
        dates = [r.date.isoformat() for r in results]
        assert dates == ["2026-10-15", "2026-10-10", "2026-10-01"]

    def test_delete_existing_returns_true(self, tx_repo: SQLTransactionRepository):
        t = _make_txn()
        tx_repo.save(t)
        assert tx_repo.delete(t.id) is True
        assert tx_repo.get(t.id) is None

    def test_delete_nonexistent_returns_false(self, tx_repo: SQLTransactionRepository):
        assert tx_repo.delete("unknown-id") is False

    def test_clear_removes_all(self, tx_repo: SQLTransactionRepository):
        tx_repo.save(_make_txn())
        tx_repo.save(_make_txn())
        assert len(tx_repo.all()) == 2
        tx_repo.clear()
        assert len(tx_repo.all()) == 0


class TestSQLTransactionRepositoryFiltering:
    """Test SQL query filtering capabilities."""

    def test_filter_by_date_range(self, tx_repo: SQLTransactionRepository):
        tx_repo.save(_make_txn(txn_date="2026-09-01"))
        tx_repo.save(_make_txn(txn_date="2026-09-15"))
        tx_repo.save(_make_txn(txn_date="2026-09-30"))

        filtered = tx_repo.filter(
            start_date=ISODate(2026, 9, 10),
            end_date=ISODate(2026, 9, 20),
        )
        assert len(filtered) == 1
        assert filtered[0].date == ISODate(2026, 9, 15)

    def test_filter_by_transaction_type(self, tx_repo: SQLTransactionRepository):
        tx_repo.save(_make_txn(txn_type=TransactionType.income))
        tx_repo.save(_make_txn(txn_type=TransactionType.expense))
        tx_repo.save(_make_txn(txn_type=TransactionType.expense))

        incomes = tx_repo.filter(transaction_type=TransactionType.income)
        expenses = tx_repo.filter(transaction_type=TransactionType.expense)
        assert len(incomes) == 1
        assert len(expenses) == 2

    def test_filter_by_category_case_insensitive(self, tx_repo: SQLTransactionRepository):
        tx_repo.save(_make_txn(category="Groceries"))
        tx_repo.save(_make_txn(category="Utilities"))

        results = tx_repo.filter(category="groceries")
        assert len(results) == 1
        assert results[0].category.lower() == "groceries"


class TestSQLTransactionRepositoryBatchOperations:
    """Test save_many atomicity and integrity guarantees."""

    def test_save_many_success(self, tx_repo: SQLTransactionRepository):
        items = [_make_txn(desc=f"Item {i}") for i in range(5)]
        tx_repo.save_many(items)
        assert len(tx_repo.all()) == 5

    def test_save_many_empty_list(self, tx_repo: SQLTransactionRepository):
        tx_repo.save_many([])
        assert len(tx_repo.all()) == 0

    def test_save_many_duplicate_within_batch_rolls_back(self, tx_repo: SQLTransactionRepository):
        dup_id = "duplicate-batch-id"
        t1 = _make_txn(txn_id=dup_id, desc="First")
        t2 = _make_txn(txn_id="unique-id-1", desc="Second")
        t3 = _make_txn(txn_id=dup_id, desc="Third duplicate")

        with pytest.raises(ValueError, match="Duplicate transaction ID"):
            tx_repo.save_many([t1, t2, t3])

        # Atomicity check: none of the records should have been saved
        assert len(tx_repo.all()) == 0

    def test_save_many_duplicate_against_db_rolls_back(self, tx_repo: SQLTransactionRepository):
        existing_id = "already-in-db"
        tx_repo.save(_make_txn(txn_id=existing_id, desc="Pre-existing"))
        assert len(tx_repo.all()) == 1

        t1 = _make_txn(txn_id="new-item-1", desc="New item")
        t2 = _make_txn(txn_id=existing_id, desc="Clashing item")

        with pytest.raises(ValueError, match="Duplicate transaction ID"):
            tx_repo.save_many([t1, t2])

        # Atomicity check: new-item-1 must not have been persisted
        assert len(tx_repo.all()) == 1
        assert tx_repo.get("new-item-1") is None


class TestSQLProfileRepository:
    """Test SQLProfileRepository configuration storage and updates."""

    def test_get_nonexistent_profile_returns_none(self, profile_repo: SQLProfileRepository):
        assert profile_repo.get_emergency_fund_config("nonexistent") is None

    def test_save_and_get_emergency_fund_config(self, profile_repo: SQLProfileRepository):
        config = {
            "emergency_fund_balance": "150000.00",
            "essential_categories": ["rent", "groceries", "utilities"],
            "analysis_window_months": 12,
            "min_cash_buffer": "30000.00",
        }
        profile_repo.save_emergency_fund_config(config)

        saved = profile_repo.get_emergency_fund_config("default")
        assert saved is not None
        assert saved["emergency_fund_balance"] == "150000.00"
        assert saved["essential_categories"] == ["rent", "groceries", "utilities"]
        assert saved["analysis_window_months"] == 12
        assert saved["min_cash_buffer"] == "30000.00"
        assert saved["currency"] == "INR"

    def test_update_existing_profile(self, profile_repo: SQLProfileRepository):
        initial = {
            "emergency_fund_balance": "100000.00",
            "essential_categories": ["rent"],
            "analysis_window_months": 6,
        }
        profile_repo.save_emergency_fund_config(initial)

        updated = {
            "emergency_fund_balance": "200000.00",
            "essential_categories": ["rent", "healthcare"],
            "analysis_window_months": 12,
        }
        profile_repo.save_emergency_fund_config(updated)

        fetched = profile_repo.get_emergency_fund_config("default")
        assert fetched["emergency_fund_balance"] == "200000.00"
        assert fetched["essential_categories"] == ["rent", "healthcare"]
        assert fetched["analysis_window_months"] == 12

    def test_save_with_null_balance_preserves_unknown(self, profile_repo: SQLProfileRepository):
        config = {
            "emergency_fund_balance": None,
            "essential_categories": ["rent", "groceries"],
            "analysis_window_months": 12,
        }
        profile_repo.save_emergency_fund_config(config)

        fetched = profile_repo.get_emergency_fund_config("default")
        assert fetched["emergency_fund_balance"] is None
