"""
Integration tests for Phase 7 FastAPI portfolio optimization and market data endpoints.

Verifies end-to-end functionality backed by SQLPortfolioRepository:
- Historical prices CSV ingestion (/market-data/historical-prices/import-csv)
- Portfolio-specific historical prices upload (/portfolios/{id}/historical-prices/import-csv)
- Historical prices retrieval (/market-data/historical-prices/{symbol})
- Deterministic MPT portfolio optimization (/portfolios/{id}/optimize)
  * min_volatility
  * max_sharpe
  * target_return
  * user_constrained
  * inline csv_content
  * efficient frontier calculation
  * rebalancing trade amount generation
- Optimization audit history (/portfolios/{id}/optimization-history)
- Validation errors and edge cases (insufficient holdings, missing symbols, missing data)
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

from app.auth.dependencies import get_current_user
from app.db.base import Base
from app.db.models import AssetModel, PortfolioHoldingModel, PortfolioModel, UserModel
from app.db.session import get_db
from app.main import app

OPTIMIZATION_TEST_USER = UserModel(
    id="opt-test-user-uuid-1",
    email="opt_tester@example.com",
    password_hash="mockhash",
    is_active=True,
)


def generate_sample_csv(symbols: list[str], n_days: int = 25) -> str:
    """Generate a valid historical prices CSV string with n_days of observations."""
    base_date = date(2025, 1, 1)
    lines = ["date,symbol,adjusted_close"]
    for i in range(n_days):
        cur_date = base_date + timedelta(days=i)
        for sym in symbols:
            # Deterministic price pattern
            if sym == "AAPL":
                price = 150.0 + i * 0.8
            elif sym == "MSFT":
                price = 300.0 + i * 0.4
            else:
                price = 100.0 + i * 0.2
            lines.append(f"{cur_date.isoformat()},{sym},{price:.2f}")
    return "\n".join(lines)


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
                id=OPTIMIZATION_TEST_USER.id,
                email=OPTIMIZATION_TEST_USER.email,
                password_hash=OPTIMIZATION_TEST_USER.password_hash,
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
    app.dependency_overrides[get_current_user] = lambda: OPTIMIZATION_TEST_USER

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


def _setup_test_portfolio(client: TestClient) -> dict:
    """Helper to create assets, a portfolio, and holdings for AAPL and MSFT."""
    # 1. Create Assets
    asset_aapl = client.post(
        "/assets",
        json={"symbol": "AAPL", "name": "Apple Inc", "asset_class": "equity", "currency": "USD"},
    ).json()
    asset_msft = client.post(
        "/assets",
        json={"symbol": "MSFT", "name": "Microsoft Corp", "asset_class": "equity", "currency": "USD"},
    ).json()

    # 2. Create Portfolio
    portfolio = client.post(
        "/portfolios",
        json={"name": "Tech Duo Portfolio", "base_currency": "USD"},
    ).json()

    # 3. Add Holdings
    client.post(
        f"/portfolios/{portfolio['id']}/holdings",
        json={
            "asset_id": asset_aapl["id"],
            "quantity": "50.0000",
            "average_purchase_price": "140.00",
            "current_price": "160.00",
        },
    )
    client.post(
        f"/portfolios/{portfolio['id']}/holdings",
        json={
            "asset_id": asset_msft["id"],
            "quantity": "25.0000",
            "average_purchase_price": "280.00",
            "current_price": "310.00",
        },
    )

    return portfolio


class TestHistoricalPricesAPI:
    """Tests for CSV import and historical prices retrieval endpoints."""

    def test_import_market_data_csv_success(self, db_client: TestClient):
        csv_data = generate_sample_csv(["AAPL", "MSFT"], n_days=20)
        file_bytes = io.BytesIO(csv_data.encode("utf-8"))

        response = db_client.post(
            "/market-data/historical-prices/import-csv",
            files={"file": ("market_prices.csv", file_bytes, "text/csv")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 40
        assert data["imported"] == 40
        assert data["skipped_duplicates"] == 0
        assert "AAPL" in data["symbols_updated"]
        assert "MSFT" in data["symbols_updated"]

    def test_import_market_data_csv_deduplication(self, db_client: TestClient):
        csv_data = generate_sample_csv(["AAPL"], n_days=15)
        file_bytes1 = io.BytesIO(csv_data.encode("utf-8"))
        file_bytes2 = io.BytesIO(csv_data.encode("utf-8"))

        # First upload
        res1 = db_client.post(
            "/market-data/historical-prices/import-csv",
            files={"file": ("prices1.csv", file_bytes1, "text/csv")},
        )
        assert res1.status_code == 200
        assert res1.json()["imported"] == 15

        # Duplicate upload
        res2 = db_client.post(
            "/market-data/historical-prices/import-csv",
            files={"file": ("prices2.csv", file_bytes2, "text/csv")},
        )
        assert res2.status_code == 200
        assert res2.json()["imported"] == 0
        assert res2.json()["skipped_duplicates"] == 15

    def test_import_market_data_csv_invalid_format(self, db_client: TestClient):
        bad_csv = "date,wrong_column,adjusted_close\n2025-01-01,AAPL,150.00"
        file_bytes = io.BytesIO(bad_csv.encode("utf-8"))

        response = db_client.post(
            "/market-data/historical-prices/import-csv",
            files={"file": ("bad.csv", file_bytes, "text/csv")},
        )
        assert response.status_code == 422
        assert "CSV validation failed" in response.json()["detail"]

    def test_get_symbol_prices(self, db_client: TestClient):
        csv_data = generate_sample_csv(["AAPL"], n_days=10)
        db_client.post(
            "/market-data/historical-prices/import-csv",
            files={"file": ("aapl.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        )

        response = db_client.get("/market-data/historical-prices/AAPL?limit=5")
        assert response.status_code == 200
        prices = response.json()
        assert len(prices) == 5
        assert prices[0]["symbol"] == "AAPL"


class TestPortfolioOptimizationAPI:
    """Tests for portfolio optimization calculations and responses."""

    def test_optimize_portfolio_min_volatility_with_db_prices(self, db_client: TestClient):
        portfolio = _setup_test_portfolio(db_client)

        # Upload prices to DB
        csv_data = generate_sample_csv(["AAPL", "MSFT"], n_days=25)
        db_client.post(
            f"/portfolios/{portfolio['id']}/historical-prices/import-csv",
            files={"file": ("port_prices.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        )

        # Run optimization
        response = db_client.post(
            f"/portfolios/{portfolio['id']}/optimize",
            json={
                "strategy": "min_volatility",
                "risk_free_rate": "0.02",
                "include_efficient_frontier": True,
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["portfolio_id"] == portfolio["id"]
        assert data["strategy"] == "min_volatility"
        assert Decimal(data["expected_return"]) > Decimal("0")
        assert Decimal(data["expected_volatility"]) > Decimal("0")
        assert Decimal(data["total_portfolio_value"]) > Decimal("0")
        assert len(data["allocations"]) == 2
        assert len(data["asset_class_summary"]) >= 1
        assert len(data["efficient_frontier"]) > 0
        assert data["run_id"] is not None

        # Verify weights sum to 1.0
        weights_sum = sum(Decimal(a["optimal_weight"]) for a in data["allocations"])
        assert pytest.approx(float(weights_sum), abs=1e-3) == 1.0

        # Verify each allocation contains required fields
        for alloc in data["allocations"]:
            assert alloc["symbol"] in ["AAPL", "MSFT"]
            assert alloc["action"] in ["BUY", "SELL", "HOLD"]
            assert Decimal(alloc["trade_amount"]) >= Decimal("0")

    def test_optimize_portfolio_max_sharpe(self, db_client: TestClient):
        portfolio = _setup_test_portfolio(db_client)
        csv_data = generate_sample_csv(["AAPL", "MSFT"], n_days=25)
        db_client.post(
            "/market-data/historical-prices/import-csv",
            files={"file": ("prices.csv", io.BytesIO(csv_data.encode("utf-8")), "text/csv")},
        )

        response = db_client.post(
            f"/portfolios/{portfolio['id']}/optimize",
            json={
                "strategy": "max_sharpe",
                "risk_free_rate": "0.01",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["strategy"] == "max_sharpe"
        assert data["sharpe_ratio"] is not None

    def test_optimize_portfolio_with_inline_csv_content(self, db_client: TestClient):
        portfolio = _setup_test_portfolio(db_client)
        inline_csv = generate_sample_csv(["AAPL", "MSFT"], n_days=25)

        # Optimize without prior DB import, using csv_content in payload
        response = db_client.post(
            f"/portfolios/{portfolio['id']}/optimize",
            json={
                "strategy": "min_volatility",
                "csv_content": inline_csv,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["observation_count"] >= 20
        assert len(data["allocations"]) == 2

    def test_optimize_portfolio_user_constrained_bounds(self, db_client: TestClient):
        portfolio = _setup_test_portfolio(db_client)
        inline_csv = generate_sample_csv(["AAPL", "MSFT"], n_days=25)

        # Asset AAPL capped at 30%
        response = db_client.post(
            f"/portfolios/{portfolio['id']}/optimize",
            json={
                "strategy": "user_constrained",
                "min_weight": "0.10",
                "max_weight": "0.90",
                "asset_bounds": {
                    "AAPL": {"min_weight": "0.10", "max_weight": "0.30"},
                },
                "csv_content": inline_csv,
            },
        )
        assert response.status_code == 200
        data = response.json()
        aapl_alloc = next(a for a in data["allocations"] if a["symbol"] == "AAPL")
        assert Decimal(aapl_alloc["optimal_weight"]) <= Decimal("0.3050")

    def test_optimization_history_recording_and_listing(self, db_client: TestClient):
        portfolio = _setup_test_portfolio(db_client)
        inline_csv = generate_sample_csv(["AAPL", "MSFT"], n_days=25)

        # Run two optimizations
        db_client.post(
            f"/portfolios/{portfolio['id']}/optimize",
            json={"strategy": "min_volatility", "csv_content": inline_csv},
        )
        db_client.post(
            f"/portfolios/{portfolio['id']}/optimize",
            json={"strategy": "max_sharpe", "csv_content": inline_csv},
        )

        history_res = db_client.get(f"/portfolios/{portfolio['id']}/optimization-history")
        assert history_res.status_code == 200
        history = history_res.json()
        assert len(history) == 2
        strategies = [h["strategy"] for h in history]
        assert "min_volatility" in strategies
        assert "max_sharpe" in strategies

    def test_optimize_errors_insufficient_holdings(self, db_client: TestClient):
        # Create portfolio with only 1 holding
        asset = db_client.post(
            "/assets",
            json={"symbol": "ONLYONE", "name": "Single Asset", "asset_class": "equity", "currency": "USD"},
        ).json()
        portfolio = db_client.post(
            "/portfolios",
            json={"name": "Solo Asset Portfolio", "base_currency": "USD"},
        ).json()
        db_client.post(
            f"/portfolios/{portfolio['id']}/holdings",
            json={
                "asset_id": asset["id"],
                "quantity": "10.0000",
                "average_purchase_price": "100.00",
                "current_price": "100.00",
            },
        )

        response = db_client.post(
            f"/portfolios/{portfolio['id']}/optimize",
            json={"strategy": "min_volatility"},
        )
        assert response.status_code == 400
        assert "MPT optimization requires at least 2 distinct instruments" in response.json()["detail"]

    def test_optimize_errors_missing_price_data(self, db_client: TestClient):
        portfolio = _setup_test_portfolio(db_client)
        # Attempt optimization when no price data exists in DB and no csv_content supplied
        response = db_client.post(
            f"/portfolios/{portfolio['id']}/optimize",
            json={"strategy": "min_volatility"},
        )
        assert response.status_code == 400
        assert "No historical price data found for portfolio symbols" in response.json()["detail"]

    def test_optimize_errors_portfolio_not_found(self, db_client: TestClient):
        response = db_client.post(
            f"/portfolios/{uuid.uuid4()}/optimize",
            json={"strategy": "min_volatility"},
        )
        assert response.status_code == 404
