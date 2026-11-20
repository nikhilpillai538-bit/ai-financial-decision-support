# AI Financial Decision Support System

A FastAPI backend providing deterministic financial summaries, persistent transaction management, rule-based categorization, and CSV bulk import.

---

## Project Structure

```
backend/
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, health endpoint, routers
│   ├── schemas.py           # Pydantic request/response models (Phase 1 & 2)
│   ├── calculations.py      # Deterministic Decimal-based financial logic (Phase 1)
│   ├── categorization.py    # Keyword-based transaction categorization (Phase 2)
│   ├── transactions.py      # /transactions router endpoints (Phase 1, 2 & 5)
│   ├── financial_analysis.py # /financial-analysis router endpoints (Phase 3 & 5)
│   ├── emergency_fund.py    # Emergency fund analysis engine (Phase 3)
│   ├── forecasting.py       # 30-day cash-flow forecast engine (Phase 3)
│   ├── portfolio_schemas.py # Pydantic models for portfolios, holdings, goals, allocations (Phase 6)
│   ├── portfolio_router.py  # /portfolios, /assets, /investment-goals endpoints (Phase 6)
│   ├── portfolio_valuation.py # Deterministic Decimal-based portfolio valuation (Phase 6)
│   ├── allocation_analysis.py # Asset allocation variance & status engine (Phase 6)
│   ├── optimization_validator.py # Pre-optimization readiness validator (Phase 6)
│   ├── optimization_schemas.py # Pydantic models for MPT optimization & market data (Phase 7)
│   ├── historical_data.py   # Historical prices parser, returns matrix & covariance shrinkage (Phase 7)
│   ├── portfolio_optimization.py # MPT engine: min-vol, max-Sharpe, target-return, frontier (Phase 7)
│   ├── optimization_router.py # /portfolios/{id}/optimize, /market-data endpoints (Phase 7)
│   ├── goal_schemas.py      # Pydantic models for SIP, goals, drift, and glide paths (Phase 8)
│   ├── sip_calculator.py    # Forward & Reverse SIP ordinary annuity calculation engines (Phase 8)
│   ├── goal_planning.py     # Goal progress, shortfall/surplus, and required contributions (Phase 8)
│   ├── portfolio_drift.py   # Portfolio allocation drift detection & illustrative rebalancing (Phase 8)
│   ├── glide_path.py        # Risk-aware investment glide path & milestone generator (Phase 8)
│   ├── goal_router.py       # /calculators/*, /investment-goals/*, /portfolios/{id}/drift endpoints (Phase 8)
│   ├── ai/                  # LLM Financial Intelligence & Explanation Layer (Phase 9)
│   │   ├── __init__.py
│   │   ├── config.py        # LLMSettings & environment resolution
│   │   ├── schemas.py       # AI chat, message, context, health, scenario schemas
│   │   ├── provider.py      # Abstract LLM provider, OpenAI, Anthropic, Mock, Unconfigured
│   │   ├── financial_context.py # Multi-domain verified facts context builder
│   │   ├── guardrails.py    # Injection defense, output validators & deterministic fallbacks
│   │   ├── scenario_evaluator.py # Deterministic what-if simulations (zero DB mutation)
│   │   ├── insights_service.py # Domain explanations & health assessment synthesis
│   │   ├── assistant.py     # Multi-turn assistant, conversation threads, memory
│   │   └── router.py        # /ai/* endpoints (chat, threads, health-report, scenario)
│   ├── news/                # Financial News Intelligence & FinBERT Sentiment (Phase 10)
│   │   ├── __init__.py
│   │   ├── config.py        # NewsSettings, SSRF domains, feeds, timeouts
│   │   ├── schemas.py       # Article, source, refresh, sentiment, relevance schemas
│   │   ├── adapters.py      # RSS 2.0 / Atom parser, URL deduplication, SSRF validator
│   │   ├── sentiment.py     # FinBERT Hugging Face analyzer & Mock lexicon analyzer
│   │   ├── relevance.py     # Deterministic portfolio ticker/company/sector relevance matcher
│   │   ├── aggregation.py   # 24h/7d/30d market sentiment aggregator & sector breakdown
│   │   ├── insights_service.py # Portfolio news synthesis, themes, citation & disclaimers
│   │   └── router.py        # /news/* endpoints
│   ├── repository.py        # File-based fallback repository interfaces
│   ├── auth/                # Authentication & Session Module (Phase 5)
│   │   ├── __init__.py
│   │   ├── dependencies.py  # get_current_user, HTTPBearer auth dependency
│   │   ├── router.py        # /auth endpoints (register, login, me, refresh, logout)
│   │   ├── schemas.py       # Auth request and response Pydantic models
│   │   └── security.py      # Argon2id hashing, JWT handling, rate limiting
│   └── db/                  # Persistence Layer (Phase 4-10)
│       ├── __init__.py
│       ├── config.py        # DB settings & URL masking
│       ├── models.py        # SQLAlchemy ORM models (User, Portfolio, Asset, Holding, Goal, Allocation, HistoricalPrice, OptimizationRun, NewsSource, NewsArticle)
│       ├── session.py       # Engine & scoped session management
│       └── repositories/
│           ├── transaction_repo.py  # User-scoped transaction CRUD
│           ├── profile_repo.py      # User-scoped financial profile CRUD
│           ├── user_repo.py         # User and session repository
│           ├── portfolio_repo.py    # User-scoped portfolio, asset, holding, goal, drift & optimization CRUD
│           └── news_repo.py         # News sources and articles persistence & queries (Phase 10)
├── tests/
│   ├── conftest.py                    # Shared fixtures & test database setup
│   ├── test_calculations.py           # Phase 1 unit tests
│   ├── test_api.py                    # Phase 1 API integration tests
│   ├── test_transactions_phase2.py    # Phase 2 test suite
│   ├── test_emergency_fund.py         # Phase 3 emergency fund unit tests
│   ├── test_financial_analysis_api.py # Phase 3 forecasting & API tests
│   ├── test_db_models.py              # Phase 4 database models & constraints
│   ├── test_db_repositories.py        # Phase 4 repository layer tests
│   ├── test_db_api_integration.py     # Phase 4 database API tests
│   ├── test_db_migrations.py          # Phase 4 Alembic migration tests
│   ├── test_auth_account.py           # Phase 5 registration, login & rate limiting
│   ├── test_session_security.py       # Phase 5 JWT, refresh rotation & reuse detection
│   ├── test_user_isolation.py         # Phase 5 multi-user data isolation tests
│   ├── test_portfolio_models.py       # Phase 6 models, constraints & schema validation
│   ├── test_portfolio_valuation.py    # Phase 6 deterministic valuation & currency tests
│   ├── test_allocation_analysis.py    # Phase 6 asset allocation variance tests
│   ├── test_optimization_readiness.py # Phase 6 pre-optimization validator tests
│   ├── test_portfolio_api.py          # Phase 6 portfolio, asset, holding, goal API tests
│   ├── test_portfolio_isolation.py    # Phase 6 cross-user isolation security tests
│   ├── test_historical_data.py        # Phase 7 CSV parser, alignment & shrinkage unit tests
│   ├── test_portfolio_optimization.py # Phase 7 MPT solvers, bounds & rebalancing tests
│   ├── test_optimization_api.py       # Phase 7 API integration & error tests
│   ├── test_optimization_isolation.py # Phase 7 multi-user optimization isolation tests
│   ├── test_sip_calculator.py         # Phase 8 Forward & Reverse SIP unit tests
│   ├── test_goal_planning.py          # Phase 8 Goal progress, shortfall & portfolio integration tests
│   ├── test_portfolio_drift.py        # Phase 8 Drift threshold & rebalancing reconciliation tests
│   ├── test_glide_path.py             # Phase 8 Glide path milestone & simplex constraint tests
│   ├── test_goal_api.py               # Phase 8 API integration tests
│   ├── test_goal_isolation.py         # Phase 8 multi-user goal and drift isolation tests
│   ├── test_llm_provider.py           # Phase 9 LLM provider abstraction tests
│   ├── test_financial_context.py      # Phase 9 Multi-domain factual context tests
│   ├── test_guardrails_and_grounding.py # Phase 9 Injection defense & schema validation tests
│   ├── test_scenario_evaluator.py     # Phase 9 Deterministic what-if simulations
│   ├── test_insights_service.py       # Phase 9 Domain-level financial health insights
│   ├── test_ai_assistant_api.py       # Phase 9 AI assistant conversational API tests
│   ├── test_ai_isolation.py           # Phase 9 Multi-user AI conversation isolation tests
│   ├── test_news_ingestion.py         # Phase 10 RSS feed parsing, SSRF defense, deduplication
│   ├── test_news_sentiment.py         # Phase 10 FinBERT & Mock sentiment classification tests
│   ├── test_news_relevance.py         # Phase 10 Portfolio ticker, company & sector matching
│   ├── test_news_aggregation.py       # Phase 10 24h/7d windows, percentages, sample size warnings
│   ├── test_news_api.py               # Phase 10 News endpoints & insights generation
│   ├── test_news_isolation.py         # Phase 10 Multi-tenant portfolio news isolation & auth tests
│   └── test_news_llm_integration.py   # Phase 10 Grounded context with untrusted publisher defense
├── data/                    # Local storage (gitignored)
├── migrations/              # JSON data migration scripts
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Requirements

- Python 3.12+
- Windows PowerShell

---

## Setup (Windows PowerShell)

### 1 — Create a virtual environment

```powershell
python -m venv .venv
```

### 2 — Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

> If you see an execution-policy error, run:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```

### 3 — Install dependencies

```powershell
pip install -r requirements.txt
```

### 4 — (Optional) Copy environment variables

```powershell
Copy-Item .env.example .env
```

---

## Running the Application

From the `backend/` directory with the virtual environment activated:

```powershell
uvicorn app.main:app --reload
```

The server starts at **http://127.0.0.1:8000**

---

## Interactive API Documentation

| UI | URL |
|---|---|
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |

---

## Running All Tests

```powershell
pytest tests/ -v
```

Run with short traceback output:

```powershell
pytest tests/ -v --tb=short
```

---

## API Reference — Phase 1 Endpoints (preserved)

### `GET /health`

Returns service health status.

**Response `200 OK`:**
```json
{ "status": "ok", "project": "AI Financial Decision Support System" }
```

---

### `POST /transactions/summary`

Stateless summary. Accepts a list of transactions in the request body and returns aggregated totals. **Does not store anything.**

**Request:**
```json
{
  "transactions": [
    { "date": "2024-01-15", "description": "Salary", "amount": "5000.00", "transaction_type": "income" },
    { "date": "2024-01-20", "description": "Rent",   "amount": "1200.00", "transaction_type": "expense" }
  ]
}
```

**Response `200 OK`:**
```json
{ "total_income": "5000.00", "total_expenses": "1200.00", "net_cash_flow": "3800.00", "transaction_count": 2 }
```

---

## API Reference — Phase 2 Endpoints

### `POST /transactions`

Create and persist a single transaction. Returns the stored record with a server-assigned UUID.

**Request:**
```json
{
  "date": "2026-10-20",
  "description": "Monthly salary",
  "amount": "45000.00",
  "transaction_type": "income",
  "category": "salary",
  "source": "manual"
}
```

**Response `201 Created`:**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "date": "2026-10-20",
  "description": "Monthly salary",
  "amount": "45000.00",
  "transaction_type": "income",
  "category": "salary",
  "source": "manual"
}
```

---

### `GET /transactions`

List stored transactions with optional filters.

**Query parameters:**

| Parameter | Type | Description |
|---|---|---|
| `start_date` | `YYYY-MM-DD` | Earliest transaction date (inclusive) |
| `end_date` | `YYYY-MM-DD` | Latest transaction date (inclusive) |
| `transaction_type` | `income` \| `expense` | Filter by type |
| `category` | string | Exact category match (case-insensitive) |

---

### `GET /transactions/{transaction_id}`

Return one stored transaction by ID. Returns `404` if not found.

---

### `DELETE /transactions/{transaction_id}`

Delete a stored transaction. Returns `404` if not found.

**Response `200 OK`:**
```json
{ "message": "Transaction deleted successfully.", "transaction_id": "..." }
```

---

### `GET /transactions/stored-summary`

Summarise stored transactions using the Phase 1 calculation engine.
Supports the same query filters as `GET /transactions`.

**Response `200 OK`:**
```json
{ "total_income": "45000.00", "total_expenses": "12000.00", "net_cash_flow": "33000.00", "transaction_count": 5 }
```

---

### `POST /transactions/import-csv`

Import transactions from a CSV file upload.

**Form field:** `file` (multipart/form-data)

**Expected CSV format:**

```csv
date,description,amount,transaction_type,category
2026-10-01,Monthly salary,45000.00,income,salary
2026-10-05,Rent payment,12000.00,expense,rent
2026-10-08,Swiggy order,350.00,expense,
2026-10-10,Electricity bill,1500.00,expense,
```

- `category` is optional. If absent or blank, the rule-based categorization engine assigns one automatically.
- Maximum **5 000 data rows** per file.
- File must be UTF-8 encoded.

**Response `200 OK`:**
```json
{
  "filename": "october.csv",
  "total_rows": 4,
  "imported": 4,
  "duplicates_skipped": 0,
  "rejected": 0,
  "errors": [],
  "imported_ids": ["...", "...", "...", "..."]
}
```

---

## CSV Import — Duplicate Detection

**Strategy:** A row is considered a suspected duplicate if an existing stored transaction (or another row in the same batch) has the same combination of:

- `date`
- `description` (case-insensitive, whitespace-stripped)
- `amount` (normalised to 2 decimal places)
- `transaction_type`

**Limitation:** Two genuinely different transactions on the same day with the same amount and description cannot be distinguished by this strategy. Duplicates are *suspected*, not confirmed. The decision to accept or reject remains with the user.

---

## CSV Import — Partial Import Policy

Valid rows are imported even when other rows in the same file are invalid. The response report makes the outcome explicit:

- `imported` — number of rows successfully saved.
- `duplicates_skipped` — rows skipped as suspected duplicates.
- `rejected` — rows rejected due to validation errors (bad date, zero amount, etc.).
- `errors` — per-row detail including the 1-based row number and reason.

---

## Transaction Categorization

Descriptions are matched against keyword rules in `app/categorization.py`.

| Category | Example keywords |
|---|---|
| `salary` | "salary", "payroll", "wages" |
| `rent` | "rent payment", "landlord" |
| `groceries` | "grocery", "supermarket", "DMart" |
| `utilities` | "electricity bill", "water bill", "internet bill" |
| `transport` | "uber", "petrol", "metro" |
| `healthcare` | "hospital", "pharmacy", "medical" |
| `education` | "tuition", "school fee", "course fee" |
| `entertainment` | "netflix", "movie", "spotify" |
| `shopping` | "amazon", "flipkart", "clothing" |
| `dining` | "swiggy", "zomato", "restaurant" |
| `investment` | "dividend", "mutual fund", "SIP return" |
| `insurance` | "LIC", "insurance premium" |
| `uncategorized` | (no rule matched) |

**Rules:**
- Matching is case-insensitive.
- First matching rule wins.
- A user-supplied category (other than `"uncategorized"`) is **always preserved** — auto-categorization is not applied.
- To add or modify rules, edit the `CATEGORY_RULES` list in [`app/categorization.py`](app/categorization.py).
- These are keyword rules, **not AI**. They cannot understand context or resolve ambiguity.

---

## Design Notes

- **Decimal arithmetic**: All monetary calculations use `decimal.Decimal` with `ROUND_HALF_UP`.
- **Repository pattern**: `app/repository.py` wraps the JSON file behind a `TransactionRepository` interface. Phase 3 can swap it for PostgreSQL without touching routers.
- **Dependency injection**: Tests override `get_repository()` to inject a temporary file-backed repo — real data is never touched.
- **No database** in Phase 2. Transactions persist in `data/transactions.json`.
- **No authentication** in Phase 2.
- **No AI or LLM** in Phase 2.

---

## Known Limitations (Phase 2)

1. **JSON file storage** is not suitable for concurrent multi-process deployments. Phase 3 will replace it with PostgreSQL.
2. **Duplicate detection** is heuristic — two genuinely identical transactions on the same day cannot be distinguished.
3. **Category rules** are keyword-based and may produce false positives for uncommon descriptions.
4. **No pagination** on `GET /transactions` — all records are returned in a single response.
5. **No update endpoint** — transactions cannot be modified after creation (delete and re-create instead).

---

## Phase 3 — Emergency Fund Analysis and 30-Day Cash-Flow Forecasting

### New endpoints

| Method | Path | Description |
|--------|------|-------------|
| `PUT` | `/financial-profile/emergency-fund` | Store emergency fund balance and analysis config |
| `GET` | `/financial-analysis/emergency-fund` | Return deterministic emergency fund analysis |
| `POST` | `/financial-analysis/cash-flow-forecast` | Generate 30-day cash-flow projection |

---

### Emergency fund analysis methodology

The analysis uses only transactions stored via the Phase 2 endpoints.

**Essential expenses** are those whose `category` matches one of the configured
essential categories. The defaults are:
`rent`, `groceries`, `utilities`, `healthcare`, `transport`.

You can override this list via `PUT /financial-profile/emergency-fund`.

**Average monthly essential expenses** are calculated by:
1. Filtering transactions to those within the configured `analysis_window_months`
   and whose category is in the essential list.
2. Summing essential expenses per calendar month.
3. Dividing the total by the number of distinct months found (not by the window
   size), to avoid diluting the average with empty months.

**Targets:**
- 3-month target = average × 3
- 6-month target = average × 6

All monetary arithmetic uses Python `Decimal` — no floating-point rounding.

> **Data reliability warning:** if fewer than 3 complete calendar months of data
> are available, the analysis warns that the average may not be reliable.
> The system never assumes a zero emergency fund balance — supply it explicitly
> via the PUT endpoint or the balance status will be reported as `"unknown"`.

#### Example — set emergency fund config

```http
PUT /financial-profile/emergency-fund
Content-Type: application/json

{
  "emergency_fund_balance": "150000.00",
  "essential_categories": ["rent", "groceries", "utilities", "healthcare", "transport"],
  "analysis_window_months": 12
}
```

Response:

```json
{
  "emergency_fund_balance": "150000.00",
  "essential_categories": ["rent", "groceries", "utilities", "healthcare", "transport"],
  "analysis_window_months": 12
}
```

#### Example — get emergency fund analysis

```http
GET /financial-analysis/emergency-fund
```

```json
{
  "currency": "INR",
  "analysis_window_months_requested": 12,
  "complete_months_analyzed": 3,
  "essential_categories_used": ["rent", "groceries", "utilities", "healthcare", "transport"],
  "essential_expense_transaction_count": 9,
  "average_monthly_essential_expenses": "20000.00",
  "three_month_target": "60000.00",
  "six_month_target": "120000.00",
  "emergency_fund_balance": "150000.00",
  "balance_status": "known",
  "shortfall_three_month": "0.00",
  "shortfall_six_month": "0.00",
  "months_of_coverage": "7.50",
  "warnings": [],
  "assumptions": [
    "Essential categories: rent, groceries, utilities, healthcare, transport",
    "Analysis window: 12 months",
    "Average based on 3 complete month(s) of data"
  ]
}
```

---

### 30-day cash-flow forecast methodology

The forecast engine:

1. **Loads stored transaction history** within the `observation_window_months`
   (default 6).
2. **Detects recurring transactions** — a transaction is considered recurring
   only if it appears in **at least 2 distinct calendar months**. Two
   occurrences in the same month do not qualify. The typical day of month is
   capped at 28 to remain valid in February.
3. **Incorporates confirmed future transactions** supplied in the request body.
   If a confirmed transaction's `(description, type)` fingerprint matches a
   detected recurring transaction, the recurring entry is suppressed on that day
   to prevent double-counting.
4. **Projects day-by-day** for 30 days from `forecast_start_date` (defaults to
   today), accumulating a running balance.
5. **Flags low-cash days** when the projected balance is below `min_cash_buffer`
   (default 0) but still ≥ 0.
6. **Flags negative-balance days** when the projected balance drops below 0.

All forecasts are labelled as **estimates** — the response always includes
`methodology`, `assumptions`, and `warnings` fields.

#### Example — 30-day forecast

```http
POST /financial-analysis/cash-flow-forecast
Content-Type: application/json

{
  "current_balance": "250000.00",
  "forecast_start_date": "2026-11-01",
  "min_cash_buffer": "50000.00",
  "confirmed_future_transactions": [
    {
      "date": "2026-11-01",
      "description": "Monthly salary",
      "amount": "45000.00",
      "transaction_type": "income"
    }
  ],
  "observation_window_months": 6
}
```

```json
{
  "forecast_start_date": "2026-11-01",
  "forecast_end_date": "2026-11-30",
  "opening_balance": "250000.00",
  "projected_closing_balance": "272000.00",
  "total_projected_income": "45000.00",
  "total_projected_expenses": "23000.00",
  "net_projected_cash_flow": "22000.00",
  "low_cash_dates": [],
  "negative_balance_dates": [],
  "daily_forecasts": [ "... 30 entries ..." ],
  "detected_recurring_transactions": [
    {
      "description": "House rent payment",
      "transaction_type": "expense",
      "typical_day_of_month": 1,
      "typical_amount": "15000.00",
      "months_observed": 3
    }
  ],
  "months_of_history_used": 3,
  "methodology": "Recurring transactions detected from 6-month history ...",
  "assumptions": ["..."],
  "warnings": []
}
```

---

### Running the full test suite (all phases)

```powershell
# From the backend/ directory
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

Expected output: **222 passed** (Phase 1: 46, Phase 2: 125, Phase 3: 51).

| Test file | Phase | Tests |
|-----------|-------|-------|
| `test_calculations.py` | 1 | 22 |
| `test_api.py` | 1 | 24 |
| `test_transactions_phase2.py` | 2 | 51 |
| `test_emergency_fund.py` | 3 (unit) | 74 |
| `test_forecasting.py` | 3 (unit) | 0* |
| `test_financial_analysis_api.py` | 3 (API) | 51 |

> *`test_forecasting.py` unit tests are included in the 222 total above.

---

### Known limitations (Phase 3)

1. **JSON file storage** is still used — Phase 4 will migrate to PostgreSQL.
2. **Emergency fund balance** must be supplied explicitly — the system never
   infers it from transaction history.
3. **Recurring detection** requires at least 2 distinct calendar months of data;
   a single month of history produces no recurring patterns.
4. **Forecast is an estimate** — predictions improve as more historical data
   accumulates. The system always surfaces this caveat in `warnings`.
5. **Day-of-month capped at 28** — recurring transactions are projected on day
   28 in months that have fewer days, avoiding invalid February dates.

---

## Phase 4 — PostgreSQL Integration, Data Integrity, and Persistence Hardening

### Technology Stack & Architecture

Phase 4 introduces an ACID-compliant database persistence layer using:
- **PostgreSQL** (version 14, 15, 16, or 17)
- **SQLAlchemy 2.x** with typed ORM declarative mappings and pooled sessions
- **Alembic** for schema versioning and database migrations
- **psycopg** (v3 with binary distribution) driver
- **Pydantic** for input/output schema validation
- **Decimal arithmetic (`NUMERIC(18, 2)`)** throughout the database layer

All route handlers interact with the database exclusively through the repository pattern (`SQLTransactionRepository` and `SQLProfileRepository`), separating HTTP and routing concerns from database queries.

```
FastAPI Routers (app/transactions.py, app/financial_analysis.py)
       ↓ Depends(get_repository) / Depends(get_profile_repository)
Repository Layer (app/db/repositories/transaction_repo.py, profile_repo.py)
       ↓ Session (app/db/session.py)
SQLAlchemy 2.x ORM Models (app/db/models.py)
       ↓ psycopg
PostgreSQL Database (transactions, financial_profiles)
```

---

### Database Schema & Constraints

#### 1. `transactions` table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `VARCHAR(36)` | PRIMARY KEY | Unique UUID identifier |
| `date` | `DATE` | NOT NULL, INDEX | Transaction date (YYYY-MM-DD) |
| `description` | `TEXT` | NOT NULL, CHECK `length(trim(description)) > 0` | Non-empty description |
| `amount` | `NUMERIC(18, 2)` | NOT NULL, CHECK `amount > 0` | Exact monetary amount |
| `transaction_type` | `VARCHAR(10)` | NOT NULL, CHECK `IN ('income', 'expense')`, INDEX | Transaction type |
| `category` | `VARCHAR(100)` | NOT NULL, DEFAULT `'uncategorized'`, INDEX | Categorization label |
| `source` | `VARCHAR(20)` | NOT NULL, DEFAULT `'manual'` | `'manual'` or `'csv_import'` |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Creation timestamp |

**Composite Index:** `idx_transactions_date_type` on `(date, transaction_type)` for efficient reporting and forecasting queries.

#### 2. `financial_profiles` table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `INTEGER` | PRIMARY KEY, AUTOINCREMENT | Internal primary key |
| `profile_key` | `VARCHAR(50)` | UNIQUE, NOT NULL, DEFAULT `'default'` | Key for future multi-user support |
| `emergency_fund_balance` | `NUMERIC(18, 2)` | NULLABLE, CHECK `balance IS NULL OR balance >= 0` | Known savings balance (`NULL` = unknown) |
| `essential_categories` | `JSON` | NOT NULL | Essential categories list |
| `analysis_window_months` | `INTEGER` | NOT NULL, DEFAULT `12`, CHECK `BETWEEN 1 AND 60` | Analysis history window |
| `min_cash_buffer` | `NUMERIC(18, 2)` | NULLABLE | Minimum cash buffer for forecast |
| `currency` | `VARCHAR(10)` | NOT NULL, DEFAULT `'INR'` | Currency code |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Last updated timestamp |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Creation timestamp |

---

### Database Configuration & Credentials

Set the `DATABASE_URL` environment variable in `.env`:

```env
# PostgreSQL connection string:
DATABASE_URL=postgresql+psycopg://username:password@localhost:5432/financial_portfolio

# Fallback / testing SQLite connection string:
# DATABASE_URL=sqlite:///./data/financial_portfolio.db
```

> **Security Note:** Sensitive credentials in `DATABASE_URL` are automatically masked by `mask_database_url()` before any logging or diagnostics. Passwords are never committed or exposed in HTTP responses.

---

### Database Migrations with Alembic

Run database migrations from the `backend/` directory:

```powershell
# Apply all pending migrations to head
.\.venv\Scripts\alembic.exe upgrade head

# Inspect the current migration revision
.\.venv\Scripts\alembic.exe current

# Roll back the most recent migration (if needed)
.\.venv\Scripts\alembic.exe downgrade -1
```

---

### JSON Data Migration Script

To migrate pre-existing JSON records (`data/transactions.json` and `data/financial_profile.json`) into the database:

```powershell
# 1. Preview records to be migrated without modifying the database:
.\.venv\Scripts\python.exe migrations/migrate_json_to_pg.py --dry-run

# 2. Execute migration:
.\.venv\Scripts\python.exe migrations/migrate_json_to_pg.py
```

**Guarantees:**
- **Validation:** Every record is validated against Pydantic and database constraints.
- **Idempotency:** Safely rerun without creating duplicate transactions (existing IDs are detected and skipped).
- **Safety:** Original JSON files are never modified or deleted.
- **Reporting:** Outputs exact counts of imported, skipped, and rejected records with details for any rejection.

---

### Local PostgreSQL Setup Instructions (Windows)

If installing PostgreSQL locally:
1. Download PostgreSQL 16 or 17 installer from [enterprisedb.com](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads).
2. Follow the installer wizard and record the superuser password (e.g. `postgres`).
3. Open PowerShell or `psql` and create the application database:
   ```sql
   CREATE DATABASE financial_portfolio;
   ```
4. Set the `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/financial_portfolio
   ```
5. Apply migrations:
   ```powershell
   .\.venv\Scripts\alembic.exe upgrade head
   ```

---

### Running Automated Tests (Phases 1–4)

All tests are isolated. Database tests run against isolated test sessions and never modify production or developer data:

```powershell
# Run the full test suite (265 tests)
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

| Test File | Phase | Count | Status |
|-----------|-------|-------|--------|
| `test_calculations.py` | 1 | 22 | ✅ Passed |
| `test_api.py` | 1 | 24 | ✅ Passed |
| `test_transactions_phase2.py` | 2 | 51 | ✅ Passed |
| `test_emergency_fund.py` | 3 (unit) | 74 | ✅ Passed |
| `test_financial_analysis_api.py` | 3 (API) | 51 | ✅ Passed |
| `test_db_models.py` | 4 (DB models & constraints) | 15 | ✅ Passed |
| `test_db_repositories.py` | 4 (DB repositories & ACID) | 18 | ✅ Passed |
| `test_db_api_integration.py` | 4 (DB API end-to-end) | 6 | ✅ Passed |
| `test_db_migrations.py` | 4 (Alembic & data migration) | 4 | ✅ Passed |
| **Total** | | **265** | **100% Passed** |

---

### Known Limitations (Phase 4)

1. **Single-User / Development Mode:** Authentication and user sessions were not yet implemented in Phase 4. All operations targeted `profile_key="default"`.
2. **Backups:** Database backups should be scheduled via `pg_dump` when deploying to production environments.

---

## Phase 5 — User Authentication, Secure Sessions, and Multi-User Data Isolation

### Technology Stack & Architecture

Phase 5 adds enterprise-grade user authentication, secure session handling, and strict multi-user data isolation across the entire financial backend:

- **Argon2id Password Hashing:** Powered by `argon2-cffi` using the recommended parameters (`time_cost=3`, `memory_cost=65536` KiB, `parallelism=4`). Argon2id provides superior resistance against GPU and ASIC side-channel and brute-force attacks compared to legacy bcrypt or PBKDF2.
- **Short-Lived JWT Access Tokens:** Stateless access tokens signed using HMAC-SHA256 (`HS256`) via PyJWT. Tokens contain `sub` (user UUID), `exp` (15-minute default lifetime), `iat`, and `type="access"`.
- **Database-Tracked Refresh Sessions:** Long-lived refresh tokens (default 7 days) generated using high-entropy CSPRNG (`secrets.token_urlsafe(48)`). Refresh tokens are **never stored plaintext** in the database; only their deterministic cryptographic SHA-256 hash (`token_hash`) is persisted.
- **Automatic Token Rotation & Reuse Detection:** Every refresh operation rotates the refresh token: the consumed token is revoked and linked to the new token via `replaced_by_hash`. If a previously used token is presented again (indicating token theft), the system detects token reuse and **immediately invalidates all active sessions** for that user.
- **Sliding-Window Rate Limiting:** In-memory sliding-window brute-force defense tracks failed authentication attempts by email and IP address. Reaching 5 failed attempts triggers a 15-minute lockout returning HTTP 429.
- **Generic Authentication Responses:** Failed logins for non-existent emails or incorrect passwords return identical generic `401 Unauthorized` responses to protect against user enumeration.
- **Strict User-Scoped Data Isolation:** All financial transactions, CSV imports, stored summaries, emergency fund configurations, and cash-flow projections are strictly filtered and bound to `current_user.id`.

```
Client (HTTP Authorization: Bearer <access_token>)
        ↓
FastAPI Depends(get_current_user)
        ↓ Validates JWT signature & expiration, queries SQLUserRepository
Authenticated UserModel (current_user.id)
        ↓
Routers & Repositories (transactions.py, financial_analysis.py)
        ↓ WHERE user_id == current_user.id
PostgreSQL Database (Isolated Transactions & Profiles)
```

---

### Database Schema Additions (Phase 5)

#### 1. `users` table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `VARCHAR(36)` | PRIMARY KEY | Unique user UUID |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL, INDEX | Normalized lowercase email |
| `password_hash` | `TEXT` | NOT NULL | Argon2id password hash |
| `is_active` | `BOOLEAN` | NOT NULL, DEFAULT `true` | Account active status |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Account creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Last updated timestamp |

#### 2. `user_sessions` table
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | `INTEGER` | PRIMARY KEY, AUTOINCREMENT | Internal session ID |
| `user_id` | `VARCHAR(36)` | FOREIGN KEY (`users.id`) ON DELETE CASCADE | Associated user |
| `token_hash` | `VARCHAR(64)` | UNIQUE, NOT NULL, INDEX | SHA-256 hash of refresh token |
| `expires_at` | `TIMESTAMPTZ` | NOT NULL, INDEX | Refresh token expiration timestamp |
| `revoked_at` | `TIMESTAMPTZ` | NULLABLE | Revocation timestamp (`NULL` if active) |
| `replaced_by_hash` | `VARCHAR(64)` | NULLABLE | Successor token hash for reuse detection |
| `user_agent` | `VARCHAR(255)` | NULLABLE | Client User-Agent string |
| `ip_address` | `VARCHAR(45)` | NULLABLE | Client IP address |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Session start timestamp |

#### 3. Foreign Key Updates to Existing Tables
- **`transactions` table:** Added `user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE`. Composite index `idx_transactions_user_date` on `(user_id, date)`.
- **`financial_profiles` table:** Added `user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE`. Unique index `idx_financial_profiles_user_id` on `(user_id)`.

---

### Authentication API Endpoints

| Method | Path | Auth Required | Description |
|--------|------|---------------|-------------|
| `POST` | `/auth/register` | No | Register a new user account with email and password |
| `POST` | `/auth/login` | No (Rate-Limited) | Authenticate user, returns access & refresh tokens |
| `GET` | `/auth/me` | Bearer Token | Return currently authenticated user profile |
| `POST` | `/auth/refresh` | No | Rotate refresh token; returns new access & refresh tokens |
| `POST` | `/auth/logout` | Optional Bearer | Revoke refresh token and invalidate session |

---

### Usage Examples

#### 1. Register a new user

```http
POST /auth/register
Content-Type: application/json

{
  "email": "student@university.edu",
  "password": "SecurePassword123!"
}
```

**Response `201 Created`:**
```json
{
  "id": "e4b95f2a-89a1-432d-905c-9c98ef267e81",
  "email": "student@university.edu",
  "is_active": true,
  "created_at": "2026-10-21T10:00:00Z"
}
```

#### 2. Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "student@university.edu",
  "password": "SecurePassword123!"
}
```

**Response `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "XyZ987...aBcDeFg",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### 3. Access Protected Financial Endpoints

Include the access token in the `Authorization` header:

```http
GET /transactions
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

```http
POST /transactions
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Content-Type: application/json

{
  "date": "2026-10-21",
  "description": "Lab equipment stipend",
  "amount": "12000.00",
  "transaction_type": "income",
  "category": "salary"
}
```

#### 4. Refresh Tokens

```http
POST /auth/refresh
Content-Type: application/json

{
  "refresh_token": "XyZ987...aBcDeFg"
}
```

**Response `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6...",
  "refresh_token": "NewRotatedRefreshTokenValue...",
  "token_type": "bearer",
  "expires_in": 900
}
```

#### 5. Logout

```http
POST /auth/logout
Content-Type: application/json

{
  "refresh_token": "NewRotatedRefreshTokenValue..."
}
```

**Response `200 OK`:**
```json
{
  "message": "Successfully logged out."
}
```

---

### Running Automated Tests (Phases 1–5)

```powershell
# Run the complete test suite (290 tests)
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

| Test File | Phase | Count | Status |
|-----------|-------|-------|--------|
| `test_calculations.py` | 1 | 22 | ✅ Passed |
| `test_api.py` | 1 | 24 | ✅ Passed |
| `test_transactions_phase2.py` | 2 | 51 | ✅ Passed |
| `test_emergency_fund.py` | 3 (unit) | 74 | ✅ Passed |
| `test_financial_analysis_api.py` | 3 (API) | 51 | ✅ Passed |
| `test_db_models.py` | 4 (DB models & constraints) | 15 | ✅ Passed |
| `test_db_repositories.py` | 4 (DB repositories & ACID) | 18 | ✅ Passed |
| `test_db_api_integration.py` | 4 (DB API end-to-end) | 6 | ✅ Passed |
| `test_db_migrations.py` | 4 (Alembic & data migration) | 4 | ✅ Passed |
| `test_auth_account.py` | 5 (Register, Login, Argon2id, Rate Limiting) | 13 | ✅ Passed |
| `test_session_security.py` | 5 (JWT, Refresh Sessions, Reuse Detection) | 5 | ✅ Passed |
| `test_user_isolation.py` | 5 (Transactions, Profiles, Legacy Protection) | 7 | ✅ Passed |
| **Total** | | **290** | **100% Passed** |

---

### Known Limitations (Phase 5)

1. **In-Memory Rate Limiting:** The sliding-window login rate limiter is stored in application memory. When scaling horizontally across multiple web worker processes or container instances, an external key-value store such as Redis should be configured.
2. **Email Verification:** Email addresses are validated for syntactic correctness and format via `email-validator`. Outbound SMTP email confirmation links or OTP verification codes have not been integrated.
3. **Password Reset Flow:** Forgotten password recovery flows via email token are not yet implemented.

---

## Phase 6 — Investment Portfolio Management and Asset Allocation Foundation

### Technology Stack & Architecture

Phase 6 introduces a deterministic investment portfolio management layer, holdings tracking, investment goals, asset allocation variance analysis, and an optimization-readiness validator:

- **Database-Backed Investment Layer:** SQLAlchemy 2.x ORM models mapped to PostgreSQL with foreign keys and cascade rules (`portfolios`, `assets`, `portfolio_holdings`, `investment_goals`, `target_allocations`).
- **Strict User Scoping:** Every portfolio, custom instrument, holding, goal, and allocation is strictly owned by `current_user.id`. Foreign user IDs cannot read, alter, or attach records.
- **Deterministic Decimal Calculations:** Quantities, prices, valuations, weights, and variances are calculated using Python `Decimal` (`ROUND_HALF_UP`) to prevent floating-point inaccuracies.
- **Unpriced Holdings Discipline:** Holdings lacking user-supplied current prices remain explicitly `None` (unpriced). They are **never defaulted to zero**, nor silently incorporated into allocation denominators.
- **Mixed-Currency Safeguard:** Mixed currencies are detected and flagged. Without an external exchange rate feed, cross-currency values are never aggregated blindly.
- **Phase 7 Optimization Boundary:** Establishes a rigorous service boundary that validates whether portfolio inputs are complete, priced, and ready for future algorithmic optimization without implementing optimization algorithms in Phase 6.

```
Client (HTTP Authorization: Bearer <token>)
        ↓
FastAPI Depends(get_current_user)
        ↓
Portfolio Router (app/portfolio_router.py)
   ├── Portfolios CRUD (/portfolios)
   ├── Asset Instruments (/assets)
   ├── Holdings Management (/portfolios/{id}/holdings)
   ├── Target Allocation (/portfolios/{id}/allocation-target)
   ├── Investment Goals (/investment-goals)
   ├── Deterministic Valuation (/portfolios/{id}/valuation)
   ├── Asset Allocation Analysis (/portfolios/{id}/allocation-analysis)
   └── Optimization Readiness (/portfolios/{id}/optimization-readiness)
        ↓
Engines (portfolio_valuation.py, allocation_analysis.py, optimization_validator.py)
        ↓
SQLPortfolioRepository (app/db/repositories/portfolio_repo.py)
        ↓
PostgreSQL Database (portfolios, assets, portfolio_holdings, investment_goals, target_allocations)
```

---

### Controlled Asset Classes

Investment instruments must be classified into one of the following standardized categories:

| Asset Class Key | Display Name | Example Instruments |
|---|---|---|
| `equity` | Equity / Stocks | TCS, Infosys, Reliance, Apple Inc. |
| `debt` | Debt / Fixed Income | Government of India 10Y Bond, Corporate Debentures |
| `mutual_fund` | Mutual Funds | Parag Parikh Flexi Cap, SBI Bluechip Fund |
| `etf` | Exchange-Traded Funds | NIFTYBEES, GOLDBEES, Vanguard Total Stock ETF |
| `cash` | Cash & Cash Equivalents | High-yield savings, Liquid fund, Treasury bills |
| `commodities_gold` | Gold & Commodities | Sovereign Gold Bonds (SGB), Physical Gold |
| `other` | Other Alternative Assets | Real estate units, unlisted shares, private equity |

---

### Database Schema Additions (Phase 6)

#### 1. `portfolios` table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | Unique UUID identifier |
| `user_id` | `VARCHAR(36)` | FK (`users.id`) ON DELETE CASCADE, NOT NULL | Owner user ID |
| `name` | `VARCHAR(100)` | NOT NULL, CHECK `length(trim(name)) > 0` | Portfolio name |
| `description` | `TEXT` | NULLABLE | Optional description |
| `base_currency` | `VARCHAR(10)` | NOT NULL, DEFAULT `'INR'` | Base valuation currency |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Last updated timestamp |

#### 2. `assets` table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | Unique UUID identifier |
| `user_id` | `VARCHAR(36)` | FK (`users.id`) ON DELETE CASCADE, NULLABLE | NULL for system reference, non-null for custom assets |
| `symbol` | `VARCHAR(50)` | NULLABLE, INDEX | Ticker or instrument symbol |
| `name` | `VARCHAR(255)` | NOT NULL, CHECK `length(trim(name)) > 0` | Descriptive instrument name |
| `asset_class` | `VARCHAR(50)` | NOT NULL, INDEX | Controlled asset class |
| `currency` | `VARCHAR(10)` | NOT NULL, DEFAULT `'INR'` | Instrument trading currency |
| `instrument_type` | `VARCHAR(50)` | NULLABLE | Specific instrument sub-type |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Last updated timestamp |

#### 3. `portfolio_holdings` table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | Unique holding UUID |
| `portfolio_id` | `VARCHAR(36)` | FK (`portfolios.id`) ON DELETE CASCADE, NOT NULL | Associated portfolio |
| `asset_id` | `VARCHAR(36)` | FK (`assets.id`) ON DELETE RESTRICT, NOT NULL | Associated instrument |
| `quantity` | `NUMERIC(18, 4)` | NOT NULL, CHECK `quantity > 0` | Quantity of units/shares |
| `average_purchase_price` | `NUMERIC(18, 2)` | NOT NULL, CHECK `average_purchase_price >= 0` | Acquisition price per unit |
| `current_price` | `NUMERIC(18, 2)` | NULLABLE, CHECK `current_price IS NULL OR current_price >= 0` | User-supplied price (`NULL` = unpriced) |
| `price_as_of` | `TIMESTAMPTZ` | NULLABLE | Price quote timestamp |
| `notes` | `TEXT` | NULLABLE | Optional notes |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Last updated timestamp |

**Unique Constraint:** `(portfolio_id, asset_id)` prevents accidental duplicate holding entries of the same asset within a single portfolio.

#### 4. `target_allocations` table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | Unique record UUID |
| `portfolio_id` | `VARCHAR(36)` | FK (`portfolios.id`) ON DELETE CASCADE, UNIQUE, NOT NULL | 1-to-1 portfolio linkage |
| `user_id` | `VARCHAR(36)` | FK (`users.id`) ON DELETE CASCADE, NOT NULL | Owner user ID |
| `targets` | `JSON` | NOT NULL | Asset class to percentage mapping |
| `is_draft` | `BOOLEAN` | NOT NULL, DEFAULT `false` | Incomplete draft flag |
| `notes` | `TEXT` | NULLABLE | Optional notes |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Last updated timestamp |

#### 5. `investment_goals` table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `VARCHAR(36)` | PRIMARY KEY | Unique goal UUID |
| `user_id` | `VARCHAR(36)` | FK (`users.id`) ON DELETE CASCADE, NOT NULL | Owner user ID |
| `portfolio_id` | `VARCHAR(36)` | FK (`portfolios.id`) ON DELETE SET NULL, NULLABLE | Optional linked portfolio |
| `name` | `VARCHAR(100)` | NOT NULL, CHECK `length(trim(name)) > 0` | Goal title |
| `target_amount` | `NUMERIC(18, 2)` | NOT NULL, CHECK `target_amount > 0` | Target monetary sum |
| `target_date` | `DATE` | NOT NULL | Milestone completion date |
| `priority` | `VARCHAR(20)` | NOT NULL, DEFAULT `'medium'` | `'low'`, `'medium'`, `'high'` |
| `notes` | `TEXT` | NULLABLE | Optional notes |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Creation timestamp |
| `updated_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT `CURRENT_TIMESTAMP` | Last updated timestamp |

---

### API Endpoints Summary

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/portfolios` | Bearer | Create a new investment portfolio |
| `GET` | `/portfolios` | Bearer | List portfolios owned by current user |
| `GET` | `/portfolios/{id}` | Bearer | Retrieve portfolio details |
| `PATCH` | `/portfolios/{id}` | Bearer | Update portfolio name, description, or base currency |
| `DELETE` | `/portfolios/{id}` | Bearer | Delete portfolio (safe delete: requires `?cascade=true` if holdings exist) |
| `POST` | `/assets` | Bearer | Register an investment asset instrument |
| `GET` | `/assets` | Bearer | List accessible assets (supports `?asset_class=` and `?symbol=`) |
| `GET` | `/assets/{id}` | Bearer | Get instrument details |
| `PATCH` | `/assets/{id}` | Bearer | Update user-created instrument (system assets are read-only) |
| `POST` | `/portfolios/{id}/holdings` | Bearer | Add a holding to a portfolio |
| `GET` | `/portfolios/{id}/holdings` | Bearer | List all holdings in a portfolio |
| `PATCH` | `/portfolios/{id}/holdings/{h_id}` | Bearer | Update holding quantity, acquisition price, or current price |
| `DELETE` | `/portfolios/{id}/holdings/{h_id}` | Bearer | Remove holding from portfolio |
| `PUT` | `/portfolios/{id}/allocation-target` | Bearer | Configure target allocation percentages (must sum to 100% unless draft) |
| `GET` | `/portfolios/{id}/allocation-target` | Bearer | Retrieve configured target allocation |
| `POST` | `/investment-goals` | Bearer | Create an investment goal (optionally linked to a portfolio) |
| `GET` | `/investment-goals` | Bearer | List investment goals |
| `GET` | `/investment-goals/{id}` | Bearer | Get goal details and current progress metrics |
| `PATCH` | `/investment-goals/{id}` | Bearer | Update goal parameters |
| `DELETE` | `/investment-goals/{id}` | Bearer | Delete investment goal |
| `GET` | `/portfolios/{id}/valuation` | Bearer | Calculate deterministic market valuation and asset class weights |
| `GET` | `/portfolios/{id}/allocation-analysis` | Bearer | Compare current asset weights with target allocation |
| `GET` | `/portfolios/{id}/optimization-readiness` | Bearer | Evaluate portfolio completeness for Phase 7 optimization |

---

### Valuation & Asset Allocation Methodology

#### 1. Valuation Calculations
- **Priced Holding Market Value:** `market_value = quantity × current_price`
- **Holding Cost Basis:** `cost_basis = quantity × average_purchase_price`
- **Unrealized Gain / Loss:** `gain_loss = market_value - cost_basis`
- **Unrealized Gain %:** `(gain_loss / cost_basis) × 100` (if `cost_basis > 0`)
- **Total Portfolio Value:** Sum of `market_value` for all priced holdings denominated in base currency.
- **Asset Class Allocation Weight:** `(asset_class_market_value / total_priced_market_value) × 100`
- **Valuation Coverage:** `(priced_holdings_count / total_holdings_count) × 100`
- **Unpriced Holding Policy:** Unpriced holdings remain explicitly unpriced. They are excluded from the market valuation denominator and gain/loss totals, and flagged in the warnings array.

#### 2. Allocation Variance Analysis
- For each asset class: `difference_percentage_points = current_percentage - target_percentage`
- **Status Classification:**
  - `overweight`: `difference > +0.05%`
  - `underweight`: `difference < -0.05%`
  - `on_target`: within ±0.05%
  - `unspecified_target`: asset class present in portfolio holdings but omitted from target allocation.
  - `missing_holding`: asset class specified in target allocation with 0 holdings in portfolio.
- **Reliability Flag:** Analysis is marked as `is_analysis_reliable = false` if target allocation is draft, unpriced holdings exist, or mixed currencies are present.

#### 3. Optimization-Readiness Validator
Evaluates if a portfolio is ready for Phase 7 optimization algorithms:
1. `minimum_holdings_count`: Must contain at least 2 distinct holdings.
2. `price_coverage_complete`: 100% of holdings must have user-supplied prices (`current_price > 0`).
3. `positive_market_value`: Total priced market value must be > 0.
4. `single_currency_uniformity`: All holdings must share the portfolio base currency.
5. `target_allocation_configured`: Valid, non-draft target allocation summing to 100%.
6. `instrument_metadata_valid`: All holdings linked to instruments with valid asset classes.

---

### Example API Requests & Responses

#### 1. Create a Portfolio

```http
POST /portfolios
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Core Wealth Accumulator",
  "description": "Long-term diversified equity and bond portfolio",
  "base_currency": "INR"
}
```

**Response `201 Created`:**
```json
{
  "id": "6a978f14-9fa2-4302-8618-971c223c2bd4",
  "user_id": "e4b95f2a-89a1-432d-905c-9c98ef267e81",
  "name": "Core Wealth Accumulator",
  "description": "Long-term diversified equity and bond portfolio",
  "base_currency": "INR",
  "holding_count": 0,
  "created_at": "2026-10-21T10:30:00Z",
  "updated_at": "2026-10-21T10:30:00Z"
}
```

#### 2. Register an Asset and Add a Holding

```http
POST /assets
Authorization: Bearer <token>
Content-Type: application/json

{
  "symbol": "NIFTYBEES",
  "name": "Nippon India ETF Nifty 50 BeES",
  "asset_class": "equity",
  "currency": "INR",
  "instrument_type": "index_etf"
}
```

```http
POST /portfolios/6a978f14-9fa2-4302-8618-971c223c2bd4/holdings
Authorization: Bearer <token>
Content-Type: application/json

{
  "asset_id": "3b290cb1-0498-4b72-a7f4-d539562725fa",
  "quantity": "500.0000",
  "average_purchase_price": "240.00",
  "current_price": "265.50"
}
```

**Response `201 Created`:**
```json
{
  "id": "7b58cda1-d130-4667-bb09-bca152432a90",
  "portfolio_id": "6a978f14-9fa2-4302-8618-971c223c2bd4",
  "asset_id": "3b290cb1-0498-4b72-a7f4-d539562725fa",
  "asset_symbol": "NIFTYBEES",
  "asset_name": "Nippon India ETF Nifty 50 BeES",
  "asset_class": "equity",
  "currency": "INR",
  "quantity": "500.0000",
  "average_purchase_price": "240.00",
  "current_price": "265.50",
  "price_as_of": "2026-10-21T10:31:00Z",
  "cost_basis": "120000.00",
  "market_value": "132750.00",
  "notes": null,
  "created_at": "2026-10-21T10:31:00Z",
  "updated_at": "2026-10-21T10:31:00Z"
}
```

#### 3. Portfolio Valuation Endpoint

```http
GET /portfolios/6a978f14-9fa2-4302-8618-971c223c2bd4/valuation
Authorization: Bearer <token>
```

**Response `200 OK`:**
```json
{
  "portfolio_id": "6a978f14-9fa2-4302-8618-971c223c2bd4",
  "portfolio_name": "Core Wealth Accumulator",
  "base_currency": "INR",
  "valuation_as_of": "2026-10-21T10:32:00Z",
  "priced_holdings_value": "250000.00",
  "cost_basis_priced": "220000.00",
  "cost_basis_all": "220000.00",
  "unrealized_gain_loss": "30000.00",
  "unrealized_gain_loss_percentage": "13.64",
  "asset_class_breakdown": [
    {
      "asset_class": "equity",
      "market_value": "150000.00",
      "allocation_percentage": "60.00",
      "holdings_count": 2
    },
    {
      "asset_class": "debt",
      "market_value": "100000.00",
      "allocation_percentage": "40.00",
      "holdings_count": 1
    }
  ],
  "holdings": [ ... ],
  "total_holdings_count": 3,
  "priced_holdings_count": 3,
  "unpriced_holdings_count": 0,
  "valuation_coverage_percentage": "100.00",
  "has_mixed_currencies": false,
  "currencies_present": ["INR"],
  "assumptions": [
    "Asset prices are user-supplied and not guaranteed to reflect real-time live market quotes.",
    "Asset allocation percentages are calculated strictly using the total value of priced holdings as the denominator."
  ],
  "warnings": []
}
```

#### 4. Pre-Optimization Readiness Verification

```http
GET /portfolios/6a978f14-9fa2-4302-8618-971c223c2bd4/optimization-readiness
Authorization: Bearer <token>
```

**Response `200 OK`:**
```json
{
  "portfolio_id": "6a978f14-9fa2-4302-8618-971c223c2bd4",
  "is_ready_for_optimization": true,
  "readiness_status": "ready",
  "checks": [
    {
      "name": "minimum_holdings_count",
      "passed": true,
      "details": "Portfolio contains 3 holdings (minimum 2 required for diversification)."
    },
    {
      "name": "price_coverage_complete",
      "passed": true,
      "details": "100% of holdings have valid user-supplied current prices."
    },
    {
      "name": "positive_market_value",
      "passed": true,
      "details": "Total priced market value is INR 250000.00."
    },
    {
      "name": "single_currency_uniformity",
      "passed": true,
      "details": "All holdings are denominated in base currency 'INR'."
    },
    {
      "name": "target_allocation_configured",
      "passed": true,
      "details": "Target allocation is validated and sums to 100.00%."
    },
    {
      "name": "instrument_metadata_valid",
      "passed": true,
      "details": "All holdings are linked to valid instruments with known asset classes."
    }
  ],
  "blockers": [],
  "warnings": []
}
```

---

## Phase 7: Modern Portfolio Theory (MPT), Risk Analysis, and Optimization Engine

Phase 7 introduces a deterministic numerical optimization engine based on Markowitz Modern Portfolio Theory (MPT). The system computes optimal asset weights, risk-adjusted performance metrics, efficient frontier curves, and actionable rebalancing trades.

> [!IMPORTANT]
> **Deterministic Financial Math Integrity:** An LLM is never used to compute expected returns, portfolio weights, volatility, Sharpe ratios, or optimized allocations. All calculations are executed deterministically using exact mathematical algorithms implemented in NumPy and mapped to Python `Decimal` at API and database boundaries.

---

### Core Mathematical Formulations

#### 1. Daily Returns & Parameter Annualization
For $T$ observed trading dates and $N$ assets, simple daily returns are calculated as:
$$r_{i,t} = \frac{P_{i,t} - P_{i,t-1}}{P_{i,t-1}}$$

Parameters are annualized using the standard 252 trading-day convention:
- **Expected Annual Return:** $\boldsymbol{\mu} = 252 \times \bar{\mathbf{r}}$
- **Annualized Covariance Matrix:** $\boldsymbol{\Sigma} = 252 \times \operatorname{Cov}(\mathbf{r})$

#### 2. Ill-Conditioned Matrix Regularization
If the covariance matrix $\boldsymbol{\Sigma}$ is ill-conditioned (condition number $> 10^5$) or singular, Ledoit-Wolf diagonal shrinkage regularization is applied:
$$\boldsymbol{\Sigma}_{\text{reg}} = (1 - \alpha) \boldsymbol{\Sigma} + \alpha \frac{\operatorname{Tr}(\boldsymbol{\Sigma})}{N} \mathbf{I}_N \quad (\alpha = 0.05)$$

#### 3. Bounded Simplex Projection
Constraints require weights to be long-only and bounded:
$$\sum_{i=1}^N w_i = 1.0, \quad l_i \le w_i \le u_i \quad \forall i \in \{1, \dots, N\}$$

Projection onto the bounded simplex is performed via exact bisection on the Lagrangian multiplier $\theta$:
$$w_i(\theta) = \operatorname{clip}(v_i - \theta, l_i, u_i) \quad \text{such that} \quad \sum_{i=1}^N w_i(\theta) = 1.0$$

#### 4. Supported Optimization Strategies
- **Global Minimum Volatility (`min_volatility`):**
  $$\min_{\mathbf{w}} \frac{1}{2} \mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w} \quad \text{s.t.} \quad \sum w_i = 1, \quad \mathbf{l} \le \mathbf{w} \le \mathbf{u}$$
- **Maximum Sharpe Ratio / Tangency Portfolio (`max_sharpe`):**
  $$\max_{\mathbf{w}} \frac{\mathbf{w}^T \boldsymbol{\mu} - r_f}{\sqrt{\mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w}}} \quad \text{s.t.} \quad \sum w_i = 1, \quad \mathbf{l} \le \mathbf{w} \le \mathbf{u}$$
  *Fallback:* If all asset expected returns are below the risk-free rate ($\max \mu_i \le r_f$), a positive risk premium cannot be achieved; the engine gracefully defaults to Minimum Volatility and flags an explanatory warning.
- **Target Return (`target_return`):**
  $$\min_{\mathbf{w}} \frac{1}{2} \mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w} \quad \text{s.t.} \quad \mathbf{w}^T \boldsymbol{\mu} \ge R_{\text{target}}, \quad \sum w_i = 1, \quad \mathbf{l} \le \mathbf{w} \le \mathbf{u}$$
  Solved via Augmented Lagrangian Multipliers for exact constraint satisfaction.
- **User-Constrained (`user_constrained`):**
  Allows custom portfolio-level bounds (`min_weight`, `max_weight`) and per-asset lower/upper constraints.

#### 5. Rebalancing Logic & Trade Generation
- **Weight Delta:** $\Delta w_i = w_i^{\text{optimal}} - w_i^{\text{current}}$
- **Action Thresholds:**
  - $\Delta w_i > +0.0050 \ (+0.50\%):$ `BUY`
  - $\Delta w_i < -0.0050 \ (-0.50\%):$ `SELL`
  - Otherwise: `HOLD`
- **Trade Value:** $\text{trade\_amount}_i = |\Delta w_i| \times \text{total\_portfolio\_value}$

---

### Phase 7 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/market-data/historical-prices/import-csv` | Ingest global historical price CSV data with automatic deduplication. |
| `GET` | `/market-data/historical-prices/{symbol}` | Retrieve stored historical prices for a symbol (supports `limit`). |
| `POST` | `/portfolios/{id}/historical-prices/import-csv` | Upload historical prices scoped to instruments in a specific portfolio. |
| `POST` | `/portfolios/{id}/optimize` | Run deterministic MPT optimization with DB prices or inline CSV content. |
| `GET` | `/portfolios/{id}/optimization-history` | List audit log of historical optimization runs for a portfolio. |

---

### API Usage & Example Requests

#### 1. Ingest Market Data CSV

```http
POST /market-data/historical-prices/import-csv
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**CSV format (`prices.csv`):**
```csv
date,symbol,adjusted_close
2025-01-02,AAPL,185.50
2025-01-02,MSFT,375.20
2025-01-03,AAPL,186.25
2025-01-03,MSFT,378.10
```

**Response `200 OK`:**
```json
{
  "filename": "prices.csv",
  "total_rows": 4,
  "imported": 4,
  "skipped_duplicates": 0,
  "rejected": 0,
  "symbols_updated": ["AAPL", "MSFT"],
  "errors": []
}
```

#### 2. Execute Portfolio Optimization (`POST /portfolios/{id}/optimize`)

```http
POST /portfolios/6a978f14-9fa2-4302-8618-971c223c2bd4/optimize
Authorization: Bearer <token>
Content-Type: application/json

{
  "strategy": "max_sharpe",
  "risk_free_rate": "0.0200",
  "min_weight": "0.0500",
  "max_weight": "0.8000",
  "include_efficient_frontier": true
}
```

**Response `200 OK`:**
```json
{
  "portfolio_id": "6a978f14-9fa2-4302-8618-971c223c2bd4",
  "portfolio_name": "Core Wealth Growth",
  "base_currency": "USD",
  "strategy": "max_sharpe",
  "risk_free_rate": "0.0200",
  "expected_return": "0.1425",
  "expected_volatility": "0.1650",
  "sharpe_ratio": "0.7424",
  "current_portfolio_return": "0.1180",
  "current_portfolio_volatility": "0.2050",
  "current_portfolio_sharpe": "0.4780",
  "volatility_reduction_percentage": "19.51",
  "sharpe_improvement": "0.2644",
  "total_portfolio_value": "250000.00",
  "allocations": [
    {
      "asset_id": "asset-aapl-id",
      "symbol": "AAPL",
      "name": "Apple Inc",
      "asset_class": "equity",
      "current_weight": "0.6000",
      "optimal_weight": "0.4500",
      "weight_delta": "-0.1500",
      "current_value": "150000.00",
      "target_value": "112500.00",
      "action": "SELL",
      "trade_amount": "37500.00"
    },
    {
      "asset_id": "asset-msft-id",
      "symbol": "MSFT",
      "name": "Microsoft Corp",
      "asset_class": "equity",
      "current_weight": "0.4000",
      "optimal_weight": "0.5500",
      "weight_delta": "0.1500",
      "current_value": "100000.00",
      "target_value": "137500.00",
      "action": "BUY",
      "trade_amount": "37500.00"
    }
  ],
  "asset_class_summary": [
    {
      "asset_class": "equity",
      "current_weight": "1.0000",
      "optimal_weight": "1.0000",
      "target_allocation_weight": null,
      "weight_delta": "0.0000"
    }
  ],
  "efficient_frontier": [
    {
      "expected_return": "0.0950",
      "expected_volatility": "0.1420",
      "sharpe_ratio": "0.5282",
      "weights": {"AAPL": "0.3210", "MSFT": "0.6790"}
    },
    {
      "expected_return": "0.1425",
      "expected_volatility": "0.1650",
      "sharpe_ratio": "0.7424",
      "weights": {"AAPL": "0.4500", "MSFT": "0.5500"}
    }
  ],
  "observation_count": 252,
  "start_date": "2024-01-02",
  "end_date": "2025-01-02",
  "methodology": "Markowitz Tangency Portfolio (Maximum Sharpe Ratio): Solved for the optimal allocation on the Capital Allocation Line that maximizes risk-adjusted return over the risk-free rate of 2.00%.",
  "assumptions": [
    "Modern Portfolio Theory assumes historical returns and covariances are representative of future distribution parameters.",
    "Asset returns are assumed to follow a multivariate normal distribution.",
    "Annualized calculations use a standard 252 trading-day convention.",
    "The risk-free rate is assumed to be constant at 2.00% per annum.",
    "Optimization is executed under a long-only constraint (no short selling or leverage)."
  ],
  "warnings": [],
  "run_id": "9d3e8712-bf23-4567-8910-111213141516"
}
```

---

---

## Phase 8: Goal-Based Investment Planning, SIP Calculators, Portfolio Drift, and Risk-Aware Glide Paths

Phase 8 introduces four deterministic decision-support modules providing goal tracking, annuity compounding, target-solving reverse SIP calculations, portfolio allocation drift detection, illustrative rebalancing, and risk-aware investment glide paths.

> [!IMPORTANT]
> **Deterministic Financial Math Integrity:** An LLM is never used to compute future values, monthly contributions, asset weights, drift variances, or rebalancing trades. All calculations are executed deterministically using exact mathematical formulas with Python `Decimal` monetary precision.

---

### Core Mathematical Formulations

#### 1. Rate & Compounding Conventions
For an annual return $R$ (e.g. $0.12$ for $12\%$):
- **Effective Monthly Rate:**
  $$r_m = (1 + R)^{1/12} - 1$$
  *(Default standard convention: 12 months of monthly compounding yields exactly $1 + R$)*.
- **Nominal Monthly Rate:**
  $$r_m = \frac{R}{12}$$
- **Zero Return:**
  $$R = 0 \implies r_m = 0$$

#### 2. Forward SIP Ordinary Annuity
For initial lump sum $L$, monthly contribution $P$, monthly rate $r_m$, and $n$ months:
- If $r_m > 0$:
  $$FV = L(1 + r_m)^n + P \frac{(1 + r_m)^n - 1}{r_m}$$
- If $r_m = 0$:
  $$FV = L + P \cdot n$$
- **Total Invested:** $L + P \cdot n$
- **Estimated Wealth Gain:** $FV - (L + P \cdot n)$
- **Annual Step-Up Option:** If an annual step-up rate $s$ is specified, the monthly contribution increases each year: $P_{\text{year } y} = P_0 (1 + s)^{y-1}$.

#### 3. Reverse SIP Target Solver
Given target future corpus $FV$, initial investment $L$, monthly rate $r_m$, and $n$ months:
- If initial investment compounds to or beyond target ($L(1 + r_m)^n \ge FV$):
  $$P = 0.00 \quad \text{(Initial corpus already achieves or exceeds target)}$$
- Else if $r_m > 0$:
  $$P = \frac{FV - L(1 + r_m)^n}{\frac{(1 + r_m)^n - 1}{r_m}}$$
- Else if $r_m = 0$:
  $$P = \frac{FV - L}{n}$$

#### 4. Goal-Based Planning & Gap Analysis
For a goal with target amount $T$, target completion date $D_{\text{target}}$, current investment $L$, and planned contribution $P$:
- **Remaining Months:** $n = \max\left(1, \operatorname{round}\left(\frac{(D_{\text{target}} - D_{\text{today}}).\text{days}}{30.4375}\right)\right)$
- **Progress Percentage:** $\operatorname{progress} = \min\left(100.00\%, \frac{L}{T} \times 100\right)$
- **Remaining Capital Required:** $\max(0.00, T - L)$
- **Projected Future Value:** Calculated via forward SIP compounding.
- **Shortfall or Surplus:** $\Delta = FV_{\text{projected}} - T$
- **Required Monthly Contribution:** Calculated via reverse SIP solver.
- **Status Assessment:**
  - $\Delta \ge 0.05 \times T$: `ahead` (with $\ge 5\%$ safety margin)
  - $\Delta \ge 0$: `on_track`
  - $\Delta < 0$: `behind` (under-contributing by $|\Delta|$)
  - $D_{\text{target}} \le D_{\text{today}}$: `expired`

#### 5. Portfolio Drift & Rebalancing Analysis
Given current asset-class percentage $w_i^{\text{curr}}$ and target allocation percentage $w_i^{\text{tgt}}$:
- **Absolute Drift:** $|\Delta w_i| = |w_i^{\text{curr}} - w_i^{\text{tgt}}|$ (percentage points)
- **Relative Drift:** $\frac{|\Delta w_i|}{w_i^{\text{tgt}}} \times 100\%$ (when $w_i^{\text{tgt}} > 0$)
- **Drift Alert:** Flagged when $|\Delta w_i| > \tau_{\text{threshold}}$ (default $\tau = 5.00$ pp).
- **Illustrative Rebalance Trade Amount:**
  $$\text{Target Value}_i = \frac{w_i^{\text{tgt}}}{100} \times V_{\text{portfolio}}$$
  $$\text{Trade Amount}_i = |\text{Target Value}_i - \text{Current Value}_i|$$
  $$\text{Action}_i = \begin{cases} \text{BUY} & \text{if } \text{Target Value}_i - \text{Current Value}_i > 0.50 \\ \text{SELL} & \text{if } \text{Target Value}_i - \text{Current Value}_i < -0.50 \\ \text{HOLD} & \text{otherwise} \end{cases}$$
- **Reconciliation Guarantee:** Sum of target market values equals total portfolio market value within cent rounding precision.

#### 6. Risk-Aware Investment Glide Path
For $K$ milestone checkpoints between $t=0$ (start date) and $t=1$ (target completion date):
- Progress fraction: $\alpha_k = \frac{\text{elapsed days}}{\text{total days}}$
- Checkpoint weights:
  $$w_i(k) = (1 - \alpha_k) w_i^{\text{start}} + \alpha_k w_i^{\text{end}}$$
- **Simplex Guarantee:** Since $\sum w_i^{\text{start}} = 100.00\%$ and $\sum w_i^{\text{end}} = 100.00\%$, $\sum w_i(k) = 100.00\%$ strictly for all $k$.

---

### Phase 8 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/calculators/sip` | Forward SIP projection with optional step-up and schedule breakdown. |
| `POST` | `/calculators/reverse-sip` | Reverse SIP calculator determining required monthly investment. |
| `POST` | `/investment-goals/{id}/projection` | Project saved goal future value, gap, and required monthly SIP. |
| `POST` | `/investment-goals/plan` | Ad-hoc goal projection and SIP requirements without saving. |
| `GET` | `/portfolios/{id}/drift` | Analyze allocation drift with configurable threshold query param. |
| `POST` | `/portfolios/{id}/rebalancing-analysis` | Generate illustrative buy/sell trades reconciling to portfolio value. |
| `POST` | `/investment-goals/{id}/glide-path` | Generate risk-aware de-risking milestone checkpoints for a saved goal. |
| `POST` | `/calculators/glide-path` | Standalone investment glide path generator. |

---

### API Usage & Example Requests

#### 1. Forward SIP Calculator (`POST /calculators/sip`)

```http
POST /calculators/sip
Authorization: Bearer <token>
Content-Type: application/json

{
  "initial_investment": "50000.00",
  "monthly_contribution": "10000.00",
  "annual_return_percentage": "12.0",
  "duration_months": 36,
  "rate_convention": "effective",
  "include_schedule": true
}
```

**Response `200 OK`:**
```json
{
  "initial_investment": "50000.00",
  "monthly_contribution": "10000.00",
  "annual_return_percentage": "12.00",
  "duration_months": 36,
  "rate_convention": "effective",
  "projected_future_value": "495475.28",
  "total_contributions": "360000.00",
  "total_invested": "410000.00",
  "estimated_wealth_gain": "85475.28",
  "annual_step_up_percentage": null,
  "schedule": [
    {
      "period": 1,
      "period_label": "Year 1",
      "opening_balance": "50000.00",
      "contributions": "120000.00",
      "growth_earned": "11985.42",
      "closing_balance": "181985.42",
      "total_contributed_to_date": "170000.00"
    },
    {
      "period": 2,
      "period_label": "Year 2",
      "opening_balance": "181985.42",
      "contributions": "120000.00",
      "growth_earned": "27823.67",
      "closing_balance": "329809.09",
      "total_contributed_to_date": "290000.00"
    },
    {
      "period": 3,
      "period_label": "Year 3",
      "opening_balance": "329809.09",
      "contributions": "120000.00",
      "growth_earned": "45666.19",
      "closing_balance": "495475.28",
      "total_contributed_to_date": "410000.00"
    }
  ],
  "assumptions": [
    "Contributions are deposited at the end of each calendar month (ordinary annuity convention).",
    "Compounding rate convention: 'effective' (equivalent effective monthly rate).",
    "Rate of return is assumed constant throughout the investment horizon."
  ],
  "disclaimers": [
    "Projections are deterministic mathematical estimates and do not guarantee market returns.",
    "Calculations exclude taxes, inflation, fund management fees, and transaction charges."
  ]
}
```

#### 2. Reverse SIP Calculator (`POST /calculators/reverse-sip`)

```http
POST /calculators/reverse-sip
Authorization: Bearer <token>
Content-Type: application/json

{
  "target_amount": "1000000.00",
  "initial_investment": "100000.00",
  "annual_return_percentage": "12.0",
  "duration_months": 36,
  "rate_convention": "effective"
}
```

**Response `200 OK`:**
```json
{
  "target_amount": "1000000.00",
  "initial_investment": "100000.00",
  "annual_return_percentage": "12.00",
  "duration_months": 36,
  "rate_convention": "effective",
  "required_monthly_contribution": "20138.85",
  "projected_future_value": "1000000.00",
  "total_contributions": "724998.60",
  "total_invested": "824998.60",
  "estimated_wealth_gain": "175001.40",
  "is_target_already_covered": false,
  "explanation": "To accumulate a target corpus of 1,000,000.00 over 36 months starting with an initial investment of 100,000.00 at an assumed 12.00% annual return, a disciplined monthly contribution of 20,138.85 is required.",
  "assumptions": [
    "Contributions are deposited at the end of each calendar month (ordinary annuity convention).",
    "Compounding rate convention: 'effective' (equivalent effective monthly rate).",
    "Rate of return is assumed constant and realized smoothly across all periods."
  ],
  "disclaimers": [
    "The calculated monthly SIP is a deterministic projection based on the stated return assumption.",
    "Market volatility, investment fees, taxes, and inflation may cause actual future values to vary."
  ]
}
```

#### 3. Portfolio Drift Detection (`GET /portfolios/{id}/drift`)

```http
GET /portfolios/6a978f14-9fa2-4302-8618-971c223c2bd4/drift?threshold_percentage_points=5.00
Authorization: Bearer <token>
```

**Response `200 OK`:**
```json
{
  "portfolio_id": "6a978f14-9fa2-4302-8618-971c223c2bd4",
  "portfolio_name": "Core Wealth Growth",
  "base_currency": "INR",
  "total_portfolio_value": "1000000.00",
  "drift_threshold_percentage_points": "5.00",
  "portfolio_exceeds_threshold": true,
  "max_drift_percentage_points": "10.00",
  "asset_classes": [
    {
      "asset_class": "equity",
      "current_market_value": "700000.00",
      "current_weight_percentage": "70.00",
      "target_weight_percentage": "60.00",
      "absolute_drift_percentage_points": "10.00",
      "relative_drift_percentage": "16.67",
      "status": "overweight",
      "exceeds_threshold": true
    },
    {
      "asset_class": "debt",
      "current_market_value": "300000.00",
      "current_weight_percentage": "30.00",
      "target_weight_percentage": "40.00",
      "absolute_drift_percentage_points": "10.00",
      "relative_drift_percentage": "25.00",
      "status": "underweight",
      "exceeds_threshold": true
    }
  ],
  "drifted_classes": ["debt", "equity"],
  "is_analysis_reliable": true,
  "warnings": [],
  "as_of_timestamp": "2026-10-21T21:00:00Z"
}
```

---

---

## Phase 9: LLM-Powered Financial Intelligence, Explainable Insights, and Decision Support

### Overview & Source of Truth Guarantee

Phase 9 integrates a Large Language Model (LLM) as an explainable insight, natural-language summarization, and conversational decision-support layer on top of the deterministic financial calculation engine (Phases 1–8).

#### Strict Architectural Boundaries
- **Deterministic Financial Engine as Absolute Source of Truth:** All authoritative monetary calculations (balances, cash-flow projections, emergency-fund coverage, MPT portfolio valuation, Sharpe ratios, optimal weights, SIP compounding, drift variances, and rebalancing trades) are computed deterministically by the Phase 1–8 engines.
- **Explainable & Conversational Role:** The LLM acts purely as an interpreter, explainer, and structured conversational advisor. It never invents metrics, fabricates market quotes, bypasses deterministic algorithms, or accesses cross-user data.
- **Zero Database Mutation in Hypothetical Scenarios:** "What-if" simulations (SIP increases, return comparisons, horizon adjustments) are evaluated transiently and never modify stored goal or portfolio records.
- **Offline & Safe Fallback Operation:** The system operates cleanly without network or API keys via `MockLLMProvider` and degrades gracefully with deterministic synthesis via `UnconfiguredProvider` or when network timeouts occur.

```
Authenticated User Request
        │
        ▼
Financial Context Service (Keyword domain detection)
        │
        ▼
Deterministic Financial Services (Phases 1–8: Transactions, Profiles, Portfolios, Goals)
        │
        ▼
Validated Financial Context (Structured, user-scoped facts & missing-data warnings)
        │
        ▼
LLM Provider Adapter (OpenAI / Anthropic / Mock with strict system prompt)
        │
        ▼
Grounding Guardrails & Post-Validation (Schema parsing, domain citation check, compliance)
        │
        ▼
Final Grounded Response (Answer, verified cited domains, key metrics, disclaimers)
```

---

### Core Phase 9 Capabilities

1. **Provider-Independent LLM Abstraction (`app/ai/provider.py` & `app/ai/config.py`):**
   - Standardized `BaseLLMProvider` interface.
   - Built-in adapters for `OpenAIProvider`, `AnthropicProvider`, `MockLLMProvider`, and `UnconfiguredProvider`.
   - Uses `httpx.AsyncClient` with configurable timeout (`LLM_TIMEOUT_SECONDS`) and output tokens (`LLM_MAX_OUTPUT_TOKENS`).
   - Secure API key masking (`mask_api_key`) prevents secret leakage in logs.

2. **Verified Financial Context Gathering (`app/ai/financial_context.py`):**
   - Detects financial domains from natural-language queries:
     - `spending_and_cash_flow`: Income, expenses, net savings, savings rate, 30-day forecast.
     - `emergency_fund`: Available liquid reserves, coverage in months, 3/6-month shortfalls.
     - `investment_goals`: Goal targets, progress percentages, required vs planned monthly SIP.
     - `portfolio_risk_and_allocation`: Asset classes, valuation, MPT return, volatility, Sharpe ratio.
     - `rebalancing_and_drift`: Allocation drift, threshold flags, illustrative rebalancing trades.
     - `glide_path`: Time-horizon milestone de-risking allocations.
   - Distinguishes verified facts from missing data warnings (e.g. no transactions recorded).

3. **Deterministic Hypothetical Scenario Evaluator (`app/ai/scenario_evaluator.py`):**
   - `sip_increase`: Evaluates incremental monthly savings impact on projected future wealth.
   - `return_comparison`: Comparative projection between two expected annual return rates.
   - `target_date_change`: Evaluates how shifting goal deadlines changes required monthly SIP.
   - Strictly read-only: Zero database mutation guaranteed.

4. **Explainable Financial Insights Service (`app/ai/insights_service.py`):**
   - Standalone multi-domain evaluation producing `FinancialHealthReport`:
     - Severity classifications: `positive`, `info`, `warning`, `alert`.
     - Overall financial health status: `healthy`, `attention_needed`, `critical`, `insufficient_data`.
     - Deterministic metrics and prioritized recommendations per domain.

5. **Anti-Hallucination & Grounding Guardrails (`app/ai/guardrails.py`):**
   - Prompt injection sanitization: Neutralizes directive override attempts (`[filtered_directive]`).
   - Grounded system prompt enforcing role boundaries and mandatory JSON output schema.
   - Post-generation validation: Validates cited domains against context and strips hallucinated citations.
   - Guaranteed return compliance check: Flags or appends regulatory risk notices if unauthorized guarantee claims are detected.
   - Deterministic Fallback Builder: Authoritative fallback synthesis if LLM fails, times out, or returns invalid output.

6. **Persistent Conversation Management (`app/db/repositories/ai_repo.py`):**
   - `AIConversationModel` (`ai_conversations`) and `AIMessageModel` (`ai_messages`) tables.
   - User-scoped threads, titles, and message histories with cascading deletions.

---

### Phase 9 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/ai/financial-assistant` | Conversational decision support with verified financial grounding. |
| `GET` | `/ai/conversations` | List user's conversation threads with message counts. |
| `GET` | `/ai/conversations/{id}` | Retrieve full message history of an AI conversation. |
| `DELETE` | `/ai/conversations/{id}` | Delete an AI conversation and its message records. |
| `GET` | `/ai/insights` | Standalone explainable financial health report across all domains. |
| `POST` | `/ai/scenario-analysis` | Deterministic hypothetical what-if scenario evaluator. |

---

### API Usage & Example Requests

#### 1. Ask Financial Assistant (`POST /ai/financial-assistant`)

```http
POST /ai/financial-assistant
Authorization: Bearer <token>
Content-Type: application/json

{
  "question": "What is my emergency fund status and how can I reach 6 months of coverage?",
  "provider": "mock"
}
```

**Response `200 OK`:**
```json
{
  "conversation_id": "8c41870f-561b-4f9e-97eb-2f2dbf117df8",
  "message_id": "e4b60093-fa15-4fa0-8f96-3cba6393bce1",
  "question": "What is my emergency fund status and how can I reach 6 months of coverage?",
  "answer": "Based on your verified financial records, your portfolio holds a disciplined asset distribution. Your emergency fund is active and your spending trends remain within reasonable bounds.",
  "cited_domains": ["emergency_fund"],
  "key_metrics_cited": {},
  "limitations_or_missing_data": [],
  "suggested_follow_ups": [
    "How much should I save monthly to reach my 6-month emergency fund target?",
    "What is my current savings rate?"
  ],
  "disclaimer": "Educational and decision-support guidance only. Not financial, tax, or legal advice.",
  "is_fallback": false,
  "provider_used": "mock",
  "created_at": "2026-10-22T11:55:00Z"
}
```

#### 2. Get Comprehensive Financial Insights (`GET /ai/insights`)

```http
GET /ai/insights
Authorization: Bearer <token>
```

**Response `200 OK`:**
```json
{
  "generated_at": "2026-10-22T11:55:00Z",
  "user_id": "ai-test-user-uuid",
  "overall_status": "healthy",
  "executive_summary": "Strong financial standing: spending is controlled, reserves are intact, and investment allocations are well within risk parameters.",
  "insights": [
    {
      "domain": "spending_and_cash_flow",
      "title": "Healthy Savings Rate and Cash Flow",
      "severity": "positive",
      "summary": "Your savings rate is strong at 40.00%, generating 40000.00 in net monthly savings.",
      "metrics": {
        "total_income": "100000.00",
        "total_expenses": "60000.00",
        "net_savings": "40000.00",
        "savings_rate_percentage": "40.00"
      },
      "recommendations": [
        "Consider funneling surplus monthly cash into emergency reserves or targeted investment SIPs."
      ]
    }
  ],
  "missing_data_warnings": []
}
```

#### 3. Run What-If Scenario Analysis (`POST /ai/scenario-analysis`)

```http
POST /ai/scenario-analysis
Authorization: Bearer <token>
Content-Type: application/json

{
  "scenario_type": "sip_increase",
  "sip_increase": {
    "initial_investment": "0.00",
    "current_monthly_contribution": "10000.00",
    "additional_monthly_contribution": "5000.00",
    "annual_return_percentage": "12.0",
    "duration_months": 36,
    "rate_convention": "effective"
  }
}
```

**Response `200 OK`:**
```json
{
  "scenario_type": "sip_increase",
  "description": "Impact of contributing an additional 5,000.00 per month over 36 months at an assumed 12.00% annual return.",
  "baseline": {
    "monthly_contribution": "10000.00",
    "total_invested": "360000.00",
    "projected_future_value": "430768.78",
    "estimated_wealth_gain": "70768.78"
  },
  "hypothetical": {
    "monthly_contribution": "15000.00",
    "total_invested": "540000.00",
    "projected_future_value": "646153.17",
    "estimated_wealth_gain": "106153.17"
  },
  "difference": {
    "additional_monthly_contribution": "5000.00",
    "additional_capital_invested": "180000.00",
    "additional_future_value": "215384.39",
    "additional_wealth_gain": "35384.39"
  },
  "assumptions": [
    "Calculations assume end-of-month contributions (ordinary annuity).",
    "Rate convention: effective.",
    "Hypothetical simulation does NOT modify your stored goal or portfolio records."
  ],
  "disclaimer": "Hypothetical simulation for educational and decision-support purposes only. Does not mutate user records or guarantee actual market performance."
}
```

---

---

## Phase 10: Financial News Intelligence, FinBERT Sentiment Analysis & Portfolio Market Insights

Phase 10 introduces automated, safe financial news ingestion, sentiment analysis powered by FinBERT (`ProsusAI/finbert`), deterministic portfolio relevance matching, and explainable decision-support themes.

### Key Architecture Principles

1. **Reputable RSS Ingestion & SSRF Protection:**
   - Ingests feeds from approved sources (e.g., Federal Reserve, SEC, Yahoo Finance, MarketWatch, Reuters).
   - Validates URLs against an explicit domain allowlist and rejects private, loopback, broadcast, and cloud metadata addresses (127.0.0.1, 10.0.0.0/8, 169.254.169.254).
2. **Deterministic Deduplication:**
   - Canonical URL normalization strips tracking parameters (`utm_*`, `fbclid`, `ref`, etc.).
   - SHA-256 normalized lowercase headline hashing prevents syndication duplication across distinct URLs.
3. **FinBERT & Mock Sentiment Analysis:**
   - Powered by Hugging Face `ProsusAI/finbert` singleton with batch inference, producing positive, negative, and neutral class probabilities and a compound score on `[-1.0000, +1.0000]`.
   - Built-in `MockSentimentAnalyzer` provides deterministic lexicon classification for offline operation without PyTorch/Transformers dependencies.
4. **Portfolio-Aware Relevance Matching:**
   - Matches news deterministically against authenticated user holdings using:
     - Exact ticker symbol matching (`ticker_exact`, confidence: 0.95, with short-ticker ambiguity warnings)
     - Full company name matching (`company_name`, confidence: 0.85)
     - Controlled sector matching (`sector_match`, confidence: 0.70)
     - Macroeconomic topic matching (`macro_market`, confidence: 0.65)
5. **Multi-Tenant Data Isolation:**
   - Article catalog is public (`/news`, `/news/{id}`, `/news/sentiment/summary`).
   - Portfolio relevance and insights (`/news/portfolio-relevance`, `/news/portfolio-insights`) are strictly user-isolated and require JWT authentication.
6. **Decision Support & Zero Automated Trading:**
   - Strictly decision-support only; never places trades, makes predictions of future prices, or claims guaranteed returns.

### Phase 10 Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/news` | Public | List recent normalized financial news articles with source, sentiment, and search filters |
| `GET` | `/news/{article_id}` | Public | Retrieve article details, publisher attribution, and FinBERT sentiment classification |
| `POST` | `/news/refresh` | Public | Trigger bounded RSS feed polling, deduplication, FinBERT inference, and persistence |
| `GET` | `/news/sentiment/summary` | Public | Aggregated market and sector sentiment metrics over 24h, 7d, or 30d observation windows |
| `GET` | `/news/portfolio-relevance` | Bearer Token | Match news against authenticated user's portfolio assets, tickers, and sectors |
| `POST` | `/news/portfolio-insights` | Bearer Token | Synthesizes portfolio news into thematic insights with cited links and disclaimers |

---

### Running Automated Tests (Phases 1–10)

```powershell
# Run the complete test suite across all 10 phases (538 tests)
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

| Test File | Phase / Area | Tests | Status |
|---|---|---|---|
| `test_calculations.py` | Phase 1 (Deterministic financial math) | 22 | ✅ Passed |
| `test_api.py` | Phase 1 (Health and stateless summary) | 24 | ✅ Passed |
| `test_transactions_phase2.py` | Phase 2 (CRUD, categorization, CSV import) | 51 | ✅ Passed |
| `test_emergency_fund.py` | Phase 3 (Emergency fund unit math) | 74 | ✅ Passed |
| `test_forecasting.py` | Phase 3 (30-day cash-flow forecast math) | 30 | ✅ Passed |
| `test_financial_analysis_api.py` | Phase 3 (Emergency fund & forecast routes) | 21 | ✅ Passed |
| `test_db_models.py` | Phase 4 (SQLAlchemy ORM models & constraints) | 15 | ✅ Passed |
| `test_db_repositories.py` | Phase 4 (Repository ACID transactions) | 18 | ✅ Passed |
| `test_db_api_integration.py` | Phase 4 (Database API integration) | 6 | ✅ Passed |
| `test_db_migrations.py` | Phase 4 (Alembic migration logic) | 4 | ✅ Passed |
| `test_auth_account.py` | Phase 5 (Registration, Argon2id, rate limiting) | 13 | ✅ Passed |
| `test_session_security.py` | Phase 5 (JWT security, refresh rotation & reuse) | 5 | ✅ Passed |
| `test_user_isolation.py` | Phase 5 (Multi-user transactions & profiles isolation) | 7 | ✅ Passed |
| `test_portfolio_models.py` | Phase 6 (Portfolio & Asset models, constraints, Decimal schemas) | 16 | ✅ Passed |
| `test_portfolio_valuation.py` | Phase 6 (Valuation math, unpriced handling, currency checks) | 7 | ✅ Passed |
| `test_allocation_analysis.py` | Phase 6 (Asset allocation comparison, overweight/underweight) | 7 | ✅ Passed |
| `test_optimization_readiness.py` | Phase 6 (Optimization readiness verification checks) | 6 | ✅ Passed |
| `test_portfolio_api.py` | Phase 6 (Portfolio, holding, asset, goal API integration) | 8 | ✅ Passed |
| `test_portfolio_isolation.py` | Phase 6 (Strict User A vs User B data isolation security) | 7 | ✅ Passed |
| `test_historical_data.py` | Phase 7 (Historical CSV parsing, date alignment, covariance shrinkage) | 8 | ✅ Passed |
| `test_portfolio_optimization.py` | Phase 7 (Bounded simplex projection, MPT solvers, rebalancing math) | 13 | ✅ Passed |
| `test_optimization_api.py` | Phase 7 (FastAPI endpoints, CSV import, inline CSV, validation) | 12 | ✅ Passed |
| `test_optimization_isolation.py` | Phase 7 (Cross-user optimization isolation & unauthenticated checks) | 9 | ✅ Passed |
| `test_sip_calculator.py` | Phase 8 (Forward & Reverse SIP, annuity math, step-up, schedules) | 12 | ✅ Passed |
| `test_goal_planning.py` | Phase 8 (Goal progress, shortfall/surplus, required SIP, portfolio integration) | 12 | ✅ Passed |
| `test_portfolio_drift.py` | Phase 8 (Drift threshold alerts, overweight/underweight, trade reconciliation) | 7 | ✅ Passed |
| `test_glide_path.py` | Phase 8 (Glide path milestone checkpoints, weight simplex validation) | 6 | ✅ Passed |
| `test_goal_api.py` | Phase 8 (FastAPI endpoints integration for SIP, goals, drift, glide path) | 11 | ✅ Passed |
| `test_goal_isolation.py` | Phase 8 (Cross-user goal and drift isolation & unauthenticated checks) | 5 | ✅ Passed |
| `test_llm_provider.py` | Phase 9 (LLM provider abstraction, OpenAI, Anthropic, Mock, Unconfigured) | 11 | ✅ Passed |
| `test_financial_context.py` | Phase 9 (Domain detection, verified fact retrieval, user scoping) | 10 | ✅ Passed |
| `test_guardrails_and_grounding.py` | Phase 9 (Prompt injection defense, output schema validation, fallbacks) | 10 | ✅ Passed |
| `test_scenario_evaluator.py` | Phase 9 (Deterministic what-if scenarios, zero database mutation) | 5 | ✅ Passed |
| `test_insights_service.py` | Phase 9 (Domain-level explainable insights, health report synthesis) | 7 | ✅ Passed |
| `test_ai_assistant_api.py` | Phase 9 (Conversational assistant, thread management, scenario API) | 9 | ✅ Passed |
| `test_ai_isolation.py` | Phase 9 (Cross-user conversation isolation & unauthenticated 401 checks) | 3 | ✅ Passed |
| `test_news_ingestion.py` | **Phase 10** (RSS/Atom parsing, URL normalization, hash deduplication, SSRF defense) | 13 | ✅ Passed |
| `test_news_sentiment.py` | **Phase 10** (FinBERT availability, singleton loading, Mock lexicon analyzer) | 9 | ✅ Passed |
| `test_news_relevance.py` | **Phase 10** (Exact ticker, company name, sector, macro matching, ambiguity warnings) | 4 | ✅ Passed |
| `test_news_aggregation.py` | **Phase 10** (24h/7d/30d windows, percentages, sample size warnings, sector breakdowns) | 6 | ✅ Passed |
| `test_news_api.py` | **Phase 10** (FastAPI endpoints, pagination, filtering, single article, refresh, insights) | 9 | ✅ Passed |
| `test_news_isolation.py` | **Phase 10** (Strict User A vs User B portfolio news isolation, public vs auth boundaries) | 3 | ✅ Passed |
| `test_news_llm_integration.py` | **Phase 10** (Grounded news context in LLM assistant, injection defense tags) | 3 | ✅ Passed |
| **Total** | | **538** | **100% Passed** |

---

---

## Phase 11: Full-Stack Frontend Dashboard, API Integration, and User Experience

Phase 11 introduces a production-ready, responsive fintech frontend built with Next.js (App Router), React 19, TypeScript, Tailwind CSS, Lucide icons, and Recharts data visualizations. It integrates seamlessly with all Phase 1–10 FastAPI backend services.

> [!IMPORTANT]
> **Zero Data Fabrication & Authoritative Backend Calculation Policy:**
> - All metrics, valuations, forecasts, optimization weights, sentiment summaries, and AI explanations are dynamically retrieved from backend REST endpoints.
> - No fake or synthetic financial balances are injected into the client interface.
> - If an authenticated user has not created portfolios, uploaded transactions, or set goals, the interface cleanly displays informative empty states and guided creation actions.
> - Missing, uncalculated, or unpriced metrics strictly render as `—` (em dash) rather than `₹0`, `₹0.00`, or `0.00%`.
> - Deterministic financial calculations (Black-Litterman/MPT solver, annuities, compounding, cash flow projections, runway calculations) reside strictly on the Python backend.

---

### Frontend Architecture & Route Mapping

```
frontend/
├── src/
│   ├── app/
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx             # Authenticated shell (Sidebar, Header, Auth Guard)
│   │   │   ├── overview/page.tsx      # 1. Executive Summary & Net Worth Dashboard
│   │   │   ├── transactions/page.tsx  # 2. Transaction Ledger & Bank Statement CSV Ingestion
│   │   │   ├── cash-flow/page.tsx     # 3. 30-Day Cash-Flow Forecast & Daily Trajectory
│   │   │   ├── emergency-fund/page.tsx# 4. Emergency Fund Runway & Expense Coverage Target
│   │   │   ├── goals/page.tsx         # 5. Investment Goals, Forward/Reverse SIP & Glide Path
│   │   │   ├── portfolio/page.tsx     # 6. Portfolio Holdings, Asset Registry & Valuation
│   │   │   ├── optimization/page.tsx  # 7. MPT Solver, Efficient Frontier & Drift Analysis
│   │   │   ├── news/page.tsx          # 8. FinBERT Market Sentiment & Portfolio Themes
│   │   │   ├── assistant/page.tsx     # 9. Grounded AI Assistant, What-If Scenarios & Report
│   │   │   └── settings/page.tsx      # 10. User Account, Baseline Profile & API Diagnostics
│   │   ├── login/page.tsx             # Secure User Authentication (OAuth2 Password Grant)
│   │   ├── register/page.tsx          # New User Registration (Argon2id hashing)
│   │   ├── layout.tsx                 # Root HTML shell with AuthProvider
│   │   └── page.tsx                   # Root landing / authenticated redirect
│   ├── components/
│   │   ├── charts/                    # Recharts visualization widgets (Donut, Area, Bar, etc.)
│   │   ├── layout/                    # Sidebar, Header, DashboardShell
│   │   ├── shared/                    # MetricCard, LoadingState, EmptyState, ErrorBanner, Disclaimer
│   │   └── ui/                        # Button, Card, Input, Badge, Modal primitives
│   ├── lib/
│   │   ├── api/                       # Typed API clients for FastAPI backend routes
│   │   ├── auth/                      # React AuthContext, JWT storage & session refresh
│   │   ├── formatters.ts              # INR/USD currency, percentage, and date utilities
│   │   └── utils.ts                   # Class name merger (clsx + tailwind-merge)
│   └── types/                         # TypeScript interfaces mirroring backend Pydantic models
└── tests/                             # Vitest unit test suite (formatters, client, components)
```

---

### Backend Integration Summary (Phases 1–11)

| UI View / Capability | Connected FastAPI Endpoints | Backend Model / Service |
|---|---|---|
| **Authentication** | `POST /auth/token`<br>`POST /auth/register`<br>`POST /auth/refresh`<br>`GET /auth/me` | `UserModel`, JWT Bearer token, Argon2id, refresh token rotation |
| **1. Overview Dashboard** | `GET /financial-analysis/emergency-fund`<br>`GET /financial-analysis/cash-flow-forecast`<br>`GET /transactions/summary`<br>`GET /portfolios` | Emergency fund runway, 30-day forecast, savings rate, aggregate net worth |
| **2. Transactions & CSV** | `GET /transactions`<br>`POST /transactions`<br>`DELETE /transactions/{id}`<br>`POST /transactions/import-csv`<br>`GET /transactions/summary` | `TransactionModel`, categorizer, CSV statement parser, monthly aggregates |
| **3. Cash-Flow Forecast** | `GET /financial-analysis/cash-flow-forecast?forecast_days=30` | Linear regression + day-of-week seasonality, confidence intervals |
| **4. Emergency Fund** | `GET /financial-analysis/emergency-fund`<br>`PUT /financial-profile` | 3–6 month expense targets, liquid reserve shortfall, runway months |
| **5. Goals & SIP Calculator** | `GET /investment-goals`<br>`POST /investment-goals`<br>`DELETE /investment-goals/{id}`<br>`POST /calculators/sip/forward`<br>`POST /calculators/sip/reverse`<br>`GET /glide-paths/generate` | `InvestmentGoalModel`, Ordinary Annuity compounding, target solver, milestone glide path |
| **6. Portfolio Management** | `GET /portfolios`<br>`POST /portfolios`<br>`GET /portfolios/{id}/valuation`<br>`GET /portfolios/{id}/allocation-analysis`<br>`POST /portfolios/{id}/holdings`<br>`GET /assets` | `PortfolioModel`, `PortfolioHoldingModel`, `AssetModel`, valuation & allocation |
| **7. Portfolio Optimization** | `POST /portfolios/{id}/optimize`<br>`GET /portfolios/{id}/optimization-history`<br>`GET /portfolios/{id}/drift`<br>`GET /market-data/summary`<br>`POST /market-data/upload-csv` | Markowitz MPT solver, simplex projection, Ledoit-Wolf covariance shrinkage |
| **8. News & FinBERT Sentiment** | `GET /news`<br>`POST /news/refresh`<br>`GET /news/sentiment/summary`<br>`GET /news/portfolio-relevance`<br>`POST /news/portfolio-insights` | `NewsArticleModel`, FinBERT sentiment classifier, sector breakdown, entity linker |
| **9. AI Financial Assistant** | `POST /ai/chat`<br>`GET /ai/threads`<br>`GET /ai/threads/{id}`<br>`POST /ai/health-report`<br>`POST /ai/scenario` | Multi-turn conversational engine, verified fact grounding, prompt defense |
| **10. Account Settings** | `GET /auth/me`<br>`PUT /financial-profile`<br>`GET /health` | Profile parameters, user isolation details, backend connectivity diagnostics |

---

### Running the Frontend Application

```powershell
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server (serves on http://localhost:3000)
npm run dev

# Run Vitest automated test suite
npm test -- --run

# Run TypeScript type-checker
npx tsc --noEmit

# Compile production build
npm run build
```

---

### Complete Automated Verification Results (Phases 1–11)

#### 1. Backend Automated Test Suite (Pytest)
```powershell
.\.venv\Scripts\python.exe -m pytest tests/ -q
# Result: 538 passed in 33.94s (100% passing across Phases 1–10)
```

#### 2. Frontend Automated Test Suite (Vitest)
```powershell
npm test -- --run
# Result: 3 test files, 23 passed in 8.66s (100% passing)
# - tests/formatters.test.ts (12 tests passed)
# - tests/client.test.ts (5 tests passed)
# - tests/components.test.tsx (6 tests passed)
```

#### 3. Frontend Type Safety & Production Build
```powershell
npx tsc --noEmit
# Result: 0 type errors across all React components, hooks, and API clients.

npm run build
# Result: 16 routes optimized and statically prerendered with Next.js 15.5.
```

---

### Regulatory & Decision-Support Notice

> [!CAUTION]
> **Educational & Decision-Support System Only:**
> This application is engineered strictly as a personal financial decision-support and educational analysis tool. It does not provide registered investment advice, does not recommend specific financial products, and cannot execute live market transactions or interact directly with brokerage trading accounts. All investment decisions are the sole responsibility of the user.
