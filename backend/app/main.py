"""
AI Financial Decision Support System — FastAPI application entry point.

Phase 4: PostgreSQL Integration, Data Integrity, and Persistence Hardening.
All Phase 1, Phase 2, and Phase 3 behaviour is preserved.

Run from the ``backend/`` directory with:

    uvicorn app.main:app --reload

Interactive docs: http://127.0.0.1:8000/docs
"""

import logging
import os
from contextlib import asynccontextmanager

try:
    import truststore
    truststore.inject_into_ssl()
except Exception:
    pass

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.ai import ai_router
from app.auth import auth_router
from app.db.base import Base
from app.db.session import check_db_connection, engine
from app.financial_analysis import analysis_router, profile_router
from app.goal_router import goal_router
from app.news import news_router
from app.optimization_router import optimization_router
from app.portfolio_router import portfolio_router
from app.schemas import HealthResponse
from app.simulation_router import simulation_router
from app.transactions import router as transactions_router

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown lifecycle.

    On startup:
    - Tests database connection safely without leaking credentials.
    - Creates database tables if they do not exist (idempotent, never deletes/resets).
    """
    is_connected, msg = check_db_connection(engine)
    if is_connected:
        logger.info("Database: %s", msg)
        try:
            Base.metadata.create_all(bind=engine, checkfirst=True)
            logger.info("Database schema verified/initialized.")
            from app.seed import ensure_seed_data
            ensure_seed_data(engine)
        except Exception as e:
            logger.warning("Could not auto-create tables or seed: %s", type(e).__name__)
    else:
        logger.warning("Database connection warning: %s", msg)

    yield

    # Clean shutdown tasks if any
    pass


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Financial Decision Support System",
    description=(
        "Phase 12 — End-to-End Quality Assurance, Security Hardening, Performance Optimization, "
        "and Deployment Readiness. Built on deterministic Modern Portfolio Theory, financial planning engines, "
        "FinBERT sentiment intelligence, and isolated multi-tenant architecture."
    ),
    version="12.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Security Middlewares
# ---------------------------------------------------------------------------

# Configurable CORS
cors_env = os.getenv("CORS_ORIGINS", "").strip()
if cors_env:
    allowed_origins = [orig.strip() for orig in cors_env.split(",") if orig.strip()]
else:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",  # permissive in default local development mode
    ]

allow_creds = "*" not in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=allow_creds,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Inject standard OWASP-recommended security headers into all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    return response


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router)           # Phase 5: /auth/*
app.include_router(transactions_router)   # Phase 1 & 2: /transactions/*
app.include_router(profile_router)        # Phase 3: /financial-profile/*
app.include_router(analysis_router)       # Phase 3: /financial-analysis/*
app.include_router(portfolio_router)      # Phase 6: /portfolios/*, /assets/*, /investment-goals/*
app.include_router(optimization_router)   # Phase 7: /market-data/*, /portfolios/{id}/optimize, /portfolios/{id}/optimization-history
app.include_router(goal_router)           # Phase 8: /calculators/*, /investment-goals/{id}/projection, /portfolios/{id}/drift, glide paths
app.include_router(ai_router)             # Phase 9: /ai/*
app.include_router(news_router)           # Phase 10: /news/*
app.include_router(simulation_router)     # Phase 13: /portfolio/stress-tests, /portfolio/backtests, /portfolio/monte-carlo, /goals/{id}/scenario-comparison


# ---------------------------------------------------------------------------
# Core endpoints
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Operational health check",
    tags=["System"],
)
def health_check() -> HealthResponse:
    """Return verified operational health status without leaking paths or credentials."""
    is_connected, _ = check_db_connection(engine)
    db_status = "connected" if is_connected else "disconnected"

    from app.ai.config import get_llm_settings
    ai_settings = get_llm_settings()
    ai_provider = ai_settings.provider

    overall_status = "ok" if is_connected else "degraded"

    return HealthResponse(
        status=overall_status,
        project="AI Financial Decision Support System",
        database=db_status,
        ai_provider=ai_provider,
        version="12.0.0",
    )
