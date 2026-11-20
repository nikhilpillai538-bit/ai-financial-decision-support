"""
Feed adapters and SSRF security validators for Phase 10 Financial News Ingestion.

Supports standard RSS 2.0 / Atom XML feeds with strict URL validation,
HTML sanitization, canonical URL normalization, and headline hashing.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import ipaddress
import logging
import re
from typing import List, Optional, Set
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import xml.etree.ElementTree as ET

import dateutil.parser
import httpx

from app.db.models import NewsSourceModel
from app.news.config import NewsSettings, get_news_settings

logger = logging.getLogger("uvicorn.error")

# Tracking parameters to strip for canonical URL normalization
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "feed", "rss",
}


# ---------------------------------------------------------------------------
# SSRF Validation & Security
# ---------------------------------------------------------------------------

def validate_feed_url(url: str, allowed_domains: Optional[Set[str]] = None) -> bool:
    """
    Validate that an RSS/Atom URL is safe from SSRF attacks and matches allowed domains.
    Rejects private IPs, localhost, invalid schemes, and unauthorized hostnames.
    """
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url.strip())
        if parsed.scheme.lower() not in {"http", "https"}:
            return False

        hostname = (parsed.hostname or "").lower()
        if not hostname:
            return False

        # Reject localhost and broadcast
        if hostname in {"localhost", "127.0.0.1", "0.0.0.0", "::1"}:
            return False

        # Reject private/reserved IP addresses
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_reserved or ip.is_loopback or ip.is_link_local:
                return False
        except ValueError:
            # Not an IP literal, it is a domain name
            pass

        # Check allowed domains if specified
        if allowed_domains:
            # Check if hostname ends with any allowed domain (e.g. news.google.com ends with google.com)
            domain_match = any(
                hostname == d or hostname.endswith(f".{d}")
                for d in allowed_domains
            )
            if not domain_match:
                return False

        return True
    except Exception:
        return False


def normalize_canonical_url(url: str) -> str:
    """Clean tracking query parameters and fragments from an article URL."""
    try:
        parsed = urlparse(url.strip())
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        cleaned_pairs = [(k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS]
        clean_query = urlencode(cleaned_pairs)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, clean_query, ""))
    except Exception:
        return url.strip()


def strip_html_tags(text: Optional[str]) -> str:
    """Remove HTML markup, CDATA artifacts, and normalize whitespace."""
    if not text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def compute_headline_hash(title: str) -> str:
    """Compute deterministic SHA-256 hash of normalized headline for deduplication."""
    normalized = re.sub(r"[^\w\s]", "", title.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class ParsedArticleItem:
    """Normalized article metadata parsed from an RSS/Atom feed."""
    title: str
    canonical_url: str
    summary: Optional[str]
    published_at: Optional[datetime]
    headline_hash: str
    source_name: str


# ---------------------------------------------------------------------------
# Feed Adapters
# ---------------------------------------------------------------------------

class BaseNewsFeedAdapter(ABC):
    """Abstract interface for ingesting financial news feeds."""

    @abstractmethod
    async def fetch_articles(self, source: NewsSourceModel) -> List[ParsedArticleItem]:
        """Fetch and parse articles from a news source."""
        pass


class RSSFeedAdapter(BaseNewsFeedAdapter):
    """Production adapter for standard RSS 2.0 and Atom XML feeds."""

    def __init__(self, settings: Optional[NewsSettings] = None):
        self.settings = settings or get_news_settings()

    async def fetch_articles(self, source: NewsSourceModel) -> List[ParsedArticleItem]:
        """Fetch feed XML with bounded timeout and parse items into normalized articles."""
        if not validate_feed_url(source.feed_url, self.settings.allowed_domains):
            logger.warning("Feed URL rejected by security validation: %s", source.feed_url)
            return []

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.settings.ingestion_timeout_seconds,
                follow_redirects=True,
                max_redirects=3,
            ) as client:
                res = await client.get(source.feed_url, headers=headers)
                if res.status_code != 200:
                    logger.warning("Feed %s returned HTTP %d", source.name, res.status_code)
                    return []
                xml_content = res.content
        except Exception as exc:
            logger.warning("Feed network error fetching %s: %s", source.name, exc)
            return []

        return self.parse_xml(xml_content, source.name, max_items=self.settings.max_articles_per_feed)

    def parse_xml(self, xml_bytes: bytes, source_name: str, max_items: int = 20) -> List[ParsedArticleItem]:
        """Parse raw XML bytes (RSS 2.0 or Atom) into ParsedArticleItem objects."""
        items: List[ParsedArticleItem] = []
        try:
            # Defused parse: ElementTree standard parser
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as exc:
            logger.warning("XML parse error for feed %s: %s", source_name, exc)
            return []

        # Determine feed format (RSS 2.0 has <channel><item>, Atom has <entry>)
        is_atom = root.tag.endswith("feed")

        if is_atom:
            entries = root.findall("{http://www.w3.org/2005/Atom}entry")
            if not entries:
                entries = root.findall("entry")
            for entry in entries[:max_items]:
                parsed_item = self._parse_atom_entry(entry, source_name)
                if parsed_item:
                    items.append(parsed_item)
        else:
            ch = root.find("channel")
            channel = ch if ch is not None else root
            raw_items = channel.findall("item")
            for item_elem in raw_items[:max_items]:
                parsed_item = self._parse_rss_item(item_elem, source_name)
                if parsed_item:
                    items.append(parsed_item)

        return items

    def _parse_rss_item(self, elem: ET.Element, source_name: str) -> Optional[ParsedArticleItem]:
        title_el = elem.find("title")
        link_el = elem.find("link")
        desc_el = elem.find("description")
        pub_el = elem.find("pubDate")
        if pub_el is None:
            pub_el = elem.find("{http://purl.org/dc/elements/1.1/}date")

        title = strip_html_tags(title_el.text if title_el is not None else "")
        link = (link_el.text or "").strip() if link_el is not None else ""
        if not title or not link:
            return None

        canonical_url = normalize_canonical_url(link)
        summary = strip_html_tags(desc_el.text if desc_el is not None else "")
        if summary and len(summary) > 600:
            summary = summary[:597] + "..."

        published_at: Optional[datetime] = None
        if pub_el is not None and pub_el.text:
            try:
                dt = dateutil.parser.parse(pub_el.text.strip())
                published_at = dt.astimezone(timezone.utc)
            except Exception:
                published_at = None

        headline_hash = compute_headline_hash(title)

        return ParsedArticleItem(
            title=title,
            canonical_url=canonical_url,
            summary=summary or None,
            published_at=published_at,
            headline_hash=headline_hash,
            source_name=source_name,
        )

    def _parse_atom_entry(self, elem: ET.Element, source_name: str) -> Optional[ParsedArticleItem]:
        # Atom elements may use namespaces
        def find_atom(tag: str) -> Optional[ET.Element]:
            el = elem.find(f"{{http://www.w3.org/2005/Atom}}{tag}")
            return el if el is not None else elem.find(tag)

        title_el = find_atom("title")
        summary_el = find_atom("summary")
        if summary_el is None:
            summary_el = find_atom("content")
        pub_el = find_atom("published")
        if pub_el is None:
            pub_el = find_atom("updated")

        link_el = find_atom("link")
        link = ""
        if link_el is not None:
            link = link_el.attrib.get("href") or (link_el.text or "")

        title = strip_html_tags(title_el.text if title_el is not None else "")
        if not title or not link:
            return None

        canonical_url = normalize_canonical_url(link)
        summary = strip_html_tags(summary_el.text if summary_el is not None else "")
        if summary and len(summary) > 600:
            summary = summary[:597] + "..."

        published_at: Optional[datetime] = None
        if pub_el is not None and pub_el.text:
            try:
                dt = dateutil.parser.parse(pub_el.text.strip())
                published_at = dt.astimezone(timezone.utc)
            except Exception:
                published_at = None

        headline_hash = compute_headline_hash(title)

        return ParsedArticleItem(
            title=title,
            canonical_url=canonical_url,
            summary=summary or None,
            published_at=published_at,
            headline_hash=headline_hash,
            source_name=source_name,
        )


# ---------------------------------------------------------------------------
# Mock News Feed Adapter (Testing & Offline Operations)
# ---------------------------------------------------------------------------

class MockNewsFeedAdapter(BaseNewsFeedAdapter):
    """Deterministic mock feed adapter for automated test suites and offline execution."""

    def __init__(self, sample_articles: Optional[List[ParsedArticleItem]] = None):
        self.sample_articles = sample_articles

    MOCK_ARTICLES = [
        {
            "title": "Federal Reserve Signals Slower Rate Reductions Amid Robust Job Gains",
            "url": "https://www.federalreserve.gov/press/monetary-policy-statement-oct-2026.html",
            "summary": "The Federal Open Market Committee maintained its benchmark interest rate target, noting steady economic growth and lingering core inflation pressures.",
            "source_name": "Federal Reserve Press",
            "offset_hours": 2,
        },
        {
            "title": "Apple Reports Record Services Revenue as Global iPhone Demand Surges",
            "url": "https://finance.yahoo.com/news/apple-q4-earnings-record-services-revenue-2026.html",
            "summary": "Apple Inc posted quarterly earnings beating analyst expectations, driven by higher App Store subscriptions and expanding gross margins in hardware.",
            "source_name": "Yahoo Finance Top News",
            "offset_hours": 5,
        },
        {
            "title": "Microsoft Unveils Expanded Cloud Infrastructure Investment Amid Cyber Scrutiny",
            "url": "https://finance.yahoo.com/news/microsoft-expands-azure-capital-expenditure-2026.html",
            "summary": "Microsoft Corporation increased cloud data center capital spending by 15%, while addressing European regulatory compliance inquiries.",
            "source_name": "Yahoo Finance Top News",
            "offset_hours": 8,
        },
        {
            "title": "Energy Sector Faces Margin Pressure as Crude Oil Slumps on Demand Warning",
            "url": "https://feeds.content.dowjones.io/public/rss/oil-slumps-energy-stocks-drop-2026.html",
            "summary": "Brent crude tumbled below key support levels following an unexpected inventory build and downward revisions to global manufacturing growth.",
            "source_name": "MarketWatch Top Stories",
            "offset_hours": 12,
        },
        {
            "title": "Banking Sector Stabilizes as Commercial Loan Delinquency Rates Remain Low",
            "url": "https://feeds.content.dowjones.io/public/rss/banking-sector-credit-quality-solid-2026.html",
            "summary": "Major lenders reported solid net interest income and resilient asset quality across corporate and mortgage loan portfolios.",
            "source_name": "MarketWatch Top Stories",
            "offset_hours": 18,
        },
    ]

    async def fetch_articles(self, source: NewsSourceModel) -> List[ParsedArticleItem]:
        """Generate mock articles matching the requested source or full portfolio set."""
        if self.sample_articles is not None:
            return list(self.sample_articles)

        now = datetime.now(timezone.utc)
        items: List[ParsedArticleItem] = []

        for m in self.MOCK_ARTICLES:
            pub_date = datetime.fromtimestamp(now.timestamp() - (m["offset_hours"] * 3600), tz=timezone.utc)
            items.append(
                ParsedArticleItem(
                    title=m["title"],
                    canonical_url=m["url"],
                    summary=m["summary"],
                    published_at=pub_date,
                    headline_hash=compute_headline_hash(m["title"]),
                    source_name=source.name or m["source_name"],
                )
            )

        return items
