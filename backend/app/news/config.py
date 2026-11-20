"""
Configuration for Phase 10: Financial News Intelligence & FinBERT Sentiment Analysis.
"""

import os
from typing import List, Set
from pydantic import BaseModel, Field


DEFAULT_APPROVED_DOMAINS: Set[str] = {
    "federalreserve.gov",
    "sec.gov",
    "finance.yahoo.com",
    "reutersagency.com",
    "reuters.com",
    "dowjones.io",
    "marketwatch.com",
    "investing.com",
    "bloomberg.com",
    "ft.com",
    "cnbc.com",
    "indiatimes.com",
    "economictimes.indiatimes.com",
    "google.com",
    "news.google.com",
    "moneycontrol.com",
}

DEFAULT_FEED_SOURCES = [
    {
        "name": "Economic Times Markets",
        "feed_url": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
        "site_url": "https://economictimes.indiatimes.com",
        "description": "Live Indian stock markets, equities, NSE/BSE updates and economic trends.",
        "refresh_interval_minutes": 15,
    },
    {
        "name": "Google Business & Markets",
        "feed_url": "https://news.google.com/rss/headlines/section/topic/BUSINESS",
        "site_url": "https://news.google.com",
        "description": "Global and domestic business headlines, earnings reports, and market movements.",
        "refresh_interval_minutes": 15,
    },
    {
        "name": "MarketWatch Top Stories",
        "feed_url": "https://feeds.content.dowjones.io/public/rss/mw_topstories",
        "site_url": "https://www.marketwatch.com",
        "description": "MarketWatch financial and stock market news.",
        "refresh_interval_minutes": 30,
    },
    {
        "name": "Federal Reserve Press",
        "feed_url": "https://www.federalreserve.gov/feeds/press_all.xml",
        "site_url": "https://www.federalreserve.gov",
        "description": "Official press releases and monetary policy statements from the Federal Reserve.",
        "refresh_interval_minutes": 60,
    },
]


class NewsSettings(BaseModel):
    """Runtime configuration for financial news ingestion and sentiment analysis."""

    mock_mode: bool = Field(
        default_factory=lambda: os.getenv("NEWS_MOCK_MODE", "true").strip().lower() in {"1", "true", "yes"}
    )
    finbert_model_name: str = Field(
        default_factory=lambda: os.getenv("FINBERT_MODEL_NAME", "ProsusAI/finbert").strip()
    )
    finbert_device: str = Field(
        default_factory=lambda: os.getenv("FINBERT_DEVICE", "cpu").strip().lower()
    )
    finbert_batch_size: int = Field(
        default_factory=lambda: int(os.getenv("FINBERT_BATCH_SIZE", "16"))
    )
    ingestion_timeout_seconds: float = Field(
        default_factory=lambda: float(os.getenv("NEWS_INGESTION_TIMEOUT_SECONDS", "10.0"))
    )
    max_articles_per_feed: int = Field(
        default_factory=lambda: int(os.getenv("NEWS_MAX_ARTICLES_PER_FEED", "20"))
    )
    max_total_refresh_articles: int = Field(
        default_factory=lambda: int(os.getenv("NEWS_MAX_TOTAL_REFRESH_ARTICLES", "100"))
    )
    refresh_cooldown_seconds: int = Field(
        default_factory=lambda: int(os.getenv("NEWS_REFRESH_COOLDOWN_SECONDS", "60"))
    )
    sentiment_cache_days: int = Field(
        default_factory=lambda: int(os.getenv("NEWS_SENTIMENT_CACHE_DAYS", "30"))
    )
    allowed_domains: Set[str] = Field(
        default_factory=lambda: (
            set(os.getenv("NEWS_ALLOWED_DOMAINS", "").lower().split(",")) - {""}
            if os.getenv("NEWS_ALLOWED_DOMAINS")
            else DEFAULT_APPROVED_DOMAINS
        )
    )


def get_news_settings() -> NewsSettings:
    """Load news intelligence settings dynamically."""
    return NewsSettings()
