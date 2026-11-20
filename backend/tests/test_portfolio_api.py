"""
Integration tests for Phase 6 FastAPI portfolio endpoints.

Verifies end-to-end functionality backed by SQLPortfolioRepository:
- Portfolios CRUD and safe deletion behavior.
- Asset instruments management.
- Holdings management and duplicate protection.
- Target asset allocation.
- Investment goals and progress tracking.
- Deterministic valuation, allocation analysis, and optimization readiness.
"""

from datetime import date as ISODate
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
from app.db.session import get_db
from app.main import app

PORTFOLIO_TEST_USER = UserModel(
    id="portfolio-test-user-uuid-1",
    email="portfolio_tester@example.com",
    password_hash="mockhash",
    is_active=True,
)


@pytest.fixture()
def db_client() -> TestClient:
    """FastAPI TestClient wired to an isolated in-memory database and authenticated test user."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    # Pre-insert user into DB
    with TestingSessionLocal() as session:
        session.add(
            UserModel(
                id=PORTFOLIO_TEST_USER.id,
                email=PORTFOLIO_TEST_USER.email,
                password_hash=PORTFOLIO_TEST_USER.password_hash,
                is_active=True,
            )
        )
        session.commit()

    def override_get_db():
        session: Session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: PORTFOLIO_TEST_USER

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


class TestPortfolioCRUD:
    """Tests for portfolio create, read, update, delete endpoints."""

    def test_create_and_list_portfolio(self, db_client: TestClient):
        r = db_client.post(
            "/portfolios",
            json={
                "name": "Core Wealth",
                "description": "Primary long term portfolio",
                "base_currency": "INR",
            },
        )
        assert r.status_code == 201
        data = r.json()
        p_id = data["id"]
        assert data["name"] == "Core Wealth"
        assert data["base_currency"] == "INR"
        assert data["holding_count"] == 0

        # List portfolios
        r_list = db_client.get("/portfolios")
        assert r_list.status_code == 200
        items = r_list.json()
        assert len(items) == 1
        assert items[0]["id"] == p_id

    def test_get_and_patch_portfolio(self, db_client: TestClient):
        r = db_client.post("/portfolios", json={"name": "Tactical"})
        p_id = r.json()["id"]

        # Patch name
        r_patch = db_client.patch(f"/portfolios/{p_id}", json={"name": "Tactical Opportunities"})
        assert r_patch.status_code == 200
        assert r_patch.json()["name"] == "Tactical Opportunities"

        # Get
        r_get = db_client.get(f"/portfolios/{p_id}")
        assert r_get.status_code == 200
        assert r_get.json()["name"] == "Tactical Opportunities"

    def test_delete_portfolio_protection(self, db_client: TestClient):
        # 1. Create portfolio and asset
        p = db_client.post("/portfolios", json={"name": "Safe Delete"}).json()
        a = db_client.post("/assets", json={"name": "Asset X", "asset_class": "equity"}).json()

        # 2. Add holding
        db_client.post(
            f"/portfolios/{p['id']}/holdings",
            json={"asset_id": a["id"], "quantity": "10", "average_purchase_price": "100"},
        )

        # 3. Attempt delete without cascade -> 400 Bad Request
        r_del = db_client.delete(f"/portfolios/{p['id']}")
        assert r_del.status_code == 400
        assert "contains 1 active holding" in r_del.json()["detail"]

        # 4. Delete with cascade=true -> 200 OK
        r_del_cascade = db_client.delete(f"/portfolios/{p['id']}?cascade=true")
        assert r_del_cascade.status_code == 200

        # 5. Verify 404 now
        assert db_client.get(f"/portfolios/{p['id']}").status_code == 404


class TestAssetAndHoldingsAPI:
    """Tests for assets and holdings endpoints."""

    def test_asset_creation_and_listing(self, db_client: TestClient):
        r1 = db_client.post(
            "/assets",
            json={
                "symbol": "HDFCBANK",
                "name": "HDFC Bank Ltd",
                "asset_class": "equity",
                "currency": "INR",
            },
        )
        assert r1.status_code == 201
        assert r1.json()["symbol"] == "HDFCBANK"

        r_list = db_client.get("/assets?asset_class=equity")
        assert r_list.status_code == 200
        assert any(a["symbol"] == "HDFCBANK" for a in r_list.json())

    def test_holdings_crud_and_duplicate_rejection(self, db_client: TestClient):
        p = db_client.post("/portfolios", json={"name": "Holdings Test"}).json()
        a = db_client.post("/assets", json={"name": "TCS", "asset_class": "equity"}).json()

        # Add holding
        r_h = db_client.post(
            f"/portfolios/{p['id']}/holdings",
            json={
                "asset_id": a["id"],
                "quantity": "25.0",
                "average_purchase_price": "3200.00",
                "current_price": "3500.00",
            },
        )
        assert r_h.status_code == 201
        h_data = r_h.json()
        h_id = h_data["id"]
        assert h_data["cost_basis"] == "80000.00"
        assert h_data["market_value"] == "87500.00"

        # Attempt to add duplicate holding of same asset -> 400
        r_dup = db_client.post(
            f"/portfolios/{p['id']}/holdings",
            json={"asset_id": a["id"], "quantity": "10", "average_purchase_price": "3300"},
        )
        assert r_dup.status_code == 400
        assert "already exists" in r_dup.json()["detail"]

        # Patch holding price
        r_patch = db_client.patch(
            f"/portfolios/{p['id']}/holdings/{h_id}",
            json={"current_price": "3600.00"},
        )
        assert r_patch.status_code == 200
        assert r_patch.json()["market_value"] == "90000.00"

        # Delete holding
        r_del = db_client.delete(f"/portfolios/{p['id']}/holdings/{h_id}")
        assert r_del.status_code == 200


class TestTargetAllocationAndGoalsAPI:
    """Tests for target allocations and investment goals."""

    def test_set_and_get_target_allocation(self, db_client: TestClient):
        p = db_client.post("/portfolios", json={"name": "Allocation Portfolio"}).json()

        # Set valid allocation (sums to 100)
        r = db_client.put(
            f"/portfolios/{p['id']}/allocation-target",
            json={
                "targets": {
                    "equity": "60.00",
                    "debt": "30.00",
                    "cash": "10.00",
                },
                "is_draft": False,
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["total_target_percentage"] == "100.00"
        assert data["is_draft"] is False

        # Retrieve
        r_get = db_client.get(f"/portfolios/{p['id']}/allocation-target")
        assert r_get.status_code == 200
        assert r_get.json()["targets"]["equity"] == "60.00"

    def test_goals_crud_and_progress_calculation(self, db_client: TestClient):
        # Create portfolio with holding (value = 50,000)
        p = db_client.post("/portfolios", json={"name": "Goal Portfolio"}).json()
        a = db_client.post("/assets", json={"name": "Index Fund", "asset_class": "mutual_fund"}).json()
        db_client.post(
            f"/portfolios/{p['id']}/holdings",
            json={"asset_id": a["id"], "quantity": "500", "average_purchase_price": "100", "current_price": "100"},
        )

        # Create goal linked to portfolio
        r_goal = db_client.post(
            "/investment-goals",
            json={
                "name": "Higher Studies",
                "target_amount": "100000.00",
                "target_date": "2030-01-01",
                "portfolio_id": p["id"],
                "priority": "high",
            },
        )
        assert r_goal.status_code == 201
        g = r_goal.json()
        assert g["current_portfolio_value"] == "50000.00"
        assert g["progress_percentage"] == "50.00"
        assert g["remaining_amount"] == "50000.00"

        # List goals
        r_list = db_client.get("/investment-goals")
        assert len(r_list.json()) == 1

        # Delete goal
        r_del = db_client.delete(f"/investment-goals/{g['id']}")
        assert r_del.status_code == 200


class TestValuationAllocationAndOptimizationReadiness:
    """Tests for valuation, allocation-analysis, and optimization-readiness endpoints."""

    def test_end_to_end_valuation_and_readiness(self, db_client: TestClient):
        # 1. Create portfolio
        p = db_client.post("/portfolios", json={"name": "Complete Strategy"}).json()
        p_id = p["id"]

        # 2. Check readiness before holdings -> not ready
        r_ready_empty = db_client.get(f"/portfolios/{p_id}/optimization-readiness")
        assert r_ready_empty.status_code == 200
        assert r_ready_empty.json()["is_ready_for_optimization"] is False

        # 3. Add 2 holdings (Equity 60%, Debt 40%)
        a_eq = db_client.post("/assets", json={"name": "Stock A", "asset_class": "equity"}).json()
        a_debt = db_client.post("/assets", json={"name": "Bond B", "asset_class": "debt"}).json()

        db_client.post(
            f"/portfolios/{p_id}/holdings",
            json={"asset_id": a_eq["id"], "quantity": "60", "average_purchase_price": "100", "current_price": "100"},
        )
        db_client.post(
            f"/portfolios/{p_id}/holdings",
            json={"asset_id": a_debt["id"], "quantity": "40", "average_purchase_price": "100", "current_price": "100"},
        )

        # 4. Valuation endpoint
        r_val = db_client.get(f"/portfolios/{p_id}/valuation")
        assert r_val.status_code == 200
        val_data = r_val.json()
        assert val_data["priced_holdings_value"] == "10000.00"
        assert val_data["valuation_coverage_percentage"] == "100.00"

        # 5. Set target allocation (60 equity, 40 debt)
        db_client.put(
            f"/portfolios/{p_id}/allocation-target",
            json={"targets": {"equity": "60.00", "debt": "40.00"}, "is_draft": False},
        )

        # 6. Allocation analysis endpoint
        r_analysis = db_client.get(f"/portfolios/{p_id}/allocation-analysis")
        assert r_analysis.status_code == 200
        an_data = r_analysis.json()
        assert an_data["is_analysis_reliable"] is True
        for c in an_data["comparisons"]:
            assert c["status"] == "on_target"
            assert c["difference_percentage_points"] == "0.00"

        # 7. Optimization readiness endpoint -> ready!
        r_ready = db_client.get(f"/portfolios/{p_id}/optimization-readiness")
        assert r_ready.status_code == 200
        assert r_ready.json()["is_ready_for_optimization"] is True
        assert r_ready.json()["readiness_status"] == "ready"
        assert len(r_ready.json()["blockers"]) == 0
