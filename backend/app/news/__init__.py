"""
Financial News Intelligence, FinBERT Sentiment Analysis, and Portfolio-Aware Insights (Phase 10).
"""

from app.news.adapters import (
    BaseNewsFeedAdapter,
    MockNewsFeedAdapter,
    ParsedArticleItem,
    RSSFeedAdapter,
    compute_headline_hash,
    normalize_canonical_url,
    validate_feed_url,
)
from app.news.aggregation import MarketSentimentAggregator, MarketSentimentSummary, SectorSentimentItem
from app.news.config import NewsSettings, get_news_settings
from app.news.ingestion import IngestionBatchReport, NewsIngestionService, SourceIngestionReport
from app.news.insights_service import (
    NewsArticleReference,
    PortfolioNewsInsightsReport,
    PortfolioNewsInsightsService,
    PortfolioNewsTheme,
)
from app.news.relevance import PortfolioNewsRelevanceMatcher, RelevanceMatchItem
from app.news.router import news_router
from app.news.sentiment import (
    BaseSentimentAnalyzer,
    FinBERTSentimentAnalyzer,
    FinBERTUnavailableError,
    MockSentimentAnalyzer,
    SentimentAnalysisError,
    SentimentResult,
    get_sentiment_analyzer,
)

__all__ = [
    "news_router",
    "NewsSettings",
    "get_news_settings",
    "BaseNewsFeedAdapter",
    "RSSFeedAdapter",
    "MockNewsFeedAdapter",
    "ParsedArticleItem",
    "validate_feed_url",
    "normalize_canonical_url",
    "compute_headline_hash",
    "BaseSentimentAnalyzer",
    "FinBERTSentimentAnalyzer",
    "MockSentimentAnalyzer",
    "FinBERTUnavailableError",
    "SentimentAnalysisError",
    "SentimentResult",
    "get_sentiment_analyzer",
    "NewsIngestionService",
    "IngestionBatchReport",
    "SourceIngestionReport",
    "PortfolioNewsRelevanceMatcher",
    "RelevanceMatchItem",
    "MarketSentimentAggregator",
    "MarketSentimentSummary",
    "SectorSentimentItem",
    "PortfolioNewsInsightsService",
    "PortfolioNewsInsightsReport",
    "PortfolioNewsTheme",
    "NewsArticleReference",
]
