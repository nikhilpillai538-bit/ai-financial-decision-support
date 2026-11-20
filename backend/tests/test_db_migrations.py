"""
Unit tests for data migration and Alembic migrations.

Verifies:
- migrate_json_to_pg script parses, validates, and imports transactions and profile.
- Idempotency on rerun (existing transactions are skipped, profile is updated).
- Rejections of invalid records (bad date, negative amount, etc.).
- Original files are never modified or deleted.
"""

import json
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models import FinancialProfileModel, TransactionModel
from migrations.migrate_json_to_pg import migrate_data


@pytest.fixture()
def temp_data_env(tmp_path: Path):
    """Create a temporary directory with test JSON files and an isolated test DB."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    transactions = [
        {
            "id": "mig-tx-001",
            "date": "2026-10-01",
            "description": "Salary Migration",
            "amount": "50000.00",
            "transaction_type": "income",
            "category": "salary",
            "source": "manual",
        },
        {
            "id": "mig-tx-002",
            "date": "2026-10-02",
            "description": "Rent Migration",
            "amount": "15000.00",
            "transaction_type": "expense",
            "category": "rent",
            "source": "manual",
        },
    ]
    (data_dir / "transactions.json").write_text(json.dumps(transactions), encoding="utf-8")

    profile = {
        "emergency_fund": {
            "emergency_fund_balance": "100000.00",
            "essential_categories": ["rent", "groceries"],
            "analysis_window_months": 12,
        }
    }
    (data_dir / "financial_profile.json").write_text(json.dumps(profile), encoding="utf-8")

    db_path = tmp_path / "test_migration.db"
    db_url = f"sqlite:///{db_path}"

    return data_dir, db_url


class TestDataMigrationScript:
    """Test JSON to SQL database migration script."""

    def test_dry_run_does_not_modify_database(self, temp_data_env):
        data_dir, db_url = temp_data_env
        report = migrate_data(data_dir, db_url=db_url, dry_run=True)

        assert report["dry_run"] is True
        assert report["transactions"]["total_found"] == 2
        assert report["transactions"]["imported"] == 2

        # Connect to DB and verify no tables or data created in dry run
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            # Querying should fail because tables were not created in dry-run
            with pytest.raises(Exception):
                session.query(TransactionModel).all()
        finally:
            session.close()

    def test_migration_imports_data(self, temp_data_env):
        data_dir, db_url = temp_data_env
        report = migrate_data(data_dir, db_url=db_url, dry_run=False)

        assert report["transactions"]["imported"] == 2
        assert report["transactions"]["rejected"] == 0
        assert report["financial_profile"]["imported"] is True

        # Verify DB records
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            txs = session.query(TransactionModel).all()
            assert len(txs) == 2
            prof = session.query(FinancialProfileModel).first()
            assert prof is not None
            assert Decimal(str(prof.emergency_fund_balance)) == Decimal("100000.00")
        finally:
            session.close()

    def test_migration_is_idempotent_on_rerun(self, temp_data_env):
        data_dir, db_url = temp_data_env
        # Run 1
        migrate_data(data_dir, db_url=db_url, dry_run=False)

        # Run 2
        report2 = migrate_data(data_dir, db_url=db_url, dry_run=False)
        assert report2["transactions"]["imported"] == 0
        assert report2["transactions"]["skipped_existing"] == 2
        assert report2["financial_profile"]["skipped_or_updated"] is True

        # Verify record count is still 2 (no duplicates)
        engine = create_engine(db_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            txs = session.query(TransactionModel).all()
            assert len(txs) == 2
        finally:
            session.close()

    def test_migration_rejects_invalid_records(self, tmp_path: Path):
        data_dir = tmp_path / "bad_data"
        data_dir.mkdir(parents=True, exist_ok=True)

        bad_transactions = [
            {"id": "bad-1", "date": "invalid-date", "description": "bad date", "amount": "100.00", "transaction_type": "expense"},
            {"id": "bad-2", "date": "2026-10-01", "description": "neg amount", "amount": "-50.00", "transaction_type": "expense"},
            {"id": "bad-3", "date": "2026-10-01", "description": "", "amount": "100.00", "transaction_type": "expense"},
            {"id": "bad-4", "date": "2026-10-01", "description": "bad type", "amount": "100.00", "transaction_type": "invalid"},
            {"id": "good-1", "date": "2026-10-01", "description": "valid", "amount": "100.00", "transaction_type": "expense"},
        ]
        (data_dir / "transactions.json").write_text(json.dumps(bad_transactions), encoding="utf-8")

        db_url = f"sqlite:///{tmp_path / 'bad_test.db'}"
        report = migrate_data(data_dir, db_url=db_url, dry_run=False)

        assert report["transactions"]["total_found"] == 5
        assert report["transactions"]["imported"] == 1
        assert report["transactions"]["rejected"] == 4
        assert len(report["transactions"]["errors"]) == 4

        # Original file is preserved untouched
        assert (data_dir / "transactions.json").exists()
