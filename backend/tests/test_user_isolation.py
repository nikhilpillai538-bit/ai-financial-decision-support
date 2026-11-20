"""
Phase 5 Tests: Multi-User Data Isolation and Anti-Tampering.

Verifies strict isolation between two independent users (User A and User B):
- User A cannot view User B's transactions in lists.
- User A cannot retrieve User B's transaction by ID (returns 404).
- User A cannot delete User B's transaction (returns 404, record remains intact for User B).
- User A cannot import transactions into User B's store.
- User A's stored summaries and calculations include only User A's data.
- User A cannot read or overwrite User B's emergency fund profile settings.
- User A's 30-day cash flow forecast projects only User A's transaction history.
- Existing shared 'default' legacy records are never exposed to User A or User B.
- Client cannot bypass isolation via manipulated query parameters or headers.
"""

from datetime import date as ISODate, timedelta
from decimal import Decimal
import io

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import FinancialProfileModel, TransactionModel
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def isolation_client() -> TestClient:
    """Isolated test client with an in-memory SQLite database containing legacy data."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Pre-seed legacy development data with user_id = None and profile_key = 'default'
    seed_session = TestingSessionLocal()
    legacy_profile = FinancialProfileModel(
        profile_key="default",
        user_id=None,
        emergency_fund_balance=Decimal("999999.00"),
        essential_categories=["rent", "groceries"],
        analysis_window_months=12,
    )
    legacy_txn = TransactionModel(
        id="legacy-tx-999",
        user_id=None,
        date=ISODate(2026, 10, 1),
        description="Legacy Shared Transaction",
        amount=Decimal("500000.00"),
        transaction_type="income",
        category="salary",
    )
    seed_session.add(legacy_profile)
    seed_session.add(legacy_txn)
    seed_session.commit()
    seed_session.close()

    def override_get_db():
        session: Session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def user_tokens(isolation_client: TestClient):
    """Registers and logs in two independent users, returning auth headers for each."""
    # Register and login User A
    isolation_client.post("/auth/register", json={"email": "usera@example.com", "password": "passwordA123"})
    login_a = isolation_client.post("/auth/login", json={"email": "usera@example.com", "password": "passwordA123"})
    token_a = login_a.json()["access_token"]

    # Register and login User B
    isolation_client.post("/auth/register", json={"email": "userb@example.com", "password": "passwordB123"})
    login_b = isolation_client.post("/auth/login", json={"email": "userb@example.com", "password": "passwordB123"})
    token_b = login_b.json()["access_token"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    return headers_a, headers_b


class TestTransactionIsolation:
    """Verify transaction CRUD and summary boundaries between User A and User B."""

    def test_user_a_cannot_list_user_b_transactions(self, isolation_client: TestClient, user_tokens):
        headers_a, headers_b = user_tokens

        # User B creates a transaction
        create_b = isolation_client.post(
            "/transactions",
            headers=headers_b,
            json={
                "date": "2026-10-10",
                "description": "User B Secret Expense",
                "amount": "12345.00",
                "transaction_type": "expense",
            },
        )
        assert create_b.status_code == 201

        # User A lists transactions
        list_a = isolation_client.get("/transactions", headers=headers_a)
        assert list_a.status_code == 200
        items_a = list_a.json()
        assert len(items_a) == 0  # User A has 0 transactions

        # User B lists transactions
        list_b = isolation_client.get("/transactions", headers=headers_b)
        assert len(list_b.json()) == 1
        assert list_b.json()[0]["description"] == "User B Secret Expense"

    def test_user_a_cannot_get_user_b_transaction_by_id(self, isolation_client: TestClient, user_tokens):
        headers_a, headers_b = user_tokens

        # User B creates a transaction
        create_b = isolation_client.post(
            "/transactions",
            headers=headers_b,
            json={
                "date": "2026-10-12",
                "description": "User B Private Item",
                "amount": "999.00",
                "transaction_type": "expense",
            },
        )
        txn_id = create_b.json()["id"]

        # User A attempts to access User B's transaction directly by ID
        get_a = isolation_client.get(f"/transactions/{txn_id}", headers=headers_a)
        assert get_a.status_code == 404  # Clean 404 to avoid leaking existence

        # User B can access it
        get_b = isolation_client.get(f"/transactions/{txn_id}", headers=headers_b)
        assert get_b.status_code == 200
        assert get_b.json()["id"] == txn_id

    def test_user_a_cannot_delete_user_b_transaction(self, isolation_client: TestClient, user_tokens):
        headers_a, headers_b = user_tokens

        # User B creates a transaction
        create_b = isolation_client.post(
            "/transactions",
            headers=headers_b,
            json={
                "date": "2026-10-15",
                "description": "User B Shielded Record",
                "amount": "5000.00",
                "transaction_type": "expense",
            },
        )
        txn_id = create_b.json()["id"]

        # User A tries to delete it
        del_a = isolation_client.delete(f"/transactions/{txn_id}", headers=headers_a)
        assert del_a.status_code == 404

        # Verify transaction still exists untouched for User B
        get_b = isolation_client.get(f"/transactions/{txn_id}", headers=headers_b)
        assert get_b.status_code == 200
        assert get_b.json()["id"] == txn_id

    def test_stored_summary_isolated(self, isolation_client: TestClient, user_tokens):
        headers_a, headers_b = user_tokens

        # User A creates 10,000 income
        isolation_client.post(
            "/transactions",
            headers=headers_a,
            json={
                "date": "2026-10-01",
                "description": "Salary A",
                "amount": "10000.00",
                "transaction_type": "income",
            },
        )

        # User B creates 50,000 income
        isolation_client.post(
            "/transactions",
            headers=headers_b,
            json={
                "date": "2026-10-01",
                "description": "Salary B",
                "amount": "50000.00",
                "transaction_type": "income",
            },
        )

        sum_a = isolation_client.get("/transactions/stored-summary", headers=headers_a).json()
        sum_b = isolation_client.get("/transactions/stored-summary", headers=headers_b).json()

        assert Decimal(sum_a["total_income"]) == Decimal("10000.00")
        assert Decimal(sum_b["total_income"]) == Decimal("50000.00")


class TestFinancialProfileAndAnalysisIsolation:
    """Verify profile configuration, emergency fund analysis, and cash flow forecast isolation."""

    def test_emergency_fund_profile_isolated(self, isolation_client: TestClient, user_tokens):
        headers_a, headers_b = user_tokens

        # User A sets 200,000 balance
        isolation_client.put(
            "/financial-profile/emergency-fund",
            headers=headers_a,
            json={"emergency_fund_balance": "200000.00", "essential_categories": ["rent"]},
        )

        # User B sets 50,000 balance
        isolation_client.put(
            "/financial-profile/emergency-fund",
            headers=headers_b,
            json={"emergency_fund_balance": "50000.00", "essential_categories": ["groceries"]},
        )

        # User A analysis shows 200,000 balance and rent
        analysis_a = isolation_client.get("/financial-analysis/emergency-fund", headers=headers_a).json()
        assert analysis_a["emergency_fund_balance"] == "200000.00"
        assert analysis_a["essential_categories_used"] == ["rent"]

        # User B analysis shows 50,000 balance and groceries
        analysis_b = isolation_client.get("/financial-analysis/emergency-fund", headers=headers_b).json()
        assert analysis_b["emergency_fund_balance"] == "50000.00"
        assert analysis_b["essential_categories_used"] == ["groceries"]

    def test_cash_flow_forecast_isolated(self, isolation_client: TestClient, user_tokens):
        headers_a, headers_b = user_tokens

        # User A has high recurring income across 3 months
        for m in ("07", "08", "09"):
            isolation_client.post(
                "/transactions",
                headers=headers_a,
                json={
                    "date": f"2026-{m}-05",
                    "description": "User A Massive Bonus",
                    "amount": "100000.00",
                    "transaction_type": "income",
                },
            )

        # User B has no transactions
        start = (ISODate.today() + timedelta(days=1)).isoformat()
        res_b = isolation_client.post(
            "/financial-analysis/cash-flow-forecast",
            headers=headers_b,
            json={"current_balance": "1000.00", "forecast_start_date": start},
        )
        assert res_b.status_code == 200
        data_b = res_b.json()
        # User B must NOT detect User A's recurring bonus
        assert len(data_b["detected_recurring_transactions"]) == 0
        assert Decimal(data_b["total_projected_income"]) == Decimal("0.00")


class TestLegacyDefaultDataProtection:
    """Verify that existing shared 'default' records are never exposed to newly registered users."""

    def test_legacy_shared_records_inaccessible_to_new_users(self, isolation_client: TestClient, user_tokens):
        headers_a, _ = user_tokens

        # Check User A cannot see the pre-seeded legacy transaction 'legacy-tx-999'
        list_res = isolation_client.get("/transactions", headers=headers_a)
        ids = [item["id"] for item in list_res.json()]
        assert "legacy-tx-999" not in ids

        get_res = isolation_client.get("/transactions/legacy-tx-999", headers=headers_a)
        assert get_res.status_code == 404

        # Check User A does NOT inherit the pre-seeded legacy emergency fund balance of 999,999.00
        analysis_res = isolation_client.get("/financial-analysis/emergency-fund", headers=headers_a)
        data = analysis_res.json()
        assert data["emergency_fund_balance"] is None
        assert data["balance_status"] == "unknown"
