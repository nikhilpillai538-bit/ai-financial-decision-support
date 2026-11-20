# AI-Powered Personal Financial Portfolio Management and Decision Support System

An end-to-end, multi-tier personal wealth intelligence and financial decision-support platform combining rigorous deterministic financial engineering (Modern Portfolio Theory, annuity mathematics, cash-flow forecasting) with an evidence-grounded AI explanation assistant and natural-language financial news intelligence.

---

## System Architecture Overview

```
                                  +------------------------------------------+
                                  |     Next.js / React 19 Web Dashboard     |
                                  |  (TypeScript, Tailwind CSS, Recharts)   |
                                  +--------------------+---------------------+
                                                       |
                                               REST / JSON APIs
                                           Bearer JWT Authentication
                                                       |
                                                       v
                                  +--------------------+---------------------+
                                  |         FastAPI Backend Engine           |
                                  |     (Python 3.12, Decimal Precision)     |
                                  +----+---------------+----------------+----+
                                       |               |                |
           +---------------------------+               |                +---------------------------+
           |                                           |                                            |
           v                                           v                                            v
+---------------------+                     +---------------------+                      +---------------------+
| Deterministic Math  |                     | AI / FinBERT Layer  |                      | PostgreSQL Database |
| - MPT Sharpe Solver |                     | - Grounded LLM Chat |                      | - Multi-User Tables |
| - Annuity SIP Calc  |                     | - FinBERT Sentiment |                      | - Strict Isolation  |
| - Cash-Flow Forecast|                     | - Injection Defense |                      | - Alembic Migration |
| - Emergency Runway  |                     | - Thematic Clusters |                      | - ACID Repositories |
+---------------------+                     +---------------------+                      +---------------------+
```

---

## Completed Phases (Phases 1–11)

- **Phase 1: Deterministic Financial Engine** — FastAPI REST foundations, exact monetary arithmetic using Python `Decimal`, and fundamental personal financial health indices.
- **Phase 2: Transaction Management & CSV Ingestion** — Bank statement CSV parser, categorization engine, transaction ledger, and monthly aggregate cash-flow metrics.
- **Phase 3: Emergency Fund & Cash-Flow Forecasting** — 3–6 month essential expense reserve models, runway calculations, and 30-day linear regression cash-flow forecasts with day-of-week seasonality.
- **Phase 4: PostgreSQL Persistence & Data Integrity** — SQLAlchemy ORM schema, Alembic migration pipeline, Foreign Key constraints, unique indices, and atomic repository transactions.
- **Phase 5: User Authentication & Multi-Tenant Data Isolation** — Argon2id password hashing, OAuth2 Password Bearer flow, JWT access & refresh token rotation, strict User A vs User B cryptographic isolation.
- **Phase 6: Portfolio Management & Asset Allocation Foundation** — Multi-currency portfolio accounts, asset registry (Equity, Fixed Income, Cash, Alternatives), holdings tracking, portfolio valuation, and allocation variance analysis.
- **Phase 7: Modern Portfolio Theory (MPT) & Optimization Engine** — Markowitz mean-variance optimization, bounded simplex projection, Maximum Sharpe tangency portfolio, Global Minimum Volatility, Ledoit-Wolf covariance shrinkage, and illustrative rebalancing trade generation.
- **Phase 8: Goal-Based Planning, SIP Calculators & Glide Paths** — Forward ordinary annuity compounding, step-up SIPs, reverse target-amount solving, portfolio allocation drift detection, and life-cycle risk glide paths.
- **Phase 9: Grounded LLM Financial Assistant & Decision Support** — Multi-turn conversational interface, domain fact retrieval grounding (holdings, transactions, forecasts), prompt injection protection delimiters, deterministic what-if scenario simulations, and financial health reports.
- **Phase 10: Financial News Intelligence & FinBERT Sentiment Analysis** — RSS/Atom feed parser, cryptographic hash deduplication, FinBERT sentiment scoring (positive/negative/neutral), sector breakdowns, and portfolio asset relevance entity linking.
- **Phase 11: Full-Stack Frontend Dashboard & Experience** — Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Recharts visualizations, 10 authenticated views, zero data fabrication policy, and strict client-side session management.
- **Phase 12: End-to-End Quality Assurance, Security Hardening & Deployment Readiness** — OWASP security headers, configurable CORS, 10MB upload payload bounds, 23 deterministic financial math edge case tests, 6 cross-user tenant isolation tests, ESLint & TypeScript clean build, multi-container Docker Compose stack, and GitHub Actions CI pipeline.
- **Phase 13: Portfolio Stress Testing, Historical Backtesting & Monte Carlo Simulation** — Deterministic macroeconomic crisis shocks, historical replay with anti-lookahead bias and turnover fees, vectorized Geometric Brownian Motion stochastic wealth simulator with percentile fan charts, and goal scenario trade-off comparison matrix.

---

## Phase 13 Analytics & Simulation Engine

### 1. Macroeconomic Stress Testing Methodology
- **Linear Shock Model**: Simulates immediate asset-class and ticker-level price shocks without relying on fragile correlation assumptions during crises.
- **Curated Presets**: Includes historical market shock templates:
  - `equity_market_crash`: Equities -25%, Fixed Income +3% (flight to safety), Crypto -40%.
  - `bond_market_decline`: Fixed Income -12%, Equities -8%, Cash +2% (rate hike regime).
  - `stagflation_shock`: Commodities +25%, Equities -20%, Fixed Income -15%, Cash -5%.
  - `tech_sector_rout`: Tech equities -35%, broad equities -15%.
  - `covid_liquidity_shock`: Equities -30%, Real Estate -20%, Commodities -35%.
- **Unpriced Asset Safety**: Missing or unpriced holdings emit explicit warnings and are excluded from linear shock totals rather than silently assumed to be zero.
- **Loss Attribution**: Computes exact percentage contribution to total portfolio dollar losses by asset and asset category.

### 2. Historical Portfolio Backtesting Methodology
- **Anti-Lookahead Bias Rule**: Decisions and rebalancing actions execute strictly at trading date $t$ using prices known on or before $t$. Future prices are never utilized for historical weighting.
- **Data Gap Handling**: Non-overlapping exchange holidays are forward-filled up to 1 day; series with fewer than 5 aligned observations or missing assets trigger explicit data-readiness errors without fabricating returns.
- **Periodic Rebalancing Schedules**: `none` (buy & hold), `monthly`, `quarterly`, `annual`, and `drift_5pct` (rebalance when allocation drifts $> 5\%$).
- **Turnover & Fee Friction**: Models transaction costs in basis points on rebalance turnover volume (`fee_bps`).
- **Performance Metrics**: Cumulative Return, CAGR (annualized return), Annualized Volatility, Peak-to-Trough Maximum Drawdown, Sharpe Ratio, and Calmar Ratio.
- **Corporate Action Assumption**: Adjusted close prices account for historical stock splits and reflect dividend reinvestment.

### 3. Stochastic Monte Carlo Simulation Methodology
- **Vectorized Geometric Brownian Motion**: Models stochastic wealth paths via continuous log-normal diffusion with Itô drift:
  $$\Delta t = \frac{1}{12}, \quad \alpha = \left(\mu - \frac{1}{2}\sigma^2\right)\Delta t, \quad \beta = \sigma\sqrt{\Delta t}$$
  $$W_{s, t} = (W_{s, t-1} + C) \cdot \exp(\alpha + \beta Z_{s, t})$$
- **Zero-Volatility Collapse**: When $\sigma = 0.0$, the stochastic engine collapses to deterministic ordinary annuity compounding matching Phase 8 SIP formulas.
- **Percentile Fan Trajectory**: Computes the 5th, 25th, 50th (median), 75th, and 95th percentile curves across time steps.
- **Goal Achievement Probability**: Calculates empirical frequency of paths exceeding target corpus ($W_{s, M} \ge G$).
- **Seed Reproducibility**: Supports fixed integer random seeds (`seed=42`) for deterministic verification.

### 4. Goal Multi-Scenario Trade-Off Matrix
- **Side-by-Side Evaluation**: Simultaneously evaluates up to 6 hypothetical parameter variations (contribution deltas, deadline extensions, return rates).
- **Dual Perspective**: Compares deterministic future value against stochastic Monte Carlo success probability.
- **Zero Database Mutation**: All simulations are read-only and never alter user-persisted goal records.

---

## Quickstart Guide

### Prerequisites
- Python 3.12+
- Node.js 18+ and npm
- PostgreSQL 15+ (or SQLite local fallback for quick tests)

---

### 1. Backend Setup & Run

```powershell
cd backend

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install backend dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI server (runs on http://127.0.0.1:8000)
uvicorn app.main:app --reload --port 8000
```

To run all backend tests:
```powershell
pytest tests/ -v
# 591 tests passing (100% pass rate)
```

---

### 2. Frontend Setup & Run

```powershell
cd frontend

# Install frontend dependencies
npm install

# Start Next.js development server (runs on http://localhost:3000)
npm run dev

# Run Vitest test suite
npm test
# 23 tests passing

# Run TypeScript type-checker
npm run typecheck

# Run ESLint check
npm run lint

# Compile production build
npm run build
```

---

### 3. One-Click Batch Launchers (Windows)

For streamlined local development and execution without manually managing terminal windows:

- **`start.bat`**: Automatically initializes the Python virtualenv (or creates one if missing), installs required backend and frontend dependencies, applies database migrations, starts both FastAPI (port 8000) and Next.js (port 3000) in background windows, and launches your default browser at `http://localhost:3000`.
- **`stop.bat`**: Gracefully terminates running background Uvicorn and Node/Next processes on ports 8000 and 3000.
- **`start_dev.bat`**: Runs backend and frontend development servers with live reload enabled.

---

### 4. Containerized Deployment (Docker Compose)

The entire multi-tier stack (PostgreSQL 16, FastAPI Backend, Next.js Frontend) can be orchestrated with a single command:

```bash
docker-compose up --build
```

- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI API & OpenAPI Docs**: `http://localhost:8000/docs`
- **Health Check Endpoint**: `http://localhost:8000/health`
- **PostgreSQL Database**: Port 5432 with persistent Docker volume `ai_portfolio_postgres_data`

To run in detached background mode:
```bash
docker-compose up -d
```

To stop and tear down containers:
```bash
docker-compose down
```

---

## Regulatory & Decision-Support Notice

> [!CAUTION]
> **Educational and Decision Support Only:**
> This platform is engineered exclusively for personal financial education, analytics, and decision-support. It does not provide registered financial advice, does not recommend securities or specific investment vehicles, and does not execute automated trades. All optimization weights, rebalancing trades, and what-if simulations are illustrative models. Users bear sole responsibility for their personal investment choices.
