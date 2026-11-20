"""
Multi-user data isolation tests for Phase 6 investment portfolio management.

Verifies strict cross-user security and isolation between User A and User B using real Bearer tokens:
- Portfolios, holdings, target allocations, and goals belonging to User A are invisible to User B.
- Any attempt by User B to access, update, or attach holdings to User A's resources returns 404.
- User B cannot link User A's portfolio to User B's investment goals.
- Unauthenticated requests return 401 Unauthorized.
"""

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

USER_A_ID = "user-a-portfolio-uuid"
USER_A_EMAIL = "user_a_port@example.com"

USER_B_ID = "user-b-portfolio-uuid"
USER_B_EMAIL = "user_b_port@example.com"


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


class TestPortfolioUserIsolation:
    """Security tests verifying complete isolation between User A and User B."""

    def test_user_b_cannot_list_or_get_user_a_portfolio(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        # User A creates portfolio
        p_a = test_client.post(
            "/portfolios",
            json={"name": "User A Private Portfolio"},
            headers=headers_a,
        ).json()
        p_id = p_a["id"]

        # User B lists portfolios -> empty list
        r_b_list = test_client.get("/portfolios", headers=headers_b)
        assert r_b_list.status_code == 200
        assert len(r_b_list.json()) == 0

        # User B attempts to get User A's portfolio by ID -> 404 (does not leak existence)
        r_b_get = test_client.get(f"/portfolios/{p_id}", headers=headers_b)
        assert r_b_get.status_code == 404

    def test_user_b_cannot_patch_or_delete_user_a_portfolio(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        p_a = test_client.post(
            "/portfolios",
            json={"name": "User A Secure Portfolio"},
            headers=headers_a,
        ).json()
        p_id = p_a["id"]

        # User B attempts PATCH
        r_patch = test_client.patch(
            f"/portfolios/{p_id}",
            json={"name": "Hijacked Name"},
            headers=headers_b,
        )
        assert r_patch.status_code == 404

        # User B attempts DELETE
        r_del = test_client.delete(f"/portfolios/{p_id}", headers=headers_b)
        assert r_del.status_code == 404

        # User A verifies portfolio is untouched
        r_a_check = test_client.get(f"/portfolios/{p_id}", headers=headers_a)
        assert r_a_check.status_code == 200
        assert r_a_check.json()["name"] == "User A Secure Portfolio"

    def test_user_b_cannot_add_or_view_holdings_in_user_a_portfolio(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        p_a = test_client.post(
            "/portfolios",
            json={"name": "User A Holdings Test"},
            headers=headers_a,
        ).json()
        p_id = p_a["id"]

        asset = test_client.post(
            "/assets",
            json={"name": "Common Equity", "asset_class": "equity"},
            headers=headers_a,
        ).json()
        a_id = asset["id"]

        # User A adds holding
        h_a = test_client.post(
            f"/portfolios/{p_id}/holdings",
            json={"asset_id": a_id, "quantity": "10", "average_purchase_price": "100"},
            headers=headers_a,
        ).json()
        h_id = h_a["id"]

        # User B attempts to list holdings in User A's portfolio -> 404
        r_b_holdings = test_client.get(f"/portfolios/{p_id}/holdings", headers=headers_b)
        assert r_b_holdings.status_code == 404

        # User B attempts to add a holding to User A's portfolio -> 404
        r_b_add = test_client.post(
            f"/portfolios/{p_id}/holdings",
            json={"asset_id": a_id, "quantity": "50", "average_purchase_price": "200"},
            headers=headers_b,
        )
        assert r_b_add.status_code == 404

        # User B attempts to patch User A's holding -> 404
        r_b_patch = test_client.patch(
            f"/portfolios/{p_id}/holdings/{h_id}",
            json={"quantity": "999"},
            headers=headers_b,
        )
        assert r_b_patch.status_code == 404

        # User B attempts to delete User A's holding -> 404
        r_b_del = test_client.delete(f"/portfolios/{p_id}/holdings/{h_id}", headers=headers_b)
        assert r_b_del.status_code == 404

    def test_user_b_cannot_access_or_set_user_a_target_allocation(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        p_a = test_client.post(
            "/portfolios",
            json={"name": "User A Allocation Test"},
            headers=headers_a,
        ).json()
        p_id = p_a["id"]

        # User A sets allocation
        test_client.put(
            f"/portfolios/{p_id}/allocation-target",
            json={"targets": {"equity": "100.00"}, "is_draft": False},
            headers=headers_a,
        )

        # User B attempts GET allocation -> 404
        assert test_client.get(f"/portfolios/{p_id}/allocation-target", headers=headers_b).status_code == 404

        # User B attempts PUT allocation -> 404
        assert test_client.put(
            f"/portfolios/{p_id}/allocation-target",
            json={"targets": {"equity": "50.00", "debt": "50.00"}, "is_draft": False},
            headers=headers_b,
        ).status_code == 404

    def test_user_b_cannot_access_or_link_user_a_goals(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        p_a = test_client.post(
            "/portfolios",
            json={"name": "User A Goals Test"},
            headers=headers_a,
        ).json()
        p_id = p_a["id"]

        # User A creates goal linked to portfolio
        g_a = test_client.post(
            "/investment-goals",
            json={
                "name": "User A Private Goal",
                "target_amount": "500000.00",
                "target_date": "2032-12-31",
                "portfolio_id": p_id,
            },
            headers=headers_a,
        ).json()
        g_id = g_a["id"]

        # User B lists goals -> empty
        r_b_goals = test_client.get("/investment-goals", headers=headers_b)
        assert len(r_b_goals.json()) == 0

        # User B GET goal by ID -> 404
        assert test_client.get(f"/investment-goals/{g_id}", headers=headers_b).status_code == 404

        # User B PATCH goal -> 404
        assert test_client.patch(f"/investment-goals/{g_id}", json={"name": "Hacked"}, headers=headers_b).status_code == 404

        # User B DELETE goal -> 404
        assert test_client.delete(f"/investment-goals/{g_id}", headers=headers_b).status_code == 404

        # User B attempts to create goal linked to User A's portfolio -> 400 Bad Request
        r_b_link = test_client.post(
            "/investment-goals",
            json={
                "name": "User B Goal with foreign portfolio",
                "target_amount": "10000.00",
                "target_date": "2030-01-01",
                "portfolio_id": p_id,
            },
            headers=headers_b,
        )
        assert r_b_link.status_code == 400
        assert "not found or access denied" in r_b_link.json()["detail"]

    def test_user_b_cannot_modify_user_a_custom_asset(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        # User A creates custom asset
        a_a = test_client.post(
            "/assets",
            json={"name": "User A Private Equity", "asset_class": "equity", "currency": "INR"},
            headers=headers_a,
        ).json()
        a_id = a_a["id"]

        # User B attempts to patch User A's asset -> 404
        r_patch = test_client.patch(
            f"/assets/{a_id}",
            json={"name": "Renamed by User B"},
            headers=headers_b,
        )
        assert r_patch.status_code == 404

    def test_unauthenticated_requests_rejected(self, test_client: TestClient):
        # All portfolio endpoints require authentication
        assert test_client.get("/portfolios").status_code == 401
        assert test_client.post("/portfolios", json={"name": "Secret"}).status_code == 401
        assert test_client.post("/assets", json={"name": "Secret", "asset_class": "equity"}).status_code == 401
        assert test_client.get("/investment-goals").status_code == 401
