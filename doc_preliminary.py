"""
Preliminary pages generator for BIT Durg SEPM Project Report.
Includes:
1. Cover Page (Matching BIT Durg Reference format with Logo)
2. Declaration by Project Members
3. Certificate by Supervisor
4. Certificate by Examiners
5. Acknowledgement
6. Abstract
7. List of Symbols
8. List of Abbreviations
9. List of Tables
10. List of Figures
11. Table of Contents
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

def add_cover_page(doc, logo_path):
    # Cover page should strictly follow Page 1 of reference format
    p_top = doc.add_paragraph()
    p_top.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_top.paragraph_format.space_before = Pt(0)
    p_top.paragraph_format.space_after = Pt(8)
    
    # Project Title
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(12)
    p_title.paragraph_format.space_after = Pt(12)
    r_title = p_title.add_run("AI-POWERED PERSONAL FINANCIAL PORTFOLIO MANAGEMENT AND DECISION SUPPORT SYSTEM")
    r_title.font.name = "Times New Roman"
    r_title.font.size = Pt(16)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(15, 23, 42)
    
    # Submission statement
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(4)
    r_sub = p_sub.add_run("A SEPM Project Submitted\n\nTo\n\nBHILAI INSTITUTE OF TECHNOLOGY, DURG (C.G.)\n(An Autonomous Institute affiliated to CSVTU Bhilai)")
    r_sub.font.name = "Times New Roman"
    r_sub.font.size = Pt(13)
    r_sub.font.bold = True
    
    p_degree = doc.add_paragraph()
    p_degree.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_degree.paragraph_format.space_before = Pt(6)
    p_degree.paragraph_format.space_after = Pt(12)
    r_deg = p_degree.add_run("for the Award of Degree\n\nof\n\nBachelor of Technology\n\nin\n\nInformation Technology")
    r_deg.font.name = "Times New Roman"
    r_deg.font.size = Pt(12)
    r_deg.font.bold = True
    
    # Submitted By & Under Guidance Of in structured format
    p_by = doc.add_paragraph()
    p_by.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_by.paragraph_format.space_before = Pt(4)
    p_by.paragraph_format.space_after = Pt(4)
    r_by = p_by.add_run("Submitted By:")
    r_by.font.name = "Times New Roman"
    r_by.font.size = Pt(12)
    r_by.font.bold = True
    
    # Students List Table
    tbl = doc.add_table(rows=3, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    students = [
        ("1. NIKHIL P", "Roll No: [Insert Roll No]    Enrollment No: [Insert Enrollment No]"),
        ("2. ABHISHEK PATEL", "Roll No: [Insert Roll No]    Enrollment No: [Insert Enrollment No]"),
        ("3. KUNAL PRASAD", "Roll No: [Insert Roll No]    Enrollment No: [Insert Enrollment No]")
    ]
    for idx, (s_name, s_meta) in enumerate(students):
        row = tbl.rows[idx]
        cell_0 = row.cells[0]
        cell_1 = row.cells[1]
        cell_0.width = Inches(2.5)
        cell_1.width = Inches(3.8)
        
        p0 = cell_0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r0 = p0.add_run(s_name)
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(11)
        r0.font.bold = True
        
        p1 = cell_1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r1 = p1.add_run(s_meta)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10.5)
        r1.font.color.rgb = RGBColor(71, 85, 105)
        
    p_guide = doc.add_paragraph()
    p_guide.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_guide.paragraph_format.space_before = Pt(12)
    p_guide.paragraph_format.space_after = Pt(2)
    r_ghead = p_guide.add_run("Under the Guidance of:\n")
    r_ghead.font.name = "Times New Roman"
    r_ghead.font.size = Pt(11)
    r_ghead.font.bold = True
    
    r_gname = p_guide.add_run("[Supervisor Name]\n[Designation]\nDepartment of Information Technology")
    r_gname.font.name = "Times New Roman"
    r_gname.font.size = Pt(11)
    r_gname.font.bold = True
    
    # BIT Durg Logo Banner
    p_logo = doc.add_paragraph()
    p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_logo.paragraph_format.space_before = Pt(12)
    p_logo.paragraph_format.space_after = Pt(6)
    p_logo.add_run().add_picture(logo_path, width=Inches(5.8))
    
    p_sess = doc.add_paragraph()
    p_sess.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sess.paragraph_format.space_before = Pt(6)
    p_sess.paragraph_format.space_after = Pt(0)
    r_sess = p_sess.add_run("Session: [Insert Academic Session]")
    r_sess.font.name = "Times New Roman"
    r_sess.font.size = Pt(12)
    r_sess.font.bold = True
    
    doc.add_page_break()


def add_declaration_page(doc):
    p_head = doc.add_paragraph()
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_head.paragraph_format.space_before = Pt(12)
    p_head.paragraph_format.space_after = Pt(24)
    r_h = p_head.add_run("DECLARATION")
    r_h.font.name = "Times New Roman"
    r_h.font.size = Pt(14)
    r_h.font.bold = True
    
    p1 = doc.add_paragraph()
    p1.paragraph_format.line_spacing = 1.3
    p1.paragraph_format.space_after = Pt(12)
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r1 = p1.add_run(
        "We the undersigned solemnly declare that the report of the SEPM Project work entitled "
        "\"AI-POWERED PERSONAL FINANCIAL PORTFOLIO MANAGEMENT AND DECISION SUPPORT SYSTEM\" "
        "is based on our own work carried out during the course of our study under the supervision of "
        "[Supervisor Name], [Designation], Department of Information Technology, Bhilai Institute of Technology, Durg (C.G.)."
    )
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    
    p2 = doc.add_paragraph()
    p2.paragraph_format.line_spacing = 1.3
    p2.paragraph_format.space_after = Pt(36)
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r2 = p2.add_run(
        "We assert that the statements made and conclusions drawn are an outcome of the project work. "
        "We further declare that to the best of our knowledge and belief the report does not contain any work "
        "which has been submitted for the award of any other degree/diploma/certificate in this university "
        "or any other university/deemed university of India or any other country."
    )
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)
    
    # Candidate Signatures Table
    tbl = doc.add_table(rows=1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    candidates = [
        ("____________________\n(Signature of Candidate)\n\nName: NIKHIL P\nRoll No.: [Insert Roll No]\nEnrollment No.: [Insert Enrollment No]"),
        ("____________________\n(Signature of Candidate)\n\nName: ABHISHEK PATEL\nRoll No.: [Insert Roll No]\nEnrollment No.: [Insert Enrollment No]"),
        ("____________________\n(Signature of Candidate)\n\nName: KUNAL PRASAD\nRoll No.: [Insert Roll No]\nEnrollment No.: [Insert Enrollment No]")
    ]
    for idx, cand_text in enumerate(candidates):
        cell = tbl.rows[0].cells[idx]
        cell.width = Inches(2.1)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(cand_text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(10)
        
    # Supervisor Signature
    p_sup = doc.add_paragraph()
    p_sup.paragraph_format.space_before = Pt(40)
    p_sup.paragraph_format.line_spacing = 1.2
    r_sup = p_sup.add_run(
        "_____________________________\n"
        "Signature of Supervisor\n"
        "[Supervisor Name]\n"
        "[Designation]\n"
        "Department of Information Technology\n"
        "Bhilai Institute of Technology, Durg (C.G.)"
    )
    r_sup.font.name = "Times New Roman"
    r_sup.font.size = Pt(11)
    
    doc.add_page_break()


def add_supervisor_certificate(doc):
    p_head = doc.add_paragraph()
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_head.paragraph_format.space_before = Pt(12)
    p_head.paragraph_format.space_after = Pt(24)
    r_h = p_head.add_run("CERTIFICATE BY THE SUPERVISOR")
    r_h.font.name = "Times New Roman"
    r_h.font.size = Pt(14)
    r_h.font.bold = True
    
    p1 = doc.add_paragraph()
    p1.paragraph_format.line_spacing = 1.3
    p1.paragraph_format.space_after = Pt(14)
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r1 = p1.add_run(
        "This is to certify that the report of the SEPM Project entitled \"AI-POWERED PERSONAL FINANCIAL "
        "PORTFOLIO MANAGEMENT AND DECISION SUPPORT SYSTEM\" is a record of project and research work carried out by "
        "NIKHIL P (Roll No: [Insert Roll No], Enrollment No: [Insert Enrollment No]), "
        "ABHISHEK PATEL (Roll No: [Insert Roll No], Enrollment No: [Insert Enrollment No]), and "
        "KUNAL PRASAD (Roll No: [Insert Roll No], Enrollment No: [Insert Enrollment No]) "
        "under my guidance and supervision for the award of the Degree of Bachelor of Technology in Information Technology "
        "of Bhilai Institute of Technology, Durg (An Autonomous Institute affiliated to Chhattisgarh Swami Vivekanand Technical University, Bhilai (C.G.), India)."
    )
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    
    p2 = doc.add_paragraph()
    p2.paragraph_format.space_after = Pt(6)
    r2 = p2.add_run("To the best of my knowledge and belief, the project work:")
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)
    
    points = [
        "i)    Embodies the work of the candidates themselves,",
        "ii)   Has duly been completed,",
        "iii)  Fulfils the requirement of the Ordinance relating to the B.Tech. degree of the Institute and University, and",
        "iv)   Is up to the desired standard both in respect of contents and language for being referred to the examiners."
    ]
    for pt in points:
        p_pt = doc.add_paragraph()
        p_pt.paragraph_format.left_indent = Inches(0.4)
        p_pt.paragraph_format.space_after = Pt(4)
        r_pt = p_pt.add_run(pt)
        r_pt.font.name = "Times New Roman"
        r_pt.font.size = Pt(11.5)
        
    # Signatures
    p_sig = doc.add_paragraph()
    p_sig.paragraph_format.space_before = Pt(36)
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r_sig = p_sig.add_run(
        "_____________________________________\n"
        "(Signature of the Supervisor)            \n"
        "Name: [Supervisor Name]                     \n"
        "Designation: [Designation]                  \n"
        "Department: Information Technology        \n"
        "Bhilai Institute of Technology, Durg (C.G.) \n"
    )
    r_sig.font.name = "Times New Roman"
    r_sig.font.size = Pt(11)
    
    p_fwd = doc.add_paragraph()
    p_fwd.paragraph_format.space_before = Pt(20)
    p_fwd.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r_fwd = p_fwd.add_run("Forwarded to Chhattisgarh Swami Vivekanand Technical University, Bhilai\n\n\n\n"
                          "_________________________________________\n"
                          "(Signature of Head of Department)\n"
                          "Department of Information Technology\n"
                          "Bhilai Institute of Technology, Durg - 490020, CHHATTISGARH, INDIA")
    r_fwd.font.name = "Times New Roman"
    r_fwd.font.size = Pt(11)
    r_fwd.font.bold = True
    
    doc.add_page_break()


def add_examiners_certificate(doc):
    p_head = doc.add_paragraph()
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_head.paragraph_format.space_before = Pt(12)
    p_head.paragraph_format.space_after = Pt(28)
    r_h = p_head.add_run("CERTIFICATE BY THE EXAMINERS")
    r_h.font.name = "Times New Roman"
    r_h.font.size = Pt(14)
    r_h.font.bold = True
    
    p1 = doc.add_paragraph()
    p1.paragraph_format.line_spacing = 1.3
    p1.paragraph_format.space_after = Pt(20)
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r1 = p1.add_run(
        "The SEPM Project report entitled \"AI-POWERED PERSONAL FINANCIAL PORTFOLIO MANAGEMENT AND DECISION "
        "SUPPORT SYSTEM\" submitted by NIKHIL P (Roll No: [Insert Roll No], Enrollment No: [Insert Enrollment No]), "
        "ABHISHEK PATEL (Roll No: [Insert Roll No], Enrollment No: [Insert Enrollment No]), and "
        "KUNAL PRASAD (Roll No: [Insert Roll No], Enrollment No: [Insert Enrollment No]) has been examined by the "
        "undersigned as a part of the examination and is hereby recommended for the award of the degree of "
        "Bachelor of Technology in Information Technology of Bhilai Institute of Technology, Durg (Autonomous Institute "
        "affiliated to Chhattisgarh Swami Vivekanand Technical University, Bhilai (C.G.))."
    )
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    
    # Table for examiners signatures
    p_space = doc.add_paragraph()
    p_space.paragraph_format.space_before = Pt(60)
    
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    cell_l = tbl.rows[0].cells[0]
    cell_r = tbl.rows[0].cells[1]
    cell_l.width = Inches(3.2)
    cell_r.width = Inches(3.2)
    
    pl = cell_l.paragraphs[0]
    pl.alignment = WD_ALIGN_PARAGRAPH.LEFT
    rl = pl.add_run("_______________________________\nInternal Examiner\nDate:\nName:\nDesignation:")
    rl.font.name = "Times New Roman"
    rl.font.size = Pt(11)
    rl.font.bold = True
    
    pr = cell_r.paragraphs[0]
    pr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    rr = pr.add_run("_______________________________\nExternal Examiner\nDate:\nName:\nDesignation:")
    rr.font.name = "Times New Roman"
    rr.font.size = Pt(11)
    rr.font.bold = True
    
    doc.add_page_break()


def add_acknowledgement(doc):
    p_head = doc.add_paragraph()
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_head.paragraph_format.space_before = Pt(12)
    p_head.paragraph_format.space_after = Pt(20)
    r_h = p_head.add_run("ACKNOWLEDGEMENT")
    r_h.font.name = "Times New Roman"
    r_h.font.size = Pt(14)
    r_h.font.bold = True
    
    p1 = doc.add_paragraph()
    p1.paragraph_format.line_spacing = 1.3
    p1.paragraph_format.space_after = Pt(12)
    p1.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r1 = p1.add_run(
        "We wish to acknowledge with a deep sense of hearty gratitude and indebtedness to the Head of Department, "
        "Information Technology, Bhilai Institute of Technology, Durg, who provided us with this invaluable opportunity "
        "to undertake this Software Engineering and Project Management (SEPM) work and whose constructive guidance and support "
        "have been truly exemplary."
    )
    r1.font.name = "Times New Roman"
    r1.font.size = Pt(12)
    
    p2 = doc.add_paragraph()
    p2.paragraph_format.line_spacing = 1.3
    p2.paragraph_format.space_after = Pt(12)
    p2.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r2 = p2.add_run(
        "We take this opportunity to voice and record our sincerest gratefulness towards our esteemed Supervisor "
        "[Supervisor Name], [Designation], under whose able guidance, constant encouragement, and critical reviews "
        "this project has been brought to fruitful completion. His insightful recommendations on deterministic financial "
        "calculation architectures and modern AI integration paradigms provided essential direction to this work."
    )
    r2.font.name = "Times New Roman"
    r2.font.size = Pt(12)
    
    p3 = doc.add_paragraph()
    p3.paragraph_format.line_spacing = 1.3
    p3.paragraph_format.space_after = Pt(12)
    p3.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r3 = p3.add_run(
        "Our heart leaps up in thankfulness for his benevolence and time-to-time help, constructive criticism, and "
        "active interest in ensuring the theoretical and technical rigor of our software engineering artifacts."
    )
    r3.font.name = "Times New Roman"
    r3.font.size = Pt(12)
    
    p4 = doc.add_paragraph()
    p4.paragraph_format.line_spacing = 1.3
    p4.paragraph_format.space_after = Pt(28)
    p4.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    r4 = p4.add_run(
        "We are also deeply thankful to all our honorable teachers of the Information Technology Department, laboratory "
        "staff, and our parents whose unwavering moral and material support kept us motivated throughout this endeavor."
    )
    r4.font.name = "Times New Roman"
    r4.font.size = Pt(12)
    
    p_sig = doc.add_paragraph()
    p_sig.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p_sig.paragraph_format.line_spacing = 1.2
    r_sig = p_sig.add_run(
        "(Signature of Candidates)\n\n"
        "NIKHIL P\n"
        "ABHISHEK PATEL\n"
        "KUNAL PRASAD\n"
        "B.Tech (Information Technology)\n"
        "Bhilai Institute of Technology, Durg (C.G.)"
    )
    r_sig.font.name = "Times New Roman"
    r_sig.font.size = Pt(11)
    r_sig.font.bold = True
    
    doc.add_page_break()


def add_abstract(doc):
    p_head = doc.add_paragraph()
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_head.paragraph_format.space_before = Pt(12)
    p_head.paragraph_format.space_after = Pt(20)
    r_h = p_head.add_run("ABSTRACT")
    r_h.font.name = "Times New Roman"
    r_h.font.size = Pt(14)
    r_h.font.bold = True
    
    paragraphs = [
        "Modern personal financial management poses significant cognitive and analytical challenges for individual investors. "
        "The contemporary financial landscape is characterized by dispersed banking transactions, complex multi-asset investment "
        "portfolios, volatile market dynamics, and an overwhelming influx of financial news. Traditional personal finance software "
        "relies primarily on static bookkeeping and backward-looking expense charts, lacking proactive mathematical optimization, "
        "risk mitigation, and predictive forecasting. Conversely, general-purpose Large Language Models (LLMs) deployed as financial "
        "advisors suffer from severe mathematical hallucinations, ungrounded probabilistic speculation, and a complete absence "
        "of verifiable fiduciary constraints.",
        
        "To resolve this fundamental dichotomy, this project presents the design, architectural engineering, and full-stack "
        "implementation of the \"AI-Powered Personal Financial Portfolio Management and Decision Support System\". The platform "
        "introduces a novel hybrid paradigm: a Deterministic Financial Core coupled with a Probabilistic Grounded AI Interface. "
        "The deterministic core executes authoritative, mathematically verified financial calculations utilizing arbitrary-precision "
        "Decimal arithmetic (guaranteeing zero floating-point drift). Core financial modules include: automated bank CSV ingestion with "
        "MD5 duplicate detection, rule-based expense categorization, liquid emergency fund runway assessment (3-to-6 month coverage), "
        "and 30-day daily cash-flow forecasting.",
        
        "For long-term capital allocation, the system implements Modern Portfolio Theory (MPT) based on Markowitz mean-variance "
        "optimization, solved via Sequential Least Squares Programming (SLSQP). It synthesizes historical daily closing price series, "
        "constructs empirical covariance matrices, computes Sharpe ratios, traces the efficient frontier, and performs dynamic "
        "rebalancing drift analysis. Furthermore, investment goals are projected through forward and reverse Systematic Investment Plan "
        "(SIP) algorithms, glide-path formulations, stress-testing across macroeconomic shock vectors, and Monte Carlo simulation "
        "powered by Cholesky decomposition of correlated asset returns.",
        
        "The probabilistic decision-support interface is powered by Groq LPU hardware acceleration running high-parameter reasoning "
        "models. Crucially, the LLM is decoupled from mathematical computation: an automated Financial Context Retrieval Service "
        "injects deterministic database metrics into the prompt payload alongside financial news sentiment analyzed via a local "
        "FinBERT transformer pipeline. Rigid safety guardrails validate that generated advice never contradicts verified database facts "
        "or violates regulatory disclaimers. Built upon FastAPI, PostgreSQL, and Next.js 15, the entire system enforces strict multi-tenant "
        "cryptographic data isolation. Rigorous end-to-end unit and integration testing across 13 engineering phases demonstrates "
        "sub-second execution latencies, exact mathematical convergence, and complete mitigation of LLM hallucination in personal "
        "financial decision support."
    ]
    
    for text in paragraphs:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(10)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        r = p.add_run(text)
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
        
    doc.add_page_break()


def add_list_of_symbols(doc):
    p_head = doc.add_paragraph()
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_head.paragraph_format.space_before = Pt(12)
    p_head.paragraph_format.space_after = Pt(20)
    r_h = p_head.add_run("LIST OF SYMBOLS")
    r_h.font.name = "Times New Roman"
    r_h.font.size = Pt(14)
    r_h.font.bold = True
    
    symbols = [
        ("O", "Big-O Asymptotic Upper Bound Complexity Notation"),
        ("θ", "Theta Asymptotic Tight Bound Complexity Notation"),
        ("Ω", "Omega Asymptotic Lower Bound Complexity Notation"),
        ("E(Rp)", "Expected Return of the Portfolio"),
        ("σp", "Annualized Portfolio Volatility (Standard Deviation of Returns)"),
        ("σij", "Covariance between Asset i and Asset j Returns"),
        ("ρij", "Correlation Coefficient between Asset i and Asset j"),
        ("wi", "Portfolio Allocation Weight Assigned to Asset i"),
        ("Sp", "Sharpe Ratio of the Investment Portfolio"),
        ("Rf", "Risk-Free Rate of Return (Benchmark Sovereign Yield)"),
        ("FV", "Future Value of Systematic Investment Cash Flows"),
        ("PV", "Present Value / Initial Lump-Sum Investment"),
        ("PMT", "Periodic Monthly Payment / SIP Contribution Amount"),
        ("r", "Periodic Interest Rate per Compounding Period"),
        ("n", "Total Number of Investment Months / Compounding Periods"),
        ("L", "Lower Triangular Matrix from Cholesky Decomposition of Covariance"),
        ("ε", "Vector of Independent Standard Normal Random Variates N(0, 1)"),
        ("MDD", "Maximum Peak-to-Trough Drawdown of Historical Asset Series")
    ]
    
    tbl = doc.add_table(rows=len(symbols)+1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    # Header
    hdr = tbl.rows[0]
    hdr.cells[0].width = Inches(0.8)
    hdr.cells[1].width = Inches(1.6)
    hdr.cells[2].width = Inches(4.0)
    for idx, name in enumerate(["S.No.", "Symbol", "Description"]):
        p = hdr.cells[idx].paragraphs[0]
        r = p.add_run(name)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        
    for idx, (sym, desc) in enumerate(symbols):
        row = tbl.rows[idx+1]
        row.cells[0].width = Inches(0.8)
        row.cells[1].width = Inches(1.6)
        row.cells[2].width = Inches(4.0)
        
        p0 = row.cells[0].paragraphs[0]
        p0.add_run(f"{idx+1}.").font.name = "Times New Roman"
        
        p1 = row.cells[1].paragraphs[0]
        r1 = p1.add_run(sym)
        r1.font.name = "Times New Roman"
        r1.font.bold = True
        
        p2 = row.cells[2].paragraphs[0]
        p2.add_run(desc).font.name = "Times New Roman"
        
    doc.add_page_break()


def add_list_of_abbreviations(doc):
    p_head = doc.add_paragraph()
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_head.paragraph_format.space_before = Pt(12)
    p_head.paragraph_format.space_after = Pt(20)
    r_h = p_head.add_run("LIST OF ABBREVIATIONS")
    r_h.font.name = "Times New Roman"
    r_h.font.size = Pt(14)
    r_h.font.bold = True
    
    abbrevs = [
        ("SEPM", "Software Engineering and Project Management"),
        ("AI", "Artificial Intelligence"),
        ("LLM", "Large Language Model"),
        ("LPU", "Language Processing Unit (Groq Hardware Architecture)"),
        ("MPT", "Modern Portfolio Theory"),
        ("SLSQP", "Sequential Least Squares Programming"),
        ("SRS", "Software Requirements Specification"),
        ("DFD", "Data Flow Diagram"),
        ("ER", "Entity-Relationship"),
        ("API", "Application Programming Interface"),
        ("REST", "Representational State Transfer"),
        ("JWT", "JSON Web Token"),
        ("CSV", "Comma-Separated Values"),
        ("SIP", "Systematic Investment Plan"),
        ("FinBERT", "Financial Bidirectional Encoder Representations from Transformers"),
        ("NLP", "Natural Language Processing"),
        ("OWASP", "Open Worldwide Application Security Project"),
        ("SSR", "Server-Side Rendering"),
        ("CSR", "Client-Side Rendering"),
        ("ORM", "Object-Relational Mapping"),
        ("ACID", "Atomicity, Consistency, Isolation, Durability"),
        ("CAGR", "Compound Annual Growth Rate")
    ]
    
    tbl = doc.add_table(rows=len(abbrevs)+1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    hdr = tbl.rows[0]
    hdr.cells[0].width = Inches(0.8)
    hdr.cells[1].width = Inches(1.8)
    hdr.cells[2].width = Inches(3.8)
    for idx, name in enumerate(["S.No.", "Abbreviation", "Full Expansion"]):
        p = hdr.cells[idx].paragraphs[0]
        r = p.add_run(name)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        
    for idx, (abb, full) in enumerate(abbrevs):
        row = tbl.rows[idx+1]
        row.cells[0].width = Inches(0.8)
        row.cells[1].width = Inches(1.8)
        row.cells[2].width = Inches(3.8)
        
        p0 = row.cells[0].paragraphs[0]
        p0.add_run(f"{idx+1}.").font.name = "Times New Roman"
        
        p1 = row.cells[1].paragraphs[0]
        r1 = p1.add_run(abb)
        r1.font.name = "Times New Roman"
        r1.font.bold = True
        
        p2 = row.cells[2].paragraphs[0]
        p2.add_run(full).font.name = "Times New Roman"
        
    doc.add_page_break()


def add_list_of_tables(doc):
    p_head = doc.add_paragraph()
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_head.paragraph_format.space_before = Pt(12)
    p_head.paragraph_format.space_after = Pt(20)
    r_h = p_head.add_run("LIST OF TABLES")
    r_h.font.name = "Times New Roman"
    r_h.font.size = Pt(14)
    r_h.font.bold = True
    
    tables = [
        ("Table 2.1", "Comparative Evaluation of Personal Finance Systems vs. Proposed Architecture", "14"),
        ("Table 3.1", "Functional Requirements Specification (FR-01 to FR-18)", "21"),
        ("Table 3.2", "Non-Functional Requirements Specification (NFR-01 to NFR-06)", "25"),
        ("Table 3.3", "Software Environment and Technology Stack Specifications", "27"),
        ("Table 3.4", "Hardware Requirements and Infrastructure Bounds", "28"),
        ("Table 3.5", "Use Case Description: UC-01 User Authentication and Security", "31"),
        ("Table 3.6", "Use Case Description: UC-02 Financial Statement CSV Ingestion", "32"),
        ("Table 3.7", "Use Case Description: UC-03 Cash Flow and Emergency Fund Analysis", "33"),
        ("Table 3.8", "Use Case Description: UC-04 Modern Portfolio Optimization (MPT)", "34"),
        ("Table 3.9", "Use Case Description: UC-05 Goal Planning and Reverse SIP Calculation", "35"),
        ("Table 3.10", "Use Case Description: UC-06 Grounded AI Decision Support Consultation", "36"),
        ("Table 3.11", "Use Case Description: UC-07 Monte Carlo Simulation and Stress Testing", "37"),
        ("Table 4.1", "Database Relational Entities, Primary Keys, and Foreign Key Constraints", "45"),
        ("Table 4.2", "Macroeconomic Stress-Testing Scenarios and Asset Shock Multipliers", "53"),
        ("Table 5.1", "Comprehensive Automated Test Suite Execution Results (Phases 1-13)", "68"),
        ("Table 5.2", "System Latency, Execution Performance, and Precision Benchmark Summary", "70")
    ]
    
    tbl = doc.add_table(rows=len(tables)+1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    hdr = tbl.rows[0]
    hdr.cells[0].width = Inches(1.4)
    hdr.cells[1].width = Inches(4.2)
    hdr.cells[2].width = Inches(0.9)
    for idx, name in enumerate(["Table No.", "Table Title / Caption", "Page No."]):
        p = hdr.cells[idx].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if idx == 2 else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(name)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        
    for idx, (tno, title, pg) in enumerate(tables):
        row = tbl.rows[idx+1]
        row.cells[0].width = Inches(1.4)
        row.cells[1].width = Inches(4.2)
        row.cells[2].width = Inches(0.9)
        
        p0 = row.cells[0].paragraphs[0]
        p0.add_run(tno).font.name = "Times New Roman"
        
        p1 = row.cells[1].paragraphs[0]
        p1.add_run(title).font.name = "Times New Roman"
        
        p2 = row.cells[2].paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p2.add_run(pg).font.name = "Times New Roman"
        
    doc.add_page_break()


def add_list_of_figures(doc):
    p_head = doc.add_paragraph()
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_head.paragraph_format.space_before = Pt(12)
    p_head.paragraph_format.space_after = Pt(20)
    r_h = p_head.add_run("LIST OF FIGURES")
    r_h.font.name = "Times New Roman"
    r_h.font.size = Pt(14)
    r_h.font.bold = True
    
    figures = [
        ("Fig 3.1", "Context-Level Data Flow Diagram (Level 0 DFD)", "38"),
        ("Fig 3.2", "Level 1 Data Flow Diagram (P1 to P8 Functional Decomposition)", "39"),
        ("Fig 3.3", "Level 2 DFD: Transaction Processing and Categorization Sub-system", "40"),
        ("Fig 3.4", "Level 2 DFD: Financial Analysis and Cash-Flow Forecasting Sub-system", "41"),
        ("Fig 3.5", "Level 2 DFD: Portfolio Optimization and Risk Engine Sub-system", "42"),
        ("Fig 3.6", "Level 2 DFD: Grounded AI Decision Support System Sub-system", "43"),
        ("Fig 3.7", "Level 2 DFD: Stress Testing and Monte Carlo Simulation Sub-system", "44"),
        ("Fig 4.1", "Overall System Architecture: Deterministic Core with Probabilistic AI", "47"),
        ("Fig 4.2", "Entity-Relationship (ER) Schema Model and Foreign Key Mappings", "49"),
        ("Fig 4.3", "End-to-End User Journey and Execution Workflow Diagram", "51"),
        ("Fig 4.4", "Grounded AI Assistant Pipeline and Safety Guardrail Architecture", "55"),
        ("Fig 5.1", "Application Landing Page / Home Page Interface", "72"),
        ("Fig 5.2", "User Registration Interface with Validation Rules", "73"),
        ("Fig 5.3", "User Authentication and Login Interface", "73"),
        ("Fig 5.4", "Main Financial Decision Support Dashboard", "74"),
        ("Fig 5.5", "Financial Overview and Net Worth KPI Summary Cards", "74"),
        ("Fig 5.6", "Transaction Ledger and Filtering Interface", "75"),
        ("Fig 5.7", "CSV Statement Upload and Ingestion Module", "75"),
        ("Fig 5.8", "Automated Expense Categorization and Spending Breakdown", "76"),
        ("Fig 5.9", "Emergency Fund Coverage and Liquid Reserves Assessment", "76"),
        ("Fig 5.10", "30-Day Daily Cash-Flow Forecast Chart and Liquidity Warnings", "77"),
        ("Fig 5.11", "Investment Portfolio Management and Holdings Summary", "77"),
        ("Fig 5.12", "Multi-Asset Allocation Donut Chart and Target Distribution", "78"),
        ("Fig 5.13", "Portfolio Risk Analysis and Covariance Metrics", "78"),
        ("Fig 5.14", "Modern Portfolio Theory (MPT) Efficient Frontier Optimization", "79"),
        ("Fig 5.15", "Investment Goals Management and Progress Tracking", "79"),
        ("Fig 5.16", "Systematic Investment Plan (SIP) Compound Growth Projection", "80"),
        ("Fig 5.17", "Portfolio Drift Analysis and Rebalancing Trade Recommendations", "80"),
        ("Fig 5.18", "Conversational AI Financial Assistant Interface with Grounding", "81"),
        ("Fig 5.19", "Financial News Sentiment Analysis and FinBERT Scoring Dashboard", "81"),
        ("Fig 5.20", "Macroeconomic Portfolio Stress Testing Interface and Loss Vectors", "82"),
        ("Fig 5.21", "Historical Portfolio Backtesting Performance vs. Benchmark", "82"),
        ("Fig 5.22", "Monte Carlo Probability Density and Percentile Cone Projections", "83"),
        ("Fig 5.23", "Investment Goal Scenario Comparison and Horizon Simulation", "83"),
        ("Fig 5.24", "Live Market Data Auto-Fetcher and API Settings Interface", "84")
    ]
    
    tbl = doc.add_table(rows=len(figures)+1, cols=3)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    hdr = tbl.rows[0]
    hdr.cells[0].width = Inches(1.2)
    hdr.cells[1].width = Inches(4.4)
    hdr.cells[2].width = Inches(0.9)
    for idx, name in enumerate(["Fig No.", "Figure Caption / Title", "Page No."]):
        p = hdr.cells[idx].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if idx == 2 else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(name)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        
    for idx, (fno, title, pg) in enumerate(figures):
        row = tbl.rows[idx+1]
        row.cells[0].width = Inches(1.2)
        row.cells[1].width = Inches(4.4)
        row.cells[2].width = Inches(0.9)
        
        p0 = row.cells[0].paragraphs[0]
        p0.add_run(fno).font.name = "Times New Roman"
        
        p1 = row.cells[1].paragraphs[0]
        p1.add_run(title).font.name = "Times New Roman"
        
        p2 = row.cells[2].paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p2.add_run(pg).font.name = "Times New Roman"
        
    doc.add_page_break()


def add_table_of_contents(doc):
    p_head = doc.add_paragraph()
    p_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_head.paragraph_format.space_before = Pt(12)
    p_head.paragraph_format.space_after = Pt(20)
    r_h = p_head.add_run("TABLE OF CONTENTS")
    r_h.font.name = "Times New Roman"
    r_h.font.size = Pt(14)
    r_h.font.bold = True
    
    toc_entries = [
        ("Candidate's Declaration", "ii"),
        ("Certificate by the Supervisor", "iii"),
        ("Certificate by the Examiners", "iv"),
        ("Acknowledgement", "v"),
        ("Abstract", "vi"),
        ("List of Symbols", "vii"),
        ("List of Abbreviations", "viii"),
        ("List of Tables", "ix"),
        ("List of Figures", "x"),
        ("CHAPTER 1: INTRODUCTION", "1"),
        ("    1.1 Introduction to the Project", "1"),
        ("    1.2 Background and Motivation", "2"),
        ("    1.3 Problem Statement", "3"),
        ("    1.4 Objectives of the Project", "4"),
        ("    1.5 Scope of the Project", "5"),
        ("    1.6 Existing System", "6"),
        ("    1.7 Limitations of Existing Systems", "7"),
        ("    1.8 Proposed System", "8"),
        ("    1.9 Advantages of Proposed System", "9"),
        ("    1.10 Organization of the Report", "10"),
        ("CHAPTER 2: LITERATURE REVIEW", "11"),
        ("    2.1 Introduction", "11"),
        ("    2.2 Existing Personal Finance Management Systems", "11"),
        ("    2.3 Portfolio Management and Modern Portfolio Theory", "13"),
        ("    2.4 Financial Forecasting and Goal-Based Investment Planning", "14"),
        ("    2.5 AI and LLMs in Financial Decision Support", "15"),
        ("    2.6 Financial News Sentiment Analysis Using FinBERT", "16"),
        ("    2.7 Monte Carlo Simulation and Portfolio Stress Testing", "17"),
        ("    2.8 Comparative Analysis", "18"),
        ("    2.9 Research Gap and Project Motivation", "19"),
        ("CHAPTER 3: PROBLEM IDENTIFICATION & SOFTWARE REQUIREMENTS SPECIFICATION (SRS)", "20"),
        ("    3.1 Problem Identification", "20"),
        ("    3.2 Functional Requirements", "21"),
        ("    3.3 Non-Functional Requirements", "25"),
        ("    3.4 Software Requirements", "27"),
        ("    3.5 Hardware Requirements", "28"),
        ("    3.6 User Classes and Characteristics", "29"),
        ("    3.7 Operating Environment", "29"),
        ("    3.8 System Constraints", "30"),
        ("    3.9 Assumptions and Dependencies", "30"),
        ("    3.10 External Interface Requirements", "30"),
        ("    3.11 Database Requirements", "31"),
        ("    3.12 Security Requirements", "31"),
        ("    3.13 Use Case Descriptions", "31"),
        ("    3.14 Acceptance Criteria", "37"),
        ("    3.15 Context-Level Data Flow Diagram (Level 0 DFD)", "38"),
        ("    3.16 Level 1 Data Flow Diagram", "39"),
        ("    3.17 Level 2 Data Flow Diagrams", "40"),
        ("CHAPTER 4: METHODOLOGY AND SYSTEM DESIGN", "45"),
        ("    4.1 Introduction", "45"),
        ("    4.2 Development Methodology", "45"),
        ("    4.3 Overall System Architecture", "46"),
        ("    4.4 Frontend Architecture", "47"),
        ("    4.5 Backend Architecture", "48"),
        ("    4.6 Database Design and Schema Specification", "49"),
        ("    4.7 Module Description", "50"),
        ("    4.8 Data Flow and Process Design", "51"),
        ("    4.9 Authentication and Security Architecture", "52"),
        ("    4.10 Financial Analysis Engine (Decimal Precision)", "53"),
        ("    4.11 AI Integration Architecture and Grounding", "54"),
        ("    4.12 Portfolio Optimization Methodology (Markowitz MPT)", "56"),
        ("    4.13 Financial News Sentiment Analysis (FinBERT)", "57"),
        ("    4.14 Stress Testing and Simulation Methodology", "58"),
        ("    4.15 Algorithms and Mathematical Models", "60"),
        ("    4.16 Testing Strategy and Multi-Tenant Isolation", "64"),
        ("CHAPTER 5: IMPLEMENTATION, RESULTS AND DISCUSSION", "66"),
        ("    5.1 Introduction", "66"),
        ("    5.2 Technology Stack", "66"),
        ("    5.3 Frontend Implementation", "67"),
        ("    5.4 Backend Implementation", "67"),
        ("    5.5 Database Implementation", "67"),
        ("    5.6 User Authentication Implementation", "68"),
        ("    5.7 Transaction Management Implementation", "68"),
        ("    5.8 Cash-Flow and Emergency Fund Analysis", "68"),
        ("    5.9 Investment Portfolio Management", "69"),
        ("    5.10 Portfolio Optimization and Risk Analysis", "69"),
        ("    5.11 Goal-Based Financial Planning", "69"),
        ("    5.12 AI Assistant Implementation", "70"),
        ("    5.13 Financial News Sentiment Analysis", "70"),
        ("    5.14 Stress Testing and Backtesting", "70"),
        ("    5.15 Monte Carlo Simulation", "71"),
        ("    5.16 Testing and Validation", "71"),
        ("    5.17 Results and Discussion", "71"),
        ("    5.18 Application Screenshots (24 Interfaces)", "72"),
        ("CHAPTER 6: CONCLUSION AND SCOPE OF FURTHER WORK", "85"),
        ("    6.1 Conclusion", "85"),
        ("    6.2 Achievements of the Project", "85"),
        ("    6.3 Advantages of the Proposed System", "86"),
        ("    6.4 Limitations", "86"),
        ("    6.5 Future Scope", "87"),
        ("REFERENCES", "88")
    ]
    
    tbl = doc.add_table(rows=len(toc_entries)+1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    
    hdr = tbl.rows[0]
    hdr.cells[0].width = Inches(5.5)
    hdr.cells[1].width = Inches(1.0)
    for idx, name in enumerate(["Topic / Chapter Title", "Page No."]):
        p = hdr.cells[idx].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if idx == 1 else WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(name)
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        
    for idx, (title, pg) in enumerate(toc_entries):
        row = tbl.rows[idx+1]
        row.cells[0].width = Inches(5.5)
        row.cells[1].width = Inches(1.0)
        
        p0 = row.cells[0].paragraphs[0]
        r0 = p0.add_run(title)
        r0.font.name = "Times New Roman"
        if "CHAPTER" in title:
            r0.font.bold = True
            r0.font.size = Pt(11)
        else:
            r0.font.size = Pt(10.5)
            
        p1 = row.cells[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r1 = p1.add_run(pg)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(10.5)
        if "CHAPTER" in title:
            r1.font.bold = True
            
    doc.add_page_break()
