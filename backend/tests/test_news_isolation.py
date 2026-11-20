"""
Security and Multi-User Data Isolation tests for Phase 10 News Intelligence.

Verifies:
- Strict multi-tenant isolation: User A only sees relevance and insights for User A's holdings
- User B only sees relevance and insights for User B's holdings
- Cross-tenant portfolio tampering prevention (User A cannot request insights for User B's portfolio ID)
- Public vs Authenticated endpoint access control:
  - /news is public (200 OK unauthenticated)
  - /news/{article_id} is public (200 OK unauthenticated)
  - /news/sentiment/summary is public (200 OK unauthenticated)
  - /news/portfolio-relevance requires valid authentication (401 Unauthorized unauthenticated)
  - /news/portfolio-insights requires valid authentication (401 Unauthorized unauthenticated)
"""

from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth.dependencies import get_current_user
from app.db.base import Base
from app.db.models import (
    AssetModel,
    NewsArticleModel,
    NewsSourceModel,
    PortfolioHoldingModel,
    PortfolioModel,
    UserModel,
)
from app.db.session import get_db
from app.main import app

USER_A = UserModel(
    id="user-a-uuid-1111",
    email="usera@example.com",
    password_hash="mockhash_a",
    is_active=True,
)

USER_B = UserModel(
    id="user-b-uuid-2222",
    email="userb@example.com",
    password_hash="mockhash_b",
    is_active=True,
)


@pytest.fixture()
def db_session() -> Session:
    """Isolated in-memory database session."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()

    # Pre-populate both users
    session.add(
        UserModel(
            id=USER_A.id,
            email=USER_A.email,
            password_hash=USER_A.password_hash,
            is_active=True,
        )
    )
    session.add(
        UserModel(
            id=USER_B.id,
            email=USER_B.email,
            password_hash=USER_B.password_hash,
            is_active=True,
        )
    )

    # Seed news articles: one for AAPL (Tech) and one for XOM (Energy)
    src = NewsSourceModel(
        id=str(uuid.uuid4()),
        name="MarketWatch",
        feed_url="https://feeds.content.dowjones.io/public/rss/mw.xml",
        is_active=True,
    )
    session.add(src)
    session.flush()

    art_apple = NewsArticleModel(
        id="art-apple-id",
        source_id=src.id,
        title="Apple (AAPL) Announces Next-Gen Mac Hardware",
        canonical_url="https://feeds.content.dowjones.io/aapl-hardware.html",
        summary="Apple Inc revealed latest Silicon chips for high-performance laptops.",
        published_at=datetime.now(timezone.utc),
        headline_hash="hash-aapl",
        sentiment_label="positive",
        sentiment_score=Decimal("0.8000"),
    )
    art_exxon = NewsArticleModel(
        id="art-exxon-id",
        source_id=src.id,
        title="ExxonMobil (XOM) Expands Offshore Petroleum Drilling",
        canonical_url="https://feeds.content.dowjones.io/xom-drilling.html",
        summary="Exxon petroleum division reported production gains in deepwater basins.",
        published_at=datetime.now(timezone.utc),
        headline_hash="hash-xom",
        sentiment_label="neutral",
        sentiment_score=Decimal("0.0000"),
    )
    session.add_all([art_apple, art_exxon])
    session.commit()

    try:
        yield session
    finally:
        session.close()


class TestPublicVsAuthenticatedBoundaries:
    """Tests ensuring public endpoints remain accessible and private endpoints require auth."""

    def test_public_news_endpoints_allow_unauthenticated_access(self, db_session: Session):
        app.dependency_overrides[get_db] = lambda: db_session
        # Ensure get_current_user is NOT overridden so real auth dependency runs
        app.dependency_overrides.pop(get_current_user, None)

        with TestClient(app) as client:
            # 1. /news is public
            r_list = client.get("/news")
            assert r_list.status_code == 200

            # 2. /news/{id} is public
            r_single = client.get("/news/art-apple-id")
            assert r_single.status_code == 200

            # 3. /news/sentiment/summary is public
            r_summary = client.get("/news/sentiment/summary")
            assert r_summary.status_code == 200

        app.dependency_overrides.clear()

    def test_protected_news_endpoints_reject_unauthenticated_access(self, db_session: Session):
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides.pop(get_current_user, None)

        with TestClient(app) as client:
            # 1. /news/portfolio-relevance requires auth
            r_rel = client.get("/news/portfolio-relevance")
            assert r_rel.status_code == 401

            # 2. /news/portfolio-insights requires auth
            r_ins = client.post("/news/portfolio-insights")
            assert r_ins.status_code == 401

        app.dependency_overrides.clear()


class TestMultiUserPortfolioNewsIsolation:
    """Tests guaranteeing complete isolation of news relevance across distinct users."""

    def test_portfolio_news_relevance_user_isolation(self, db_session: Session):
        # Setup User A with AAPL holding
        port_a = PortfolioModel(
            id=str(uuid.uuid4()),
            user_id=USER_A.id,
            name="User A Tech Portfolio",
            base_currency="USD",
        )
        asset_a = AssetModel(
            id=str(uuid.uuid4()),
            user_id=USER_A.id,
            symbol="AAPL",
            name="Apple Inc",
            asset_class="equity",
            instrument_type="Technology",
        )
        db_session.add_all([port_a, asset_a])
        db_session.flush()
        db_session.add(
            PortfolioHoldingModel(
                id=str(uuid.uuid4()),
                portfolio_id=port_a.id,
                asset_id=asset_a.id,
                quantity=Decimal("10"),
                average_purchase_price=Decimal("150.00"),
            )
        )

        # Setup User B with XOM holding
        port_b = PortfolioModel(
            id=str(uuid.uuid4()),
            user_id=USER_B.id,
            name="User B Energy Portfolio",
            base_currency="USD",
        )
        asset_b = AssetModel(
            id=str(uuid.uuid4()),
            user_id=USER_B.id,
            symbol="XOM",
            name="ExxonMobil",
            asset_class="equity",
            instrument_type="Energy",
        )
        db_session.add_all([port_b, asset_b])
        db_session.flush()
        db_session.add(
            PortfolioHoldingModel(
                id=str(uuid.uuid4()),
                portfolio_id=port_b.id,
                asset_id=asset_b.id,
                quantity=Decimal("25"),
                average_purchase_price=Decimal("105.00"),
            )
        )
        db_session.commit()

        app.dependency_overrides[get_db] = lambda: db_session

        # 1. As User A: must see Apple, must NOT see ExxonMobil
        app.dependency_overrides[get_current_user] = lambda: USER_A
        with TestClient(app) as client_a:
            r_a = client_a.get("/news/portfolio-relevance")
            assert r_a.status_code == 200
            data_a = r_a.json()
            assert data_a["user_id"] == USER_A.id
            matches_a = data_a["matches"]
            matched_entities_a = {m["matched_entity"] for m in matches_a}
            assert "AAPL" in matched_entities_a or "Apple Inc" in matched_entities_a
            assert "XOM" not in matched_entities_a
            assert "ExxonMobil" not in matched_entities_a

        # 2. As User B: must see ExxonMobil, must NOT see Apple
        app.dependency_overrides[get_current_user] = lambda: USER_B
        with TestClient(app) as client_b:
            r_b = client_b.get("/news/portfolio-relevance")
            assert r_b.status_code == 200
            data_b = r_b.json()
            assert data_b["user_id"] == USER_B.id
            matches_b = data_b["matches"]
            matched_entities_b = {m["matched_entity"] for m in matches_b}
            assert "XOM" in matched_entities_b or "ExxonMobil" in matched_entities_b
            assert "AAPL" not in matched_entities_b
            assert "Apple Inc" not in matched_entities_b

        # 3. Cross-Tenant Tampering Check: User A requests insights specifying User B's portfolio_id
        app.dependency_overrides[get_current_user] = lambda: USER_A
        with TestClient(app) as client_tamper:
            r_tamper = client_tamper.post(f"/news/portfolio-insights?portfolio_id={port_b.id}")
            assert r_tamper.status_code == 200
            data_tamper = r_tamper.json()
            # User A cannot view User B's portfolio holdings; insights for User B's portfolio ID return empty/unmatched
            assert data_tamper["user_id"] == USER_A.id
            assert data_tamper["relevance_matches_count"] == 0

        app.dependency_overrides.clear()
