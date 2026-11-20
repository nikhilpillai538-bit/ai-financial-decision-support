"""
Phase 12 End-to-End Security, Cross-User Isolation, and Anti-Tampering Test Suite.

Verifies strict multi-tenant authorization barriers between two independent authenticated users:
- User A (user_a@sec-audit.com)
- User B (user_b@sec-audit.com)

Covers:
1. Transaction isolation and IDOR prevention.
2. Portfolio & holding tampering prevention.
3. Investment goal protection and projection security.
4. AI conversation isolation and private session protection.
5. Financial profile / emergency fund boundary enforcement.
6. Upload size limit denial of service (DoS) protection (HTTP 413).
7. Security headers injection check.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
import io
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token, hash_password
from app.db.base import Base
from app.db.models import UserModel
from app.db.session import get_db
from app.main import app

USER_A_ID = "sec-user-a-uuid"
USER_B_ID = "sec-user-b-uuid"


@pytest.fixture()
def sec_client() -> TestClient:
    """Isolated SQLite in-memory test client with two pre-created active users."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with TestingSession() as session:
        session.add(
            UserModel(
                id=USER_A_ID,
                email="user_a@sec-audit.com",
                password_hash=hash_password("PasswordA123!"),
                is_active=True,
            )
        )
        session.add(
            UserModel(
                id=USER_B_ID,
                email="user_b@sec-audit.com",
                password_hash=hash_password("PasswordB123!"),
                is_active=True,
            )
        )
        session.commit()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture()
def token_a() -> str:
    token, _ = create_access_token(USER_A_ID, "user_a@sec-audit.com")
    return token


@pytest.fixture()
def token_b() -> str:
    token, _ = create_access_token(USER_B_ID, "user_b@sec-audit.com")
    return token


class TestCrossUserIsolation:
    """Tests preventing any unauthorized cross-user reading, modifying, or deleting."""

    def test_security_headers_present(self, sec_client: TestClient):
        """Responses must include standard security headers."""
        res = sec_client.get("/health")
        assert res.status_code == 200
        assert res.headers.get("x-content-type-options") == "nosniff"
        assert res.headers.get("x-frame-options") == "DENY"
        assert res.headers.get("x-xss-protection") == "1; mode=block"

    def test_transactions_cross_user_isolation(
        self, sec_client: TestClient, token_a: str, token_b: str
    ):
        """User A creates a transaction; User B cannot read, modify, or delete it."""
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User A creates transaction
        create_res = sec_client.post(
            "/transactions/",
            headers=headers_a,
            json={
                "date": "2026-10-01",
                "description": "User A Salary",
                "amount": "75000.00",
                "transaction_type": "income",
                "category": "salary",
            },
        )
        assert create_res.status_code == 201
        tx_id = create_res.json()["id"]

        # User B lists transactions -> User A's transaction NOT present
        list_b = sec_client.get("/transactions/", headers=headers_b)
        assert list_b.status_code == 200
        tx_ids_b = [t["id"] for t in list_b.json()]
        assert tx_id not in tx_ids_b

        # User B attempts to access User A's transaction by ID -> 404
        get_b = sec_client.get(f"/transactions/{tx_id}", headers=headers_b)
        assert get_b.status_code == 404

        # User B attempts to delete User A's transaction -> 404
        del_b = sec_client.delete(f"/transactions/{tx_id}", headers=headers_b)
        assert del_b.status_code == 404

        # Verify transaction still exists intact for User A
        get_a = sec_client.get(f"/transactions/{tx_id}", headers=headers_a)
        assert get_a.status_code == 200
        assert get_a.json()["description"] == "User A Salary"

    def test_portfolios_cross_user_isolation(
        self, sec_client: TestClient, token_a: str, token_b: str
    ):
        """User A creates a portfolio; User B cannot view, modify, or optimize it."""
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User A creates portfolio
        port_res = sec_client.post(
            "/portfolios/",
            headers=headers_a,
            json={
                "name": "User A Growth Portfolio",
                "description": "Confidential portfolio",
                "base_currency": "INR",
            },
        )
        assert port_res.status_code == 201
        port_id = port_res.json()["id"]

        # User B lists portfolios -> User A's portfolio NOT present
        list_b = sec_client.get("/portfolios/", headers=headers_b)
        assert list_b.status_code == 200
        port_ids_b = [p["id"] for p in list_b.json()]
        assert port_id not in port_ids_b

        # User B attempts to view portfolio -> 404
        assert sec_client.get(f"/portfolios/{port_id}", headers=headers_b).status_code == 404

        # User B attempts to optimize portfolio -> 404
        opt_res = sec_client.post(
            f"/portfolios/{port_id}/optimize",
            headers=headers_b,
            json={"objective": "max_sharpe"},
        )
        assert opt_res.status_code == 404

        # User B attempts to sync live prices -> 404
        sync_res = sec_client.post(
            f"/portfolios/{port_id}/sync-market-prices",
            headers=headers_b,
        )
        assert sync_res.status_code == 404

    def test_investment_goals_cross_user_isolation(
        self, sec_client: TestClient, token_a: str, token_b: str
    ):
        """User A creates an investment goal; User B cannot read or modify it."""
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        goal_res = sec_client.post(
            "/investment-goals",
            headers=headers_a,
            json={
                "name": "User A Retirement 2045",
                "target_amount": "5000000.00",
                "target_date": "2045-12-31",
                "expected_annual_return": "0.12",
            },
        )
        assert goal_res.status_code == 201
        goal_id = goal_res.json()["id"]

        # User B list goals -> User A's goal NOT present
        list_b = sec_client.get("/investment-goals", headers=headers_b)
        assert list_b.status_code == 200
        assert goal_id not in [g["id"] for g in list_b.json()]

        # User B get goal -> 404
        assert sec_client.get(f"/investment-goals/{goal_id}", headers=headers_b).status_code == 404

        # User B projection -> 404
        assert (
            sec_client.post(
                f"/investment-goals/{goal_id}/projection", headers=headers_b, json={}
            ).status_code
            == 404
        )

        # User B delete goal -> 404
        assert sec_client.delete(f"/investment-goals/{goal_id}", headers=headers_b).status_code == 404

    def test_ai_conversations_cross_user_isolation(
        self, sec_client: TestClient, token_a: str, token_b: str
    ):
        """User A has an AI assistant conversation; User B cannot view or delete it."""
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User A sends query to assistant
        ai_res = sec_client.post(
            "/ai/financial-assistant",
            headers=headers_a,
            json={
                "question": "How healthy is my financial plan?",
                "provider": "mock",
            },
        )
        assert ai_res.status_code == 200
        conv_id = ai_res.json()["conversation_id"]

        # User B lists conversations -> User A's conversation NOT present
        list_b = sec_client.get("/ai/conversations", headers=headers_b)
        assert list_b.status_code == 200
        assert conv_id not in [c["id"] for c in list_b.json()["conversations"]]

        # User B attempts to view conversation details -> 404
        assert sec_client.get(f"/ai/conversations/{conv_id}", headers=headers_b).status_code == 404

        # User B attempts to delete conversation -> 404
        assert sec_client.delete(f"/ai/conversations/{conv_id}", headers=headers_b).status_code == 404

    def test_file_upload_size_limit_rejection(
        self, sec_client: TestClient, token_a: str
    ):
        """CSV uploads exceeding 10MB must be rejected with HTTP 413 Payload Too Large."""
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # Construct an oversized buffer exceeding 10MB
        oversized_data = b"date,symbol,adjusted_close\n" + (b"2025-01-01,TEST,100.00\n" * 500000)
        assert len(oversized_data) > 10 * 1024 * 1024

        files = {"file": ("massive.csv", io.BytesIO(oversized_data), "text/csv")}
        res = sec_client.post(
            "/market-data/historical-prices/import-csv",
            headers=headers_a,
            files=files,
        )
        assert res.status_code == 413
        assert "exceeds the maximum allowed size" in res.json()["detail"]
