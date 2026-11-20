"""
Sentiment Aggregation Service for Phase 10.

Computes statistically sound market and sector sentiment summaries over configurable
time windows (e.g. 24 hours, 7 days), with near-duplicate event weighting controls,
breakdowns by sector and asset, and explicit sample-size limitations.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.db.models import NewsArticleModel
from app.db.repositories.news_repo import SQLNewsRepository
from app.news.relevance import SECTOR_KEYWORDS


@dataclass
class SectorSentimentItem:
    sector: str
    article_count: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    net_sentiment_score: float  # [-1.0, +1.0]


@dataclass
class MarketSentimentSummary:
    """Aggregated market sentiment metrics over a specified observation window."""
    time_window: str  # e.g. "24h", "7d", "30d"
    window_start: str
    window_end: str
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_percentage: float
    negative_percentage: float
    neutral_percentage: float
    average_sentiment_score: float  # [-1.00, +1.00] scale: (pos - neg) / total
    overall_sentiment_label: str  # "bullish", "bearish", "neutral"
    sources_covered: List[str]
    sector_breakdown: List[SectorSentimentItem] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "time_window": self.time_window,
            "window_start": self.window_start,
            "window_end": self.window_end,
            "total_articles": self.total_articles,
            "positive_count": self.positive_count,
            "negative_count": self.negative_count,
            "neutral_count": self.neutral_count,
            "positive_percentage": round(self.positive_percentage, 2),
            "negative_percentage": round(self.negative_percentage, 2),
            "neutral_percentage": round(self.neutral_percentage, 2),
            "average_sentiment_score": round(self.average_sentiment_score, 4),
            "overall_sentiment_label": self.overall_sentiment_label,
            "sources_covered": self.sources_covered,
            "sector_breakdown": [asdict(s) for s in self.sector_breakdown],
            "warnings": self.warnings,
        }


class MarketSentimentAggregator:
    """Aggregates FinBERT sentiment metrics over time windows."""

    def __init__(self, session: Session):
        self.session = session
        self.news_repo = SQLNewsRepository(session)

    def aggregate(
        self,
        time_window: str = "24h",
        source_id: Optional[str] = None,
        deduplicate_events: bool = True,
    ) -> MarketSentimentSummary:
        """Compute aggregated sentiment metrics for the requested time window."""
        now = datetime.now(timezone.utc)
        if time_window == "24h":
            start_date = now - timedelta(hours=24)
        elif time_window == "7d":
            start_date = now - timedelta(days=7)
        elif time_window == "30d":
            start_date = now - timedelta(days=30)
        else:
            time_window = "24h"
            start_date = now - timedelta(hours=24)

        # Retrieve articles published within the window
        articles = self.news_repo.list_articles(
            source_id=source_id,
            start_date=start_date,
            end_date=now,
            limit=500,
        )

        # Near-duplicate event grouping by headline_hash if requested
        if deduplicate_events:
            unique_articles: List[NewsArticleModel] = []
            seen_hashes: Set[str] = set()
            for a in articles:
                if a.headline_hash not in seen_hashes:
                    seen_hashes.add(a.headline_hash)
                    unique_articles.append(a)
            articles = unique_articles

        total = len(articles)
        warnings: List[str] = []

        if total == 0:
            return MarketSentimentSummary(
                time_window=time_window,
                window_start=start_date.isoformat(),
                window_end=now.isoformat(),
                total_articles=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                positive_percentage=0.0,
                negative_percentage=0.0,
                neutral_percentage=0.0,
                average_sentiment_score=0.0,
                overall_sentiment_label="neutral",
                sources_covered=[],
                warnings=["No financial news articles found within the requested time window."],
            )

        if total < 5:
            warnings.append(
                f"Low sample size ({total} article(s)). Aggregate sentiment may not be statistically representative of overall market conditions."
            )

        pos_count = sum(1 for a in articles if (a.sentiment_label or "").lower() == "positive")
        neg_count = sum(1 for a in articles if (a.sentiment_label or "").lower() == "negative")
        neu_count = sum(1 for a in articles if (a.sentiment_label or "").lower() == "neutral")

        pos_pct = (pos_count / total) * 100.0
        neg_pct = (neg_count / total) * 100.0
        neu_pct = (neu_count / total) * 100.0

        # Net sentiment score on [-1.0, +1.0]: (pos - neg) / total
        avg_score = (pos_count - neg_count) / total

        if avg_score >= 0.15:
            overall_label = "bullish"
        elif avg_score <= -0.15:
            overall_label = "bearish"
        else:
            overall_label = "neutral"

        # Unique sources covered
        sources = sorted(list({a.source.name for a in articles if a.source}))

        # Sector level breakdown
        sector_items = self._compute_sector_breakdown(articles)

        return MarketSentimentSummary(
            time_window=time_window,
            window_start=start_date.isoformat(),
            window_end=now.isoformat(),
            total_articles=total,
            positive_count=pos_count,
            negative_count=neg_count,
            neutral_count=neu_count,
            positive_percentage=pos_pct,
            negative_percentage=neg_pct,
            neutral_percentage=neu_pct,
            average_sentiment_score=avg_score,
            overall_sentiment_label=overall_label,
            sources_covered=sources,
            sector_breakdown=sector_items,
            warnings=warnings,
        )

    def _compute_sector_breakdown(self, articles: List[NewsArticleModel]) -> List[SectorSentimentItem]:
        """Aggregate sentiment counts for specific sectors mentioned in news articles."""
        sector_articles: Dict[str, List[NewsArticleModel]] = {sec: [] for sec in SECTOR_KEYWORDS}

        for art in articles:
            text = f"{art.title} {art.summary or ''}".lower()
            for sec, keywords in SECTOR_KEYWORDS.items():
                if any(re.search(rf"\b{re.escape(kw)}\b", text) for kw in keywords):
                    sector_articles[sec].append(art)

        items: List[SectorSentimentItem] = []
        for sec, s_arts in sector_articles.items():
            if not s_arts:
                continue
            cnt = len(s_arts)
            pos = sum(1 for a in s_arts if (a.sentiment_label or "").lower() == "positive")
            neg = sum(1 for a in s_arts if (a.sentiment_label or "").lower() == "negative")
            neu = sum(1 for a in s_arts if (a.sentiment_label or "").lower() == "neutral")

            net_score = (pos - neg) / cnt
            items.append(
                SectorSentimentItem(
                    sector=sec,
                    article_count=cnt,
                    positive_percentage=round((pos / cnt) * 100.0, 2),
                    negative_percentage=round((neg / cnt) * 100.0, 2),
                    neutral_percentage=round((neu / cnt) * 100.0, 2),
                    net_sentiment_score=round(net_score, 4),
                )
            )

        items.sort(key=lambda x: x.article_count, reverse=True)
        return items
