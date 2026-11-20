"""
Unit tests for SQLAlchemy models, constraints, and database connection lifecycle.

Verifies:
- TransactionModel and FinancialProfileModel schema mappings.
- CHECK constraints (positive amounts, valid transaction types, non-empty description).
- Profile constraints (non-negative emergency fund balance, window 1-60).
- Safe URL masking (credentials not exposed).
- Connection health check diagnostics.
"""

from datetime import date as ISODate
from decimal import Decimal
import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import FinancialProfileModel, TransactionModel
from app.db.session import check_db_connection, mask_database_url


@pytest.fixture()
def db_session() -> Session:
    """Provide an isolated in-memory SQLite database session for unit tests."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    SessionMaker = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionMaker()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


class TestDatabaseConnectionLifecycle:
    """Test connection handling, diagnostics, and credential protection."""

    def test_mask_database_url_with_password(self):
        url = "postgresql+psycopg://myuser:supersecretpass@localhost:5432/myfinancialdb"
        masked = mask_database_url(url)
        assert "supersecretpass" not in masked
        assert "***" in masked
        assert "myuser" in masked
        assert "localhost:5432/myfinancialdb" in masked

    def test_mask_database_url_without_password(self):
        url = "sqlite:///./data/test.db"
        assert mask_database_url(url) == url

    def test_check_db_connection_success(self):
        test_engine = create_engine("sqlite:///:memory:")
        ok, msg = check_db_connection(test_engine)
        assert ok is True
        assert "Successfully connected" in msg

    def test_check_db_connection_failure(self):
        # Invalid host/port should report failure safely without crashing or leaking password
        bad_engine = create_engine(
            "postgresql+psycopg://user:pass@127.0.0.1:54329/nonexistent",
            connect_args={"connect_timeout": 1},
        )
        ok, msg = check_db_connection(bad_engine)
        assert ok is False
        assert "Failed to connect" in msg
        assert "pass" not in msg  # Ensure password is NOT leaked in message


class TestTransactionModelConstraints:
    """Test database column types, precision, and CHECK constraints for transactions."""

    def test_create_valid_transaction(self, db_session: Session):
        txn = TransactionModel(
            id=str(uuid.uuid4()),
            date=ISODate(2026, 10, 1),
            description="October Salary",
            amount=Decimal("75000.50"),
            transaction_type="income",
            category="salary",
            source="manual",
        )
        db_session.add(txn)
        db_session.commit()

        retrieved = db_session.get(TransactionModel, txn.id)
        assert retrieved is not None
        assert retrieved.description == "October Salary"
        assert Decimal(str(retrieved.amount)) == Decimal("75000.50")
        assert retrieved.transaction_type == "income"

    def test_negative_amount_violates_constraint(self, db_session: Session):
        txn = TransactionModel(
            id=str(uuid.uuid4()),
            date=ISODate(2026, 10, 1),
            description="Invalid negative amount",
            amount=Decimal("-100.00"),
            transaction_type="expense",
        )
        db_session.add(txn)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_zero_amount_violates_constraint(self, db_session: Session):
        txn = TransactionModel(
            id=str(uuid.uuid4()),
            date=ISODate(2026, 10, 1),
            description="Zero amount",
            amount=Decimal("0.00"),
            transaction_type="expense",
        )
        db_session.add(txn)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_invalid_transaction_type_violates_constraint(self, db_session: Session):
        txn = TransactionModel(
            id=str(uuid.uuid4()),
            date=ISODate(2026, 10, 1),
            description="Investment",
            amount=Decimal("500.00"),
            transaction_type="investment",  # invalid: only 'income' or 'expense' allowed
        )
        db_session.add(txn)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_empty_description_violates_constraint(self, db_session: Session):
        txn = TransactionModel(
            id=str(uuid.uuid4()),
            date=ISODate(2026, 10, 1),
            description="   ",  # whitespace only
            amount=Decimal("150.00"),
            transaction_type="expense",
        )
        db_session.add(txn)
        with pytest.raises(IntegrityError):
            db_session.commit()


class TestFinancialProfileModelConstraints:
    """Test financial_profiles table behavior and constraints."""

    def test_create_valid_profile_with_known_balance(self, db_session: Session):
        prof = FinancialProfileModel(
            profile_key="default",
            emergency_fund_balance=Decimal("180000.00"),
            essential_categories=["rent", "groceries", "utilities"],
            analysis_window_months=12,
            min_cash_buffer=Decimal("25000.00"),
            currency="INR",
        )
        db_session.add(prof)
        db_session.commit()

        retrieved = db_session.get(FinancialProfileModel, prof.id)
        assert retrieved is not None
        assert retrieved.profile_key == "default"
        assert Decimal(str(retrieved.emergency_fund_balance)) == Decimal("180000.00")
        assert retrieved.essential_categories == ["rent", "groceries", "utilities"]

    def test_profile_with_unknown_balance_is_null(self, db_session: Session):
        prof = FinancialProfileModel(
            profile_key="user_2",
            emergency_fund_balance=None,  # unknown balance
            essential_categories=["rent", "healthcare"],
            analysis_window_months=6,
        )
        db_session.add(prof)
        db_session.commit()

        retrieved = db_session.get(FinancialProfileModel, prof.id)
        assert retrieved.emergency_fund_balance is None

    def test_negative_emergency_fund_balance_violates_constraint(self, db_session: Session):
        prof = FinancialProfileModel(
            profile_key="neg_user",
            emergency_fund_balance=Decimal("-5000.00"),
            essential_categories=["rent"],
            analysis_window_months=12,
        )
        db_session.add(prof)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_analysis_window_below_1_violates_constraint(self, db_session: Session):
        prof = FinancialProfileModel(
            profile_key="zero_window",
            emergency_fund_balance=Decimal("1000.00"),
            essential_categories=["rent"],
            analysis_window_months=0,
        )
        db_session.add(prof)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_analysis_window_above_60_violates_constraint(self, db_session: Session):
        prof = FinancialProfileModel(
            profile_key="high_window",
            emergency_fund_balance=Decimal("1000.00"),
            essential_categories=["rent"],
            analysis_window_months=61,
        )
        db_session.add(prof)
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_duplicate_profile_key_violates_unique(self, db_session: Session):
        prof1 = FinancialProfileModel(profile_key="key_1", essential_categories=["rent"])
        prof2 = FinancialProfileModel(profile_key="key_1", essential_categories=["groceries"])
        db_session.add(prof1)
        db_session.commit()

        db_session.add(prof2)
        with pytest.raises(IntegrityError):
            db_session.commit()
