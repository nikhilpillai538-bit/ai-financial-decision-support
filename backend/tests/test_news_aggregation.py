"""
Unit and integration tests for Phase 10 Market Sentiment Aggregation.

Verifies:
- 24h, 7d, and 30d time window calculations
- Proportion calculations (positive, negative, neutral percentages)
- Net compound sentiment score calculation
- Bullish, bearish, and neutral market labeling thresholds
- Low sample size caveats for < 5 articles
- Empty window handling with zeroed metrics and clean warning
- Sector-level sentiment breakdown
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import NewsArticleModel, NewsSourceModel
from app.news.aggregation import MarketSentimentAggregator, MarketSentimentSummary


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
def sample_source(db_session: Session) -> NewsSourceModel:
    source = NewsSourceModel(
        id=str(uuid.uuid4()),
        name="Yahoo Finance",
        feed_url="https://feeds.finance.yahoo.com/rss/headlines",
        is_active=True,
    )
    db_session.add(source)
    db_session.commit()
    return source


class TestMarketSentimentAggregation:
    """Tests for aggregating news sentiment across time windows and sectors."""

    def test_empty_window_handling(self, db_session: Session):
        aggregator = MarketSentimentAggregator(db_session)
        summary = aggregator.aggregate(time_window="24h")

        assert isinstance(summary, MarketSentimentSummary)
        assert summary.total_articles == 0
        assert summary.positive_count == 0
        assert summary.negative_count == 0
        assert summary.neutral_count == 0
        assert summary.average_sentiment_score == 0.0
        assert summary.overall_sentiment_label == "neutral"
        assert len(summary.warnings) == 1
        assert "No financial news articles found" in summary.warnings[0]

    def test_low_sample_size_warning(self, db_session: Session, sample_source: NewsSourceModel):
        now = datetime.now(timezone.utc)
        # Create 3 articles (< 5 sample size threshold)
        for i in range(3):
            art = NewsArticleModel(
                id=str(uuid.uuid4()),
                source_id=sample_source.id,
                title=f"Sample News Article {i}",
                canonical_url=f"https://feeds.finance.yahoo.com/news/sample-{i}.html",
                published_at=now - timedelta(hours=2),
                headline_hash=f"hash-{i}",
                sentiment_label="positive",
                sentiment_score=Decimal("0.7500"),
            )
            db_session.add(art)
        db_session.commit()

        aggregator = MarketSentimentAggregator(db_session)
        summary = aggregator.aggregate(time_window="24h")

        assert summary.total_articles == 3
        assert summary.positive_count == 3
        assert summary.positive_percentage == 100.0
        assert any("Low sample size" in w for w in summary.warnings)

    def test_bullish_market_aggregation(self, db_session: Session, sample_source: NewsSourceModel):
        now = datetime.now(timezone.utc)
        # 10 articles: 7 positive, 1 negative, 2 neutral
        labels = ["positive"] * 7 + ["negative"] * 1 + ["neutral"] * 2
        for i, lbl in enumerate(labels):
            art = NewsArticleModel(
                id=str(uuid.uuid4()),
                source_id=sample_source.id,
                title=f"Headline {i} about market rally or move",
                canonical_url=f"https://feeds.finance.yahoo.com/news/rally-{i}.html",
                published_at=now - timedelta(hours=i + 1),
                headline_hash=f"hash-rally-{i}",
                sentiment_label=lbl,
                sentiment_score=Decimal("0.8000") if lbl == "positive" else (Decimal("-0.8000") if lbl == "negative" else Decimal("0.0")),
            )
            db_session.add(art)
        db_session.commit()

        aggregator = MarketSentimentAggregator(db_session)
        summary = aggregator.aggregate(time_window="24h")

        assert summary.total_articles == 10
        assert summary.positive_count == 7
        assert summary.negative_count == 1
        assert summary.neutral_count == 2
        assert summary.positive_percentage == 70.0
        assert summary.negative_percentage == 10.0
        assert summary.neutral_percentage == 20.0
        # (7 - 1) / 10 = 0.60
        assert pytest.approx(summary.average_sentiment_score, 0.001) == 0.60
        assert summary.overall_sentiment_label == "bullish"
        assert not any("Low sample size" in w for w in summary.warnings)

    def test_bearish_market_aggregation(self, db_session: Session, sample_source: NewsSourceModel):
        now = datetime.now(timezone.utc)
        # 8 articles: 1 positive, 6 negative, 1 neutral
        labels = ["positive"] * 1 + ["negative"] * 6 + ["neutral"] * 1
        for i, lbl in enumerate(labels):
            art = NewsArticleModel(
                id=str(uuid.uuid4()),
                source_id=sample_source.id,
                title=f"Article {i} on economic downturn and drop",
                canonical_url=f"https://feeds.finance.yahoo.com/news/drop-{i}.html",
                published_at=now - timedelta(hours=i + 1),
                headline_hash=f"hash-drop-{i}",
                sentiment_label=lbl,
                sentiment_score=Decimal("-0.7500") if lbl == "negative" else Decimal("0.7500"),
            )
            db_session.add(art)
        db_session.commit()

        aggregator = MarketSentimentAggregator(db_session)
        summary = aggregator.aggregate(time_window="24h")

        assert summary.total_articles == 8
        assert summary.positive_count == 1
        assert summary.negative_count == 6
        # (1 - 6) / 8 = -0.625
        assert pytest.approx(summary.average_sentiment_score, 0.001) == -0.625
        assert summary.overall_sentiment_label == "bearish"

    def test_time_window_filtering(self, db_session: Session, sample_source: NewsSourceModel):
        now = datetime.now(timezone.utc)

        # Article from 5 hours ago (in 24h and 7d)
        art_recent = NewsArticleModel(
            id=str(uuid.uuid4()),
            source_id=sample_source.id,
            title="Recent Tech Rally",
            canonical_url="https://feeds.finance.yahoo.com/recent.html",
            published_at=now - timedelta(hours=5),
            headline_hash="hash-recent",
            sentiment_label="positive",
            sentiment_score=Decimal("0.7000"),
        )
        # Article from 3 days ago (outside 24h, inside 7d)
        art_older = NewsArticleModel(
            id=str(uuid.uuid4()),
            source_id=sample_source.id,
            title="Older Earnings Report",
            canonical_url="https://feeds.finance.yahoo.com/older.html",
            published_at=now - timedelta(days=3),
            headline_hash="hash-older",
            sentiment_label="negative",
            sentiment_score=Decimal("-0.6000"),
        )
        db_session.add_all([art_recent, art_older])
        db_session.commit()

        aggregator = MarketSentimentAggregator(db_session)

        summary_24h = aggregator.aggregate(time_window="24h")
        assert summary_24h.total_articles == 1
        assert summary_24h.positive_count == 1

        summary_7d = aggregator.aggregate(time_window="7d")
        assert summary_7d.total_articles == 2
        assert summary_7d.positive_count == 1
        assert summary_7d.negative_count == 1

    def test_sector_breakdown(self, db_session: Session, sample_source: NewsSourceModel):
        now = datetime.now(timezone.utc)
        # 3 Technology articles, 2 Healthcare articles
        tech1 = NewsArticleModel(
            id=str(uuid.uuid4()),
            source_id=sample_source.id,
            title="Cloud Software Demand Accelerates for Tech Giants",
            canonical_url="https://feeds.finance.yahoo.com/tech1.html",
            summary="Enterprise cloud architecture software contracts surged.",
            published_at=now - timedelta(hours=1),
            headline_hash="tech1-hash",
            sentiment_label="positive",
            sentiment_score=Decimal("0.8500"),
        )
        tech2 = NewsArticleModel(
            id=str(uuid.uuid4()),
            source_id=sample_source.id,
            title="Semiconductor Chipmakers Expand Production Capacity",
            canonical_url="https://feeds.finance.yahoo.com/tech2.html",
            summary="Hardware AI semiconductors saw robust orders.",
            published_at=now - timedelta(hours=2),
            headline_hash="tech2-hash",
            sentiment_label="positive",
            sentiment_score=Decimal("0.8000"),
        )
        health1 = NewsArticleModel(
            id=str(uuid.uuid4()),
            source_id=sample_source.id,
            title="Biotech Firm Receives FDA Approval for Oncology Drug",
            canonical_url="https://feeds.finance.yahoo.com/health1.html",
            summary="Healthcare pharma developer achieved clinical medical milestone.",
            published_at=now - timedelta(hours=3),
            headline_hash="health1-hash",
            sentiment_label="positive",
            sentiment_score=Decimal("0.9000"),
        )
        db_session.add_all([tech1, tech2, health1])
        db_session.commit()

        aggregator = MarketSentimentAggregator(db_session)
        summary = aggregator.aggregate(time_window="24h")

        sectors = {s.sector: s for s in summary.sector_breakdown}
        assert "Technology" in sectors
        assert sectors["Technology"].article_count == 2
        assert sectors["Technology"].positive_percentage == 100.0

        assert "Healthcare" in sectors
        assert sectors["Healthcare"].article_count == 1
