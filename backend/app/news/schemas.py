"""
Pydantic Schemas for Phase 10: Financial News Intelligence & FinBERT Sentiment Analysis.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# News Source Schemas
# ---------------------------------------------------------------------------

class NewsSourceResponse(BaseModel):
    id: str
    name: str
    feed_url: str
    site_url: Optional[str] = None
    description: Optional[str] = None
    is_active: bool
    refresh_interval_minutes: int
    last_fetched_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# News Article Schemas
# ---------------------------------------------------------------------------

class NewsArticleResponse(BaseModel):
    id: str
    source_id: str
    source_name: Optional[str] = None
    title: str
    canonical_url: str
    summary: Optional[str] = None
    published_at: Optional[datetime] = None
    fetched_at: datetime
    sentiment_label: Optional[Literal["positive", "negative", "neutral"]] = None
    sentiment_score: Optional[Decimal] = None
    sentiment_probabilities: Optional[Dict[str, float]] = None
    sentiment_model: Optional[str] = None
    sentiment_analyzed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class NewsArticleListResponse(BaseModel):
    articles: List[NewsArticleResponse]
    total_count: int
    limit: int
    offset: int


# ---------------------------------------------------------------------------
# Ingestion / Refresh Schemas
# ---------------------------------------------------------------------------

class NewsRefreshRequest(BaseModel):
    source_id: Optional[str] = Field(
        None, description="Optional news source ID to refresh exclusively."
    )
    force: bool = Field(
        False, description="Bypass the refresh cooldown interval if True."
    )


class SourceIngestionReportItem(BaseModel):
    source_id: str
    source_name: str
    status: str
    articles_fetched: int
    new_articles_saved: int
    duplicates_skipped: int
    error_message: Optional[str] = None


class NewsRefreshResponse(BaseModel):
    started_at: str
    completed_at: str
    sources_polled: int
    total_articles_fetched: int
    total_new_articles_saved: int
    total_duplicates_skipped: int
    source_reports: List[SourceIngestionReportItem]


# ---------------------------------------------------------------------------
# Sentiment Aggregation Schemas
# ---------------------------------------------------------------------------

class SectorSentimentResponseItem(BaseModel):
    sector: str
    article_count: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    net_sentiment_score: float


class SentimentSummaryResponse(BaseModel):
    time_window: str
    window_start: str
    window_end: str
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    average_sentiment_score: float
    overall_sentiment_label: str
    sources_covered: List[str]
    sector_breakdown: List[SectorSentimentResponseItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Portfolio Relevance & Insights Schemas
# ---------------------------------------------------------------------------

class PortfolioNewsRelevanceItemSchema(BaseModel):
    article_id: str
    article_title: str
    canonical_url: str
    source_name: str
    published_at: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[str] = None
    matched_entity: str
    entity_type: str
    match_method: str
    match_confidence: float
    ambiguity_warning: Optional[str] = None


class PortfolioNewsRelevanceResponse(BaseModel):
    user_id: str
    portfolio_id: Optional[str] = None
    matches_count: int
    matches: List[PortfolioNewsRelevanceItemSchema]


class NewsArticleReferenceSchema(BaseModel):
    article_id: str
    title: str
    canonical_url: str
    source_name: str
    published_at: Optional[str] = None
    sentiment_label: Optional[str] = None
    sentiment_score: Optional[str] = None


class PortfolioNewsThemeSchema(BaseModel):
    theme_title: str
    sentiment: str
    relevance_to_portfolio: str
    articles: List[NewsArticleReferenceSchema] = Field(default_factory=list)


class PortfolioNewsInsightsResponse(BaseModel):
    user_id: str
    generated_at: str
    portfolio_name: Optional[str] = None
    executive_summary: str
    themes: List[PortfolioNewsThemeSchema]
    relevance_matches_count: int
    coverage_notes: List[str]
    disclaimers: List[str]
