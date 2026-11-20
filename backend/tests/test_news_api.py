"""
Integration tests for Phase 10 FastAPI News Intelligence & Sentiment Analysis endpoints.

Verifies:
- GET /news: Pagination, sentiment filtering, search query
- GET /news/{article_id}: Retrieval of article metadata & 404 handling
- POST /news/refresh: Bounded ingestion and batch summary report
- GET /news/sentiment/summary: Aggregation metrics and sector breakdowns
- GET /news/portfolio-relevance: User portfolio matching (authenticated)
- POST /news/portfolio-insights: Thematic summaries & regulatory disclaimers
"""

from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db.base import Base
from app.db.models import (
    AssetModel,
    NewsArticleModel,
    NewsSourceModel,
    PortfolioHoldingModel,
    PortfolioModel,
    UserModel,
)
from app.db.session import get_db
from app.main import app

NEWS_TEST_USER = UserModel(
    id="news-test-user-uuid-1",
    email="news_user@example.com",
    password_hash="mockhash",
    is_active=True,
)


@pytest.fixture()
def db_session() -> Session:
    """Isolated in-memory database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()

    # Pre-populate test user
    session.add(
        UserModel(
            id=NEWS_TEST_USER.id,
            email=NEWS_TEST_USER.email,
            password_hash=NEWS_TEST_USER.password_hash,
            is_active=True,
        )
    )
    session.commit()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session: Session) -> TestClient:
    """FastAPI TestClient wired to the test session and authenticated test user."""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: NEWS_TEST_USER

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture()
def seed_news_data(db_session: Session) -> dict[str, object]:
    """Seed test sources and articles."""
    src = NewsSourceModel(
        id=str(uuid.uuid4()),
        name="Reuters Finance",
        feed_url="https://reuters.com/rss/finance.xml",
        is_active=True,
    )
    db_session.add(src)
    db_session.flush()

    art1 = NewsArticleModel(
        id="art-uuid-1",
        source_id=src.id,
        title="NVIDIA (NVDA) Surges on Massive Cloud AI Semiconductor Gain",
        canonical_url="https://reuters.com/nvda-gain.html",
        summary="NVDA shares rallied 8% after reporting bullish net income beat in enterprise cloud AI.",
        published_at=datetime.now(timezone.utc),
        headline_hash="hash-nvda-1",
        sentiment_label="positive",
        sentiment_score=Decimal("0.8500"),
        sentiment_probabilities={"positive": 0.85, "negative": 0.05, "neutral": 0.10},
        sentiment_model="MockFinancialSentiment:v1.0",
    )
    art2 = NewsArticleModel(
        id="art-uuid-2",
        source_id=src.id,
        title="Crude Oil Prices Drop Amid Global Demand Decline",
        canonical_url="https://reuters.com/oil-drop.html",
        summary="Energy sector facing margin headwinds and persistent inventory builds.",
        published_at=datetime.now(timezone.utc),
        headline_hash="hash-oil-2",
        sentiment_label="negative",
        sentiment_score=Decimal("-0.7000"),
        sentiment_probabilities={"positive": 0.10, "negative": 0.70, "neutral": 0.20},
        sentiment_model="MockFinancialSentiment:v1.0",
    )
    db_session.add_all([art1, art2])
    db_session.commit()
    return {"source": src, "articles": [art1, art2]}


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------

class TestNewsArticlesAPI:
    """Tests for public article browsing, filtering, and single retrieval."""

    def test_list_news_articles(self, client: TestClient, seed_news_data):
        r = client.get("/news")
        assert r.status_code == 200
        data = r.json()
        assert data["total_count"] == 2
        assert len(data["articles"]) == 2
        assert data["limit"] == 50
        assert data["offset"] == 0

    def test_list_news_articles_filtered_by_sentiment(self, client: TestClient, seed_news_data):
        r = client.get("/news?sentiment_label=positive")
        assert r.status_code == 200
        data = r.json()
        assert data["total_count"] == 1
        assert data["articles"][0]["id"] == "art-uuid-1"
        assert data["articles"][0]["sentiment_label"] == "positive"

    def test_list_news_articles_search(self, client: TestClient, seed_news_data):
        r = client.get("/news?search=NVIDIA")
        assert r.status_code == 200
        data = r.json()
        assert len(data["articles"]) == 1
        assert "NVIDIA" in data["articles"][0]["title"]

    def test_get_single_news_article(self, client: TestClient, seed_news_data):
        r = client.get("/news/art-uuid-1")
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "art-uuid-1"
        assert data["source_name"] == "Reuters Finance"
        assert data["sentiment_label"] == "positive"
        assert float(data["sentiment_score"]) == 0.85

    def test_get_single_news_article_not_found(self, client: TestClient, seed_news_data):
        r = client.get("/news/non-existent-article-uuid")
        assert r.status_code == 404
        assert "not found" in r.json()["detail"]


class TestNewsRefreshAndSentimentAPI:
    """Tests for feed refresh ingestion and aggregated market sentiment metrics."""

    def test_news_refresh_endpoint(self, client: TestClient):
        r = client.post("/news/refresh", json={"force": True})
        assert r.status_code == 200
        data = r.json()
        assert "started_at" in data
        assert "completed_at" in data
        assert data["sources_polled"] >= 1
        assert isinstance(data["source_reports"], list)

    def test_get_sentiment_summary(self, client: TestClient, seed_news_data):
        r = client.get("/news/sentiment/summary?time_window=24h")
        assert r.status_code == 200
        data = r.json()
        assert data["time_window"] == "24h"
        assert data["total_articles"] == 2
        assert data["positive_count"] == 1
        assert data["negative_count"] == 1
        assert data["neutral_count"] == 0
        assert data["positive_percentage"] == 50.0
        assert data["negative_percentage"] == 50.0
        assert isinstance(data["sector_breakdown"], list)


class TestPortfolioNewsRelevanceAndInsightsAPI:
    """Tests for authenticated portfolio relevance matching and decision support insights."""

    def test_portfolio_news_relevance(self, client: TestClient, db_session: Session, seed_news_data):
        # Create a portfolio holding NVDA
        portfolio = PortfolioModel(
            id=str(uuid.uuid4()),
            user_id=NEWS_TEST_USER.id,
            name="AI & Semiconductors",
            base_currency="USD",
        )
        asset_nvda = AssetModel(
            id=str(uuid.uuid4()),
            user_id=NEWS_TEST_USER.id,
            symbol="NVDA",
            name="NVIDIA Corporation",
            asset_class="equity",
            instrument_type="Technology",
        )
        db_session.add_all([portfolio, asset_nvda])
        db_session.flush()

        holding = PortfolioHoldingModel(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio.id,
            asset_id=asset_nvda.id,
            quantity=Decimal("15"),
            average_purchase_price=Decimal("120.00"),
        )
        db_session.add(holding)
        db_session.commit()

        r = client.get("/news/portfolio-relevance")
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == NEWS_TEST_USER.id
        assert data["matches_count"] >= 1

        matches = data["matches"]
        assert any(m["matched_entity"] in {"NVDA", "NVIDIA Corporation", "Technology"} for m in matches)

    def test_portfolio_news_insights(self, client: TestClient, db_session: Session, seed_news_data):
        # Create a portfolio
        portfolio = PortfolioModel(
            id=str(uuid.uuid4()),
            user_id=NEWS_TEST_USER.id,
            name="Wealth Portfolio",
            base_currency="USD",
        )
        asset = AssetModel(
            id=str(uuid.uuid4()),
            user_id=NEWS_TEST_USER.id,
            symbol="NVDA",
            name="NVIDIA Corporation",
            asset_class="equity",
            instrument_type="Technology",
        )
        db_session.add_all([portfolio, asset])
        db_session.flush()

        holding = PortfolioHoldingModel(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio.id,
            asset_id=asset.id,
            quantity=Decimal("30"),
            average_purchase_price=Decimal("110.00"),
        )
        db_session.add(holding)
        db_session.commit()

        r = client.post("/news/portfolio-insights")
        assert r.status_code == 200
        data = r.json()
        assert data["user_id"] == NEWS_TEST_USER.id
        assert data["portfolio_name"] == "Wealth Portfolio"
        assert "executive_summary" in data
        assert isinstance(data["themes"], list)
        assert len(data["disclaimers"]) >= 1
        assert any("decision-support" in d.lower() or "investment advice" in d.lower() for d in data["disclaimers"])
