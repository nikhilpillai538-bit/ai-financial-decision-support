"""
SQLAlchemy repository for Phase 10 Financial News Ingestion & Sentiment Storage.

Handles persistent operations for news sources and normalized news articles
with deduplication checks, sentiment updates, and filtered querying.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.db.models import NewsArticleModel, NewsSourceModel


class SQLNewsRepository:
    """Repository for managing news sources, articles, and FinBERT sentiment records."""

    def __init__(self, session: Session):
        self.session = session

    # -----------------------------------------------------------------------
    # News Source Operations
    # -----------------------------------------------------------------------

    def create_source(
        self,
        name: str,
        feed_url: str,
        site_url: Optional[str] = None,
        description: Optional[str] = None,
        is_active: bool = True,
        refresh_interval_minutes: int = 60,
    ) -> NewsSourceModel:
        """Create or return an existing news source by name/URL."""
        existing = self.get_source_by_url(feed_url)
        if existing:
            return existing

        source = NewsSourceModel(
            id=str(uuid.uuid4()),
            name=name.strip(),
            feed_url=feed_url.strip(),
            site_url=site_url.strip() if site_url else None,
            description=description.strip() if description else None,
            is_active=is_active,
            refresh_interval_minutes=refresh_interval_minutes,
        )
        self.session.add(source)
        self.session.commit()
        self.session.refresh(source)
        return source

    def get_source(self, source_id: str) -> Optional[NewsSourceModel]:
        """Retrieve news source by ID."""
        stmt = select(NewsSourceModel).where(NewsSourceModel.id == source_id)
        return self.session.scalars(stmt).first()

    def get_source_by_url(self, feed_url: str) -> Optional[NewsSourceModel]:
        """Retrieve news source by canonical feed URL."""
        stmt = select(NewsSourceModel).where(NewsSourceModel.feed_url == feed_url.strip())
        return self.session.scalars(stmt).first()

    def list_sources(self, active_only: bool = False) -> List[NewsSourceModel]:
        """List configured news sources."""
        stmt = select(NewsSourceModel)
        if active_only:
            stmt = stmt.where(NewsSourceModel.is_active.is_(True))
        stmt = stmt.order_by(NewsSourceModel.name.asc())
        return list(self.session.scalars(stmt).all())

    def update_source_fetch_timestamp(self, source_id: str, fetch_time: Optional[datetime] = None) -> None:
        """Record the timestamp of a feed fetch."""
        source = self.get_source(source_id)
        if source:
            source.last_fetched_at = fetch_time or datetime.now(timezone.utc)
            self.session.commit()

    # -----------------------------------------------------------------------
    # News Article Operations
    # -----------------------------------------------------------------------

    def article_exists_by_hash_or_url(self, canonical_url: str, headline_hash: str) -> bool:
        """Check if an article is already stored via canonical URL or headline hash."""
        stmt = select(NewsArticleModel.id).where(
            or_(
                NewsArticleModel.canonical_url == canonical_url.strip(),
                NewsArticleModel.headline_hash == headline_hash.strip(),
            )
        )
        return self.session.scalars(stmt).first() is not None

    def save_article(self, article: NewsArticleModel) -> NewsArticleModel:
        """Save a new news article record."""
        self.session.add(article)
        self.session.commit()
        self.session.refresh(article)
        return article

    def batch_save_articles(self, articles: List[NewsArticleModel]) -> int:
        """Persist a list of unique news articles, skipping duplicates."""
        saved_count = 0
        for art in articles:
            if not self.article_exists_by_hash_or_url(art.canonical_url, art.headline_hash):
                self.session.add(art)
                saved_count += 1
        if saved_count > 0:
            self.session.commit()
        return saved_count

    def get_article(self, article_id: str) -> Optional[NewsArticleModel]:
        """Retrieve an article by ID with eager-loaded source."""
        stmt = (
            select(NewsArticleModel)
            .where(NewsArticleModel.id == article_id)
            .options(joinedload(NewsArticleModel.source))
        )
        return self.session.scalars(stmt).first()

    def get_article_by_canonical_url(self, canonical_url: str) -> Optional[NewsArticleModel]:
        """Retrieve an article by canonical URL."""
        stmt = select(NewsArticleModel).where(NewsArticleModel.canonical_url == canonical_url.strip())
        return self.session.scalars(stmt).first()

    def list_articles(
        self,
        source_id: Optional[str] = None,
        sentiment_label: Optional[str] = None,
        search: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[NewsArticleModel]:
        """List articles with multi-criteria filtering and pagination."""
        stmt = select(NewsArticleModel).options(joinedload(NewsArticleModel.source))

        filters = []
        if source_id:
            filters.append(NewsArticleModel.source_id == source_id)
        if sentiment_label:
            filters.append(NewsArticleModel.sentiment_label == sentiment_label.lower())
        if start_date:
            filters.append(NewsArticleModel.published_at >= start_date)
        if end_date:
            filters.append(NewsArticleModel.published_at <= end_date)
        if search:
            search_term = f"%{search.strip().lower()}%"
            filters.append(
                or_(
                    func.lower(NewsArticleModel.title).like(search_term),
                    func.lower(NewsArticleModel.summary).like(search_term),
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = (
            stmt.order_by(
                NewsArticleModel.published_at.desc().nullslast(),
                NewsArticleModel.fetched_at.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(stmt).unique().all())

    def count_articles(
        self,
        source_id: Optional[str] = None,
        sentiment_label: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> int:
        """Count total matching articles for pagination metadata."""
        stmt = select(func.count(NewsArticleModel.id))
        filters = []
        if source_id:
            filters.append(NewsArticleModel.source_id == source_id)
        if sentiment_label:
            filters.append(NewsArticleModel.sentiment_label == sentiment_label.lower())
        if start_date:
            filters.append(NewsArticleModel.published_at >= start_date)
        if end_date:
            filters.append(NewsArticleModel.published_at <= end_date)

        if filters:
            stmt = stmt.where(and_(*filters))
        return self.session.scalar(stmt) or 0

    def update_article_sentiment(
        self,
        article_id: str,
        label: str,
        score: Decimal,
        probabilities: Dict[str, float],
        model_name: str,
        analyzed_at: Optional[datetime] = None,
    ) -> Optional[NewsArticleModel]:
        """Update FinBERT sentiment classification results for an article."""
        article = self.get_article(article_id)
        if not article:
            return None
        article.sentiment_label = label.lower()
        article.sentiment_score = score
        article.sentiment_probabilities = probabilities
        article.sentiment_model = model_name
        article.sentiment_analyzed_at = analyzed_at or datetime.now(timezone.utc)
        self.session.commit()
        self.session.refresh(article)
        return article

    def update_article_relevance(
        self, article_id: str, relevance_metadata: Dict[str, Any]
    ) -> Optional[NewsArticleModel]:
        """Update portfolio/sector relevance cache on an article."""
        article = self.get_article(article_id)
        if not article:
            return None
        article.relevance_metadata = relevance_metadata
        self.session.commit()
        self.session.refresh(article)
        return article
