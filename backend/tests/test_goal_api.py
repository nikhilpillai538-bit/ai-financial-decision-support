"""
Integration tests for Phase 8 FastAPI Goal Planning, SIP Calculators, and Portfolio Drift API.

Tests end-to-end functionality backed by in-memory SQLite database:
- Forward SIP calculator (/calculators/sip)
- Reverse SIP calculator (/calculators/reverse-sip)
- Goal projection and gap analysis (/investment-goals/{id}/projection)
- Standalone goal planner (/investment-goals/plan)
- Portfolio drift detection (/portfolios/{id}/drift)
- Illustrative rebalancing analysis (/portfolios/{id}/rebalancing-analysis)
- Goal glide path (/investment-goals/{id}/glide-path)
- Standalone glide path (/calculators/glide-path)
- Validation errors and 404 checks
"""

from datetime import date, timedelta
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

PHASE8_TEST_USER = UserModel(
    id="phase8-test-user-uuid",
    email="phase8_tester@example.com",
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

    with TestingSessionLocal() as session:
        session.add(
            UserModel(
                id=PHASE8_TEST_USER.id,
                email=PHASE8_TEST_USER.email,
                password_hash=PHASE8_TEST_USER.password_hash,
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
    app.dependency_overrides[get_current_user] = lambda: PHASE8_TEST_USER

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


class TestSIPCalculatorAPI:
    """Tests for /calculators/sip and /calculators/reverse-sip."""

    def test_forward_sip_api_success(self, db_client: TestClient):
        response = db_client.post(
            "/calculators/sip",
            json={
                "initial_investment": "20000.00",
                "monthly_contribution": "10000.00",
                "annual_return_percentage": "12.0",
                "duration_months": 24,
                "rate_convention": "effective",
                "include_schedule": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["projected_future_value"]) > Decimal("280000.00")
        assert Decimal(data["total_invested"]) == Decimal("260000.00")
        assert len(data["schedule"]) == 2  # 2 years

    def test_forward_sip_with_annual_step_up(self, db_client: TestClient):
        response = db_client.post(
            "/calculators/sip",
            json={
                "initial_investment": "0.00",
                "monthly_contribution": "10000.00",
                "annual_return_percentage": "10.0",
                "duration_months": 24,
                "annual_step_up_percentage": "10.0",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["total_contributions"]) == Decimal("252000.00")

    def test_reverse_sip_api_success(self, db_client: TestClient):
        response = db_client.post(
            "/calculators/reverse-sip",
            json={
                "target_amount": "500000.00",
                "initial_investment": "50000.00",
                "annual_return_percentage": "12.0",
                "duration_months": 36,
                "rate_convention": "nominal",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["required_monthly_contribution"]) > Decimal("0.00")
        assert data["is_target_already_covered"] is False

    def test_reverse_sip_target_already_covered(self, db_client: TestClient):
        response = db_client.post(
            "/calculators/reverse-sip",
            json={
                "target_amount": "100000.00",
                "initial_investment": "100000.00",
                "annual_return_percentage": "10.0",
                "duration_months": 12,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert Decimal(data["required_monthly_contribution"]) == Decimal("0.00")
        assert data["is_target_already_covered"] is True


class TestGoalPlanningAPI:
    """Tests for goal projection and standalone goal planning."""

    def test_project_saved_goal_and_overrides(self, db_client: TestClient):
        future_date = (date.today() + timedelta(days=730)).isoformat()  # 2 years
        # 1. Create a goal
        goal_res = db_client.post(
            "/investment-goals",
            json={
                "name": "Dream Vacation Fund",
                "target_amount": "300000.00",
                "target_date": future_date,
                "current_amount": "50000.00",
                "expected_annual_return": "0.1000",
                "monthly_contribution": "10000.00",
                "priority": "medium",
            },
        )
        assert goal_res.status_code == 201
        goal_id = goal_res.json()["id"]

        # 2. Run projection without overrides
        proj_res = db_client.post(
            f"/investment-goals/{goal_id}/projection",
            json={},
        )
        assert proj_res.status_code == 200
        data = proj_res.json()
        assert data["goal_name"] == "Dream Vacation Fund"
        assert Decimal(data["current_amount"]) == Decimal("50000.00")
        assert data["remaining_months"] >= 23
        assert Decimal(data["projected_future_value"]) > Decimal("300000.00")
        assert data["status_assessment"] in ["on_track", "ahead"]

    def test_project_goal_not_found(self, db_client: TestClient):
        response = db_client.post(
            f"/investment-goals/{uuid.uuid4()}/projection",
            json={},
        )
        assert response.status_code == 404

    def test_standalone_goal_planner(self, db_client: TestClient):
        future_date = (date.today() + timedelta(days=1095)).isoformat()  # 3 years
        response = db_client.post(
            "/investment-goals/plan",
            json={
                "goal_name": "Vehicle Purchase",
                "target_amount": "800000.00",
                "target_date": future_date,
                "current_amount": "200000.00",
                "expected_annual_return": "0.0900",
                "planned_monthly_contribution": "15000.00",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["goal_name"] == "Vehicle Purchase"
        assert data["remaining_months"] >= 35
        assert Decimal(data["required_monthly_contribution"]) > Decimal("0.00")


class TestPortfolioDriftAPI:
    """Tests for /portfolios/{id}/drift and /portfolios/{id}/rebalancing-analysis."""

    def _setup_portfolio_with_target(self, client: TestClient) -> str:
        # Create Assets
        a_eq = client.post(
            "/assets",
            json={"symbol": "NIFTY50", "name": "Nifty 50 ETF", "asset_class": "equity", "currency": "INR"},
        ).json()
        a_db = client.post(
            "/assets",
            json={"symbol": "GILT", "name": "Govt Bond Fund", "asset_class": "debt", "currency": "INR"},
        ).json()

        # Create Portfolio
        port = client.post("/portfolios", json={"name": "Retirement Portfolio", "base_currency": "INR"}).json()

        # Add Holdings: 70k Equity, 30k Debt (Total 100k)
        client.post(
            f"/portfolios/{port['id']}/holdings",
            json={"asset_id": a_eq["id"], "quantity": "700.0000", "average_purchase_price": "100.00", "current_price": "100.00"},
        )
        client.post(
            f"/portfolios/{port['id']}/holdings",
            json={"asset_id": a_db["id"], "quantity": "300.0000", "average_purchase_price": "100.00", "current_price": "100.00"},
        )

        # Set Target Allocation: 60% Equity, 40% Debt (Current is 70/30 -> Drift 10%)
        client.put(
            f"/portfolios/{port['id']}/allocation-target",
            json={"targets": {"equity": "60.00", "debt": "40.00"}},
        )
        return port["id"]

    def test_get_portfolio_drift_success(self, db_client: TestClient):
        port_id = self._setup_portfolio_with_target(db_client)

        # Default threshold is 5.0% -> 10% drift exceeds threshold
        response = db_client.get(f"/portfolios/{port_id}/drift")
        assert response.status_code == 200
        data = response.json()
        assert data["portfolio_exceeds_threshold"] is True
        assert Decimal(data["max_drift_percentage_points"]) == Decimal("10.00")
        assert "equity" in data["drifted_classes"]

        # Setting threshold to 15% -> 10% drift does not exceed
        res2 = db_client.get(f"/portfolios/{port_id}/drift?threshold_percentage_points=15.0")
        assert res2.status_code == 200
        assert res2.json()["portfolio_exceeds_threshold"] is False

    def test_rebalancing_analysis_success(self, db_client: TestClient):
        port_id = self._setup_portfolio_with_target(db_client)

        response = db_client.post(f"/portfolios/{port_id}/rebalancing-analysis")
        assert response.status_code == 200
        data = response.json()

        assert data["is_rebalancing_recommended"] is True
        assert Decimal(data["total_buy_amount"]) == Decimal("10000.00")
        assert Decimal(data["total_sell_amount"]) == Decimal("10000.00")
        assert Decimal(data["reconciliation_difference"]) == Decimal("0.00")

        eq_trade = next(t for t in data["trades"] if t["asset_class"] == "equity")
        assert eq_trade["action"] == "SELL"
        assert Decimal(eq_trade["trade_amount"]) == Decimal("10000.00")

        db_trade = next(t for t in data["trades"] if t["asset_class"] == "debt")
        assert db_trade["action"] == "BUY"
        assert Decimal(db_trade["trade_amount"]) == Decimal("10000.00")


class TestGlidePathAPI:
    """Tests for glide path generation endpoints."""

    def test_goal_glide_path_api(self, db_client: TestClient):
        future_date = (date.today() + timedelta(days=1825)).isoformat()  # 5 years
        goal = db_client.post(
            "/investment-goals",
            json={
                "name": "Child Education",
                "target_amount": "1000000.00",
                "target_date": future_date,
            },
        ).json()

        response = db_client.post(
            f"/investment-goals/{goal['id']}/glide-path",
            json={"risk_profile": "moderate", "interval_months": 12},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["goal_name"] == "Child Education"
        assert len(data["checkpoints"]) >= 5
        # Verify first and last checkpoints
        assert data["checkpoints"][0]["risk_level"] == "aggressive"
        assert data["checkpoints"][-1]["risk_level"] == "conservative"

    def test_standalone_glide_path_api(self, db_client: TestClient):
        future_date = (date.today() + timedelta(days=1095)).isoformat()
        response = db_client.post(
            "/calculators/glide-path",
            json={
                "target_date": future_date,
                "risk_profile": "aggressive",
                "interval_months": 12,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["checkpoints"]) >= 3
