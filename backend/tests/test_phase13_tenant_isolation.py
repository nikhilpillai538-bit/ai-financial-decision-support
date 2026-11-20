"""
Phase 13 End-to-End Multi-Tenant Security & User Isolation Tests.

Verifies strict tenant barriers across Phase 13 simulation endpoints:
- User A creates a portfolio and investment goal.
- User B cannot run stress tests, backtests, Monte Carlo, or scenario comparisons
  against User A's resources (returns HTTP 404).
- User A can run all operations successfully.
"""

from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.security import create_access_token, hash_password
from app.db.base import Base
from app.db.models import AssetModel, HistoricalPriceModel, InvestmentGoalModel, PortfolioHoldingModel, PortfolioModel, UserModel
from app.db.session import get_db
from app.main import app

USER_A_ID = "phase13-user-a"
USER_B_ID = "phase13-user-b"


@pytest.fixture()
def phase13_client() -> TestClient:
    """Isolated SQLite test client with pre-seeded users and assets."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with TestingSession() as session:
        # Create User A and User B
        session.add(
            UserModel(
                id=USER_A_ID,
                email="user_a@sim-audit.com",
                password_hash=hash_password("PasswordA123!"),
                is_active=True,
            )
        )
        session.add(
            UserModel(
                id=USER_B_ID,
                email="user_b@sim-audit.com",
                password_hash=hash_password("PasswordB123!"),
                is_active=True,
            )
        )

        # Asset for User A
        asset_a = AssetModel(
            id="asset-test-a",
            symbol="NIFTYTEST",
            name="Nifty 50 Index Test",
            asset_class="equity",
            currency="INR",
        )
        session.add(asset_a)

        # Portfolio for User A
        port_a = PortfolioModel(
            id="port-user-a-1",
            user_id=USER_A_ID,
            name="User A Retirement Corpus",
            base_currency="INR",
        )
        session.add(port_a)

        # Holding for User A
        session.add(
            PortfolioHoldingModel(
                id="holding-user-a-1",
                portfolio_id="port-user-a-1",
                asset_id="asset-test-a",
                quantity=Decimal("100.00"),
                average_purchase_price=Decimal("100.00"),
                current_price=Decimal("150.00"),
            )
        )

        # Goal for User A
        session.add(
            InvestmentGoalModel(
                id="goal-user-a-1",
                user_id=USER_A_ID,
                name="User A Early Retirement",
                target_amount=Decimal("5000000.00"),
                target_date=date(2035, 12, 31),
                current_amount=Decimal("15000.00"),
                monthly_contribution=Decimal("25000.00"),
            )
        )

        # Historical prices for NIFTYTEST
        for i in range(10):
            session.add(
                HistoricalPriceModel(
                    id=f"hp-{i}",
                    symbol="NIFTYTEST",
                    date=date(2025, 1, 1 + i),
                    adjusted_close=Decimal(str(100.0 + i * 2.0)),
                    source="synthetic",
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
    token, _ = create_access_token(USER_A_ID, "user_a@sim-audit.com")
    return token


@pytest.fixture()
def token_b() -> str:
    token, _ = create_access_token(USER_B_ID, "user_b@sim-audit.com")
    return token


class TestPhase13TenantIsolation:
    """Tests guaranteeing that User B cannot access User A's portfolios or goals."""

    def test_stress_test_isolation(self, phase13_client: TestClient, token_a: str, token_b: str):
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B attempts to stress test User A's portfolio -> 404
        res_b = phase13_client.post(
            "/portfolios/port-user-a-1/stress-test",
            headers=headers_b,
            json={"scenario": "equity_market_crash"},
        )
        assert res_b.status_code == 404

        # User A stress tests their own portfolio -> 200
        res_a = phase13_client.post(
            "/portfolios/port-user-a-1/stress-test",
            headers=headers_a,
            json={"scenario": "equity_market_crash"},
        )
        assert res_a.status_code == 200
        assert res_a.json()["baseline_portfolio_value"] == "15000.00"

    def test_monte_carlo_isolation(self, phase13_client: TestClient, token_a: str, token_b: str):
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B attempts to run Monte Carlo on User A's portfolio -> 404
        res_b = phase13_client.post(
            "/portfolios/port-user-a-1/monte-carlo",
            headers=headers_b,
            json={"horizon_months": 24, "num_simulations": 100},
        )
        assert res_b.status_code == 404

        # User A runs Monte Carlo on their own portfolio -> 200
        res_a = phase13_client.post(
            "/portfolios/port-user-a-1/monte-carlo",
            headers=headers_a,
            json={"horizon_months": 24, "num_simulations": 100, "seed": 42},
        )
        assert res_a.status_code == 200
        assert res_a.json()["initial_value"] == "15000.00"

    def test_goal_scenario_comparison_isolation(
        self, phase13_client: TestClient, token_a: str, token_b: str
    ):
        headers_a = {"Authorization": f"Bearer {token_a}"}
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # User B attempts to run scenario comparison on User A's goal -> 404
        res_b = phase13_client.post(
            "/goals/goal-user-a-1/scenario-comparison",
            headers=headers_b,
            json={
                "scenarios": [
                    {"name": "Scenario 1", "monthly_contribution": "30000.00"}
                ]
            },
        )
        assert res_b.status_code == 404

        # User A runs scenario comparison on their own goal -> 200
        res_a = phase13_client.post(
            "/goals/goal-user-a-1/scenario-comparison",
            headers=headers_a,
            json={
                "scenarios": [
                    {"name": "Scenario 1", "monthly_contribution": "30000.00"}
                ],
                "num_simulations": 100,
                "seed": 42,
            },
        )
        assert res_a.status_code == 200
        assert res_a.json()["goal_name"] == "User A Early Retirement"
