"""
Portfolio News Relevance Service for Phase 10.

Deterministically matches ingested financial news articles to the authenticated user's
portfolio assets, tickers, company names, sectors, and asset classes with confidence scores
and ambiguity warnings.
"""

from dataclasses import asdict, dataclass
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.db.models import NewsArticleModel, PortfolioModel, UserModel
from app.db.repositories.portfolio_repo import SQLPortfolioRepository

# Macro topics affecting broad market asset classes
MACRO_KEYWORDS = {
    "Federal Reserve": ["federal reserve", "fed", "fomc", "powell", "monetary policy"],
    "Interest Rates": ["interest rate", "rate cut", "rate hike", "yield curve", "benchmark rate"],
    "Inflation": ["inflation", "cpi", "consumer price index", "ppi", "core pce"],
    "GDP & Economic Growth": ["gdp", "recession", "economic growth", "jobless claims", "employment report"],
}

# Standard sector keywords
SECTOR_KEYWORDS = {
    "Technology": ["tech", "technology", "software", "semiconductor", "cloud", "artificial intelligence", "ai"],
    "Financials": ["bank", "banking", "lender", "credit", "financial services", "insurance", "brokerage"],
    "Healthcare": ["healthcare", "pharma", "biotech", "drug", "fda approval", "medical"],
    "Energy": ["oil", "crude", "energy", "petroleum", "gas", "renewable energy", "opec"],
    "Consumer": ["retail", "consumer spending", "e-commerce", "household", "discretionary"],
    "Industrials": ["industrial", "manufacturing", "aerospace", "defense", "freight", "logistics"],
}


@dataclass
class RelevanceMatchItem:
    """Individual match between a news article and a portfolio asset or sector."""
    article_id: str
    article_title: str
    canonical_url: str
    source_name: str
    published_at: Optional[str]
    sentiment_label: Optional[str]
    sentiment_score: Optional[str]
    matched_entity: str
    entity_type: str  # "ticker", "company", "sector", "macro"
    match_method: str  # "ticker_exact", "company_name", "sector_match", "macro_market"
    match_confidence: float
    ambiguity_warning: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PortfolioNewsRelevanceMatcher:
    """Matches news articles to user portfolio holdings and sector allocations."""

    def __init__(self, session: Session):
        self.session = session
        self.portfolio_repo = SQLPortfolioRepository(session)

    def extract_portfolio_entities(
        self, user: UserModel, portfolio_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract all tickers, company names, and sectors held by the user."""
        portfolios = self.portfolio_repo.list_portfolios(user_id=user.id)
        if portfolio_id:
            portfolios = [p for p in portfolios if p.id == portfolio_id]

        tickers: Set[str] = set()
        company_names: Set[str] = set()
        sectors: Set[str] = set()
        asset_classes: Set[str] = set()

        for port in portfolios:
            for holding in port.holdings:
                asset = holding.asset
                if asset:
                    if asset.symbol:
                        tickers.add(asset.symbol.strip().upper())
                    if asset.name:
                        company_names.add(asset.name.strip())
                    if getattr(asset, "sector", None):
                        sectors.add(asset.sector.strip())
                    elif asset.instrument_type:
                        sectors.add(asset.instrument_type.strip())
                    if asset.asset_class:
                        asset_classes.add(str(asset.asset_class).strip())

        return {
            "tickers": sorted(list(tickers)),
            "company_names": sorted(list(company_names)),
            "sectors": sorted(list(sectors)),
            "asset_classes": sorted(list(asset_classes)),
        }

    def match_articles(
        self,
        articles: List[NewsArticleModel],
        user: UserModel,
        portfolio_id: Optional[str] = None,
        min_confidence: float = 0.60,
    ) -> List[RelevanceMatchItem]:
        """Match a collection of news articles against user portfolio entities."""
        entities = self.extract_portfolio_entities(user, portfolio_id=portfolio_id)
        tickers = entities["tickers"]
        companies = entities["company_names"]
        user_sectors = entities["sectors"]

        matches: List[RelevanceMatchItem] = []

        for art in articles:
            text_to_search = f"{art.title} {art.summary or ''}".lower()
            text_title_only = art.title

            art_source_name = art.source.name if art.source else "Financial News"
            pub_iso = art.published_at.isoformat() if art.published_at else None
            score_str = str(art.sentiment_score) if art.sentiment_score is not None else None

            # 1. Exact Ticker matching
            for ticker in tickers:
                # Word boundary match e.g. \bAAPL\b (case sensitive on title or uppercase in text)
                ticker_pattern = rf"\b{re.escape(ticker)}\b"
                if re.search(ticker_pattern, text_title_only) or re.search(ticker_pattern, art.title):
                    ambiguity = None
                    if len(ticker) <= 2:
                        ambiguity = f"Short ticker symbol '{ticker}' may have ambiguous meanings."
                    matches.append(
                        RelevanceMatchItem(
                            article_id=art.id,
                            article_title=art.title,
                            canonical_url=art.canonical_url,
                            source_name=art_source_name,
                            published_at=pub_iso,
                            sentiment_label=art.sentiment_label,
                            sentiment_score=score_str,
                            matched_entity=ticker,
                            entity_type="ticker",
                            match_method="ticker_exact",
                            match_confidence=0.95 if not ambiguity else 0.75,
                            ambiguity_warning=ambiguity,
                        )
                    )

            # 2. Company Name matching
            for comp in companies:
                if len(comp) >= 3:
                    comp_pattern = rf"\b{re.escape(comp.lower())}\b"
                    if re.search(comp_pattern, text_to_search):
                        matches.append(
                            RelevanceMatchItem(
                                article_id=art.id,
                                article_title=art.title,
                                canonical_url=art.canonical_url,
                                source_name=art_source_name,
                                published_at=pub_iso,
                                sentiment_label=art.sentiment_label,
                                sentiment_score=score_str,
                                matched_entity=comp,
                                entity_type="company",
                                match_method="company_name",
                                match_confidence=0.85,
                            )
                        )

            # 3. Sector matching
            for sec in user_sectors:
                sec_lower = sec.lower()
                kw_list = SECTOR_KEYWORDS.get(sec, [sec_lower])
                if any(re.search(rf"\b{re.escape(kw)}\b", text_to_search) for kw in kw_list):
                    matches.append(
                        RelevanceMatchItem(
                            article_id=art.id,
                            article_title=art.title,
                            canonical_url=art.canonical_url,
                            source_name=art_source_name,
                            published_at=pub_iso,
                            sentiment_label=art.sentiment_label,
                            sentiment_score=score_str,
                            matched_entity=sec,
                            entity_type="sector",
                            match_method="sector_match",
                            match_confidence=0.70,
                        )
                    )

            # 4. Macro Market matching (only if portfolio holds equities or fixed income)
            if entities["tickers"] or entities["sectors"]:
                for macro_name, macro_kws in MACRO_KEYWORDS.items():
                    if any(re.search(rf"\b{re.escape(kw)}\b", text_to_search) for kw in macro_kws):
                        matches.append(
                            RelevanceMatchItem(
                                article_id=art.id,
                                article_title=art.title,
                                canonical_url=art.canonical_url,
                                source_name=art_source_name,
                                published_at=pub_iso,
                                sentiment_label=art.sentiment_label,
                                sentiment_score=score_str,
                                matched_entity=macro_name,
                                entity_type="macro",
                                match_method="macro_market",
                                match_confidence=0.65,
                            )
                        )

        # Deduplicate matches per article and entity, filter by min_confidence
        seen = set()
        filtered_matches = []
        for m in matches:
            key = (m.article_id, m.matched_entity)
            if key not in seen and m.match_confidence >= min_confidence:
                seen.add(key)
                filtered_matches.append(m)

        # Sort highest confidence first, then newest published
        filtered_matches.sort(
            key=lambda x: (x.match_confidence, x.published_at or ""),
            reverse=True,
        )
        return filtered_matches
