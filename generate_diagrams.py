"""
Generate professional architectural, DFD, ER, and workflow diagrams for
SEPM Project Documentation using matplotlib.
All diagrams are saved as high-resolution 300 DPI PNGs.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, Arrow, FancyArrowPatch
import numpy as np

def setup_ax(w=10, h=6):
    fig, ax = plt.subplots(figsize=(w, h), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    return fig, ax

def draw_box(ax, x, y, w, h, text, bg='#EEF2F6', border='#1E293B', lw=1.5, fs=9, bold=False, boxstyle="round,pad=0.3,rounding_size=2"):
    p = FancyBboxPatch((x, y), w, h, boxstyle=boxstyle, facecolor=bg, edgecolor=border, linewidth=lw)
    ax.add_patch(p)
    weight = 'bold' if bold else 'normal'
    ax.text(x + w/2, y + h/2, text, ha='center', va='center', fontsize=fs, weight=weight, color='#0F172A', wrap=True)

def draw_datastore(ax, x, y, w, h, label, bg='#FEF3C7', border='#D97706', fs=8):
    # DFD Data Store: Top and bottom horizontal lines, open on ends or light box
    rect = Rectangle((x, y), w, h, facecolor=bg, edgecolor='none')
    ax.add_patch(rect)
    ax.plot([x, x + w], [y, y], color=border, lw=1.8)
    ax.plot([x, x + w], [y + h, y + h], color=border, lw=1.8)
    ax.plot([x, x], [y, y + h], color=border, lw=1.8)
    ax.text(x + w/2, y + h/2, label, ha='center', va='center', fontsize=fs, weight='bold', color='#78350F')

def draw_arrow(ax, x1, y1, x2, y2, label='', color='#334155', lw=1.3, rad=0.0, fs=7.5, ha='center', va='bottom'):
    arrow = FancyArrowPatch((x1, y1), (x2, y2),
                             arrowstyle='-|>,head_length=5,head_width=3',
                             connectionstyle=f"arc3,rad={rad}",
                             color=color, linewidth=lw)
    ax.add_patch(arrow)
    if label:
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        ax.text(mx, my + 1.2, label, ha=ha, va=va, fontsize=fs, color='#1E293B', weight='semibold',
                bbox=dict(boxstyle='square,pad=0.15', facecolor='#FFFFFF', edgecolor='none', alpha=0.85))


# ---------------------------------------------------------------------------
# 1. Figure 3.1: Context-Level DFD (Level 0)
# ---------------------------------------------------------------------------
def make_dfd_level_0():
    fig, ax = setup_ax(10, 5.5)
    ax.text(50, 95, "Context-Level Data Flow Diagram (Level 0)", ha='center', fontsize=12, weight='bold', color='#1E3A8A')
    
    # External Entities
    draw_box(ax, 5, 60, 20, 16, "End User /\nInvestor\n[External Entity]", bg='#E0F2FE', border='#0284C7', bold=True)
    draw_box(ax, 5, 20, 20, 16, "Financial Data /\nCSV Statement\n[External Source]", bg='#F1F5F9', border='#64748B', bold=True)
    draw_box(ax, 75, 60, 20, 16, "LLM Service Provider\n(Groq / OpenAI LPU)\n[External System]", bg='#F3E8FF', border='#9333EA', bold=True)
    draw_box(ax, 75, 20, 20, 16, "Financial News\nFeeds / RSS / APIs\n[External Source]", bg='#ECFDF5', border='#059669', bold=True)
    
    # Central Process
    p_circle = Circle((50, 48), 16, facecolor='#DBEAFE', edgecolor='#1D4ED8', linewidth=2.2)
    ax.add_patch(p_circle)
    ax.text(50, 51, "0.0\nAI-Powered Personal\nFinancial Portfolio\nManagement & Decision\nSupport System",
            ha='center', va='center', fontsize=8.5, weight='bold', color='#1E3A8A')
    
    # Arrows
    draw_arrow(ax, 25, 71, 35, 57, "Queries, Portfolios, Goals")
    draw_arrow(ax, 35, 48, 25, 65, "Dashboard, Advice, Drift")
    draw_arrow(ax, 25, 30, 36, 42, "Bank Statements (CSV)")
    draw_arrow(ax, 63, 56, 75, 67, "Grounded Prompt")
    draw_arrow(ax, 75, 62, 65, 50, "Synthesized Insights")
    draw_arrow(ax, 75, 29, 64, 42, "Market News & Tickers")
    
    plt.tight_layout()
    plt.savefig('dfd_level_0.png', dpi=300)
    plt.close()
    print("Saved dfd_level_0.png")


# ---------------------------------------------------------------------------
# 2. Figure 3.2: Level 1 DFD
# ---------------------------------------------------------------------------
def make_dfd_level_1():
    fig, ax = setup_ax(11, 7.5)
    ax.text(50, 96, "Level 1 Data Flow Diagram (P1 to P8 Processes & Data Stores)", ha='center', fontsize=12, weight='bold', color='#1E3A8A')
    
    # External Entities
    draw_box(ax, 2, 75, 14, 12, "User /\nInvestor", bg='#E0F2FE', border='#0284C7', bold=True, fs=8)
    draw_box(ax, 2, 18, 14, 12, "External Data\n(CSV/Yahoo)", bg='#F1F5F9', border='#64748B', bold=True, fs=8)
    draw_box(ax, 84, 75, 14, 12, "Groq / LLM\nProvider", bg='#F3E8FF', border='#9333EA', bold=True, fs=8)
    draw_box(ax, 84, 18, 14, 12, "News Feeds\n& FinBERT", bg='#ECFDF5', border='#059669', bold=True, fs=8)
    
    # Processes P1 to P8
    procs = [
        ("P1: Auth & User\nProfile Isolation", 24, 76, '#EFF6FF', '#2563EB'),
        ("P2: Transaction\nImport & Parsing", 24, 54, '#EFF6FF', '#2563EB'),
        ("P3: Financial Analysis\n& Cash Flow", 24, 32, '#EFF6FF', '#2563EB'),
        ("P4: Portfolio Valuation\n& MPT Optimization", 48, 76, '#EFF6FF', '#2563EB'),
        ("P5: Goal Planning\n& Reverse SIP", 48, 54, '#EFF6FF', '#2563EB'),
        ("P6: News Sentiment\nAttribution", 48, 32, '#EFF6FF', '#2563EB'),
        ("P7: AI Financial\nDecision Assistant", 68, 65, '#EFF6FF', '#2563EB'),
        ("P8: Stress Testing &\nMonte Carlo Sim", 48, 10, '#EFF6FF', '#2563EB'),
    ]
    for text, px, py, bg, bd in procs:
        draw_box(ax, px, py, 17, 11, text, bg=bg, border=bd, bold=True, fs=7.5)
        
    # Data Stores D1 to D6
    draw_datastore(ax, 24, 10, 17, 8, "D1: Users Store", bg='#FEF3C7', border='#D97706', fs=7.5)
    draw_datastore(ax, 2, 45, 14, 8, "D2: Transactions", bg='#FEF3C7', border='#D97706', fs=7.5)
    draw_datastore(ax, 68, 45, 14, 8, "D3: Portfolios", bg='#FEF3C7', border='#D97706', fs=7.5)
    draw_datastore(ax, 68, 25, 14, 8, "D4: Goals Store", bg='#FEF3C7', border='#D97706', fs=7.5)
    draw_datastore(ax, 68, 5, 14, 8, "D5: Market Prices", bg='#FEF3C7', border='#D97706', fs=7.5)
    draw_datastore(ax, 84, 45, 14, 8, "D6: News & Scores", bg='#FEF3C7', border='#D97706', fs=7.5)
    
    # Key Connecting Flows
    draw_arrow(ax, 16, 81, 24, 81, "Credentials")
    draw_arrow(ax, 32, 76, 32, 18, "Store User")
    draw_arrow(ax, 16, 24, 24, 57, "Upload CSV")
    draw_arrow(ax, 24, 59, 16, 49, "D2 Write")
    draw_arrow(ax, 32, 54, 32, 43, "Tx Stream")
    draw_arrow(ax, 41, 81, 48, 81, "Allocations")
    draw_arrow(ax, 56, 76, 68, 49, "Save Portfolio")
    draw_arrow(ax, 56, 54, 68, 29, "Save Goals")
    draw_arrow(ax, 65, 78, 68, 72, "Verified Context")
    draw_arrow(ax, 76, 76, 84, 79, "Grounded Prompt")
    draw_arrow(ax, 84, 76, 81, 71, "Inference")
    draw_arrow(ax, 84, 24, 65, 36, "Raw Articles")
    draw_arrow(ax, 65, 34, 84, 47, "Tagged News")
    draw_arrow(ax, 56, 65, 56, 21, "Simulation Params")
    
    plt.tight_layout()
    plt.savefig('dfd_level_1.png', dpi=300)
    plt.close()
    print("Saved dfd_level_1.png")


# ---------------------------------------------------------------------------
# 3. Figure 3.3: Level 2 DFD - Transaction Processing
# ---------------------------------------------------------------------------
def make_dfd_level_2_tx():
    fig, ax = setup_ax(10, 5)
    ax.text(50, 94, "Level 2 DFD: Transaction Processing & Categorization (Sub-system P2)", ha='center', fontsize=11, weight='bold', color='#1E3A8A')
    
    draw_box(ax, 2, 55, 16, 18, "User /\nStatement File", bg='#E0F2FE', border='#0284C7', bold=True, fs=8)
    draw_box(ax, 24, 55, 18, 18, "2.1 CSV Parser\n& Sanitize", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 48, 55, 18, 18, "2.2 Duplicate\nDetector (MD5)", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 74, 55, 22, 18, "2.3 Categorizer\n(Rules & Regex)", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_datastore(ax, 40, 12, 28, 14, "D2: Stored Transactions\n(user_id isolated)", bg='#FEF3C7', border='#D97706', fs=8)
    
    draw_arrow(ax, 18, 64, 24, 64, "Raw CSV")
    draw_arrow(ax, 42, 64, 48, 64, "Parsed Records")
    draw_arrow(ax, 66, 64, 74, 64, "Unique Rows")
    draw_arrow(ax, 85, 55, 68, 23, "Assigned Category & Amount")
    draw_arrow(ax, 54, 55, 54, 26, "Hash Comparison")
    
    plt.tight_layout()
    plt.savefig('dfd_level_2_tx.png', dpi=300)
    plt.close()
    print("Saved dfd_level_2_tx.png")


# ---------------------------------------------------------------------------
# 4. Figure 3.4: Level 2 DFD - Financial Analysis & Forecasting
# ---------------------------------------------------------------------------
def make_dfd_level_2_analysis():
    fig, ax = setup_ax(10, 5)
    ax.text(50, 94, "Level 2 DFD: Financial Analysis & Cash Flow Forecasting (Sub-system P3)", ha='center', fontsize=11, weight='bold', color='#1E3A8A')
    
    draw_datastore(ax, 2, 45, 18, 18, "D2: Transactions\nStore", bg='#FEF3C7', border='#D97706', fs=8)
    draw_box(ax, 26, 60, 20, 18, "3.1 Spending & Inflow\nAggregator", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 52, 60, 20, 18, "3.2 Emergency Fund\nCoverage Evaluator", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 77, 60, 20, 18, "3.3 30-Day Daily Cash\nFlow Forecaster", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 45, 12, 28, 16, "Dashboard Analytics &\nLiquidity Warnings", bg='#DCFCE7', border='#16A34A', bold=True, fs=8)
    
    draw_arrow(ax, 20, 69, 26, 69, "Monthly Inflows/Outflows")
    draw_arrow(ax, 46, 69, 52, 69, "Essential Expenses")
    draw_arrow(ax, 72, 69, 77, 69, "Baseline Balances")
    draw_arrow(ax, 36, 60, 48, 28, "Savings Rate")
    draw_arrow(ax, 62, 60, 58, 28, "Months Coverage (3-6 mo)")
    draw_arrow(ax, 87, 60, 70, 26, "Lowest Balance Date")
    
    plt.tight_layout()
    plt.savefig('dfd_level_2_analysis.png', dpi=300)
    plt.close()
    print("Saved dfd_level_2_analysis.png")


# ---------------------------------------------------------------------------
# 5. Figure 3.5: Level 2 DFD - Portfolio Optimization & Risk
# ---------------------------------------------------------------------------
def make_dfd_level_2_portfolio():
    fig, ax = setup_ax(10, 5.2)
    ax.text(50, 94, "Level 2 DFD: Portfolio Optimization & Risk Engine (Sub-system P4)", ha='center', fontsize=11, weight='bold', color='#1E3A8A')
    
    draw_datastore(ax, 2, 55, 18, 16, "D3: Portfolios\n& Holdings", bg='#FEF3C7', border='#D97706', fs=8)
    draw_datastore(ax, 2, 15, 18, 16, "D5: Historical Prices\n(Daily Adjusted)", bg='#FEF3C7', border='#D97706', fs=8)
    draw_box(ax, 26, 40, 19, 20, "4.1 Covariance &\nReturn Estimator", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 51, 40, 20, 20, "4.2 Quadratic\nSolver (SLSQP / MPT)", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 76, 40, 21, 20, "4.3 Frontier & Drift\nRebalancing", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    
    draw_arrow(ax, 20, 63, 26, 54, "Holdings & Weights")
    draw_arrow(ax, 20, 23, 26, 44, "Price Series")
    draw_arrow(ax, 45, 50, 51, 50, "Cov Matrix & Exp Returns")
    draw_arrow(ax, 71, 50, 76, 50, "Optimal Weights")
    
    plt.tight_layout()
    plt.savefig('dfd_level_2_portfolio.png', dpi=300)
    plt.close()
    print("Saved dfd_level_2_portfolio.png")


# ---------------------------------------------------------------------------
# 6. Figure 3.6: Level 2 DFD - AI Decision Support & Grounding
# ---------------------------------------------------------------------------
def make_dfd_level_2_ai():
    fig, ax = setup_ax(10, 5.2)
    ax.text(50, 94, "Level 2 DFD: Grounded AI Decision Support System (Sub-system P7)", ha='center', fontsize=11, weight='bold', color='#1E3A8A')
    
    draw_box(ax, 2, 55, 16, 18, "User Financial\nQuery", bg='#E0F2FE', border='#0284C7', bold=True, fs=8)
    draw_box(ax, 23, 55, 19, 18, "7.1 Input Sanitizer\n& Injection Filter", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 47, 55, 23, 18, "7.2 Financial Context\nRetrieval Engine", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 76, 55, 21, 18, "7.3 LLM Prompt\nBuilder & Provider", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 47, 12, 23, 18, "7.4 Guardrail\nValidator & Fallback", bg='#DCFCE7', border='#16A34A', bold=True, fs=8)
    
    draw_arrow(ax, 18, 64, 23, 64, "Prompt")
    draw_arrow(ax, 42, 64, 47, 64, "Sanitized")
    draw_arrow(ax, 70, 64, 76, 64, "Verified Facts")
    draw_arrow(ax, 86, 55, 68, 25, "Inference Stream")
    draw_arrow(ax, 47, 21, 10, 55, "Grounded Insights + Followups")
    
    plt.tight_layout()
    plt.savefig('dfd_level_2_ai.png', dpi=300)
    plt.close()
    print("Saved dfd_level_2_ai.png")


# ---------------------------------------------------------------------------
# 7. Figure 3.7: Level 2 DFD - Stress Testing & Monte Carlo
# ---------------------------------------------------------------------------
def make_dfd_level_2_sim():
    fig, ax = setup_ax(10, 5.2)
    ax.text(50, 94, "Level 2 DFD: Stress Testing & Monte Carlo Simulation (Sub-system P8)", ha='center', fontsize=11, weight='bold', color='#1E3A8A')
    
    draw_box(ax, 2, 55, 18, 18, "Scenario Config\n(Horizon, Shocks)", bg='#E0F2FE', border='#0284C7', bold=True, fs=8)
    draw_box(ax, 26, 55, 20, 18, "8.1 Deterministic\nStress Engine", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 52, 55, 22, 18, "8.2 Historical Backtester\n(Rebalancing/T-Costs)", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 78, 55, 20, 18, "8.3 Monte Carlo\nCorrelated Sim", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 45, 12, 28, 16, "Goal Probability & Percentile\nDistribution (5th, 50th, 95th)", bg='#DCFCE7', border='#16A34A', bold=True, fs=8)
    
    draw_arrow(ax, 20, 64, 26, 64, "Shock Vector")
    draw_arrow(ax, 46, 64, 52, 64, "Allocation Weights")
    draw_arrow(ax, 74, 64, 78, 64, "Cholesky Decomp")
    draw_arrow(ax, 36, 55, 48, 27, "Hypothetical Losses")
    draw_arrow(ax, 63, 55, 59, 28, "Max Drawdown & Sharpe")
    draw_arrow(ax, 88, 55, 71, 26, "Success Probability (%)")
    
    plt.tight_layout()
    plt.savefig('dfd_level_2_sim.png', dpi=300)
    plt.close()
    print("Saved dfd_level_2_sim.png")


# ---------------------------------------------------------------------------
# 8. Figure 4.1: System Architecture Diagram
# ---------------------------------------------------------------------------
def make_system_architecture():
    fig, ax = setup_ax(11, 7.5)
    ax.text(50, 96, "Overall System Architecture: Deterministic Financial Core with Probabilistic AI Interface",
            ha='center', fontsize=11, weight='bold', color='#1E3A8A')
    
    # 3 Primary Tiers
    # Tier 1: Presentation Tier
    draw_box(ax, 4, 68, 92, 23, "", bg='#F8FAFC', border='#0284C7', lw=1.5)
    ax.text(6, 88, "PRESENTATION TIER (Next.js 15 App Router + TailwindCSS + Recharts)", fontsize=8.5, weight='bold', color='#0284C7')
    draw_box(ax, 7, 71, 15, 15, "Auth & Profile\nViews", bg='#E0F2FE', border='#0284C7', fs=7.5)
    draw_box(ax, 25, 71, 15, 15, "Transaction &\nCSV Upload", bg='#E0F2FE', border='#0284C7', fs=7.5)
    draw_box(ax, 43, 71, 16, 15, "Portfolio & MPT\nVisualizer", bg='#E0F2FE', border='#0284C7', fs=7.5)
    draw_box(ax, 62, 71, 16, 15, "Simulation &\nStress Tests", bg='#E0F2FE', border='#0284C7', fs=7.5)
    draw_box(ax, 81, 71, 13, 15, "AI Assistant\nChat UI", bg='#E0F2FE', border='#0284C7', fs=7.5)
    
    # Tier 2: Application Tier (FastAPI)
    draw_box(ax, 4, 30, 92, 34, "", bg='#F8FAFC', border='#2563EB', lw=1.5)
    ax.text(6, 61, "APPLICATION TIER (FastAPI Backend Architecture - Python 3.12)", fontsize=8.5, weight='bold', color='#2563EB')
    
    # Core Deterministic Engines
    draw_box(ax, 7, 34, 26, 24, "DETERMINISTIC FINANCIAL CORE\n• Financial Analysis Engine (Decimal)\n• Markowitz MPT Optimizer (SLSQP)\n• Reverse SIP & Glide Path Engine\n• Stress Testing & Backtest Simulator",
             bg='#DBEAFE', border='#1D4ED8', bold=True, fs=7.5)
    
    # Auth & Security
    draw_box(ax, 36, 34, 26, 24, "SECURITY & REPOSITORIES\n• Multi-Tenant User Isolation\n• JWT Token & Argon2 Hasher\n• Repository Pattern (SQLAlchemy)\n• Deterministic Audit Logs",
             bg='#EDE9FE', border='#6D28D9', bold=True, fs=7.5)
             
    # Intelligence & NLP
    draw_box(ax, 65, 34, 28, 24, "PROBABILISTIC AI INTERFACE\n• Context Grounding Service\n• LLM Provider Layer (Groq LPU)\n• Safety Guardrails & Validation\n• FinBERT Sentiment Pipeline",
             bg='#DCFCE7', border='#15803D', bold=True, fs=7.5)
             
    # Tier 3: Persistence & External Tier
    draw_box(ax, 4, 4, 92, 22, "", bg='#F8FAFC', border='#D97706', lw=1.5)
    ax.text(6, 23, "PERSISTENCE & EXTERNAL INTEGRATION TIER", fontsize=8.5, weight='bold', color='#D97706')
    
    draw_box(ax, 7, 7, 28, 14, "PostgreSQL 16 Database\n(Users, Portfolios, Transactions,\nGoals, Market Price Cache)", bg='#FEF3C7', border='#D97706', bold=True, fs=7.5)
    draw_box(ax, 39, 7, 28, 14, "External Financial Sources\n(Yahoo Finance Market Data,\nFinancial News RSS Feeds)", bg='#FEF3C7', border='#D97706', bold=True, fs=7.5)
    draw_box(ax, 71, 7, 22, 14, "Groq Cloud API\n(Ultra-low latency LLM inference,\nOpenAI / Llama models)", bg='#FEF3C7', border='#D97706', bold=True, fs=7.5)
    
    # Tier Arrows
    draw_arrow(ax, 50, 68, 50, 64, "HTTPS / REST JSON APIs with JWT Authentication", lw=1.5)
    draw_arrow(ax, 50, 30, 50, 26, "SQLAlchemy ORM Queries & External Secure Handshakes", lw=1.5)
    
    plt.tight_layout()
    plt.savefig('system_architecture.png', dpi=300)
    plt.close()
    print("Saved system_architecture.png")


# ---------------------------------------------------------------------------
# 9. Figure 4.2: Database ER Diagram
# ---------------------------------------------------------------------------
def make_database_er_diagram():
    fig, ax = setup_ax(11, 7)
    ax.text(50, 96, "Entity-Relationship (ER) Schema Model & Relational Constraints", ha='center', fontsize=11, weight='bold', color='#1E3A8A')
    
    # Entities
    # Users
    draw_box(ax, 3, 50, 20, 38, "USERS (Table)\n---\nPK: id (UUID)\nemail (VARCHAR, UQ)\npassword_hash (VARCHAR)\nfull_name (VARCHAR)\nis_active (BOOLEAN)\ncreated_at (TIMESTAMP)\nupdated_at (TIMESTAMP)", bg='#EFF6FF', border='#2563EB', fs=7)
    
    # Portfolios
    draw_box(ax, 28, 54, 20, 34, "PORTFOLIOS (Table)\n---\nPK: id (UUID)\nFK: user_id -> Users\nname (VARCHAR)\ndescription (TEXT)\nbase_currency (VARCHAR)\ncreated_at (TIMESTAMP)", bg='#EFF6FF', border='#2563EB', fs=7)
    
    # Holdings
    draw_box(ax, 53, 54, 20, 34, "HOLDINGS (Table)\n---\nPK: id (UUID)\nFK: portfolio_id -> Portfolios\nFK: asset_id -> Assets\nquantity (NUMERIC)\naverage_buy_price (NUMERIC)\ncurrent_price (NUMERIC)", bg='#EFF6FF', border='#2563EB', fs=7)

    # Assets
    draw_box(ax, 78, 54, 19, 34, "ASSETS (Table)\n---\nPK: id (UUID)\nsymbol (VARCHAR, UQ)\nname (VARCHAR)\nasset_class (VARCHAR)\ncurrency (VARCHAR)", bg='#EFF6FF', border='#2563EB', fs=7)

    # Transactions
    draw_box(ax, 3, 5, 22, 38, "TRANSACTIONS (Table)\n---\nPK: id (UUID)\nFK: user_id -> Users\ndate (DATE)\namount (NUMERIC 14,2)\ntype (INCOME/EXPENSE)\ncategory (VARCHAR)\ndescription (TEXT)\nsource (CSV/MANUAL)\ncontent_hash (CHAR 32)", bg='#FEF3C7', border='#D97706', fs=7)

    # Investment Goals
    draw_box(ax, 30, 5, 20, 38, "INVESTMENT_GOALS (Table)\n---\nPK: id (UUID)\nFK: user_id -> Users\nFK: portfolio_id -> Portfolios\nname (VARCHAR)\ntarget_amount (NUMERIC)\ntarget_date (DATE)\ncurrent_amount (NUMERIC)\nmonthly_sip (NUMERIC)", bg='#FEF3C7', border='#D97706', fs=7)

    # AI Conversations & News
    draw_box(ax, 55, 5, 20, 38, "AI_CONVERSATIONS (Table)\n---\nPK: id (UUID)\nFK: user_id -> Users\ntitle (VARCHAR)\ncreated_at (TIMESTAMP)\nupdated_at (TIMESTAMP)\n---\nAI_MESSAGES (Table)\nrole, content, domains", bg='#ECFDF5', border='#059669', fs=7)

    draw_box(ax, 78, 5, 19, 38, "FINANCIAL_NEWS (Table)\n---\nPK: id (UUID)\ntitle (VARCHAR)\nurl (VARCHAR)\npublished_at (TIMESTAMP)\nsentiment_label (VARCHAR)\nsentiment_score (FLOAT)\nmatched_entities (JSON)", bg='#ECFDF5', border='#059669', fs=7)
    
    # Relationships
    draw_arrow(ax, 23, 70, 28, 70, "1 : N")
    draw_arrow(ax, 48, 70, 53, 70, "1 : N")
    draw_arrow(ax, 78, 70, 73, 70, "1 : N")
    draw_arrow(ax, 13, 50, 13, 43, "1 : N")
    draw_arrow(ax, 23, 55, 30, 35, "1 : N")
    draw_arrow(ax, 23, 52, 55, 35, "1 : N")
    
    plt.tight_layout()
    plt.savefig('database_er_diagram.png', dpi=300)
    plt.close()
    print("Saved database_er_diagram.png")


# ---------------------------------------------------------------------------
# 10. Figure 4.3: Application Workflow Diagram
# ---------------------------------------------------------------------------
def make_workflow_diagram():
    fig, ax = setup_ax(10, 5.2)
    ax.text(50, 94, "End-to-End User Journey and Execution Workflow", ha='center', fontsize=11, weight='bold', color='#1E3A8A')
    
    steps = [
        ("1. Registration\n& Auth Token", 3, 50),
        ("2. Import CSV\nTransactions", 19, 50),
        ("3. Cash Flow &\nEmergency Fund", 36, 50),
        ("4. Asset Weights &\nMPT Optimize", 54, 50),
        ("5. Set Goals &\nGlide Path", 71, 50),
        ("6. AI Assist &\nStress Sim", 88, 50)
    ]
    for text, sx, sy in steps:
        draw_box(ax, sx, sy, 10, 26, text, bg='#EFF6FF', border='#2563EB', bold=True, fs=7.5)
        
    for i in range(len(steps)-1):
        x1 = steps[i][1] + 10
        x2 = steps[i+1][1]
        draw_arrow(ax, x1, 63, x2, 63, "")
        
    # Bottom verification loop
    draw_box(ax, 25, 10, 50, 22, "DETERMINISTIC VERIFICATION & AUDIT LOOP\n• Decimal Precision Calculations (Zero IEEE-754 drift)\n• Strict Tenant Isolation at Repository Boundaries\n• Mathematical Bounds Verification (Weights sum to 100%)",
             bg='#FEF3C7', border='#D97706', bold=True, fs=8)
             
    draw_arrow(ax, 50, 50, 50, 32, "Verify Context")
    draw_arrow(ax, 75, 32, 88, 50, "Verified Grounding")
    
    plt.tight_layout()
    plt.savefig('workflow_diagram.png', dpi=300)
    plt.close()
    print("Saved workflow_diagram.png")


# ---------------------------------------------------------------------------
# 11. Figure 4.4: Grounded AI Assistant Pipeline Diagram
# ---------------------------------------------------------------------------
def make_ai_pipeline_diagram():
    fig, ax = setup_ax(10, 5.2)
    ax.text(50, 94, "Grounded AI Assistant Dual-Stage Architecture", ha='center', fontsize=11, weight='bold', color='#1E3A8A')
    
    draw_box(ax, 3, 45, 16, 26, "User Query\n(Natural Language\nPrompt)", bg='#E0F2FE', border='#0284C7', bold=True, fs=8)
    draw_box(ax, 23, 45, 22, 26, "Stage 1: Grounding\n• FinancialContextService\n• Query Deterministic DB\n• Spending, Coverage, Drift", bg='#EFF6FF', border='#2563EB', bold=True, fs=8)
    draw_box(ax, 49, 45, 23, 26, "Stage 2: Prompt Guard\n• System Directives\n• Grounded Fact Injection\n• Disclaimer Enforcement", bg='#EDE9FE', border='#6D28D9', bold=True, fs=8)
    draw_box(ax, 76, 45, 21, 26, "Stage 3: LLM Execution\n• Groq LPU Inference\n• High-Speed 120B Model\n• Auto-Failover to 27B", bg='#DCFCE7', border='#16A34A', bold=True, fs=8)
    
    draw_box(ax, 30, 10, 42, 18, "Stage 4: Post-Validation & Fallback\n• Verify cited metrics match database facts\n• Automatic fallback if provider unreachable\n• Strict Educational Disclaimers Attached",
             bg='#FEF3C7', border='#D97706', bold=True, fs=8)
             
    draw_arrow(ax, 19, 58, 23, 58, "Input")
    draw_arrow(ax, 45, 58, 49, 58, "Context Facts")
    draw_arrow(ax, 72, 58, 76, 58, "Grounded Prompt")
    draw_arrow(ax, 86, 45, 72, 20, "Response Stream")
    draw_arrow(ax, 30, 19, 11, 45, "Verified Response")
    
    plt.tight_layout()
    plt.savefig('ai_pipeline_diagram.png', dpi=300)
    plt.close()
    print("Saved ai_pipeline_diagram.png")


if __name__ == '__main__':
    print("Generating all 11 project diagrams...")
    make_dfd_level_0()
    make_dfd_level_1()
    make_dfd_level_2_tx()
    make_dfd_level_2_analysis()
    make_dfd_level_2_portfolio()
    make_dfd_level_2_ai()
    make_dfd_level_2_sim()
    make_system_architecture()
    make_database_er_diagram()
    make_workflow_diagram()
    make_ai_pipeline_diagram()
    print("All 11 diagrams generated successfully!")
