"""
Portfolio-Aware News Insights and Decision Support Service for Phase 10.

Combines verified portfolio metadata (holdings, sectors, weights) with retrieved news
articles and FinBERT sentiment classifications to deliver explainable, decision-support themes.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.db.models import PortfolioModel, UserModel
from app.db.repositories.news_repo import SQLNewsRepository
from app.db.repositories.portfolio_repo import SQLPortfolioRepository
from app.news.relevance import PortfolioNewsRelevanceMatcher, RelevanceMatchItem


@dataclass
class NewsArticleReference:
    """Attribution and sentiment metadata for an article cited in an insight theme."""
    article_id: str
    title: str
    canonical_url: str
    source_name: str
    published_at: Optional[str]
    sentiment_label: Optional[str]
    sentiment_score: Optional[str]


@dataclass
class PortfolioNewsTheme:
    """A distinct thematic group of news items relevant to the user's portfolio."""
    theme_title: str
    sentiment: str  # "positive", "negative", "neutral"
    relevance_to_portfolio: str
    articles: List[NewsArticleReference] = field(default_factory=list)


@dataclass
class PortfolioNewsInsightsReport:
    """Consolidated portfolio-aware financial news report."""
    user_id: str
    generated_at: str
    portfolio_name: Optional[str]
    executive_summary: str
    themes: List[PortfolioNewsTheme] = field(default_factory=list)
    relevance_matches_count: int = 0
    coverage_notes: List[str] = field(default_factory=list)
    disclaimers: List[str] = field(
        default_factory=lambda: [
            "Financial news sentiment reflects publisher reporting and FinBERT text classification, not confirmed future asset price movements.",
            "Correlation between sentiment and short-term volatility does not establish causation.",
            "Decision-support analysis only; does not constitute automated trading instructions or fiduciary investment advice."
        ]
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "generated_at": self.generated_at,
            "portfolio_name": self.portfolio_name,
            "executive_summary": self.executive_summary,
            "themes": [
                {
                    "theme_title": t.theme_title,
                    "sentiment": t.sentiment,
                    "relevance_to_portfolio": t.relevance_to_portfolio,
                    "articles": [asdict(a) for a in t.articles],
                }
                for t in self.themes
            ],
            "relevance_matches_count": self.relevance_matches_count,
            "coverage_notes": self.coverage_notes,
            "disclaimers": self.disclaimers,
        }


class PortfolioNewsInsightsService:
    """Generates portfolio-aware news summaries and decision-support themes."""

    def __init__(self, session: Session):
        self.session = session
        self.news_repo = SQLNewsRepository(session)
        self.portfolio_repo = SQLPortfolioRepository(session)
        self.matcher = PortfolioNewsRelevanceMatcher(session)

    def generate_portfolio_news_insights(
        self,
        user: UserModel,
        portfolio_id: Optional[str] = None,
        limit_articles: int = 25,
    ) -> PortfolioNewsInsightsReport:
        """Synthesize relevant news articles into explainable decision-support themes."""
        now_utc = datetime.now(timezone.utc)

        # 1. Resolve portfolio
        portfolios = self.portfolio_repo.list_portfolios(user_id=user.id)
        target_port = None
        if portfolio_id:
            target_port = next((p for p in portfolios if p.id == portfolio_id), None)
        elif portfolios:
            target_port = portfolios[0]

        port_name = target_port.name if target_port else None

        # 2. Query recent articles
        articles = self.news_repo.list_articles(limit=limit_articles)

        if not articles:
            return PortfolioNewsInsightsReport(
                user_id=user.id,
                generated_at=now_utc.isoformat(),
                portfolio_name=port_name,
                executive_summary="No recent financial news articles are currently recorded in the system.",
                coverage_notes=["Please trigger a news refresh via POST /news/refresh to ingest the latest publisher feeds."],
            )

        # 3. Match against portfolio
        matches = self.matcher.match_articles(
            articles=articles,
            user=user,
            portfolio_id=portfolio_id,
        )

        if not matches:
            return PortfolioNewsInsightsReport(
                user_id=user.id,
                generated_at=now_utc.isoformat(),
                portfolio_name=port_name,
                executive_summary=(
                    f"Analyzed {len(articles)} recent articles. None directly matched the specific assets or "
                    "sectors in your tracked portfolio."
                ),
                coverage_notes=["Consider expanding portfolio asset sector tags or adding general market indices."],
            )

        # 4. Group matches by entity / theme
        themes: List[PortfolioNewsTheme] = []
        entity_groups: Dict[str, List[RelevanceMatchItem]] = {}
        for m in matches:
            entity_groups.setdefault(m.matched_entity, []).append(m)

        for entity, m_list in list(entity_groups.items())[:5]:
            first_m = m_list[0]
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
            for m in m_list:
                lbl = (m.sentiment_label or "neutral").lower()
                sentiment_counts[lbl] = sentiment_counts.get(lbl, 0) + 1

            dom_sentiment = max(sentiment_counts, key=sentiment_counts.get)  # type: ignore

            if first_m.entity_type == "ticker":
                title = f"{entity} Holding: Publisher News Sentiment"
                rel_desc = f"Direct coverage concerning your portfolio holding '{entity}'."
            elif first_m.entity_type == "company":
                title = f"{entity}: Company Developments"
                rel_desc = f"Articles matching your tracked asset company '{entity}'."
            elif first_m.entity_type == "sector":
                title = f"{entity} Sector Trends"
                rel_desc = f"Industry-wide coverage relating to your {entity} sector allocation."
            else:
                title = f"{entity} Macroeconomic Impact"
                rel_desc = f"Macroeconomic conditions impacting broad market valuations and interest-rate sensitivity."

            ref_articles = [
                NewsArticleReference(
                    article_id=m.article_id,
                    title=m.article_title,
                    canonical_url=m.canonical_url,
                    source_name=m.source_name,
                    published_at=m.published_at,
                    sentiment_label=m.sentiment_label,
                    sentiment_score=m.sentiment_score,
                )
                for m in m_list[:4]
            ]

            themes.append(
                PortfolioNewsTheme(
                    theme_title=title,
                    sentiment=dom_sentiment,
                    relevance_to_portfolio=rel_desc,
                    articles=ref_articles,
                )
            )

        pos_theme_count = sum(1 for t in themes if t.sentiment == "positive")
        neg_theme_count = sum(1 for t in themes if t.sentiment == "negative")

        if pos_theme_count > neg_theme_count:
            tone = "predominantly constructive"
        elif neg_theme_count > pos_theme_count:
            tone = "cautionary"
        else:
            tone = "balanced"

        exec_summary = (
            f"Identified {len(matches)} relevant news item(s) across {len(themes)} key theme(s) "
            f"for your portfolio '{port_name or 'Default'}'. Market coverage tone is currently {tone}."
        )

        coverage_notes = [
            f"Evaluated {len(articles)} recent articles across {len({m.source_name for m in matches})} publisher source(s).",
            f"Highest match confidence observed: {round(max(m.match_confidence for m in matches), 2)}.",
        ]

        return PortfolioNewsInsightsReport(
            user_id=user.id,
            generated_at=now_utc.isoformat(),
            portfolio_name=port_name,
            executive_summary=exec_summary,
            themes=themes,
            relevance_matches_count=len(matches),
            coverage_notes=coverage_notes,
        )
