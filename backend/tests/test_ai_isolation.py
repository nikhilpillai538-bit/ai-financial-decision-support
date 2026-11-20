"""
Security and Multi-User Data Isolation tests for Phase 9 AI Assistant Endpoints.
"""

from datetime import date
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db.base import Base
from app.db.models import UserModel
from app.db.repositories.ai_repo import SQLAIRepository
from app.db.repositories.profile_repo import SQLProfileRepository
from app.db.repositories.transaction_repo import SQLTransactionRepository
from app.db.session import get_db
from app.main import app
from app.schemas import StoredTransaction, TransactionSource, TransactionType

USER_ALICE = UserModel(
    id="user-alice-uuid",
    email="alice@example.com",
    password_hash="mockhash",
    is_active=True,
)

USER_BOB = UserModel(
    id="user-bob-uuid",
    email="bob@example.com",
    password_hash="mockhash",
    is_active=True,
)


@pytest.fixture()
def shared_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with TestingSession() as session:
        session.add_all([
            UserModel(id=USER_ALICE.id, email=USER_ALICE.email, password_hash="mock", is_active=True),
            UserModel(id=USER_BOB.id, email=USER_BOB.email, password_hash="mock", is_active=True),
        ])
        session.commit()

    return TestingSession


class TestUnauthenticatedAccess:
    def test_unauthenticated_requests_fail(self):
        # Using raw client without get_current_user override
        with TestClient(app) as client:
            endpoints = [
                ("POST", "/ai/financial-assistant", {"question": "Hello"}),
                ("GET", "/ai/conversations", None),
                ("GET", "/ai/conversations/random-id", None),
                ("DELETE", "/ai/conversations/random-id", None),
                ("GET", "/ai/insights", None),
                ("POST", "/ai/scenario-analysis", {"scenario_type": "sip_increase"}),
            ]
            for method, url, json_body in endpoints:
                if method == "POST":
                    res = client.post(url, json=json_body)
                elif method == "GET":
                    res = client.get(url)
                elif method == "DELETE":
                    res = client.delete(url)
                assert res.status_code == 401, f"{method} {url} returned {res.status_code} instead of 401"


class TestMultiUserIsolation:
    def test_cross_user_conversation_isolation(self, shared_db):
        def override_db():
            s = shared_db()
            try:
                yield s
            finally:
                s.close()

        app.dependency_overrides[get_db] = override_db

        # 1. Alice creates a conversation
        app.dependency_overrides[get_current_user] = lambda: USER_ALICE
        with TestClient(app) as client_alice:
            r_alice = client_alice.post(
                "/ai/financial-assistant",
                json={"question": "Alice's secret financial question", "provider": "mock"},
            )
            assert r_alice.status_code == 200
            alice_conv_id = r_alice.json()["conversation_id"]

        # 2. Bob tries to access Alice's conversation
        app.dependency_overrides[get_current_user] = lambda: USER_BOB
        with TestClient(app) as client_bob:
            # Bob cannot view Alice's conversation
            get_res = client_bob.get(f"/ai/conversations/{alice_conv_id}")
            assert get_res.status_code == 404

            # Bob cannot delete Alice's conversation
            del_res = client_bob.delete(f"/ai/conversations/{alice_conv_id}")
            assert del_res.status_code == 404

            # Bob's conversation list is empty
            list_res = client_bob.get("/ai/conversations")
            assert list_res.status_code == 200
            assert list_res.json()["total_count"] == 0

        # Clean up
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)

    def test_financial_data_isolation_in_assistant(self, shared_db):
        def override_db():
            s = shared_db()
            try:
                yield s
            finally:
                s.close()

        app.dependency_overrides[get_db] = override_db

        # Seed data for Alice: Salary 500,000
        with shared_db() as s:
            tx_repo = SQLTransactionRepository(s)
            tx_repo.save(
                StoredTransaction(
                    id=str(uuid.uuid4()),
                    date=date(2026, 10, 1),
                    description="Alice Executive Salary",
                    amount=Decimal("500000.00"),
                    transaction_type=TransactionType.income,
                    category="salary",
                    source=TransactionSource.manual,
                ),
                user_id=USER_ALICE.id,
            )

        # Bob asks about his income
        app.dependency_overrides[get_current_user] = lambda: USER_BOB
        with TestClient(app) as client_bob:
            res_bob = client_bob.post(
                "/ai/financial-assistant",
                json={"question": "What is my income?", "provider": "mock"},
            )
            assert res_bob.status_code == 200
            data = res_bob.json()
            # Bob should NOT see Alice's 500,000 salary
            assert "500000" not in data["answer"]
            assert any("No transactions recorded yet" in w for w in data["limitations_or_missing_data"])

        # Clean up
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
