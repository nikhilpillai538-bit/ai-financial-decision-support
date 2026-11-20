"""
Tests for Market Fetcher and Yahoo Finance market data endpoints.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import uuid

import numpy as np
import pandas as pd
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
from app.market_fetcher import (
    CURATED_PRESETS,
    fetch_live_quote,
    fetch_live_quotes,
    fetch_yahoo_historical_data,
    normalize_symbol,
)

TEST_USER = UserModel(
    id="test-yf-user-uuid",
    email="yf_test@example.com",
    password_hash="mockhash",
    is_active=True,
)


@pytest.fixture()
def db_client() -> TestClient:
    """Isolated test client with in-memory DB and authenticated user."""
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
                id=TEST_USER.id,
                email=TEST_USER.email,
                password_hash=TEST_USER.password_hash,
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
    app.dependency_overrides[get_current_user] = lambda: TEST_USER

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


class TestMarketFetcherUnit:
    """Unit tests for market_fetcher helper functions."""

    def test_normalize_symbol(self):
        assert normalize_symbol("  reliance.ns  ") == "RELIANCE.NS"
        assert normalize_symbol("aapl") == "AAPL"

    @patch("app.market_fetcher.yf.download")
    def test_fetch_yahoo_historical_data_mock(self, mock_download):
        dates = pd.date_range(start="2026-01-01", periods=5, freq="D")
        cols = pd.MultiIndex.from_tuples([("Close", "RELIANCE.NS"), ("Close", "TCS.NS")])
        mock_df = pd.DataFrame(
            [
                [1200.0, 2400.0],
                [1210.0, 2410.0],
                [1220.0, 2420.0],
                [1215.0, 2415.0],
                [1225.0, 2430.0],
            ],
            index=dates,
            columns=cols,
        )
        mock_download.return_value = mock_df

        rows, succ, fail = fetch_yahoo_historical_data(["RELIANCE.NS", "TCS.NS"], period="1mo")

        assert len(rows) == 10
        assert "RELIANCE.NS" in succ
        assert "TCS.NS" in succ
        assert fail == []
        assert rows[0].symbol in ["RELIANCE.NS", "TCS.NS"]
        assert isinstance(rows[0].adjusted_close, Decimal)

    @patch("app.market_fetcher.yf.Ticker")
    def test_fetch_live_quote_mock(self, mock_ticker):
        mock_instance = MagicMock()
        mock_fast_info = MagicMock()
        mock_fast_info.last_price = 1250.50
        mock_fast_info.currency = "INR"
        mock_fast_info.previous_close = 1240.00
        mock_instance.fast_info = mock_fast_info
        mock_ticker.return_value = mock_instance

        quote = fetch_live_quote("RELIANCE.NS")
        assert quote is not None
        assert quote["symbol"] == "RELIANCE.NS"
        assert quote["last_price"] == Decimal("1250.5000")
        assert quote["currency"] == "INR"
        assert quote["change"] == Decimal("10.5000")


class TestMarketDataEndpoints:
    """Integration tests for the market data endpoints."""

    def test_get_market_presets(self, db_client: TestClient):
        response = db_client.get("/market-data/presets")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        ids = [p["id"] for p in data]
        assert "nifty_top5" in ids
        assert "us_tech_megacap" in ids

    @patch("app.optimization_router.fetch_yahoo_historical_data")
    def test_fetch_historical_endpoint(self, mock_fetch, db_client: TestClient):
        from app.optimization_schemas import HistoricalPriceRow

        sample_rows = [
            HistoricalPriceRow(
                date=date(2026, 1, 1),
                symbol="RELIANCE.NS",
                adjusted_close=Decimal("1200.00"),
            ),
            HistoricalPriceRow(
                date=date(2026, 1, 2),
                symbol="RELIANCE.NS",
                adjusted_close=Decimal("1210.00"),
            ),
        ]
        mock_fetch.return_value = (sample_rows, ["RELIANCE.NS"], [])

        payload = {"symbols": ["RELIANCE.NS"], "period": "1y"}
        response = db_client.post("/market-data/yfinance/fetch-historical", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["imported_rows"] == 2
        assert "RELIANCE.NS" in data["symbols_successful"]

    @patch("app.optimization_router.fetch_live_quotes")
    def test_get_quotes_endpoint(self, mock_quotes, db_client: TestClient):
        mock_quotes.return_value = {
            "RELIANCE.NS": {
                "symbol": "RELIANCE.NS",
                "last_price": Decimal("1250.00"),
                "currency": "INR",
                "previous_close": Decimal("1240.00"),
                "change": Decimal("10.00"),
                "change_percent": Decimal("0.81"),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }
        }

        payload = {"symbols": ["RELIANCE.NS"]}
        response = db_client.post("/market-data/quotes", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert "RELIANCE.NS" in data["quotes"]
        assert float(data["quotes"]["RELIANCE.NS"]["last_price"]) == 1250.0

    @patch("app.optimization_router.fetch_live_quotes")
    def test_sync_portfolio_live_prices(self, mock_quotes, db_client: TestClient):
        # Create a portfolio with an asset and holding
        portfolio_payload = {
            "name": "Live Sync Portfolio",
            "description": "Testing live market price sync",
            "base_currency": "INR",
        }
        res_p = db_client.post("/portfolios/", json=portfolio_payload)
        assert res_p.status_code == 201
        port_id = res_p.json()["id"]

        asset_payload = {
            "name": "Reliance Industries",
            "symbol": "RELIANCE.NS",
            "asset_class": "equity",
            "currency": "INR",
        }
        res_a = db_client.post("/assets", json=asset_payload)
        assert res_a.status_code == 201
        asset_id = res_a.json()["id"]

        holding_payload = {
            "asset_id": asset_id,
            "quantity": 10,
            "average_purchase_price": 1100.0,
            "current_price": 1150.0,
        }
        res_h = db_client.post(f"/portfolios/{port_id}/holdings", json=holding_payload)
        assert res_h.status_code == 201

        # Mock quote
        mock_quotes.return_value = {
            "RELIANCE.NS": {
                "symbol": "RELIANCE.NS",
                "last_price": Decimal("1280.00"),
                "currency": "INR",
                "previous_close": Decimal("1250.00"),
            }
        }

        # Sync
        res_sync = db_client.post(f"/portfolios/{port_id}/sync-market-prices")
        assert res_sync.status_code == 200
        sync_data = res_sync.json()
        assert sync_data["synced_count"] == 1
        assert len(sync_data["updated_holdings"]) == 1
        assert float(sync_data["updated_holdings"][0]["new_price"]) == 1280.0
