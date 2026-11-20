"""
Chapter 4: Methodology and System Design for BIT Durg SEPM Project Report.
Includes:
4.1 Introduction
4.2 Development Methodology
4.3 Overall System Architecture (with embedded diagram)
4.4 Frontend Architecture
4.5 Backend Architecture
4.6 Database Design (with embedded ER diagram & table)
4.7 Module Description
4.8 Data Flow and Process Design (with embedded workflow diagram)
4.9 Authentication and Security Architecture
4.10 Financial Analysis Engine (Decimal Precision)
4.11 AI Integration Architecture and Grounding (with embedded pipeline diagram)
4.12 Portfolio Optimization Methodology (Markowitz MPT)
4.13 Financial News Sentiment Analysis (FinBERT)
4.14 Stress Testing and Simulation Methodology (with Table 4.2)
4.15 Algorithms and Mathematical Models (All mathematical formulations)
4.16 Testing Strategy and Multi-Tenant Isolation
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

def add_formula_p(doc, formula_label, formula_text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(formula_text)
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)
    r.font.bold = True
    r.font.italic = True
    
    p_lbl = doc.add_paragraph()
    p_lbl.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_lbl.paragraph_format.space_after = Pt(6)
    r_lbl = p_lbl.add_run(f"({formula_label})")
    r_lbl.font.name = "Times New Roman"
    r_lbl.font.size = Pt(10)

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

def add_chapter_4(doc):
    p_ch = doc.add_paragraph()
    p_ch.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ch.paragraph_format.space_before = Pt(18)
    p_ch.paragraph_format.space_after = Pt(4)
    r_ch = p_ch.add_run("CHAPTER 4")
    r_ch.font.name = "Times New Roman"
    r_ch.font.size = Pt(16)
    r_ch.font.bold = True
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(18)
    r_t = p_title.add_run("METHODOLOGY AND SYSTEM DESIGN")
    r_t.font.name = "Times New Roman"
    r_t.font.size = Pt(15)
    r_t.font.bold = True
    
    add_heading_1(doc, "4.1 Introduction")
    add_body_p(
        doc,
        "This chapter presents the architectural philosophy, software engineering methodology, structural decomposition, "
        "relational data models, algorithms, and mathematical formulations governing the \"AI-Powered Personal Financial "
        "Portfolio Management and Decision Support System\". Designing a mission-critical financial system requires resolving "
        "a fundamental software engineering tension: financial calculations demand absolute deterministic precision, mathematical "
        "repeatability, and zero rounding drift, whereas conversational AI interfaces are fundamentally probabilistic, dynamic, "
        "and generative. To reconcile these paradigms, we formalize our guiding architectural design: "
        "\"The Deterministic Financial Core with Probabilistic AI Interface\"."
    )
    
    add_heading_1(doc, "4.2 Development Methodology")
    add_body_p(
        doc,
        "The project was executed following an Agile-driven, Phase-Gate Engineering Methodology organized into thirteen "
        "rigorous sequential development phases. Each phase encompassed requirement specification, mathematical formulation, "
        "test-driven development (TDD), security hardening, and end-to-end integration verification:"
    )
    add_bullet_p(doc, "Phase 1 & 2: Transactions & Ledger", "Engineered transaction models, CSV parsers, MD5 duplicate filters, and Decimal balance aggregation.")
    add_bullet_p(doc, "Phase 3 & 4: Cash Flow & PostgreSQL", "Formulated 3-to-6 month emergency fund runway, 30-day cash flow, and persistent PostgreSQL schemas.")
    add_bullet_p(doc, "Phase 5 & 6: Auth & Portfolios", "Implemented JWT security, Argon2 hashing, multi-tenant isolation, and multi-asset portfolio tracking.")
    add_bullet_p(doc, "Phase 7 & 8: Optimization & Goals", "Developed Markowitz mean-variance SLSQP optimizer, reverse SIP solvers, and multi-asset glide paths.")
    add_bullet_p(doc, "Phase 9 & 10: AI & Sentiment", "Built Groq LPU provider abstraction, FinancialContextService grounding, and FinBERT news analysis.")
    add_bullet_p(doc, "Phase 11: Unified Dashboard", "Constructed Next.js 15 single-page application dashboard with Recharts visualizations.")
    add_bullet_p(doc, "Phase 12: Security Hardening", "Executed end-to-end audit, OWASP header injection, and comprehensive multi-tenant isolation verification.")
    add_bullet_p(doc, "Phase 13: Simulations", "Engineered macroeconomic stress testing, historical rebalancing backtesting, and Cholesky Monte Carlo simulation.")

    add_heading_1(doc, "4.3 Overall System Architecture")
    add_body_p(
        doc,
        "Figure 4.1 illustrates the three-tiered system architecture. The system establishes a strict unidirectional boundary: "
        "The Presentation Tier interacts with the Application Tier via authenticated REST APIs over HTTPS. The Application Tier "
        "is split into the Deterministic Financial Core (executing all numerical analysis) and the Probabilistic AI Interface "
        "(responsible for grounded textual synthesis). The LLM is never permitted to perform numerical calculations directly."
    )
    add_diagram_image(doc, "system_architecture.png", "Overall System Architecture: Deterministic Core with Probabilistic AI", "4.1")

    add_heading_1(doc, "4.4 Frontend Architecture")
    add_body_p(
        doc,
        "The frontend is developed using Next.js 15 leveraging the modern React Server Components (RSC) and App Router architecture. "
        "Client components handle interactive charting, stateful form validation, and real-time chat streaming. Styling is managed via "
        "TailwindCSS with strict design tokens, accessible color palettes, and responsive grid layouts. High-performance financial charts "
        "(asset allocation donuts, SIP compounding curves, 30-day cash-flow lines, and Monte Carlo percentile cones) are rendered using "
        "the Recharts SVG charting library."
    )

    add_heading_1(doc, "4.5 Backend Architecture")
    add_body_p(
        doc,
        "The backend is engineered with Python 3.12 and FastAPI. It follows a clean modular service-repository architecture: "
        "Routers handle HTTP request parsing and Pydantic schema validation; Services encapsulate domain logic (MPT optimization, "
        "cash flow forecasting, reverse SIP calculation, and AI prompt building); and Repositories handle database persistence through "
        "SQLAlchemy 2.0. Asynchronous execution (async/await) is utilized across I/O-bound endpoints (Groq API calls, market price fetching), "
        "while heavy mathematical calculations are accelerated using NumPy and SciPy C-extensions."
    )

    add_heading_1(doc, "4.6 Database Design")
    add_body_p(
        doc,
        "The database design implements a normalized relational schema hosted on PostgreSQL 16. Figure 4.2 presents the Entity-Relationship (ER) "
        "model illustrating primary entities, foreign key relationships, and cardinality constraints. Table 4.1 summarizes the entity schemas."
    )
    add_diagram_image(doc, "database_er_diagram.png", "Entity-Relationship (ER) Schema Model and Foreign Key Constraints", "4.2")

    # Table 4.1
    p_tbl = doc.add_paragraph()
    p_tbl.paragraph_format.space_before = Pt(8)
    p_tbl.paragraph_format.space_after = Pt(4)
    r_tcap = p_tbl.add_run("Table 4.1: Database Relational Entities, Primary Keys, and Foreign Key Constraints")
    r_tcap.font.name = "Times New Roman"
    r_tcap.font.size = Pt(10.5)
    r_tcap.font.bold = True
    
    db_entities = [
        ("Entity / Table", "Primary Key", "Foreign Keys", "Key Attributes & Types", "Integrity Constraints"),
        ("users", "id (UUID)", "None", "email (VARCHAR), password_hash (VARCHAR), is_active (BOOL)", "email UNIQUE, NOT NULL"),
        ("portfolios", "id (UUID)", "user_id -> users.id", "name (VARCHAR), description (TEXT), base_currency", "ON DELETE CASCADE, Isolated"),
        ("holdings", "id (UUID)", "portfolio_id, asset_id", "quantity (NUMERIC), avg_buy_price (NUMERIC)", "quantity > 0, Decimal(14,2)"),
        ("assets", "id (UUID)", "None", "symbol (VARCHAR), name (VARCHAR), asset_class (VARCHAR)", "symbol UNIQUE, NOT NULL"),
        ("transactions", "id (UUID)", "user_id -> users.id", "date (DATE), amount (NUMERIC), type, category, hash", "hash UNIQUE per user (Deduplication)"),
        ("investment_goals", "id (UUID)", "user_id, portfolio_id", "target_amount (NUMERIC), target_date, monthly_sip", "target_amount > 0, ON DELETE CASCADE"),
        ("ai_conversations", "id (UUID)", "user_id -> users.id", "title (VARCHAR), created_at (TIMESTAMP)", "ON DELETE CASCADE"),
        ("ai_messages", "id (UUID)", "conversation_id", "role (user/assistant), content (TEXT), cited_domains", "ON DELETE CASCADE"),
        ("financial_news", "id (UUID)", "None", "title (VARCHAR), url (VARCHAR), sentiment_score, label", "url UNIQUE, FinBERT scored")
    ]
    
    tbl = doc.add_table(rows=len(db_entities), cols=5)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    col_w = [Inches(1.2), Inches(0.9), Inches(1.3), Inches(1.8), Inches(1.3)]
    for r_idx, r_items in enumerate(db_entities):
        row = tbl.rows[r_idx]
        for c_idx, val in enumerate(r_items):
            cell = row.cells[c_idx]
            cell.width = col_w[c_idx]
            p = cell.paragraphs[0]
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            if r_idx == 0:
                r.font.bold = True
                r.font.size = Pt(9.5)
            else:
                r.font.size = Pt(8.5)

    add_heading_1(doc, "4.7 Module Description")
    add_body_p(doc, "The system architecture is organized into ten distinct, highly cohesive functional modules:")
    add_bullet_p(doc, "1. Authentication & Tenant Security Module", "Issues signed JWTs, verifies Argon2 password hashes, and scopes all database sessions.")
    add_bullet_p(doc, "2. Transaction Management & Ingestion Module", "Parses bank CSV files, generates MD5 content hashes to eliminate duplicates, and categorizes inflows/outflows.")
    add_bullet_p(doc, "3. Financial Health & Analysis Module", "Calculates monthly essential spending, liquid reserves, emergency runway, and generates 30-day cash-flow forecasts.")
    add_bullet_p(doc, "4. Portfolio Management & Tracking Module", "Maintains multi-asset holdings across equities, debt, mutual funds, gold, and cash, tracking market valuation.")
    add_bullet_p(doc, "5. Modern Portfolio Theory Optimization Module", "Assembles historical price matrices, estimates asset covariance, and runs SLSQP quadratic optimization.")
    add_bullet_p(doc, "6. Portfolio Drift & Rebalancing Module", "Monitors holding weight drift against optimal allocations and synthesizes specific buy/sell trade recommendations.")
    add_bullet_p(doc, "7. Goal-Based Planning & Reverse SIP Module", "Computes forward compound growth, required monthly reverse SIP contributions, and horizon glide paths.")
    add_bullet_p(doc, "8. News Aggregation & FinBERT Sentiment Module", "Fetches RSS financial news, extracts mentioned asset entities, and scores polarity using transformer models.")
    add_bullet_p(doc, "9. Grounded Conversational AI Assistant Module", "Synthesizes natural language inquiries with verified metrics via Groq LPUs with strict guardrail enforcement.")
    add_bullet_p(doc, "10. Stress Testing & Monte Carlo Simulation Module", "Executes macroeconomic shock vectors, historical rebalancing backtests, and Cholesky-correlated wealth simulations.")

    add_heading_1(doc, "4.8 Data Flow and Process Design")
    add_body_p(
        doc,
        "Figure 4.3 illustrates the end-to-end execution workflow. The user imports CSV bank statements, configuring their operational profile. "
        "The system validates transactions, generates cash-flow projections, and assesses emergency reserves. Concurrently, the user manages "
        "portfolio holdings, triggering MPT optimization. When an AI inquiry is submitted, the Financial Context Service injects verified metrics "
        "into the prompt, guaranteeing factual alignment across all touchpoints."
    )
    add_diagram_image(doc, "workflow_diagram.png", "End-to-End User Journey and Execution Workflow Diagram", "4.3")

    add_heading_1(doc, "4.9 Authentication and Security Architecture")
    add_body_p(
        doc,
        "Security is enforced at multiple defense-in-depth boundaries. Passwords are cryptographic hashes produced by Argon2id with random salts. "
        "API calls require an HTTP Authorization header bearing a cryptographically signed JSON Web Token (JWT). In the repository layer, "
        "every query enforces an explicit filter: `filter_by(user_id=current_user.id)`. This guarantees that even in multi-tenant environments, "
        "no user can view, edit, or delete another tenant's financial data."
    )

    add_heading_1(doc, "4.10 Financial Analysis Engine (Decimal Precision)")
    add_body_p(
        doc,
        "To prevent floating-point rounding errors inherent in IEEE 754 representations (such as 0.1 + 0.2 = 0.30000000000000004), "
        "the Financial Analysis Engine strictly employs Python's `decimal.Decimal` module with explicit rounding modes (`ROUND_HALF_UP`). "
        "This ensures exact reconciliation of accounts down to 1 paisa (₹0.01) across millions of simulated compounding cycles."
    )

    add_heading_1(doc, "4.11 AI Integration Architecture and Grounding")
    add_body_p(
        doc,
        "Figure 4.4 illustrates the grounded AI pipeline. When an investor asks a natural language question (e.g., 'How is my 30-day cash flow looking?'), "
        "the query is first sanitized. The `FinancialContextService` queries the authoritative database to assemble verified financial metrics "
        "(current liquidity, 30-day projected closing balance, emergency runway months, asset drift). These metrics are injected into a system prompt "
        "enforcing strict directives: 'You must cite the exact metrics provided in the context; never invent numbers.' The prompt is transmitted "
        "to Groq LPU hardware, generating ultra-fast responses (~0.2s). A post-generation guardrail verifies that cited figures match the context "
        "and appends mandatory educational disclaimers."
    )
    add_diagram_image(doc, "ai_pipeline_diagram.png", "Grounded AI Assistant Pipeline and Safety Guardrail Architecture", "4.4")

    add_heading_1(doc, "4.12 Portfolio Optimization Methodology (Markowitz MPT)")
    add_body_p(
        doc,
        "The portfolio optimization module implements Markowitz Modern Portfolio Theory using the Sequential Least Squares Programming "
        "(SLSQP) algorithm provided by `scipy.optimize`. Given an asset return series, the objective function minimizes portfolio variance "
        "subject to full investment constraints (weights sum to 1.0) and no-short-sales constraints (weights between 0.0 and 1.0), "
        "or maximizes the Sharpe ratio along the efficient frontier."
    )

    add_heading_1(doc, "4.13 Financial News Sentiment Analysis (FinBERT)")
    add_body_p(
        doc,
        "The sentiment analysis module ingests continuous RSS feeds from prominent financial media. Articles are pre-processed, tokenized, "
        "and passed through the `ProsusAI/finbert` transformer pipeline. The model computes softmax probabilities across positive, negative, "
        "and neutral classes. A continuous sentiment score is formulated as: `Score = P(Positive) - P(Negative)`. Entity matching maps "
        "ticker symbols and company names to user holdings, allowing the dashboard to highlight news relevance and potential portfolio impacts."
    )

    add_heading_1(doc, "4.14 Stress Testing and Simulation Methodology")
    add_body_p(
        doc,
        "The stress-testing engine subjects portfolios to deterministic macroeconomic shocks (Table 4.2). The backtesting engine simulates historical "
        "performance with configurable quarterly or annual rebalancing and transaction cost assumptions. The Monte Carlo engine executes "
        "correlated stochastic simulations using Cholesky factorization of the empirical covariance matrix, generating 1,000+ potential terminal wealth "
        "paths and empirical goal success probabilities."
    )
    
    # Table 4.2
    p_t42 = doc.add_paragraph()
    p_t42.paragraph_format.space_before = Pt(8)
    p_t42.paragraph_format.space_after = Pt(4)
    r_t42 = p_t42.add_run("Table 4.2: Macroeconomic Stress-Testing Scenarios and Asset Shock Multipliers")
    r_t42.font.name = "Times New Roman"
    r_t42.font.size = Pt(10.5)
    r_t42.font.bold = True
    
    stress_scenarios = [
        ("Scenario Name", "Equity Impact", "Debt / Bond Impact", "Gold Impact", "Cash Impact", "Macroeconomic Rationale"),
        ("Broad Equity Crash", "-25.0%", "+4.0%", "+8.0%", "0.0%", "Flight to safety during sharp equity market liquidation"),
        ("Interest Rate Shock", "-8.0%", "-12.0%", "-3.0%", "+2.0%", "Aggressive central bank rate hikes discounting bond values"),
        ("Stagflation Crisis", "-18.0%", "-10.0%", "+15.0%", "-5.0%", "High inflation and stagnating growth boosting physical gold"),
        ("Global Tech Correction", "-30.0%", "+2.0%", "+3.0%", "0.0%", "Valuation multiple compression across technology sector"),
        ("Deflationary Contraction", "-20.0%", "+10.0%", "-6.0%", "+4.0%", "Economic slowdown favoring long-duration sovereign bonds")
    ]
    
    tbl_st = doc.add_table(rows=len(stress_scenarios), cols=6)
    tbl_st.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_st.autofit = False
    col_w_st = [Inches(1.5), Inches(0.9), Inches(1.0), Inches(0.8), Inches(0.8), Inches(1.5)]
    for r_idx, r_items in enumerate(stress_scenarios):
        row = tbl_st.rows[r_idx]
        for c_idx, val in enumerate(r_items):
            cell = row.cells[c_idx]
            cell.width = col_w_st[c_idx]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if 0 < c_idx < 5 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            if r_idx == 0:
                r.font.bold = True
                r.font.size = Pt(9.5)
            else:
                r.font.size = Pt(8.5)

    add_heading_1(doc, "4.15 Algorithms and Mathematical Models")
    add_body_p(doc, "The system's calculations are governed by the following authoritative mathematical formulations:")
    
    add_heading_2(doc, "4.15.1 Expected Portfolio Return and Variance")
    add_formula_p(doc, "4.1", "E(Rp) = Σ (wi * E(Ri))")
    add_formula_p(doc, "4.2", "σp² = Σ Σ (wi * wj * σij) = w^T * Σ_cov * w")
    add_body_p(doc, "where wi is the portfolio weight of asset i, E(Ri) is expected return, and σij is the covariance between assets i and j.")
    
    add_heading_2(doc, "4.15.2 Sharpe Ratio Formulation")
    add_formula_p(doc, "4.3", "Sp = [ E(Rp) - Rf ] / σp")
    add_body_p(doc, "where Rf is the annualized risk-free rate (assumed at 6.5% sovereign repo rate).")
    
    add_heading_2(doc, "4.15.3 Emergency Fund Runway")
    add_formula_p(doc, "4.4", "Coverage_Months = Total_Liquid_Savings / Monthly_Essential_Expenses")
    
    add_heading_2(doc, "4.15.4 Reverse SIP Annuity Formulation")
    add_body_p(doc, "To calculate the required monthly investment (PMT) to attain future target wealth (FV):")
    add_formula_p(doc, "4.5", "PMT = FV * r / [ ((1 + r)^n - 1) * (1 + r) ]")
    add_body_p(doc, "where r is the effective monthly interest rate (r = (1 + R_annual)^(1/12) - 1) and n is total months.")

    add_heading_2(doc, "4.15.5 Cholesky Decomposition for Correlated Monte Carlo Returns")
    add_body_p(doc, "Given asset covariance matrix Σ_cov, the lower triangular Cholesky factor L satisfies:")
    add_formula_p(doc, "4.6", "Σ_cov = L * L^T")
    add_formula_p(doc, "4.7", "R_correlated = μ + L * ε,   where ε ~ N(0, I)")

    add_heading_1(doc, "4.16 Testing Strategy and Multi-Tenant Isolation")
    add_body_p(
        doc,
        "Quality assurance is enforced through a comprehensive automated test pyramid. Over 50 unit and integration test modules "
        "verify mathematical edge cases (zero returns, negative weights, singular covariance matrices), API contracts, and cryptographic "
        "tenant isolation. Multi-tenant tests create two simulated users (User A and User B) and programmatically verify that User A cannot "
        "access, view, or alter User B's portfolios, transactions, or AI chat threads, guaranteeing complete data security."
    )
    
    doc.add_page_break()
