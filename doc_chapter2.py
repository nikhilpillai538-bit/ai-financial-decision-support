"""
Chapter 2: Literature Review for BIT Durg SEPM Project Report.
Sections:
2.1 Introduction
2.2 Existing Personal Finance Management Systems
2.3 Portfolio Management and Modern Portfolio Theory
2.4 Financial Forecasting and Goal-Based Investment Planning
2.5 AI and LLMs in Financial Decision Support
2.6 Financial News Sentiment Analysis Using FinBERT
2.7 Monte Carlo Simulation and Portfolio Stress Testing
2.8 Comparative Analysis (with Structured Evaluation Table)
2.9 Research Gap and Project Motivation
"""

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

def add_chapter_2(doc):
    p_ch = doc.add_paragraph()
    p_ch.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ch.paragraph_format.space_before = Pt(18)
    p_ch.paragraph_format.space_after = Pt(4)
    r_ch = p_ch.add_run("CHAPTER 2")
    r_ch.font.name = "Times New Roman"
    r_ch.font.size = Pt(16)
    r_ch.font.bold = True
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(18)
    r_t = p_title.add_run("LITERATURE REVIEW")
    r_t.font.name = "Times New Roman"
    r_t.font.size = Pt(16)
    r_t.font.bold = True
    
    add_heading_1(doc, "2.1 Introduction")
    add_body_p(
        doc,
        "A rigorous study of literature in software engineering, computational finance, and applied artificial intelligence "
        "is essential for architecting a reliable personal financial portfolio management and decision-support platform. "
        "Over the past seven decades, financial economics has evolved from rudimentary heuristic budgeting to sophisticated "
        "stochastic optimization models. Concurrently, the domain of artificial intelligence has advanced from deterministic expert systems "
        "to pre-trained transformer language models. This chapter critically reviews key academic literature, algorithms, commercial systems, "
        "and architectural paradigms across portfolio optimization, financial forecasting, Natural Language Processing (NLP) sentiment scoring, "
        "and probabilistic simulation techniques."
    )
    
    add_heading_1(doc, "2.2 Existing Personal Finance Management Systems")
    add_body_p(
        doc,
        "The evolution of Personal Finance Management (PFM) software can be traced through distinct generations. Early software such as "
        "Intuit Quicken in the 1990s introduced local computerized bookkeeping. The emergence of web-native platforms like Mint (2006) and "
        "You Need a Budget (YNAB) popularized automated bank aggregation and zero-based budgeting. Recent empirical software studies "
        "(Kaye et al., 2014) demonstrate that while traditional PFM platforms improve basic retrospective expense tracking, their retention "
        "rates decline rapidly because they demand excessive manual tagging and provide zero forward-looking financial intelligence."
    )
    add_body_p(
        doc,
        "Commercial robo-advisory platforms such as Wealthfront and Betterment (Lam, 2016) addressed part of this limitation by automating "
        "passive ETF investment allocation. However, these systems operate as closed commercial walled gardens: they do not ingest retail bank "
        "transaction statements, lack cash-flow runway forecasting, and fail to provide explainable reasoning behind allocation choices, "
        "leaving retail users without holistic decision support."
    )
    
    add_heading_1(doc, "2.3 Portfolio Management and Modern Portfolio Theory")
    add_body_p(
        doc,
        "The theoretical foundation of quantitative portfolio management was established by Harry Markowitz in his seminal 1952 paper, "
        "\"Portfolio Selection\", published in the Journal of Finance (Markowitz, 1952). Markowitz formalized the mathematical concept that "
        "an asset's risk and return should not be assessed in isolation, but by how it contributes to an overall portfolio's risk-return profile. "
        "By analyzing the covariance and correlation matrix between diverse asset pairs, Markowitz demonstrated that an investor can construct "
        "an \"Efficient Frontier\"—a set of optimal portfolios that offer the maximum possible expected return for a defined level of risk."
    )
    add_body_p(
        doc,
        "William Sharpe (1966, 1994) extended Markowitz's framework by introducing the Sharpe Ratio, measuring the excess return per unit of "
        "total risk relative to a risk-free benchmark asset. While Modern Portfolio Theory is universally recognized in institutional asset management, "
        "its practical application in retail consumer software has been severely constrained by the computational complexity of solving "
        "quadratic programming optimization problems in real-time web browsers. Our project overcomes this barrier by deploying a specialized "
        "Sequential Least Squares Programming (SLSQP) solver within a high-performance Python FastAPI backend."
    )
    
    add_heading_1(doc, "2.4 Financial Forecasting and Goal-Based Investment Planning")
    add_body_p(
        doc,
        "Financial goal planning has shifted from static lump-sum retirement calculators to dynamic goal-based wealth management "
        "(Chhabra, 2005; Das et al., 2018). Goal-based investing organizes capital into distinct mental accounts with individualized time horizons "
        "and risk tolerances. Central to this discipline are Systematic Investment Plans (SIP), governed by forward and reverse annuity formulations."
    )
    add_body_p(
        doc,
        "A critical vulnerability identified in existing literature is floating-point rounding drift. Standard IEEE 754 double-precision floating-point "
        "representation introduces subtle binary approximation errors (e.g., 0.1 + 0.2 != 0.3). In multi-decade compounding projections and reverse "
        "SIP solving, these minute rounding errors accumulate into substantial monetary discrepancies. Academic best practices in financial computing "
        "(Goldberg, 1991) mandate arbitrary-precision Decimal arithmetic, which our system strictly implements across all financial modules."
    )
    
    add_heading_1(doc, "2.5 AI and LLMs in Financial Decision Support")
    add_body_p(
        doc,
        "The deployment of Large Language Models (LLMs) such as GPT-4 and Llama-3 in finance has attracted intense academic interest (Wu et al., "
        "2023; Yang et al., 2023). LLMs excel at synthesizing complex textual reports, answering conceptual inquiries, and extracting semantic "
        "meaning from unstructured text. However, rigorous benchmark evaluations (Ji et al., 2023; Bubeck et al., 2023) highlight three fatal "
        "flaws of vanilla LLMs in finance:"
    )
    add_bullet_p(doc, "Mathematical Hallucination", "LLMs generate plausible-sounding numerical outputs that are mathematically incorrect because autoregressive transformers predict tokens statistically rather than executing arithmetic logic.")
    add_bullet_p(doc, "Knowledge Cutoff & Stale Metrics", "Pre-trained models lack real-time access to current market quotes and the user's private financial records.")
    add_bullet_p(doc, "Fiduciary Compliance Risks", "Unguided models may generate unauthorized, dangerous, or speculative advice without mandatory statutory disclaimers.")
    add_body_p(
        doc,
        "To mitigate these issues, recent research strongly advocates Retrieval-Augmented Generation (RAG) and Guardrail-Constrained Architectures "
        "(Lewis et al., 2020). By programmatically retrieving verified database metrics and injecting them into constrained prompt templates, "
        "the LLM is restricted to qualitative explanation of authoritative deterministic metrics, completely preventing calculation hallucinations."
    )
    
    add_heading_1(doc, "2.6 Financial News Sentiment Analysis Using FinBERT")
    add_body_p(
        doc,
        "Market sentiment plays a profound role in short- and medium-term asset volatility. Traditional sentiment tools (e.g., VADER or dictionary-based "
        "lexicons such as Loughran-McDonald) fail to capture the nuanced domain-specific context of financial discourse, where words like 'liability', "
        "'crude', or 'interest' carry specialized meanings."
    )
    add_body_p(
        doc,
        "Dogu Araci (2019) introduced FinBERT, a domain-adapted Bidirectional Encoder Representations from Transformers (BERT) model pre-trained "
        "on Financial PhraseBank and corporate SEC filings. FinBERT significantly outperforms general NLP models on financial sentiment classification, "
        "achieving accuracy exceeding 86% across positive, negative, and neutral sentiment polarities. In this project, we implement a dedicated "
        "sentiment-attribution pipeline utilizing ProsusAI/finbert to continuously score ingested RSS news articles and map entity sentiments directly "
        "onto the user's specific portfolio holdings."
    )
    
    add_heading_1(doc, "2.7 Monte Carlo Simulation and Portfolio Stress Testing")
    add_body_p(
        doc,
        "Deterministic projections fail to communicate the profound uncertainty inherent in capital markets. Pioneered by Stanislaw Ulam and "
        "John von Neumann (Metropolis & Ulam, 1949), and introduced to computational finance by Phelim Boyle (1977), Monte Carlo simulation "
        "models thousands of possible future economic trajectories through stochastic repeated random sampling."
    )
    add_body_p(
        doc,
        "In multi-asset portfolio simulation, assuming assets fluctuate independently produces deeply flawed risk estimates. Academic standards "
        "(Glasserman, 2004) require correlated stochastic simulation via Cholesky decomposition of the asset covariance matrix. By decomposing the "
        "positive semi-definite covariance matrix into a lower triangular matrix, random standard normal shocks can be transformed into correlated "
        "market return vectors. This allows the system to compute precise percentile confidence cones (e.g., 5th, 25th, 50th, 75th, and 95th percentiles) "
        "and empirical goal attainment probabilities."
    )
    
    add_heading_1(doc, "2.8 Comparative Analysis")
    add_body_p(
        doc,
        "Table 2.1 presents a structured comparative analysis evaluating existing personal finance paradigms against our proposed architecture "
        "across key software engineering and financial modeling criteria."
    )
    
    # Table 2.1
    p_tbl = doc.add_paragraph()
    p_tbl.paragraph_format.space_before = Pt(8)
    p_tbl.paragraph_format.space_after = Pt(4)
    r_tcap = p_tbl.add_run("Table 2.1: Comparative Evaluation of Personal Finance Systems vs. Proposed Architecture")
    r_tcap.font.name = "Times New Roman"
    r_tcap.font.size = Pt(10.5)
    r_tcap.font.bold = True
    
    comp_data = [
        ("Feature / Capability", "Traditional PFM\n(Mint / YNAB)", "Robo-Advisors\n(Groww / Wealthfront)", "Generic LLMs\n(ChatGPT / Claude)", "Proposed System\n(This Project)"),
        ("Bank Statement Ingestion", "Yes (API/Manual)", "No (Brokers only)", "No", "Yes (Automated CSV + MD5)"),
        ("Cash Flow Forecasting", "No (Historical only)", "No", "No", "Yes (30-Day Daily Forecast)"),
        ("Emergency Fund Runway", "Static Target", "No", "Qualitative only", "Yes (Liquid Coverage Runway)"),
        ("MPT Optimization (SLSQP)", "No", "Proprietary / Black-box", "No (Hallucinates Math)", "Yes (Full Markowitz SLSQP)"),
        ("Multi-Asset Drift Analysis", "No", "Basic", "No", "Yes (Threshold-based Rebalancing)"),
        ("Reverse SIP Calculator", "Linear/Naive", "Basic", "Unverified", "Yes (Deterministic Decimal Math)"),
        ("Correlated Monte Carlo", "No", "Coarse Percentiles", "No", "Yes (Cholesky Correlated Sim)"),
        ("FinBERT News Sentiment", "No", "No", "General Sentiment", "Yes (ProsusAI/finbert + Holdings)"),
        ("Sub-second AI Inference", "N/A", "N/A", "Slow (3 - 8s)", "Yes (Groq LPU ~0.2s Latency)"),
        ("Arithmetic Hallucination Guard", "N/A", "N/A", "None (High Error Rate)", "Yes (Decoupled Grounded Core)"),
        ("Multi-Tenant Data Isolation", "Yes (Proprietary)", "Yes (Proprietary)", "Shared Session", "Yes (JWT + Isolated Schema)")
    ]
    
    tbl = doc.add_table(rows=len(comp_data), cols=5)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    col_widths = [Inches(1.8), Inches(1.1), Inches(1.2), Inches(1.1), Inches(1.4)]
    
    for r_idx, row_items in enumerate(comp_data):
        row = tbl.rows[r_idx]
        for c_idx, val in enumerate(row_items):
            cell = row.cells[c_idx]
            cell.width = col_widths[c_idx]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER if c_idx > 0 else WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(val)
            r.font.name = "Times New Roman"
            if r_idx == 0:
                r.font.bold = True
                r.font.size = Pt(9.5)
            else:
                r.font.size = Pt(9)
                if c_idx == 4:
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(16, 120, 60)
                    
    add_heading_1(doc, "2.9 Research Gap and Project Motivation")
    add_body_p(
        doc,
        "The critical research gap uncovered by this literature review is the complete absence of an open, verifiable architectural framework "
        "that connects everyday cash-flow operations directly with quantitative portfolio optimization and hallucination-free generative AI. "
        "Retail users are currently forced to accept either static bookkeeping software that provides no optimization, or black-box LLMs that "
        "hallucinate financial calculations. This project directly addresses this gap by engineering a decoupled, evidence-grounded system "
        "combining deterministic Decimal computing, Markowitz optimization, FinBERT sentiment attribution, and ultra-fast Groq LPU inference."
    )
    
    doc.add_page_break()
