"""
Unit and integration tests for Phase 10 News Ingestion and Feed Adapters.

Verifies:
- SSRF prevention (IP filtering, scheme verification, domain allowlisting)
- Canonical URL normalization (query tracking stripping)
- Headline hash generation (SHA-256 deduplication)
- RSS 2.0 and Atom XML parsing
- Malformed feed error resilience
- Fallback for missing publication dates
- NewsIngestionService batch polling and deduplication
"""

from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.models import NewsArticleModel, NewsSourceModel
from app.db.repositories.news_repo import SQLNewsRepository
from app.news.adapters import (
    MockNewsFeedAdapter,
    ParsedArticleItem,
    RSSFeedAdapter,
    compute_headline_hash,
    normalize_canonical_url,
    validate_feed_url,
)
from app.news.config import NewsSettings
from app.news.ingestion import NewsIngestionService
from app.news.sentiment import MockSentimentAnalyzer


# ---------------------------------------------------------------------------
# SSRF & URL Normalization Tests
# ---------------------------------------------------------------------------

class TestSSRFAndURLValidation:
    """Tests for URL security, SSRF defense, and canonical URL normalization."""

    @pytest.fixture()
    def allowed_domains(self) -> set[str]:
        return {
            "feeds.finance.yahoo.com",
            "www.federalreserve.gov",
            "www.sec.gov",
            "feeds.content.dowjones.io",
            "reuters.com",
        }

    def test_valid_approved_url(self, allowed_domains):
        valid_url = "https://www.federalreserve.gov/feeds/press_all.xml"
        assert validate_feed_url(valid_url, allowed_domains=allowed_domains) is True

    def test_reject_unapproved_domain(self, allowed_domains):
        unapproved_url = "https://evil-untrusted-domain.com/feed.xml"
        assert validate_feed_url(unapproved_url, allowed_domains=allowed_domains) is False

    def test_reject_localhost_ssrf(self, allowed_domains):
        assert validate_feed_url("http://localhost:8000/feed.xml", allowed_domains=allowed_domains) is False
        assert validate_feed_url("http://127.0.0.1:8000/feed.xml", allowed_domains=allowed_domains) is False
        assert validate_feed_url("http://0.0.0.0:8000/feed.xml", allowed_domains=allowed_domains) is False

    def test_reject_private_network_ips(self, allowed_domains):
        private_ips = [
            "http://10.0.0.1/feed",
            "http://192.168.1.100/rss",
            "http://172.16.0.5/feed.xml",
            "http://169.254.169.254/latest/meta-data",  # Cloud metadata
        ]
        for url in private_ips:
            assert validate_feed_url(url, allowed_domains=allowed_domains) is False

    def test_reject_dangerous_schemes(self, allowed_domains):
        dangerous_urls = [
            "file:///etc/passwd",
            "ftp://ftp.example.com/rss",
            "gopher://example.com/feed",
            "javascript:alert(1)",
        ]
        for url in dangerous_urls:
            assert validate_feed_url(url, allowed_domains=allowed_domains) is False

    def test_normalize_canonical_url_strips_tracking(self):
        url_with_tracking = (
            "https://feeds.finance.yahoo.com/news/tech-rally.html"
            "?utm_source=twitter&utm_medium=social&utm_campaign=daily&fbclid=XYZ123&ref=home"
        )
        canonical = normalize_canonical_url(url_with_tracking)
        assert canonical == "https://feeds.finance.yahoo.com/news/tech-rally.html"

    def test_normalize_canonical_url_preserves_content_params(self):
        url_with_content_params = "https://www.sec.gov/news/press-release?id=2024-101&section=markets"
        canonical = normalize_canonical_url(url_with_content_params)
        assert "id=2024-101" in canonical
        assert "section=markets" in canonical

    def test_compute_headline_hash_deterministic(self):
        h1 = compute_headline_hash("Tech Stocks Surge on Strong AI Earnings")
        h2 = compute_headline_hash("   tech  stocks   surge on strong AI earnings   ")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex length

        h3 = compute_headline_hash("Federal Reserve Holds Interest Rates Steady")
        assert h1 != h3


# ---------------------------------------------------------------------------
# RSS & Atom Parsing Tests
# ---------------------------------------------------------------------------

class TestFeedParsing:
    """Tests for parsing standard RSS 2.0 and Atom XML feeds."""

    def test_parse_rss_2_0_xml(self):
        rss_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <title>Financial Feed</title>
                <item>
                    <title>Apple reports record services revenue</title>
                    <link>https://finance.yahoo.com/news/apple-services-revenue-1.html</link>
                    <description>Apple quarterly results top expectations driven by cloud and App Store.</description>
                    <pubDate>Wed, 15 Oct 2025 14:30:00 GMT</pubDate>
                </item>
                <item>
                    <title>Federal Reserve signals cautious interest rate path</title>
                    <link>https://finance.yahoo.com/news/fed-signals-path-2.html</link>
                    <description>Fed officials emphasize inflation data dependence.</description>
                    <pubDate>Wed, 15 Oct 2025 15:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""

        adapter = RSSFeedAdapter()
        items = adapter.parse_xml(rss_xml, source_name="Yahoo Finance")
        assert len(items) == 2

        item1 = items[0]
        assert item1.title == "Apple reports record services revenue"
        assert item1.canonical_url == "https://finance.yahoo.com/news/apple-services-revenue-1.html"
        assert "cloud and App Store" in item1.summary
        assert item1.source_name == "Yahoo Finance"
        assert item1.published_at.year == 2025

    def test_parse_atom_xml(self):
        atom_xml = b"""<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Fed Press Releases</title>
            <entry>
                <title>FOMC Statement on Monetary Policy</title>
                <link rel="alternate" href="https://www.federalreserve.gov/newsevents/pressreleases/monetary20251015a.htm"/>
                <id>urn:fed:release:20251015a</id>
                <published>2025-10-15T18:00:00Z</published>
                <summary>The Federal Open Market Committee decided today to maintain the target range for federal funds.</summary>
            </entry>
        </feed>"""

        adapter = RSSFeedAdapter()
        items = adapter.parse_xml(atom_xml, source_name="Federal Reserve")
        assert len(items) == 1
        item = items[0]
        assert item.title == "FOMC Statement on Monetary Policy"
        assert "federalreserve.gov" in item.canonical_url
        assert "target range" in item.summary
        assert item.published_at.year == 2025

    def test_parse_missing_pub_date_handled(self):
        rss_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rss version="2.0">
            <channel>
                <item>
                    <title>Market Wrap: Indices close mixed</title>
                    <link>https://finance.yahoo.com/news/market-wrap-3.html</link>
                    <description>S&amp;P 500 flat while Nasdaq advances.</description>
                </item>
            </channel>
        </rss>"""

        adapter = RSSFeedAdapter()
        items = adapter.parse_xml(rss_xml, source_name="Yahoo Finance")
        assert len(items) == 1
        assert items[0].title == "Market Wrap: Indices close mixed"
        # When pubDate is omitted in RSS, published_at is None
        assert items[0].published_at is None

    def test_parse_malformed_xml_returns_empty_safely(self):
        bad_xml = b"<rss><channel><item><title>Broken XML"
        adapter = RSSFeedAdapter()
        items = adapter.parse_xml(bad_xml, source_name="Broken Feed")
        assert items == []


# ---------------------------------------------------------------------------
# Ingestion Service & Deduplication Tests
# ---------------------------------------------------------------------------

class TestNewsIngestionService:
    """Tests for feed polling, deduplication, and persistence."""

    @pytest.fixture()
    def db_session(self):
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

    def test_ingestion_service_deduplicates_by_url_and_hash(self, db_session):
        import asyncio

        repo = SQLNewsRepository(db_session)
        source = repo.create_source(
            name="Mock Feed Source",
            feed_url="https://feeds.finance.yahoo.com/rss/mock.xml",
            is_active=True,
        )

        test_articles = [
            ParsedArticleItem(
                title="NVIDIA Unveils New Next-Gen AI Chip Architecture",
                canonical_url="https://feeds.finance.yahoo.com/news/nvda-chip-1.html",
                headline_hash=compute_headline_hash("NVIDIA Unveils New Next-Gen AI Chip Architecture"),
                summary="NVIDIA announced its latest Blackwell Ultra architecture for AI training.",
                published_at=datetime.now(timezone.utc),
                source_name="Mock Feed Source",
            ),
            ParsedArticleItem(
                title="Federal Reserve Signals Slower Balance Sheet Runoff",
                canonical_url="https://feeds.finance.yahoo.com/news/fed-runoff-2.html",
                headline_hash=compute_headline_hash("Federal Reserve Signals Slower Balance Sheet Runoff"),
                summary="Federal Reserve policymakers considered slowing quantitative tightening.",
                published_at=datetime.now(timezone.utc),
                source_name="Mock Feed Source",
            ),
            ParsedArticleItem(
                # Duplicate canonical URL
                title="NVIDIA Announces Architecture Update",
                canonical_url="https://feeds.finance.yahoo.com/news/nvda-chip-1.html",
                headline_hash=compute_headline_hash("NVIDIA Announces Architecture Update"),
                summary="Another syndicated article with same URL.",
                published_at=datetime.now(timezone.utc),
                source_name="Mock Feed Source",
            ),
            ParsedArticleItem(
                # Duplicate headline hash with different URL
                title="NVIDIA Unveils New Next-Gen AI Chip Architecture",
                canonical_url="https://feeds.finance.yahoo.com/news/nvda-chip-mirrored.html",
                headline_hash=compute_headline_hash("NVIDIA Unveils New Next-Gen AI Chip Architecture"),
                summary="Mirror with identical headline.",
                published_at=datetime.now(timezone.utc),
                source_name="Mock Feed Source",
            ),
        ]

        mock_adapter = MockNewsFeedAdapter(sample_articles=test_articles)
        sentiment_analyzer = MockSentimentAnalyzer()
        service = NewsIngestionService(
            session=db_session,
            adapter=mock_adapter,
            sentiment_analyzer=sentiment_analyzer,
        )

        batch_report = asyncio.run(service.refresh_feeds(source_id=source.id, force=True))
        assert batch_report.total_articles_fetched == 4
        assert batch_report.total_new_articles_saved == 2
        assert batch_report.total_duplicates_skipped == 2

        # Verify persisted articles in database
        articles = repo.list_articles()
        total = repo.count_articles()
        assert total == 2
        assert len(articles) == 2

        # Verify sentiment was computed during ingestion
        for art in articles:
            assert art.sentiment_label in {"positive", "negative", "neutral"}
            assert art.sentiment_score is not None
            assert -1.0 <= float(art.sentiment_score) <= 1.0
