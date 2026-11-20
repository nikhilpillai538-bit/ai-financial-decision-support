"""
Multi-user data isolation tests for Phase 8 Goal Planning, Calculators, and Portfolio Drift.

Verifies strict cross-user security and isolation between User A and User B using real Bearer tokens:
- Goals and portfolios belonging to User A cannot be accessed, projected, or rebalanced by User B.
- Any attempt by User B to access User A's goals or portfolios returns 404 without leaking existence.
- Unauthenticated requests to any Phase 8 endpoint return 401 Unauthorized.
"""

from datetime import date, timedelta
from decimal import Decimal
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

USER_A_ID = "goal-user-a-uuid"
USER_A_EMAIL = "goal_user_a@example.com"

USER_B_ID = "goal-user-b-uuid"
USER_B_EMAIL = "goal_user_b@example.com"


@pytest.fixture()
def db_session_maker():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with TestingSessionLocal() as session:
        session.add_all([
            UserModel(
                id=USER_A_ID,
                email=USER_A_EMAIL,
                password_hash=hash_password("PasswordA123!"),
                is_active=True,
            ),
            UserModel(
                id=USER_B_ID,
                email=USER_B_EMAIL,
                password_hash=hash_password("PasswordB456!"),
                is_active=True,
            ),
        ])
        session.commit()

    return TestingSessionLocal


@pytest.fixture()
def test_client(db_session_maker) -> TestClient:
    def override_get_db():
        session: Session = db_session_maker()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture()
def headers_a() -> dict:
    token_a, _ = create_access_token(user_id=USER_A_ID, email=USER_A_EMAIL)
    return {"Authorization": f"Bearer {token_a}"}


@pytest.fixture()
def headers_b() -> dict:
    token_b, _ = create_access_token(user_id=USER_B_ID, email=USER_B_EMAIL)
    return {"Authorization": f"Bearer {token_b}"}


class TestCrossUserGoalAndDriftIsolation:
    """Tests ensuring User B cannot project or analyze User A's resources."""

    def test_user_b_cannot_project_user_a_goal(self, test_client: TestClient, headers_a: dict, headers_b: dict):
        future_date = (date.today() + timedelta(days=730)).isoformat()
        # User A creates a goal
        goal_a = test_client.post(
            "/investment-goals",
            headers=headers_a,
            json={"name": "User A Goal", "target_amount": "500000.00", "target_date": future_date},
        ).json()

        # User B attempts to run projection on User A's goal
        res = test_client.post(
            f"/investment-goals/{goal_a['id']}/projection",
            headers=headers_b,
            json={},
        )
        assert res.status_code == 404
        assert f"Investment goal '{goal_a['id']}' not found" in res.json()["detail"]

    def test_user_b_cannot_generate_glide_path_for_user_a_goal(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        future_date = (date.today() + timedelta(days=730)).isoformat()
        goal_a = test_client.post(
            "/investment-goals",
            headers=headers_a,
            json={"name": "User A Goal", "target_amount": "500000.00", "target_date": future_date},
        ).json()

        res = test_client.post(
            f"/investment-goals/{goal_a['id']}/glide-path",
            headers=headers_b,
            json={"risk_profile": "moderate"},
        )
        assert res.status_code == 404
        assert f"Investment goal '{goal_a['id']}' not found" in res.json()["detail"]

    def test_user_b_cannot_view_user_a_portfolio_drift(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        port_a = test_client.post(
            "/portfolios",
            headers=headers_a,
            json={"name": "User A Portfolio", "base_currency": "USD"},
        ).json()

        res = test_client.get(f"/portfolios/{port_a['id']}/drift", headers=headers_b)
        assert res.status_code == 404
        assert f"Portfolio '{port_a['id']}' not found" in res.json()["detail"]

    def test_user_b_cannot_rebalance_user_a_portfolio(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        port_a = test_client.post(
            "/portfolios",
            headers=headers_a,
            json={"name": "User A Portfolio", "base_currency": "USD"},
        ).json()

        res = test_client.post(f"/portfolios/{port_a['id']}/rebalancing-analysis", headers=headers_b)
        assert res.status_code == 404
        assert f"Portfolio '{port_a['id']}' not found" in res.json()["detail"]


class TestUnauthenticatedAccess:
    """Tests ensuring that all Phase 8 endpoints reject unauthenticated requests."""

    def test_unauthenticated_requests_return_401(self, test_client: TestClient):
        dummy_id = str(uuid.uuid4())
        endpoints = [
            ("POST", "/calculators/sip", {"monthly_contribution": "1000", "annual_return_percentage": "10", "duration_months": 12}),
            ("POST", "/calculators/reverse-sip", {"target_amount": "100000", "annual_return_percentage": "10", "duration_months": 12}),
            ("POST", f"/investment-goals/{dummy_id}/projection", {}),
            ("POST", "/investment-goals/plan", {"goal_name": "G", "target_amount": "1000", "target_date": "2030-01-01"}),
            ("GET", f"/portfolios/{dummy_id}/drift", None),
            ("POST", f"/portfolios/{dummy_id}/rebalancing-analysis", None),
            ("POST", f"/investment-goals/{dummy_id}/glide-path", {}),
            ("POST", "/calculators/glide-path", {"target_date": "2030-01-01"}),
        ]

        for method, path, body in endpoints:
            if method == "GET":
                res = test_client.get(path)
            else:
                res = test_client.post(path, json=body or {})
            assert res.status_code == 401, f"Expected 401 for {method} {path}, got {res.status_code}"
