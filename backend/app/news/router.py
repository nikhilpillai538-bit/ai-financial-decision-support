"""
FastAPI Router for Phase 10: Financial News Intelligence & FinBERT Sentiment Analysis.

Endpoints:
- GET /news: List recent normalized articles with filtering and pagination
- GET /news/{article_id}: View article metadata, source attribution, and FinBERT sentiment
- POST /news/refresh: Trigger bounded feed ingestion from configured, SSRF-safe RSS publishers
- GET /news/sentiment/summary: Retrieve aggregate market and sector sentiment
- GET /news/portfolio-relevance: Retrieve news matched against authenticated user's portfolio
- POST /news/portfolio-insights: Generate explainable portfolio-aware news summaries
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.models import UserModel
from app.db.repositories.news_repo import SQLNewsRepository
from app.db.session import get_db
from app.news.aggregation import MarketSentimentAggregator
from app.news.ingestion import NewsIngestionService
from app.news.insights_service import PortfolioNewsInsightsService
from app.news.relevance import PortfolioNewsRelevanceMatcher
from app.news.schemas import (
    NewsArticleListResponse,
    NewsArticleReferenceSchema,
    NewsArticleResponse,
    NewsRefreshRequest,
    NewsRefreshResponse,
    PortfolioNewsInsightsResponse,
    PortfolioNewsRelevanceItemSchema,
    PortfolioNewsRelevanceResponse,
    PortfolioNewsThemeSchema,
    SectorSentimentResponseItem,
    SentimentSummaryResponse,
    SourceIngestionReportItem,
)

news_router = APIRouter(prefix="/news", tags=["Financial News & Sentiment Analysis"])


def get_news_repo(db: Session = Depends(get_db)) -> SQLNewsRepository:
    return SQLNewsRepository(db)


# ---------------------------------------------------------------------------
# 1. Public Articles & Sources Endpoints
# ---------------------------------------------------------------------------

@news_router.get(
    "",
    response_model=NewsArticleListResponse,
    summary="List recent normalized financial news articles",
)
def list_news_articles(
    source_id: Optional[str] = Query(None, description="Filter by publishing news source ID"),
    sentiment_label: Optional[str] = Query(None, description="Filter by sentiment: positive, negative, neutral"),
    search: Optional[str] = Query(None, description="Keyword search in headlines and summaries"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    repo: SQLNewsRepository = Depends(get_news_repo),
) -> NewsArticleListResponse:
    """Retrieve paginated financial news articles with optional source, keyword, and sentiment filters."""
    articles = repo.list_articles(
        source_id=source_id,
        sentiment_label=sentiment_label,
        search=search,
        limit=limit,
        offset=offset,
    )
    total = repo.count_articles(
        source_id=source_id,
        sentiment_label=sentiment_label,
    )

    items = [
        NewsArticleResponse(
            id=a.id,
            source_id=a.source_id,
            source_name=a.source.name if a.source else None,
            title=a.title,
            canonical_url=a.canonical_url,
            summary=a.summary,
            published_at=a.published_at,
            fetched_at=a.fetched_at,
            sentiment_label=a.sentiment_label,  # type: ignore
            sentiment_score=a.sentiment_score,
            sentiment_probabilities=a.sentiment_probabilities,
            sentiment_model=a.sentiment_model,
            sentiment_analyzed_at=a.sentiment_analyzed_at,
        )
        for a in articles
    ]
    return NewsArticleListResponse(
        articles=items,
        total_count=total,
        limit=limit,
        offset=offset,
    )


@news_router.post(
    "/refresh",
    response_model=NewsRefreshResponse,
    summary="Trigger bounded news ingestion from configured RSS publishers",
)
async def refresh_news_feeds(
    payload: Optional[NewsRefreshRequest] = None,
    db: Session = Depends(get_db),
) -> NewsRefreshResponse:
    """
    Poll configured RSS publishers, deduplicate articles, run FinBERT sentiment,
    and persist new records. Uses bounded timeouts and SSRF-safe URL validation.
    """
    src_id = payload.source_id if payload else None
    force = payload.force if payload else False

    service = NewsIngestionService(db)
    batch_report = await service.refresh_feeds(source_id=src_id, force=force)

    reports = [
        SourceIngestionReportItem(
            source_id=r.source_id,
            source_name=r.source_name,
            status=r.status,
            articles_fetched=r.articles_fetched,
            new_articles_saved=r.new_articles_saved,
            duplicates_skipped=r.duplicates_skipped,
            error_message=r.error_message,
        )
        for r in batch_report.source_reports
    ]

    return NewsRefreshResponse(
        started_at=batch_report.started_at,
        completed_at=batch_report.completed_at,
        sources_polled=batch_report.sources_polled,
        total_articles_fetched=batch_report.total_articles_fetched,
        total_new_articles_saved=batch_report.total_new_articles_saved,
        total_duplicates_skipped=batch_report.total_duplicates_skipped,
        source_reports=reports,
    )


# ---------------------------------------------------------------------------
# 2. Market Sentiment Aggregation Endpoint
# ---------------------------------------------------------------------------

@news_router.get(
    "/sentiment/summary",
    response_model=SentimentSummaryResponse,
    summary="Retrieve aggregated market and sector sentiment metrics",
)
def get_sentiment_summary(
    time_window: str = Query("24h", pattern="^(24h|7d|30d)$", description="Observation window: 24h, 7d, 30d"),
    source_id: Optional[str] = Query(None, description="Optional news source ID filter"),
    db: Session = Depends(get_db),
) -> SentimentSummaryResponse:
    """
    Calculates positive/negative/neutral proportions, net sentiment score,
    sector breakdowns, and sample-size caveats for the specified time window.
    """
    aggregator = MarketSentimentAggregator(db)
    summary = aggregator.aggregate(time_window=time_window, source_id=source_id)

    sectors = [
        SectorSentimentResponseItem(
            sector=s.sector,
            article_count=s.article_count,
            positive_percentage=s.positive_percentage,
            negative_percentage=s.negative_percentage,
            neutral_percentage=s.neutral_percentage,
            net_sentiment_score=s.net_sentiment_score,
        )
        for s in summary.sector_breakdown
    ]

    return SentimentSummaryResponse(
        time_window=summary.time_window,
        window_start=summary.window_start,
        window_end=summary.window_end,
        total_articles=summary.total_articles,
        positive_count=summary.positive_count,
        negative_count=summary.negative_count,
        neutral_count=summary.neutral_count,
        positive_percentage=summary.positive_percentage,
        negative_percentage=summary.negative_percentage,
        neutral_percentage=summary.neutral_percentage,
        average_sentiment_score=summary.average_sentiment_score,
        overall_sentiment_label=summary.overall_sentiment_label,
        sources_covered=summary.sources_covered,
        sector_breakdown=sectors,
        warnings=summary.warnings,
    )


# ---------------------------------------------------------------------------
# 3. Portfolio-Aware Relevance & Insights (Authenticated)
# ---------------------------------------------------------------------------

@news_router.get(
    "/portfolio-relevance",
    response_model=PortfolioNewsRelevanceResponse,
    summary="Retrieve news articles relevant to the authenticated user's portfolio",
)
def get_portfolio_news_relevance(
    portfolio_id: Optional[str] = Query(None, description="Optional portfolio ID filter"),
    min_confidence: float = Query(0.60, ge=0.0, le=1.0, description="Minimum match confidence threshold"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
    repo: SQLNewsRepository = Depends(get_news_repo),
) -> PortfolioNewsRelevanceResponse:
    """
    Matches recent financial news articles against the user's portfolio holdings,
    tickers, company names, and sector allocations. Strictly user-isolated.
    """
    articles = repo.list_articles(limit=50)
    matcher = PortfolioNewsRelevanceMatcher(db)
    matches = matcher.match_articles(
        articles=articles,
        user=current_user,
        portfolio_id=portfolio_id,
        min_confidence=min_confidence,
    )

    items = [
        PortfolioNewsRelevanceItemSchema(
            article_id=m.article_id,
            article_title=m.article_title,
            canonical_url=m.canonical_url,
            source_name=m.source_name,
            published_at=m.published_at,
            sentiment_label=m.sentiment_label,
            sentiment_score=m.sentiment_score,
            matched_entity=m.matched_entity,
            entity_type=m.entity_type,
            match_method=m.match_method,
            match_confidence=m.match_confidence,
            ambiguity_warning=m.ambiguity_warning,
        )
        for m in matches
    ]

    return PortfolioNewsRelevanceResponse(
        user_id=current_user.id,
        portfolio_id=portfolio_id,
        matches_count=len(items),
        matches=items,
    )


@news_router.post(
    "/portfolio-insights",
    response_model=PortfolioNewsInsightsResponse,
    summary="Generate portfolio-aware news summaries and decision-support themes",
)
def generate_portfolio_news_insights(
    portfolio_id: Optional[str] = Query(None, description="Optional portfolio ID filter"),
    current_user: UserModel = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PortfolioNewsInsightsResponse:
    """
    Synthesizes relevant articles and FinBERT sentiment into thematic decision-support insights
    tailored to the authenticated user's portfolio weights and holdings.
    """
    service = PortfolioNewsInsightsService(db)
    report = service.generate_portfolio_news_insights(
        user=current_user,
        portfolio_id=portfolio_id,
    )

    theme_schemas = []
    for t in report.themes:
        art_schemas = [
            NewsArticleReferenceSchema(
                article_id=a.article_id,
                title=a.title,
                canonical_url=a.canonical_url,
                source_name=a.source_name,
                published_at=a.published_at,
                sentiment_label=a.sentiment_label,
                sentiment_score=a.sentiment_score,
            )
            for a in t.articles
        ]
        theme_schemas.append(
            PortfolioNewsThemeSchema(
                theme_title=t.theme_title,
                sentiment=t.sentiment,
                relevance_to_portfolio=t.relevance_to_portfolio,
                articles=art_schemas,
            )
        )

    return PortfolioNewsInsightsResponse(
        user_id=report.user_id,
        generated_at=report.generated_at,
        portfolio_name=report.portfolio_name,
        executive_summary=report.executive_summary,
        themes=theme_schemas,
        relevance_matches_count=report.relevance_matches_count,
        coverage_notes=report.coverage_notes,
        disclaimers=report.disclaimers,
    )


@news_router.get(
    "/{article_id}",
    response_model=NewsArticleResponse,
    summary="Get single news article metadata and FinBERT sentiment",
)
def get_news_article(
    article_id: str,
    repo: SQLNewsRepository = Depends(get_news_repo),
) -> NewsArticleResponse:
    """Retrieve full article record, source attribution, and FinBERT classification details."""
    article = repo.get_article(article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"News article '{article_id}' not found.",
        )

    return NewsArticleResponse(
        id=article.id,
        source_id=article.source_id,
        source_name=article.source.name if article.source else None,
        title=article.title,
        canonical_url=article.canonical_url,
        summary=article.summary,
        published_at=article.published_at,
        fetched_at=article.fetched_at,
        sentiment_label=article.sentiment_label,  # type: ignore
        sentiment_score=article.sentiment_score,
        sentiment_probabilities=article.sentiment_probabilities,
        sentiment_model=article.sentiment_model,
        sentiment_analyzed_at=article.sentiment_analyzed_at,
    )
