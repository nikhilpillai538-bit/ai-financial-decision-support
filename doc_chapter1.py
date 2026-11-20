"""
Chapter 1: Introduction for BIT Durg SEPM Project Report.
Sections:
1.1 Introduction to the Project
1.2 Background and Motivation
1.3 Problem Statement
1.4 Objectives of the Project
1.5 Scope of the Project
1.6 Existing System
1.7 Limitations of Existing Systems
1.8 Proposed System
1.9 Advantages of Proposed System
1.10 Organization of the Report
"""

import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

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

def add_chapter_1(doc):
    # Chapter Title Header Box style matching BIT Durg Reference
    p_ch = doc.add_paragraph()
    p_ch.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ch.paragraph_format.space_before = Pt(18)
    p_ch.paragraph_format.space_after = Pt(4)
    r_ch = p_ch.add_run("CHAPTER 1")
    r_ch.font.name = "Times New Roman"
    r_ch.font.size = Pt(16)
    r_ch.font.bold = True
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(18)
    r_t = p_title.add_run("INTRODUCTION")
    r_t.font.name = "Times New Roman"
    r_t.font.size = Pt(16)
    r_t.font.bold = True
    
    add_heading_1(doc, "1.1 Introduction to the Project")
    add_body_p(
        doc,
        "In the contemporary digital economic ecosystem, personal wealth preservation and capital growth have become "
        "increasingly intricate tasks for retail investors. The proliferation of electronic payment gateways, multi-channel banking, "
        "equities, mutual funds, exchange-traded funds (ETFs), fixed-income instruments, and commodities has resulted in a massive "
        "fragmentation of personal financial data. Individual consumers are required to manually track and reconcile hundreds of monthly "
        "transactions across varied statements, while simultaneously attempting to formulate sound asset-allocation strategies."
    )
    add_body_p(
        doc,
        "The project, titled \"AI-Powered Personal Financial Portfolio Management and Decision Support System\", is a comprehensive, "
        "production-grade software platform engineered to provide end-to-end financial intelligence. It uniquely integrates "
        "authoritative deterministic mathematical modeling with state-of-the-art conversational artificial intelligence. Rather than "
        "relying on black-box probabilistic text generators for sensitive numerical decisions, the application establishes a rigid "
        "architectural separation: an ultra-precise deterministic calculation engine executes all financial analytics (cash-flow forecasting, "
        "Modern Portfolio Theory optimization, reverse SIP computation, and Monte Carlo simulations), while an evidence-grounded "
        "Large Language Model (LLM) synthesized with FinBERT sentiment intelligence explains these quantitative findings in plain language."
    )
    
    add_heading_1(doc, "1.2 Background and Motivation")
    add_body_p(
        doc,
        "Financial literacy and proactive capital management remain disproportionately low across retail demographics despite unprecedented "
        "growth in retail market participation. Modern individuals face two primary roadblocks: cognitive overload caused by fragmented data, "
        "and lack of access to institutional-grade wealth advisory tools. Traditional private wealth management services enforce high minimum "
        "portfolio thresholds, rendering professional financial planning inaccessible to middle-income earners and emerging retail investors."
    )
    add_body_p(
        doc,
        "Furthermore, the recent advent of generic generative artificial intelligence (such as ChatGPT) has prompted retail users to seek financial "
        "counsel from language models. However, standard LLMs inherently lack mathematical grounding: they do not perform arithmetic verification, "
        "frequently hallucinate statistical metrics, and operate without access to the user's verified historical balance ledger. The motivation "
        "of this project is to bridge this critical divide by developing an accessible, open-architecture system that delivers institutional-grade "
        "quantitative portfolio analytics, fortified by deterministic correctness and transparent, grounded AI decision support."
    )
    
    add_heading_1(doc, "1.3 Problem Statement")
    add_body_p(
        doc,
        "Retail investors currently lack an integrated software ecosystem that unifies everyday operational cash-flow management with "
        "mathematically rigorous investment portfolio optimization and verified AI guidance. Specifically, the problem encompasses:"
    )
    add_bullet_p(doc, "Data Fragmentation", "Disparate banking transactions and investment accounts require tedious manual consolidation, leading to untracked expenses and poor savings visibility.")
    add_bullet_p(doc, "Absence of Proactive Planning", "Existing budget applications only display historical charts without forward-looking daily cash-flow forecasting or emergency runway calculations.")
    add_bullet_p(doc, "Sub-optimal Asset Allocation", "Retail investors allocate capital arbitrarily based on emotional sentiment or social media hype, ignoring Markowitz Modern Portfolio Theory, variance-covariance correlation, and rebalancing drift.")
    add_bullet_p(doc, "AI Hallucination in Finance", "Commercial LLMs generate speculative, unverified, and mathematically flawed investment advice because they lack deterministic grounding in verified user ledgers.")
    add_bullet_p(doc, "Lack of Multi-tenant Data Privacy", "Financial applications often compromise user data privacy through centralized un-isolated databases and third-party tracking scripts.")
    
    add_heading_1(doc, "1.4 Objectives of the Project")
    add_body_p(
        doc,
        "The overarching objective of this project is to architect, develop, verify, and document an institutional-grade, multi-tenant "
        "personal financial management system. The specific technical objectives are as follows:"
    )
    add_bullet_p(doc, "Deterministic Financial Ledger", "Implement automated bank CSV statement ingestion with MD5 hash duplicate detection, categorization, and arbitrary-precision Decimal arithmetic (zero IEEE 754 floating-point drift).")
    add_bullet_p(doc, "Liquid Reserves & Cash-Flow Runway", "Engineer automated algorithms to determine 3-to-6 month emergency fund requirements and synthesize a 30-day forward daily cash-flow forecast with liquidity warning alerts.")
    add_bullet_p(doc, "Modern Portfolio Theory (MPT) Solver", "Implement mean-variance portfolio optimization using Sequential Least Squares Programming (SLSQP) to construct the efficient frontier and maximize the Sharpe ratio.")
    add_bullet_p(doc, "Goal Planning & Reverse SIP", "Formulate forward and reverse Systematic Investment Plan (SIP) calculators and multi-asset glide-path milestones tied to concrete financial goals.")
    add_bullet_p(doc, "Macroeconomic Stress Testing & Monte Carlo", "Construct a parametric stress-testing engine and NumPy-accelerated Monte Carlo simulation using Cholesky decomposition of correlated asset returns.")
    add_bullet_p(doc, "FinBERT Sentiment Intelligence", "Integrate automated financial news ingestion with HuggingFace ProsusAI/finbert transformer scoring to map macroeconomic sentiment onto user portfolio holdings.")
    add_bullet_p(doc, "Grounded AI Decision Support", "Integrate Groq LPU hardware acceleration running high-speed LLM models with rigid prompt guardrails, ensuring AI responses cite verified database metrics and include fiduciary disclaimers.")
    add_bullet_p(doc, "Multi-Tenant Security & Isolation", "Enforce strict cryptographic data isolation across all database queries using JWT bearer authentication and Argon2 password hashing.")
    
    add_heading_1(doc, "1.5 Scope of the Project")
    add_body_p(
        doc,
        "The functional scope of the project encompasses: authenticated multi-user management, multi-portfolio tracking across equities, "
        "mutual funds, debt, gold, and cash; automated CSV statement processing; 30-day cash-flow projection; MPT quadratic optimization; "
        "portfolio rebalancing drift detection; goal-based SIP computation; macroeconomic shock testing; Monte Carlo percentile forecasting; "
        "RSS financial news ingestion; FinBERT sentiment classification; and conversational AI assistance. The system is designed as a web "
        "application operating across desktop and modern mobile browsers."
    )
    add_body_p(
        doc,
        "Out of Scope: The current phase intentionally excludes direct automated broker order execution (automated live trading), as retail "
        "SEBI/regulatory frameworks mandate explicit human-in-the-loop trade confirmation. The system functions as an authoritative decision-support "
        "and financial intelligence system, generating actionable trade recommendations without automated execution."
    )
    
    add_heading_1(doc, "1.6 Existing System")
    add_body_p(
        doc,
        "Existing software tools in the personal financial management domain typically fall into three fragmented silos:"
    )
    add_bullet_p(doc, "Traditional Budgeting Tools", "Applications such as Mint, Walnut, or basic expense trackers focus strictly on past expenditure logs, manual pie charts, and monthly category budget limits.")
    add_bullet_p(doc, "Robo-Advisory Portals", "Commercial platforms (e.g., Zerodha Coin, Groww, Betterment) provide mutual fund distribution or fixed risk-profiling questionnaires that funnel investors into proprietary mutual fund schemes.")
    add_bullet_p(doc, "Generic Conversational LLMs", "General chat interfaces (OpenAI ChatGPT, Anthropic Claude) allow users to ask general financial questions in natural language.")
    
    add_heading_1(doc, "1.7 Limitations of Existing Systems")
    add_body_p(
        doc,
        "A rigorous engineering evaluation reveals profound structural deficiencies in the existing landscape:"
    )
    add_bullet_p(doc, "Lack of Unification", "Users must operate separate apps for daily budgeting, stock tracking, mutual fund SIPs, and news consumption. No existing platform links daily operational cash flow directly to portfolio allocation.")
    add_bullet_p(doc, "Floating-Point Calculation Errors", "Most web-based financial calculators use native JavaScript or Python standard floating-point numbers, introducing compounding rounding errors across multi-year projections.")
    add_bullet_p(doc, "Absence of Mathematical Portfolio Theory", "Budgeting tools lack mathematical risk metrics (Sharpe ratio, asset covariance matrices, volatility optimization, and rebalancing drift).")
    add_bullet_p(doc, "Hallucinatory Advice in LLMs", "Generic language models lack direct access to user balance sheets, hallucinating imaginary asset prices, fabricated mathematical formulas, and ungrounded advice.")
    add_bullet_p(doc, "Static and Unreactive Goals", "Existing goal calculators use flat linear formulas that ignore market volatility, macroeconomic shocks, and sequence-of-returns risk.")
    
    add_heading_1(doc, "1.8 Proposed System")
    add_body_p(
        doc,
        "The proposed system presents an innovative, hybrid, full-stack architectural paradigm entitled: "
        "\"Deterministic Financial Core with Probabilistic AI Interface\". The architecture is organized into two cooperating layers:"
    )
    add_bullet_p(doc, "1. The Deterministic Financial Core", "Engineered with FastAPI, SQLAlchemy, and Python's arbitrary-precision Decimal module. It computes transaction analytics, 30-day daily cash-flow simulations, emergency fund runway, Markowitz mean-variance optimization, reverse SIP schedules, portfolio rebalancing drift, macroeconomic stress-testing loss vectors, and Cholesky-correlated Monte Carlo simulations. Every calculation is authoritative, repeatable, and mathematically verified.")
    add_bullet_p(doc, "2. The Probabilistic Grounded AI Interface", "Powered by ultra-low-latency Groq LPU hardware acceleration. An automated Financial Context Retrieval Service extracts verified facts from the deterministic core and injects them into structured system prompts. Before presenting output to the user, an automated Guardrail Validation Engine verifies that the generated explanation adheres strictly to the database metrics and appends mandatory educational disclaimers.")
    
    add_heading_1(doc, "1.9 Advantages of Proposed System")
    add_bullet_p(doc, "Absolute Mathematical Correctness", "Eliminates floating-point rounding errors and LLM calculation hallucinations by enforcing deterministic Decimal execution.")
    add_bullet_p(doc, "Comprehensive Financial Synthesis", "Combines operational cash flow, liquid emergency funds, investment portfolio risk, goal pacing, and news sentiment into a unified dashboard.")
    add_bullet_p(doc, "Sub-second AI Inference", "Leverages Groq LPU acceleration to deliver grounded financial explanations in ~0.2 seconds.")
    add_bullet_p(doc, "Advanced Risk Modeling", "Equips retail investors with institutional-grade Modern Portfolio Theory, quadratic SLSQP solvers, and correlated Monte Carlo simulations.")
    add_bullet_p(doc, "Complete Multi-Tenant Privacy", "Guarantees cryptographic user isolation across all PostgreSQL database queries and API endpoints.")
    
    add_heading_1(doc, "1.10 Organization of the Report")
    add_body_p(
        doc,
        "The remainder of this project report is structured into the following chapters in accordance with academic guidelines:"
    )
    add_bullet_p(doc, "Chapter 2 - Literature Review", "Presents an academic survey of modern portfolio theory, financial forecasting, FinBERT transformer architectures, Monte Carlo methods, and comparative evaluations of existing personal finance tools.")
    add_bullet_p(doc, "Chapter 3 - Problem Identification & SRS", "Provides an exhaustive Software Requirements Specification (SRS), functional and non-functional requirements, use case descriptions, acceptance criteria, and complete Context, Level 1, and Level 2 Data Flow Diagrams (DFDs).")
    add_bullet_p(doc, "Chapter 4 - Methodology and System Design", "Details the architectural design, frontend/backend architecture, database schema, mathematical formulations, algorithms, and multi-tenant security frameworks.")
    add_bullet_p(doc, "Chapter 5 - Implementation, Results and Discussion", "Discusses the modular implementation of all 13 phases, comprehensive test suite verification, performance benchmarks, and includes 24 dedicated interface screenshot placeholders.")
    add_bullet_p(doc, "Chapter 6 - Conclusion and Future Scope", "Concludes the report with a summary of achievements, limitations, and future research vectors.")
    add_bullet_p(doc, "References", "Compiles all genuine academic, algorithmic, and software engineering literature citations.")
    
    doc.add_page_break()
