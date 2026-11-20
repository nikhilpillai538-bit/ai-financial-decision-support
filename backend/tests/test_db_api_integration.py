"""
Integration tests for FastAPI endpoints backed by database repositories.

Verifies end-to-end functionality with the database session dependency:
- Storing and retrieving transactions through API endpoints.
- CSV import with duplicate detection against the database.
- Summaries calculated from database records.
- Emergency fund analysis reading profile and transactions from database.
- 30-day cash-flow forecast incorporating database transaction history.
"""

import io
from datetime import date as ISODate, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db.base import Base
from app.db.models import UserModel
from app.db.session import get_db
from app.main import app

TEST_DB_USER = UserModel(
    id="db-test-user-id",
    email="dbtest@example.com",
    password_hash="mockhash",
    is_active=True,
)


@pytest.fixture()
def db_client() -> TestClient:
    """FastAPI TestClient wired to an isolated in-memory database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        session: Session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: TEST_DB_USER

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)
    Base.metadata.drop_all(bind=engine)


class TestDatabaseAPIEndpoints:
    """Test full HTTP transactions and analysis lifecycle backed by database."""

    def test_create_and_get_transaction(self, db_client: TestClient):
        payload = {
            "date": "2026-10-10",
            "description": "Consulting Income",
            "amount": "60000.00",
            "transaction_type": "income",
            "category": "salary",
        }
        res = db_client.post("/transactions", json=payload)
        assert res.status_code == 201
        data = res.json()
        txn_id = data["id"]
        assert data["description"] == "Consulting Income"
        assert Decimal(data["amount"]) == Decimal("60000.00")

        # Retrieve by ID
        get_res = db_client.get(f"/transactions/{txn_id}")
        assert get_res.status_code == 200
        assert get_res.json()["id"] == txn_id

        # List transactions
        list_res = db_client.get("/transactions")
        assert list_res.status_code == 200
        assert len(list_res.json()) == 1

    def test_delete_transaction(self, db_client: TestClient):
        payload = {
            "date": "2026-10-12",
            "description": "Office Supplies",
            "amount": "2500.00",
            "transaction_type": "expense",
            "category": "utilities",
        }
        create_res = db_client.post("/transactions", json=payload)
        txn_id = create_res.json()["id"]

        del_res = db_client.delete(f"/transactions/{txn_id}")
        assert del_res.status_code == 200

        # Confirm not found
        get_res = db_client.get(f"/transactions/{txn_id}")
        assert get_res.status_code == 404

    def test_stored_summary_from_database(self, db_client: TestClient):
        db_client.post("/transactions", json={
            "date": "2026-10-01",
            "description": "Monthly Salary",
            "amount": "80000.00",
            "transaction_type": "income",
        })
        db_client.post("/transactions", json={
            "date": "2026-10-02",
            "description": "Apartment Rent",
            "amount": "25000.00",
            "transaction_type": "expense",
        })
        res = db_client.get("/transactions/stored-summary")
        assert res.status_code == 200
        data = res.json()
        assert data["total_income"] == "80000.00"
        assert data["total_expenses"] == "25000.00"
        assert data["net_cash_flow"] == "55000.00"
        assert data["transaction_count"] == 2

    def test_csv_import_into_database_with_duplicates(self, db_client: TestClient):
        # First add one manual transaction
        db_client.post("/transactions", json={
            "date": "2026-10-01",
            "description": "Internet Bill",
            "amount": "1200.00",
            "transaction_type": "expense",
            "category": "utilities",
        })

        # Upload CSV containing: 1 duplicate of existing, 1 valid new, 1 intra-batch duplicate
        csv_data = (
            "date,description,amount,transaction_type,category\n"
            "2026-10-01,Internet Bill,1200.00,expense,utilities\n"
            "2026-10-05,Groceries Supermarket,4500.00,expense,groceries\n"
            "2026-10-05,Groceries Supermarket,4500.00,expense,groceries\n"
        )
        res = db_client.post(
            "/transactions/import-csv",
            files={"file": ("transactions.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        )
        assert res.status_code == 200
        report = res.json()
        assert report["total_rows"] == 3
        assert report["imported"] == 1
        assert report["duplicates_skipped"] == 2

        # Verify DB now contains exactly 2 records
        list_res = db_client.get("/transactions")
        assert len(list_res.json()) == 2


class TestDatabaseFinancialAnalysisEndpoints:
    """Test emergency fund analysis and cash flow forecasting with database persistence."""

    def test_emergency_fund_profile_and_analysis(self, db_client: TestClient):
        # 1. Check default analysis when no profile saved
        res = db_client.get("/financial-analysis/emergency-fund")
        assert res.status_code == 200
        assert res.json()["balance_status"] == "unknown"

        # 2. Add some transactions in 3 different months
        for m in ("08", "09", "10"):
            db_client.post("/transactions", json={
                "date": f"2026-{m}-05",
                "description": "Rent Payment",
                "amount": "20000.00",
                "transaction_type": "expense",
                "category": "rent",
            })
            db_client.post("/transactions", json={
                "date": f"2026-{m}-10",
                "description": "Groceries",
                "amount": "10000.00",
                "transaction_type": "expense",
                "category": "groceries",
            })

        # 3. Configure emergency fund profile in DB
        prof_res = db_client.put("/financial-profile/emergency-fund", json={
            "emergency_fund_balance": "180000.00",
            "essential_categories": ["rent", "groceries"],
            "analysis_window_months": 12,
        })
        assert prof_res.status_code == 200

        # 4. Retrieve analysis
        analysis_res = db_client.get("/financial-analysis/emergency-fund")
        assert analysis_res.status_code == 200
        data = analysis_res.json()
        assert data["balance_status"] == "known"
        assert Decimal(data["average_monthly_essential_expenses"]) == Decimal("30000.00")
        assert Decimal(data["three_month_target"]) == Decimal("90000.00")
        assert Decimal(data["six_month_target"]) == Decimal("180000.00")
        assert data["shortfall_three_month"] == "0.00"
        assert data["shortfall_six_month"] == "0.00"
        assert Decimal(data["months_of_coverage"]) == Decimal("6.00")

    def test_cash_flow_forecast_from_db(self, db_client: TestClient):
        # Store recurring salary in DB
        for m in ("08", "09", "10"):
            db_client.post("/transactions", json={
                "date": f"2026-{m}-01",
                "description": "Monthly Salary",
                "amount": "70000.00",
                "transaction_type": "income",
                "category": "salary",
            })

        start = (ISODate.today() + timedelta(days=1)).isoformat()
        res = db_client.post("/financial-analysis/cash-flow-forecast", json={
            "current_balance": "50000.00",
            "forecast_start_date": start,
            "min_cash_buffer": "10000.00",
            "observation_window_months": 6,
        })
        assert res.status_code == 200
        data = res.json()
        assert len(data["daily_forecasts"]) == 30
        assert data["opening_balance"] == "50000.00"
        assert "methodology" in data
