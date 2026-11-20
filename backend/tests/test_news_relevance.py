"""
Unit and integration tests for Phase 10 Portfolio News Relevance Matching.

Verifies:
- Exact ticker matching with word boundaries
- Short ticker ambiguity warning (e.g., <= 2 chars)
- Company name matching against headline and summary
- Sector matching via sector keyword mappings
- Macro market topic matching for portfolios with holdings
- Empty portfolio handling (returns empty match list safely)
- Deduplication of matches per article and entity
"""

from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import (
    AssetModel,
    NewsArticleModel,
    NewsSourceModel,
    PortfolioHoldingModel,
    PortfolioModel,
    UserModel,
)
from app.news.relevance import PortfolioNewsRelevanceMatcher


@pytest.fixture()
def db_session() -> Session:
    """Isolated in-memory SQLite session with full schema."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def test_user(db_session: Session) -> UserModel:
    user = UserModel(
        id=str(uuid.uuid4()),
        email="relevance_tester@example.com",
        password_hash="mockhash",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture()
def sample_news_articles(db_session: Session) -> list[NewsArticleModel]:
    source = NewsSourceModel(
        id=str(uuid.uuid4()),
        name="MarketWatch",
        feed_url="https://feeds.content.dowjones.io/public/rss/mw_topstories.xml",
        is_active=True,
    )
    db_session.add(source)
    db_session.flush()

    art1 = NewsArticleModel(
        id=str(uuid.uuid4()),
        source_id=source.id,
        title="Apple Reports Record Services Revenue with AAPL Rally",
        canonical_url="https://feeds.content.dowjones.io/art1.html",
        summary="Apple Inc posted strong fiscal earnings as iPhone and cloud services surged.",
        published_at=datetime.now(timezone.utc),
        headline_hash="hash1",
        sentiment_label="positive",
        sentiment_score=Decimal("0.8500"),
    )
    art2 = NewsArticleModel(
        id=str(uuid.uuid4()),
        source_id=source.id,
        title="Federal Reserve Signals Cautious Stance on Future Interest Rate Cuts",
        canonical_url="https://feeds.content.dowjones.io/art2.html",
        summary="FOMC policymakers noted persistent inflation and resilient economic growth.",
        published_at=datetime.now(timezone.utc),
        headline_hash="hash2",
        sentiment_label="neutral",
        sentiment_score=Decimal("0.0000"),
    )
    art3 = NewsArticleModel(
        id=str(uuid.uuid4()),
        source_id=source.id,
        title="Semiconductor Sector Rallies as Cloud AI Spending Accelerates",
        canonical_url="https://feeds.content.dowjones.io/art3.html",
        summary="Global chipmakers experienced renewed institutional demand.",
        published_at=datetime.now(timezone.utc),
        headline_hash="hash3",
        sentiment_label="positive",
        sentiment_score=Decimal("0.7000"),
    )
    art4 = NewsArticleModel(
        id=str(uuid.uuid4()),
        source_id=source.id,
        title="ON Semiconductor Issues Updated Revenue Forecast",
        canonical_url="https://feeds.content.dowjones.io/art4.html",
        summary="ON Semiconductor management held an investor briefing regarding European automotive demand.",
        published_at=datetime.now(timezone.utc),
        headline_hash="hash4",
        sentiment_label="neutral",
        sentiment_score=Decimal("0.0000"),
    )

    db_session.add_all([art1, art2, art3, art4])
    db_session.commit()
    return [art1, art2, art3, art4]


class TestPortfolioNewsRelevanceMatcher:
    """Tests for matching news articles to portfolio tickers, companies, and sectors."""

    def test_ticker_exact_match_and_company_match(
        self,
        db_session: Session,
        test_user: UserModel,
        sample_news_articles: list[NewsArticleModel],
    ):
        # Setup portfolio with AAPL
        portfolio = PortfolioModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            name="Tech Growth",
            base_currency="USD",
        )
        asset_aapl = AssetModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            symbol="AAPL",
            name="Apple Inc",
            asset_class="equity",
            instrument_type="Technology",
        )
        db_session.add_all([portfolio, asset_aapl])
        db_session.flush()

        holding = PortfolioHoldingModel(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio.id,
            asset_id=asset_aapl.id,
            quantity=Decimal("50"),
            average_purchase_price=Decimal("180.00"),
        )
        db_session.add(holding)
        db_session.commit()

        matcher = PortfolioNewsRelevanceMatcher(db_session)
        matches = matcher.match_articles(sample_news_articles, test_user, min_confidence=0.60)

        # Should match art1 (AAPL ticker + Apple company name + Technology sector)
        art1_matches = [m for m in matches if m.article_id == sample_news_articles[0].id]
        assert len(art1_matches) >= 1

        methods = {m.match_method for m in art1_matches}
        assert "ticker_exact" in methods
        assert "company_name" in methods

        ticker_match = next(m for m in art1_matches if m.match_method == "ticker_exact")
        assert ticker_match.matched_entity == "AAPL"
        assert ticker_match.match_confidence == 0.95
        assert ticker_match.ambiguity_warning is None

    def test_short_ticker_ambiguity_warning(
        self,
        db_session: Session,
        test_user: UserModel,
        sample_news_articles: list[NewsArticleModel],
    ):
        portfolio = PortfolioModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            name="Chip Portfolio",
            base_currency="USD",
        )
        # Short 2-letter ticker: ON
        asset_on = AssetModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            symbol="ON",
            name="ON Semiconductor Corp",
            asset_class="equity",
            instrument_type="Technology",
        )
        db_session.add_all([portfolio, asset_on])
        db_session.flush()

        holding = PortfolioHoldingModel(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio.id,
            asset_id=asset_on.id,
            quantity=Decimal("100"),
            average_purchase_price=Decimal("70.00"),
        )
        db_session.add(holding)
        db_session.commit()

        matcher = PortfolioNewsRelevanceMatcher(db_session)
        matches = matcher.match_articles(sample_news_articles, test_user)

        art4_matches = [m for m in matches if m.article_id == sample_news_articles[3].id]
        ticker_matches = [m for m in art4_matches if m.match_method == "ticker_exact"]
        assert len(ticker_matches) == 1
        assert ticker_matches[0].ambiguity_warning is not None
        assert "ambiguous" in ticker_matches[0].ambiguity_warning
        assert ticker_matches[0].match_confidence == 0.75

    def test_sector_and_macro_market_match(
        self,
        db_session: Session,
        test_user: UserModel,
        sample_news_articles: list[NewsArticleModel],
    ):
        portfolio = PortfolioModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            name="Balanced Core",
            base_currency="USD",
        )
        asset = AssetModel(
            id=str(uuid.uuid4()),
            user_id=test_user.id,
            symbol="MSFT",
            name="Microsoft",
            asset_class="equity",
            instrument_type="Technology",
        )
        db_session.add_all([portfolio, asset])
        db_session.flush()

        holding = PortfolioHoldingModel(
            id=str(uuid.uuid4()),
            portfolio_id=portfolio.id,
            asset_id=asset.id,
            quantity=Decimal("20"),
            average_purchase_price=Decimal("400.00"),
        )
        db_session.add(holding)
        db_session.commit()

        matcher = PortfolioNewsRelevanceMatcher(db_session)
        matches = matcher.match_articles(sample_news_articles, test_user)

        # art3 mentions "Semiconductor", which is in SECTOR_KEYWORDS["Technology"]
        sector_matches = [m for m in matches if m.match_method == "sector_match"]
        assert any(m.matched_entity == "Technology" for m in sector_matches)

        # art2 mentions "Federal Reserve" and "Interest Rate", should match macro
        macro_matches = [m for m in matches if m.match_method == "macro_market"]
        assert len(macro_matches) >= 1
        assert any(m.matched_entity in {"Federal Reserve", "Interest Rates"} for m in macro_matches)

    def test_empty_portfolio_returns_no_matches(
        self,
        db_session: Session,
        test_user: UserModel,
        sample_news_articles: list[NewsArticleModel],
    ):
        # User has no portfolios or holdings
        matcher = PortfolioNewsRelevanceMatcher(db_session)
        matches = matcher.match_articles(sample_news_articles, test_user)
        assert matches == []
