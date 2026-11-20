"""
Chapter 3: Problem Identification and Software Requirements Specification (SRS)
Includes:
3.1 Problem Identification
3.2 Functional Requirements (FR-01 to FR-18)
3.3 Non-Functional Requirements (NFR-01 to NFR-06)
3.4 Software Requirements
3.5 Hardware Requirements
3.6 User Classes and Characteristics
3.7 Operating Environment
3.8 System Constraints
3.9 Assumptions and Dependencies
3.10 External Interface Requirements
3.11 Database Requirements
3.12 Security Requirements
3.13 Use Case Descriptions (Detailed Use Cases UC-01 to UC-07)
3.14 Acceptance Criteria
3.15 Context-Level DFD (Level 0) with embedded image
3.16 Level 1 DFD with embedded image
3.17 Level 2 DFDs (5 detailed sub-DFDs with embedded images)
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

def add_heading_1(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(14)
    r.font.bold = True
    r.font.color.rgb = RGBColor(15, 23, 42)
    return p

def add_heading_2(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(30, 41, 59)
    return p

def add_heading_3(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(11.5)
    r.font.bold = True
    r.font.color.rgb = RGBColor(51, 65, 85)
    return p

def add_body_p(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.space_after = Pt(8)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r = p.add_run(text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor(30, 41, 59)
    return p

def add_bullet_p(doc, bold_prefix, text):
    p = doc.add_paragraph(style='List Bullet')
    p.paragraph_format.line_spacing = 1.2
    p.paragraph_format.space_after = Pt(4)
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r_pre = p.add_run(bold_prefix + ": ")
    r_pre.font.name = "Times New Roman"
    r_pre.font.size = Pt(11.5)
    r_pre.font.bold = True
    r_body = p.add_run(text)
    r_body.font.name = "Times New Roman"
    r_body.font.size = Pt(11.5)
    return p

def add_diagram_image(doc, img_path, caption, fig_num):
    if os.path.exists(img_path):
        p_img = doc.add_paragraph()
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(12)
        p_img.paragraph_format.space_after = Pt(4)
        p_img.paragraph_format.keep_with_next = True
        p_img.add_run().add_picture(img_path, width=Inches(6.2))
        
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_cap.paragraph_format.space_after = Pt(14)
        r_cap = p_cap.add_run(f"Figure {fig_num}: {caption}")
        r_cap.font.name = "Times New Roman"
        r_cap.font.size = Pt(10.5)
        r_cap.font.bold = True
        r_cap.font.color.rgb = RGBColor(15, 23, 42)

def add_chapter_3(doc):
    p_ch = doc.add_paragraph()
    p_ch.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ch.paragraph_format.space_before = Pt(18)
    p_ch.paragraph_format.space_after = Pt(4)
    r_ch = p_ch.add_run("CHAPTER 3")
    r_ch.font.name = "Times New Roman"
    r_ch.font.size = Pt(16)
    r_ch.font.bold = True
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(18)
    r_t = p_title.add_run("PROBLEM IDENTIFICATION AND\nSOFTWARE REQUIREMENTS SPECIFICATION (SRS)")
    r_t.font.name = "Times New Roman"
    r_t.font.size = Pt(15)
    r_t.font.bold = True
    
    add_heading_1(doc, "3.1 Problem Identification")
    add_body_p(
        doc,
        "Modern personal financial decision-making is burdened by three critical structural failures: systemic data fragmentation, "
        "absence of mathematical risk management in retail software, and the dangerous propensity of commercial LLMs to hallucinate numerical advice. "
        "An individual's financial reality is dispersed across checking accounts, credit cards, brokerage holdings, fixed deposits, and recurring bills. "
        "Without an integrated platform, users cannot evaluate the cascading impact that a short-term discretionary expense has on their liquid emergency "
        "runway, nor can they determine whether their multi-asset portfolio satisfies Harry Markowitz's mean-variance efficiency criteria."
    )
    add_body_p(
        doc,
        "Furthermore, retail investors are increasingly seeking advice from conversational AI interfaces. When queried regarding complex portfolio "
        "rebalancing or SIP allocations, commercial generative models invent speculative percentages and hallucinate mathematical formulas, "
        "creating severe financial and fiduciary risks. This Software Requirements Specification (SRS) defines the formal functional, behavioral, "
        "security, and architectural requirements for an authoritative system engineered to eliminate these defects."
    )
    
    add_heading_1(doc, "3.2 Functional Requirements")
    add_body_p(
        doc,
        "The system must fulfill eighteen core functional requirements (FR-01 to FR-18) spanning all implemented engineering modules:"
    )
    
    fr_list = [
        ("FR-01: User Registration & Authentication", "The system shall support secure user registration and login utilizing Argon2 password hashing and standard JWT bearer token authentication."),
        ("FR-02: Cryptographic Tenant Isolation", "The system shall isolate all database queries strictly by authenticated user_id, ensuring zero cross-tenant data leakage."),
        ("FR-03: Transaction Ledger & Manual Entry", "The system shall allow users to record, update, filter, paginate, and delete financial transactions with arbitrary-precision Decimal amounts."),
        ("FR-04: Automated CSV Ingestion & Deduplication", "The system shall parse heterogeneous bank statement CSV files and reject duplicate transactions utilizing MD5 content hashing."),
        ("FR-05: Expense Categorization Engine", "The system shall categorize transactions into predefined categories (Groceries, Housing, Transport, Utilities, Discretionary) using deterministic keyword rules."),
        ("FR-06: Liquid Emergency Fund Analysis", "The system shall evaluate total liquid assets against essential monthly baseline expenditures to calculate coverage runway (in months) and shortfall against 3- and 6-month targets."),
        ("FR-07: 30-Day Daily Cash-Flow Forecasting", "The system shall project daily closing balances across a forward-looking 30-day window based on recurring income/expense periodicity and generate low-balance liquidity warnings."),
        ("FR-08: Multi-Asset Portfolio Tracking", "The system shall maintain multi-asset portfolios across equities, mutual funds, debt, gold/commodities, and cash, tracking average purchase price, quantity, and real-time market value."),
        ("FR-09: Markowitz Modern Portfolio Theory (MPT) Optimization", "The system shall construct the asset covariance matrix from historical daily price series and execute Sequential Least Squares Programming (SLSQP) to determine weights that maximize the Sharpe ratio."),
        ("FR-10: Portfolio Rebalancing Drift Analysis", "The system shall compute the percentage drift of current holdings against target allocation weights and recommend specific buy/sell trade amounts when a 5% threshold is breached."),
        ("FR-11: Goal-Based Reverse SIP Planning", "The system shall calculate the required monthly SIP contribution needed to attain a target wealth goal given tenure and expected return using deterministic annuity formulas."),
        ("FR-12: Multi-Asset Glide-Path Generation", "The system shall construct age- or horizon-based asset allocation glide paths, automatically shifting weight from equities to debt as target dates approach."),
        ("FR-13: Conversational AI Decision Support", "The system shall provide a conversational interface powered by Groq LPU acceleration, synthesizing user queries with verified database metrics."),
        ("FR-14: Financial Context Grounding & Guardrails", "The system shall inject deterministic metrics into the LLM prompt and validate that generated responses do not contradict verified database facts."),
        ("FR-15: Financial News Ingestion & FinBERT Scoring", "The system shall continuously ingest financial RSS news feeds and classify article sentiment into positive, negative, and neutral scores using ProsusAI/finbert."),
        ("FR-16: Macroeconomic Stress Testing", "The system shall model deterministic hypothetical market shock vectors (broad equity crash, debt yield spikes, sector collapse) and output absolute loss and asset contribution breakdowns."),
        ("FR-17: Historical Portfolio Backtesting", "The system shall simulate portfolio performance across historical price horizons with periodic rebalancing, transaction cost deductions, and benchmark comparison (Nifty 50 / S&P 500)."),
        ("FR-18: Correlated Monte Carlo Simulation", "The system shall execute 1,000+ stochastic iterations using Cholesky decomposition of the covariance matrix to return 5th, 25th, 50th, 75th, and 95th percentile wealth cones and goal attainment probabilities.")
    ]
    
    for req_id, req_desc in fr_list:
        add_bullet_p(doc, req_id, req_desc)
        
    add_heading_1(doc, "3.3 Non-Functional Requirements")
    add_body_p(doc, "The platform must adhere to the following rigorous non-functional engineering standards:")
    add_bullet_p(doc, "NFR-01: Performance & Latency", "API endpoints executing deterministic calculations shall respond within 150 milliseconds. Conversational AI inference via Groq LPU shall achieve sub-second execution (target < 0.5s).")
    add_bullet_p(doc, "NFR-02: Numerical Precision & Correctness", "All financial calculations shall use arbitrary-precision Decimal arithmetic (Python Decimal module) to ensure zero IEEE 754 floating-point drift.")
    add_bullet_p(doc, "NFR-03: Security & Cryptography", "Passwords shall be hashed using Argon2 with salt. All API endpoints shall enforce JWT validation, CORS origin verification, SQL parameterization, and OWASP security headers.")
    add_bullet_p(doc, "NFR-04: Reliability & Graceful Fallback", "If an external provider (Groq API, Yahoo Finance) is unreachable, the system shall seamlessly fall back to deterministic database-synthesized summaries without crashing.")
    add_bullet_p(doc, "NFR-05: Usability & Responsiveness", "The frontend dashboard shall be fully responsive across desktop, tablet, and mobile displays, featuring dark/light modes, accessible contrast, and intuitive Recharts data visualizations.")
    add_bullet_p(doc, "NFR-06: Maintainability & Testability", "The backend codebase shall maintain a modular service-repository architecture with > 90% test coverage across financial math, tenant isolation, and security suites.")

    add_heading_1(doc, "3.4 Software Requirements")
    add_bullet_p(doc, "Operating System", "Microsoft Windows 10 / 11, Linux (Ubuntu 22.04 LTS), macOS.")
    add_bullet_p(doc, "Backend Framework", "Python 3.12, FastAPI 0.115+, Uvicorn ASGI Server.")
    add_bullet_p(doc, "Database & ORM", "PostgreSQL 16, SQLAlchemy 2.0 ORM, Alembic migrations.")
    add_bullet_p(doc, "Mathematical & AI Stack", "NumPy 2.0, pandas, SciPy (SLSQP solver), PyTorch, HuggingFace Transformers (ProsusAI/finbert), Groq Python SDK / HTTPX.")
    add_bullet_p(doc, "Frontend Framework", "Next.js 15 (React 19), TypeScript, TailwindCSS, Lucide Icons, Recharts.")
    add_bullet_p(doc, "Testing & Tooling", "Pytest 9.0+, AnyIO, Node.js 20+, npm, Git.")

    add_heading_1(doc, "3.5 Hardware Requirements")
    add_bullet_p(doc, "Processor", "Intel Core i5 / AMD Ryzen 5 or higher (minimum 4 cores, 8 threads).")
    add_bullet_p(doc, "System RAM", "Minimum 8 GB RAM (16 GB recommended for local transformer model caching).")
    add_bullet_p(doc, "Storage", "Minimum 10 GB free solid-state storage (SSD).")
    add_bullet_p(doc, "Network", "Standard broadband internet connection for live market price feeds and Groq LPU cloud inference.")

    add_heading_1(doc, "3.6 User Classes and Characteristics")
    add_bullet_p(doc, "Retail Investors & Salaried Individuals", "Primary users seeking automated budgeting, liquid runway checks, and disciplined long-term SIP goal planning.")
    add_bullet_p(doc, "Active Portfolio Managers", "Advanced retail users utilizing Markowitz efficient frontier optimization, rebalancing drift analysis, and Monte Carlo stress testing.")
    add_bullet_p(doc, "System Administrators", "Technical operators managing database migrations, API keys, news ingestion pipelines, and security audits.")

    add_heading_1(doc, "3.7 Operating Environment")
    add_body_p(
        doc,
        "The application operates in a client-server web architecture. The backend runs as an asynchronous ASGI service inside a Python virtual "
        "environment on port 8000. The frontend operates as a Next.js Server-Side and Client-Side Rendered web app on port 3000. Communication "
        "is conducted over HTTP/HTTPS with strict Cross-Origin Resource Sharing (CORS) security policies."
    )

    add_heading_1(doc, "3.8 System Constraints")
    add_bullet_p(doc, "Fiduciary Regulatory Constraint", "The system shall function strictly as an educational and decision-support tool. It shall not execute autonomous financial trades on commercial exchanges without explicit human sign-off.")
    add_bullet_p(doc, "Mathematical Convergence", "Portfolio optimization is subject to quadratic solver feasibility bounds; if historical return data is insufficient, explicit data-readiness warnings must be returned.")
    add_bullet_p(doc, "Third-Party Quotas", "External API ingestion (Groq LPU, Yahoo Finance) is subject to rate-limiting and network availability, requiring local caching and fallback layers.")

    add_heading_1(doc, "3.9 Assumptions and Dependencies")
    add_body_p(
        doc,
        "It is assumed that users upload valid CSV statements conforming to standard bank export formats (Date, Description, Amount, Type). "
        "The system depends on the availability of historical price data for volatility and covariance computation, and requires access to "
        "external RSS feeds for financial news sentiment analysis."
    )

    add_heading_1(doc, "3.10 External Interface Requirements")
    add_bullet_p(doc, "User Interface", "A responsive, single-page application dashboard built with Next.js, featuring navigation tabs for Overview, Transactions, Cash Flow, Emergency Fund, Portfolio, Optimization, Goals, AI Assistant, News, and Simulations.")
    add_bullet_p(doc, "Hardware Interface", "Standard web client hardware (monitor, mouse/touchscreen, keyboard).")
    add_bullet_p(doc, "Software Interface", "RESTful JSON APIs exposed via OpenAPI specification at /docs.")
    add_bullet_p(doc, "Communications Interface", "HTTPS / WebSocket connections with Bearer Authorization headers.")

    add_heading_1(doc, "3.11 Database Requirements")
    add_body_p(
        doc,
        "The database schema must enforce relational integrity, primary key UUIDs, cascading deletes on dependent user records, "
        "unique constraints on email addresses and asset tickers, and strict NUMERIC(14, 2) decimal precision on monetary balances."
    )

    add_heading_1(doc, "3.12 Security Requirements")
    add_bullet_p(doc, "OWASP Compliance", "Mandatory headers: X-Content-Type-Options: nosniff, X-Frame-Options: DENY, X-XSS-Protection: 1; mode=block.")
    add_bullet_p(doc, "SQL Injection Prevention", "All database operations shall use parameterized SQLAlchemy ORM queries; raw string concatenation is strictly forbidden.")
    add_bullet_p(doc, "Token Security", "JWT access tokens shall expire within configured time limits and contain HMAC-SHA256 signatures.")

    add_heading_1(doc, "3.13 Use Case Descriptions")
    add_body_p(doc, "The system's core capabilities are formalized through seven exhaustive use case specifications:")

    use_cases = [
        ("UC-01", "User Authentication & Session Initialization", "Investor / User", "User navigates to /login", "1. User submits email & password.\n2. Backend verifies Argon2 hash.\n3. Signed JWT token returned and stored in secure browser storage.", "Invalid credentials return HTTP 401 with descriptive error.", "User session initialized with isolated tenant context."),
        ("UC-02", "Bank Statement CSV Ingestion", "Investor / User", "User authenticated; CSV file available", "1. User uploads CSV.\n2. Parser extracts Date, Description, Amount.\n3. MD5 hash generated per row to filter duplicates.\n4. Clean records stored in DB.", "Malformed CSV returns HTTP 422 with row-level error log.", "Transaction ledger updated; spending metrics re-computed."),
        ("UC-03", "Cash Flow & Emergency Fund Runway", "Investor / User", "Transactions recorded in database", "1. User opens Cash Flow tab.\n2. Engine aggregates essential outflows.\n3. Calculates 3-to-6 mo targets & coverage months.\n4. Generates 30-day daily balance projections.", "Insufficient transaction history generates data-readiness warning.", "Dashboard displays coverage status and liquidity warnings."),
        ("UC-04", "Modern Portfolio Theory Optimization", "Investor / User", "Portfolio contains >= 2 active asset holdings", "1. User navigates to Optimization tab.\n2. Solver fetches historical prices.\n3. Builds covariance matrix & runs SLSQP.\n4. Returns optimal weights maximizing Sharpe ratio.", "Singular covariance matrix triggers Ridge-regularization fallback.", "Optimal weights and efficient frontier plotted on chart."),
        ("UC-05", "Goal-Based Reverse SIP Computation", "Investor / User", "User authenticated", "1. User inputs goal name, target amount, target date, and expected return.\n2. Engine runs reverse annuity formula.\n3. Determines exact required monthly SIP.", "Target date in the past returns validation error.", "Goal saved with tracking progress and SIP payment schedule."),
        ("UC-06", "Conversational AI Decision Support", "Investor / User", "User submits query in AI Assistant tab", "1. Input sanitized for prompt injection.\n2. FinancialContextService retrieves user metrics.\n3. Groq LPU generates response in ~0.2s.\n4. Guardrails verify metrics and append disclaimers.", "Groq network timeout triggers deterministic fallback engine.", "Grounded, evidence-based financial answer rendered in chat."),
        ("UC-07", "Monte Carlo & Stress Testing", "Investor / User", "Portfolio valued with historical price cache", "1. User selects shock vector or simulation horizon.\n2. Cholesky decomposition simulates correlated returns.\n3. Calculates 5th, 50th, 95th percentile wealth cones.", "Excessive simulation bounds restricted to safe CPU limits.", "Visual probability distribution and goal success probability output.")
    ]

    for ucid, title, actor, pre, main, alt, post in use_cases:
        p_uc = doc.add_paragraph()
        p_uc.paragraph_format.space_before = Pt(8)
        p_uc.paragraph_format.space_after = Pt(2)
        r_uc = p_uc.add_run(f"Use Case: {ucid} - {title}")
        r_uc.font.name = "Times New Roman"
        r_uc.font.size = Pt(11)
        r_uc.font.bold = True
        
        tbl_uc = doc.add_table(rows=6, cols=2)
        tbl_uc.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl_uc.autofit = False
        tbl_uc.rows[0].cells[0].width = Inches(1.8)
        tbl_uc.rows[0].cells[1].width = Inches(4.7)
        
        uc_rows = [
            ("Primary Actor", actor),
            ("Preconditions", pre),
            ("Main Success Flow", main),
            ("Alternative / Error Flow", alt),
            ("Postconditions", post),
            ("Trigger", "User UI action / API request")
        ]
        for idx, (lbl, val) in enumerate(uc_rows):
            r = tbl_uc.rows[idx]
            r.cells[0].width = Inches(1.8)
            r.cells[1].width = Inches(4.7)
            p0 = r.cells[0].paragraphs[0]
            p0.add_run(lbl).font.bold = True
            p0.runs[0].font.name = "Times New Roman"
            p0.runs[0].font.size = Pt(9.5)
            p1 = r.cells[1].paragraphs[0]
            p1.add_run(val).font.name = "Times New Roman"
            p1.runs[0].font.size = Pt(9.5)

    add_heading_1(doc, "3.14 Acceptance Criteria")
    add_bullet_p(doc, "AC-01: Deterministic Precision", "Forward and reverse SIP calculations must match to within 1 paisa (₹0.01).")
    add_bullet_p(doc, "AC-02: Zero Floating-Point Drift", "Bank statement balances must sum exactly without IEEE 754 precision loss.")
    add_bullet_p(doc, "AC-03: Zero Cross-Tenant Data Leakage", "All tenant queries must be isolated; testing must confirm 100% isolation.")
    add_bullet_p(doc, "AC-04: SLSQP Optimization Bound", "Portfolio weights must sum to 1.0000 (100%) with all weights >= 0.")
    add_bullet_p(doc, "AC-05: AI Grounding Verification", "AI responses must cite verified database metrics and include mandatory disclaimers.")

    add_heading_1(doc, "3.15 Context-Level Data Flow Diagram (Level 0 DFD)")
    add_body_p(
        doc,
        "The Context-Level DFD (Level 0) models the entire application as a single central process interacting with external entities. "
        "The external entities comprise: the End User / Investor, External Financial Statement Sources (CSV), External Financial News Providers "
        "(RSS / Media APIs), and the High-Performance LLM Cloud Service (Groq LPU). Figure 3.1 illustrates the context diagram."
    )
    add_diagram_image(doc, "dfd_level_0.png", "Context-Level Data Flow Diagram (Level 0 DFD)", "3.1")

    add_heading_1(doc, "3.16 Level 1 Data Flow Diagram")
    add_body_p(
        doc,
        "The Level 1 DFD decomposes the system into eight core functional processes (P1 through P8) and six persistent data stores (D1 through D6):"
    )
    add_bullet_p(doc, "P1: User Authentication & Isolation", "Validates credentials and scopes data access to the authenticated user ID.")
    add_bullet_p(doc, "P2: Transaction Ingestion & Parsing", "Ingests bank statement CSVs, computes MD5 hashes, and detects duplicate records.")
    add_bullet_p(doc, "P3: Financial Analysis & Forecasting", "Evaluates spending patterns, liquid emergency fund runway, and 30-day cash flow.")
    add_bullet_p(doc, "P4: Portfolio Valuation & MPT Solver", "Calculates holding valuations, asset covariance matrices, and SLSQP optimal weights.")
    add_bullet_p(doc, "P5: Goal Planning & Reverse SIP", "Computes forward and reverse annuity trajectories and multi-asset glide paths.")
    add_bullet_p(doc, "P6: News Sentiment & FinBERT", "Ingests RSS news feeds and scores article sentiment using transformer NLP models.")
    add_bullet_p(doc, "P7: AI Financial Decision Support", "Constructs grounded prompt context and streams ultra-fast Groq LPU responses.")
    add_bullet_p(doc, "P8: Stress Testing & Monte Carlo", "Executes macroeconomic shock vectors and Cholesky-correlated stochastic simulations.")
    add_diagram_image(doc, "dfd_level_1.png", "Level 1 Data Flow Diagram (P1 to P8 Functional Decomposition)", "3.2")

    add_heading_1(doc, "3.17 Level 2 Data Flow Diagrams")
    add_body_p(doc, "Detailed functional breakdowns are provided for the system's five most critical subsystems:")

    add_heading_2(doc, "3.17.1 Level 2 DFD: Transaction Processing Sub-system (P2)")
    add_body_p(doc, "Decomposes CSV upload, sanitization, MD5 duplicate verification, and rule-based expense categorization.")
    add_diagram_image(doc, "dfd_level_2_tx.png", "Level 2 DFD: Transaction Processing Sub-system", "3.3")

    add_heading_2(doc, "3.17.2 Level 2 DFD: Financial Analysis & Cash Flow Sub-system (P3)")
    add_body_p(doc, "Decomposes monthly expense summation, emergency fund runway calculation, and daily forward cash-flow forecasting.")
    add_diagram_image(doc, "dfd_level_2_analysis.png", "Level 2 DFD: Financial Analysis and Cash Flow Forecasting Sub-system", "3.4")

    add_heading_2(doc, "3.17.3 Level 2 DFD: Portfolio Optimization & Risk Engine Sub-system (P4)")
    add_body_p(doc, "Decomposes price history matrix generation, covariance calculation, SLSQP optimization, and rebalancing drift.")
    add_diagram_image(doc, "dfd_level_2_portfolio.png", "Level 2 DFD: Portfolio Optimization and Risk Engine Sub-system", "3.5")

    add_heading_2(doc, "3.17.4 Level 2 DFD: Grounded AI Decision Support Sub-system (P7)")
    add_body_p(doc, "Decomposes input prompt sanitization, verified metric retrieval, Groq LPU execution, and guardrail validation.")
    add_diagram_image(doc, "dfd_level_2_ai.png", "Level 2 DFD: Grounded AI Decision Support Sub-system", "3.6")

    add_heading_2(doc, "3.17.5 Level 2 DFD: Stress Testing & Monte Carlo Simulation Sub-system (P8)")
    add_body_p(doc, "Decomposes parametric macroeconomic shocks, historical rebalancing backtesting, and Cholesky-correlated Monte Carlo simulations.")
    add_diagram_image(doc, "dfd_level_2_sim.png", "Level 2 DFD: Stress Testing and Monte Carlo Simulation Sub-system", "3.7")

    doc.add_page_break()
