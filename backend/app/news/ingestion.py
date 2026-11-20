"""
News Ingestion and Orchestration Service for Phase 10.

Coordinates RSS/Atom feed fetching across configured publishers, handles deduplication,
isolates source-level errors, runs sentiment inference, and persists normalized articles.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.db.models import NewsArticleModel, NewsSourceModel
from app.db.repositories.news_repo import SQLNewsRepository
from app.news.adapters import (
    BaseNewsFeedAdapter,
    MockNewsFeedAdapter,
    ParsedArticleItem,
    RSSFeedAdapter,
)
from app.news.config import DEFAULT_FEED_SOURCES, NewsSettings, get_news_settings
from app.news.sentiment import BaseSentimentAnalyzer, get_sentiment_analyzer

logger = logging.getLogger("uvicorn.error")


@dataclass
class SourceIngestionReport:
    """Ingestion outcome for a single news source."""
    source_id: str
    source_name: str
    feed_url: str
    status: str  # "success", "error", "skipped_cooldown"
    articles_fetched: int = 0
    new_articles_saved: int = 0
    duplicates_skipped: int = 0
    error_message: Optional[str] = None


@dataclass
class IngestionBatchReport:
    """Overall report for an ingestion refresh batch."""
    started_at: str
    completed_at: str
    sources_polled: int = 0
    total_articles_fetched: int = 0
    total_new_articles_saved: int = 0
    total_duplicates_skipped: int = 0
    source_reports: List[SourceIngestionReport] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "sources_polled": self.sources_polled,
            "total_articles_fetched": self.total_articles_fetched,
            "total_new_articles_saved": self.total_new_articles_saved,
            "total_duplicates_skipped": self.total_duplicates_skipped,
            "source_reports": [
                {
                    "source_id": r.source_id,
                    "source_name": r.source_name,
                    "status": r.status,
                    "articles_fetched": r.articles_fetched,
                    "new_articles_saved": r.new_articles_saved,
                    "duplicates_skipped": r.duplicates_skipped,
                    "error_message": r.error_message,
                }
                for r in self.source_reports
            ],
        }


class NewsIngestionService:
    """Orchestrator for financial news feed polling and sentiment classification."""

    def __init__(
        self,
        session: Session,
        adapter: Optional[BaseNewsFeedAdapter] = None,
        sentiment_analyzer: Optional[BaseSentimentAnalyzer] = None,
        settings: Optional[NewsSettings] = None,
    ):
        self.session = session
        self.news_repo = SQLNewsRepository(session)
        self.settings = settings or get_news_settings()

        if adapter is not None:
            self.adapter = adapter
        elif self.settings.mock_mode:
            self.adapter = MockNewsFeedAdapter()
        else:
            self.adapter = RSSFeedAdapter(self.settings)

        self.sentiment_analyzer = sentiment_analyzer or get_sentiment_analyzer(
            mock_override=self.settings.mock_mode
        )

    def initialize_default_sources(self) -> List[NewsSourceModel]:
        """Ensure standard reputable financial RSS sources exist in the database."""
        sources = []
        for def_src in DEFAULT_FEED_SOURCES:
            src = self.news_repo.create_source(
                name=def_src["name"],
                feed_url=def_src["feed_url"],
                site_url=def_src.get("site_url"),
                description=def_src.get("description"),
                refresh_interval_minutes=def_src.get("refresh_interval_minutes", 60),
            )
            sources.append(src)
        return sources

    async def refresh_feeds(
        self,
        source_id: Optional[str] = None,
        force: bool = False,
    ) -> IngestionBatchReport:
        """
        Poll active news feeds, filter duplicates, perform sentiment inference, and save articles.
        Fault-isolated: failure in one feed does not interrupt processing of remaining feeds.
        """
        start_time = datetime.now(timezone.utc)
        self.initialize_default_sources()

        if source_id:
            src = self.news_repo.get_source(source_id)
            sources = [src] if src and src.is_active else []
        else:
            sources = self.news_repo.list_sources(active_only=True)

        report = IngestionBatchReport(
            started_at=start_time.isoformat(),
            completed_at=start_time.isoformat(),
            sources_polled=len(sources),
        )

        total_saved = 0
        total_fetched = 0
        total_duplicates = 0

        for src in sources:
            src_report = await self._ingest_single_source(src, force=force)
            report.source_reports.append(src_report)
            total_fetched += src_report.articles_fetched
            total_saved += src_report.new_articles_saved
            total_duplicates += src_report.duplicates_skipped

        end_time = datetime.now(timezone.utc)
        report.completed_at = end_time.isoformat()
        report.total_articles_fetched = total_fetched
        report.total_new_articles_saved = total_saved
        report.total_duplicates_skipped = total_duplicates

        return report

    async def _ingest_single_source(self, source: NewsSourceModel, force: bool = False) -> SourceIngestionReport:
        now = datetime.now(timezone.utc)

        # Check cooldown unless forced
        if not force and source.last_fetched_at:
            elapsed_seconds = (now - source.last_fetched_at).total_seconds()
            if elapsed_seconds < self.settings.refresh_cooldown_seconds:
                return SourceIngestionReport(
                    source_id=source.id,
                    source_name=source.name,
                    feed_url=source.feed_url,
                    status="skipped_cooldown",
                    error_message=f"Cooldown active: polled {int(elapsed_seconds)}s ago.",
                )

        try:
            parsed_items = await self.adapter.fetch_articles(source)
        except Exception as exc:
            logger.warning("Error fetching feed '%s': %s", source.name, exc)
            return SourceIngestionReport(
                source_id=source.id,
                source_name=source.name,
                feed_url=source.feed_url,
                status="error",
                error_message=str(exc),
            )

        new_items_to_analyze: List[ParsedArticleItem] = []
        duplicates_count = 0
        seen_batch_urls: Set[str] = set()
        seen_batch_hashes: Set[str] = set()

        for item in parsed_items:
            if (
                item.canonical_url in seen_batch_urls
                or item.headline_hash in seen_batch_hashes
                or self.news_repo.article_exists_by_hash_or_url(item.canonical_url, item.headline_hash)
            ):
                duplicates_count += 1
            else:
                seen_batch_urls.add(item.canonical_url)
                seen_batch_hashes.add(item.headline_hash)
                new_items_to_analyze.append(item)

        saved_count = 0
        if new_items_to_analyze:
            # Batch sentiment analysis
            text_tuples = [(item.title, item.summary) for item in new_items_to_analyze]
            try:
                sentiment_results = self.sentiment_analyzer.analyze_batch(text_tuples)
            except Exception as s_exc:
                logger.warning("Sentiment analysis batch failure: %s", s_exc)
                sentiment_results = [None] * len(new_items_to_analyze)

            for i, item in enumerate(new_items_to_analyze):
                s_res = sentiment_results[i]
                article_model = NewsArticleModel(
                    id=str(uuid.uuid4()),
                    source_id=source.id,
                    title=item.title,
                    canonical_url=item.canonical_url,
                    summary=item.summary,
                    published_at=item.published_at,
                    fetched_at=now,
                    headline_hash=item.headline_hash,
                    sentiment_label=s_res.label if s_res else None,
                    sentiment_score=s_res.score if s_res else None,
                    sentiment_probabilities=s_res.probabilities if s_res else None,
                    sentiment_model=s_res.model_name if s_res else None,
                    sentiment_analyzed_at=s_res.analyzed_at if s_res else None,
                )
                self.news_repo.save_article(article_model)
                saved_count += 1

        self.news_repo.update_source_fetch_timestamp(source.id, now)

        return SourceIngestionReport(
            source_id=source.id,
            source_name=source.name,
            feed_url=source.feed_url,
            status="success",
            articles_fetched=len(parsed_items),
            new_articles_saved=saved_count,
            duplicates_skipped=duplicates_count,
        )
