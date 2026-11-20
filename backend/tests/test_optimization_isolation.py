"""
Multi-user data isolation tests for Phase 7 portfolio optimization and historical market data.

Verifies strict cross-user security and isolation between User A and User B using real Bearer tokens:
- Portfolios and historical data scoped to User A cannot be optimized by User B.
- Any attempt by User B to optimize, upload historical prices to, or view the history of User A's portfolio returns 404.
- User B's optimization runs and history remain completely isolated from User A.
- Unauthenticated requests to any optimization or market data endpoint return 401 Unauthorized.
"""

from datetime import date, timedelta
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

USER_A_ID = "opt-user-a-uuid"
USER_A_EMAIL = "opt_user_a@example.com"

USER_B_ID = "opt-user-b-uuid"
USER_B_EMAIL = "opt_user_b@example.com"


def generate_sample_csv(symbols: list[str], n_days: int = 25) -> str:
    """Generate a valid historical prices CSV string with n_days of observations."""
    base_date = date(2025, 1, 1)
    lines = ["date,symbol,adjusted_close"]
    for i in range(n_days):
        cur_date = base_date + timedelta(days=i)
        for sym in symbols:
            price = 100.0 + i * 0.5
            lines.append(f"{cur_date.isoformat()},{sym},{price:.2f}")
    return "\n".join(lines)


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


def _create_user_portfolio_with_holdings(client: TestClient, headers: dict, sym1: str, sym2: str, name: str) -> str:
    """Helper to create assets, a portfolio, and 2 holdings for an authenticated user."""
    a1 = client.post(
        "/assets",
        headers=headers,
        json={"symbol": sym1, "name": f"{sym1} Corp", "asset_class": "equity", "currency": "USD"},
    ).json()
    a2 = client.post(
        "/assets",
        headers=headers,
        json={"symbol": sym2, "name": f"{sym2} Corp", "asset_class": "equity", "currency": "USD"},
    ).json()

    port = client.post(
        "/portfolios",
        headers=headers,
        json={"name": name, "base_currency": "USD"},
    ).json()

    client.post(
        f"/portfolios/{port['id']}/holdings",
        headers=headers,
        json={
            "asset_id": a1["id"],
            "quantity": "100.0000",
            "average_purchase_price": "100.00",
            "current_price": "120.00",
        },
    )
    client.post(
        f"/portfolios/{port['id']}/holdings",
        headers=headers,
        json={
            "asset_id": a2["id"],
            "quantity": "50.0000",
            "average_purchase_price": "200.00",
            "current_price": "210.00",
        },
    )
    return port["id"]


class TestCrossUserOptimizationIsolation:
    """Tests ensuring User B cannot optimize or view User A's portfolios."""

    def test_user_b_cannot_optimize_user_a_portfolio(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        port_a_id = _create_user_portfolio_with_holdings(
            test_client, headers_a, "AAPL", "MSFT", "User A Portfolio"
        )
        csv_data = generate_sample_csv(["AAPL", "MSFT"], n_days=25)

        # User B attempts to optimize User A's portfolio
        response = test_client.post(
            f"/portfolios/{port_a_id}/optimize",
            headers=headers_b,
            json={"strategy": "min_volatility", "csv_content": csv_data},
        )
        assert response.status_code == 404
        assert f"Portfolio '{port_a_id}' not found" in response.json()["detail"]

    def test_user_b_cannot_import_prices_into_user_a_portfolio(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        port_a_id = _create_user_portfolio_with_holdings(
            test_client, headers_a, "AAPL", "MSFT", "User A Portfolio"
        )
        csv_data = generate_sample_csv(["AAPL", "MSFT"], n_days=25)
        file_bytes = io.BytesIO(csv_data.encode("utf-8"))

        # User B attempts to upload prices into User A's portfolio
        response = test_client.post(
            f"/portfolios/{port_a_id}/historical-prices/import-csv",
            headers=headers_b,
            files={"file": ("prices.csv", file_bytes, "text/csv")},
        )
        assert response.status_code == 404
        assert f"Portfolio '{port_a_id}' not found" in response.json()["detail"]

    def test_user_b_cannot_view_user_a_optimization_history(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        port_a_id = _create_user_portfolio_with_holdings(
            test_client, headers_a, "AAPL", "MSFT", "User A Portfolio"
        )
        csv_data = generate_sample_csv(["AAPL", "MSFT"], n_days=25)

        # User A executes an optimization
        opt_res = test_client.post(
            f"/portfolios/{port_a_id}/optimize",
            headers=headers_a,
            json={"strategy": "min_volatility", "csv_content": csv_data},
        )
        assert opt_res.status_code == 200

        # User B attempts to read User A's portfolio optimization history
        response = test_client.get(
            f"/portfolios/{port_a_id}/optimization-history",
            headers=headers_b,
        )
        assert response.status_code == 404
        assert f"Portfolio '{port_a_id}' not found" in response.json()["detail"]

    def test_optimization_history_isolation_between_distinct_portfolios(
        self, test_client: TestClient, headers_a: dict, headers_b: dict
    ):
        port_a_id = _create_user_portfolio_with_holdings(
            test_client, headers_a, "AAPL", "MSFT", "User A Portfolio"
        )
        port_b_id = _create_user_portfolio_with_holdings(
            test_client, headers_b, "GOOGL", "AMZN", "User B Portfolio"
        )
        csv_a = generate_sample_csv(["AAPL", "MSFT"], n_days=25)

        # User A optimizes Portfolio A
        test_client.post(
            f"/portfolios/{port_a_id}/optimize",
            headers=headers_a,
            json={"strategy": "min_volatility", "csv_content": csv_a},
        )

        # User A has 1 history record
        hist_a = test_client.get(
            f"/portfolios/{port_a_id}/optimization-history",
            headers=headers_a,
        ).json()
        assert len(hist_a) == 1

        # User B's portfolio B history is empty
        hist_b = test_client.get(
            f"/portfolios/{port_b_id}/optimization-history",
            headers=headers_b,
        ).json()
        assert len(hist_b) == 0


class TestUnauthenticatedAccess:
    """Tests ensuring that all optimization endpoints reject unauthenticated requests."""

    def test_unauthenticated_optimize_returns_401(self, test_client: TestClient):
        response = test_client.post(
            f"/portfolios/{uuid.uuid4()}/optimize",
            json={"strategy": "min_volatility"},
        )
        assert response.status_code == 401

    def test_unauthenticated_history_returns_401(self, test_client: TestClient):
        response = test_client.get(f"/portfolios/{uuid.uuid4()}/optimization-history")
        assert response.status_code == 401

    def test_unauthenticated_market_data_import_returns_401(self, test_client: TestClient):
        response = test_client.post(
            "/market-data/historical-prices/import-csv",
            files={"file": ("p.csv", io.BytesIO(b"date,symbol,adjusted_close"), "text/csv")},
        )
        assert response.status_code == 401

    def test_unauthenticated_portfolio_price_import_returns_401(self, test_client: TestClient):
        response = test_client.post(
            f"/portfolios/{uuid.uuid4()}/historical-prices/import-csv",
            files={"file": ("p.csv", io.BytesIO(b"date,symbol,adjusted_close"), "text/csv")},
        )
        assert response.status_code == 401

    def test_unauthenticated_get_symbol_prices_returns_401(self, test_client: TestClient):
        response = test_client.get("/market-data/historical-prices/AAPL")
        assert response.status_code == 401
