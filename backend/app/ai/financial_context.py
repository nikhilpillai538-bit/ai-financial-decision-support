"""
Financial Context Service for Phase 9.

Gathers strictly verified, user-scoped financial data from the deterministic
calculation engines across Phases 1–8. Distinguishes verified facts from missing data,
formats structured context for the LLM, and preserves calculation warnings.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.calculations import calculate_financial_summary
from app.db.models import PortfolioModel, UserModel
from app.db.repositories.portfolio_repo import SQLPortfolioRepository
from app.db.repositories.profile_repo import SQLProfileRepository
from app.db.repositories.transaction_repo import SQLTransactionRepository
from app.emergency_fund import (
    DEFAULT_ESSENTIAL_CATEGORIES,
    calculate_emergency_fund_analysis,
)
from app.forecasting import generate_cash_flow_forecast
from app.goal_planning import calculate_goal_projection
from app.goal_schemas import GoalProjectionRequest
from app.portfolio_drift import calculate_portfolio_drift, calculate_rebalancing_analysis
from app.portfolio_valuation import calculate_portfolio_valuation
from app.schemas import StoredTransaction, Transaction, TransactionType


# ---------------------------------------------------------------------------
# Domain Detection
# ---------------------------------------------------------------------------

DOMAIN_KEYWORDS = {
    "spending_and_cash_flow": [
        "spend", "expense", "transaction", "cash", "saving", "income", "budget",
        "grocery", "groceries", "bill", "bills", "rent", "forecast", "burn", "runway",
        "monthly spending", "cash flow", "balance"
    ],
    "emergency_fund": [
        "emergency", "safety net", "cushion", "rainy day", "liquid reserve",
        "months of coverage", "liquidity", "survival fund"
    ],
    "investment_goals": [
        "goal", "target", "milestone", "college", "education", "retire", "retirement",
        "house", "down payment", "sip", "monthly contribution", "corpus", "future value"
    ],
    "portfolio_risk_and_allocation": [
        "portfolio", "stock", "equity", "debt", "bond", "bonds", "holding", "holdings",
        "risk", "volatility", "return", "sharpe", "allocation", "diversif", "valuation",
        "mpt", "asset class", "tangency"
    ],
    "rebalancing_and_drift": [
        "drift", "rebalance", "rebalancing", "overweight", "underweight", "threshold",
        "realign", "deviation", "target allocation", "variance"
    ],
    "glide_path": [
        "glide", "glide path", "de-risk", "derisk", "timeline", "age-based",
        "milestone allocation", "horizon"
    ],
    "financial_news": [
        "news", "headline", "headlines", "sentiment", "finbert", "article",
        "market news", "press", "reuters", "bloomberg", "fed announcement", "market developments"
    ],
    "stress_test_and_simulation": [
        "stress", "stress test", "crash", "backtest", "backtesting", "monte carlo",
        "simulation", "simulated", "scenario", "market shock", "rate hike", "stagflation", "drawdown"
    ],
}


def detect_financial_domains(question: str) -> Set[str]:
    """Inspect natural language query and identify relevant financial domains."""
    q_lower = question.lower()
    matched_domains: Set[str] = set()

    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            matched_domains.add(domain)

    # If general or ambiguous question, return comprehensive core domains
    if not matched_domains:
        return {
            "spending_and_cash_flow",
            "emergency_fund",
            "portfolio_risk_and_allocation",
            "investment_goals",
        }

    return matched_domains


# ---------------------------------------------------------------------------
# Context Data Structures
# ---------------------------------------------------------------------------

@dataclass
class ValidatedFinancialContext:
    user_id: str
    as_of_date: str
    domains_retrieved: List[str]
    verified_data: Dict[str, Any] = field(default_factory=dict)
    missing_data_warnings: List[str] = field(default_factory=list)

    def to_grounded_text(self) -> str:
        """Render a clean, unambiguous factual summary for LLM prompt grounding."""
        lines = [
            f"=== VERIFIED FINANCIAL RECORD FOR USER (As of {self.as_of_date}) ===",
            "NOTE: Only cite metrics listed below. If a value is NOT listed, state that it is unavailable.",
        ]

        # 1. Spending and Cash Flow
        if "spending_and_cash_flow" in self.verified_data:
            s = self.verified_data["spending_and_cash_flow"]
            lines.append("\n[Domain: Spending & Cash Flow]")
            lines.append(f"- Total Recorded Income: {s.get('total_income', '0.00')}")
            lines.append(f"- Total Recorded Expenses: {s.get('total_expenses', '0.00')}")
            lines.append(f"- Net Savings: {s.get('net_savings', '0.00')} (Savings Rate: {s.get('savings_rate_percentage', '0.00')}%)")
            lines.append(f"- Total Recorded Transactions: {s.get('transaction_count', 0)}")
            top_cats = s.get("top_spending_categories", {})
            if top_cats:
                cat_str = ", ".join(f"{k}: {v}" for k, v in list(top_cats.items())[:4])
                lines.append(f"- Top Expense Categories: {cat_str}")
            if "forecast_min_balance" in s:
                lines.append(f"- 30-Day Cash Flow Forecast Min Balance: {s.get('forecast_min_balance')} on {s.get('forecast_lowest_date')}")
                if s.get("forecast_liquidity_warning"):
                    lines.append(f"- Cash Flow Warning: {s.get('forecast_liquidity_warning')}")

        # 2. Emergency Fund
        if "emergency_fund" in self.verified_data:
            ef = self.verified_data["emergency_fund"]
            lines.append("\n[Domain: Emergency Fund]")
            lines.append(f"- Available Liquid Savings: {ef.get('available_savings', '0.00')}")
            lines.append(f"- Average Monthly Essential Expenses: {ef.get('monthly_essential_expenses', '0.00')}")
            lines.append(f"- Current Coverage: {ef.get('months_of_coverage', '0.0')} months")
            lines.append(f"- Recommended 3-Month Target: {ef.get('target_3_months', '0.00')} (Shortfall: {ef.get('shortfall_3_months', '0.00')})")
            lines.append(f"- Recommended 6-Month Target: {ef.get('target_6_months', '0.00')} (Shortfall: {ef.get('shortfall_6_months', '0.00')})")
            lines.append(f"- Target Status: {ef.get('target_status', 'unknown')}")

        # 3. Portfolio & Risk
        if "portfolio_risk_and_allocation" in self.verified_data:
            p = self.verified_data["portfolio_risk_and_allocation"]
            lines.append("\n[Domain: Portfolio Valuation & Modern Portfolio Theory Risk]")
            lines.append(f"- Portfolio Name: {p.get('portfolio_name')} ({p.get('base_currency')})")
            lines.append(f"- Total Priced Value: {p.get('total_priced_value', '0.00')}")
            lines.append(f"- Total Cost Basis: {p.get('total_cost_basis', '0.00')}")
            lines.append(f"- Unrealized Gain/Loss: {p.get('unrealized_gain_loss', '0.00')} ({p.get('unrealized_gain_loss_percentage', '0.00')}%)")
            lines.append(f"- Total Holdings: {p.get('total_holdings_count', 0)} ({p.get('unpriced_holdings_count', 0)} unpriced)")
            alloc_dict = p.get("asset_class_allocation", {})
            if alloc_dict:
                alloc_str = ", ".join(f"{k}: {v}%" for k, v in alloc_dict.items())
                lines.append(f"- Current Asset Class Allocation: {alloc_str}")
            if "latest_optimization" in p and p["latest_optimization"]:
                opt = p["latest_optimization"]
                lines.append(f"- Latest MPT Optimization Strategy: {opt.get('strategy')}")
                lines.append(f"- MPT Annualized Expected Return: {opt.get('expected_return')}")
                lines.append(f"- MPT Annualized Expected Volatility: {opt.get('expected_volatility')}")
                lines.append(f"- MPT Sharpe Ratio: {opt.get('sharpe_ratio')}")

        # 4. Rebalancing and Drift
        if "rebalancing_and_drift" in self.verified_data:
            d = self.verified_data["rebalancing_and_drift"]
            lines.append("\n[Domain: Portfolio Drift & Rebalancing Analysis]")
            lines.append(f"- Drift Threshold: {d.get('drift_threshold_percentage_points', '5.00')}%")
            lines.append(f"- Portfolio Exceeds Drift Threshold: {d.get('portfolio_exceeds_threshold')}")
            lines.append(f"- Max Asset Class Drift: {d.get('max_drift_percentage_points', '0.00')}%")
            if d.get("drifted_classes"):
                lines.append(f"- Asset Classes Exceeding Threshold: {', '.join(d.get('drifted_classes'))}")
            trades = d.get("illustrative_rebalancing_trades", [])
            if trades:
                trade_str = "; ".join(f"{t['action']} {t['trade_amount']} in {t['asset_class']}" for t in trades[:4])
                lines.append(f"- Illustrative Rebalancing Trades: {trade_str}")

        # 5. Investment Goals
        if "investment_goals" in self.verified_data:
            g_list = self.verified_data["investment_goals"]
            lines.append("\n[Domain: Investment Goals]")
            if not g_list:
                lines.append("- No active investment goals currently recorded.")
            else:
                for idx, g in enumerate(g_list, 1):
                    lines.append(
                        f"- Goal {idx} '{g.get('name')}': Target {g.get('target_amount')} by {g.get('target_date')} "
                        f"({g.get('remaining_months', 0)} months left). Progress: {g.get('progress_percentage', '0.00')}% "
                        f"(Invested: {g.get('current_amount', '0.00')}). Planned Monthly SIP: {g.get('planned_monthly_contribution', '0.00')}. "
                        f"Required Monthly SIP: {g.get('required_monthly_contribution', '0.00')}. Status: {g.get('status_assessment', 'unknown')}."
                    )

        # 6. Financial News & Sentiment
        if "financial_news" in self.verified_data:
            n_data = self.verified_data["financial_news"]
            lines.append("\n[Domain: Financial News & Market Sentiment]")
            lines.append(f"- Aggregated Market Sentiment: {n_data.get('overall_sentiment_label', 'neutral').upper()} (Net Score: {n_data.get('average_sentiment_score', '0.00')})")
            lines.append(f"- Analyzed Articles Window: {n_data.get('total_articles', 0)} articles over {n_data.get('time_window', '24h')}")
            lines.append(f"- Positive: {n_data.get('positive_percentage', '0.0')}% | Negative: {n_data.get('negative_percentage', '0.0')}% | Neutral: {n_data.get('neutral_percentage', '0.0')}%")
            relevant_items = n_data.get("portfolio_matched_articles", [])
            if relevant_items:
                lines.append("- Portfolio-Relevant News Headlines (Untrusted Publisher Text):")
                for it in relevant_items[:4]:
                    lines.append(
                        f"  * <news_article title=\"{it.get('title')}\" source=\"{it.get('source_name')}\" sentiment=\"{it.get('sentiment_label')}\" link=\"{it.get('canonical_url')}\" />"
                    )
            else:
                lines.append("- No recent articles directly matched user's specific portfolio holdings.")

        # 7. Missing Data Warnings
        if self.missing_data_warnings:
            lines.append("\n[Data Completeness Limitations]")
            for w in self.missing_data_warnings:
                lines.append(f"- Warning: {w}")

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Context Collector Service
# ---------------------------------------------------------------------------

class FinancialContextService:
    """Service that orchestrates deterministic domain engines to build verified context."""

    def __init__(self, session: Session):
        self.session = session
        self.tx_repo = SQLTransactionRepository(session)
        self.profile_repo = SQLProfileRepository(session)
        self.portfolio_repo = SQLPortfolioRepository(session)

    def build_context(
        self,
        user: UserModel,
        question: str,
        portfolio_id: Optional[str] = None,
    ) -> ValidatedFinancialContext:
        """Gather verified financial context for the requested domains."""
        domains = detect_financial_domains(question)
        today_iso = datetime.now(timezone.utc).date().isoformat()
        verified_data: Dict[str, Any] = {}
        warnings: List[str] = []

        # 1. Spending and Cash Flow
        if "spending_and_cash_flow" in domains:
            try:
                db_txs = self.tx_repo.all(user_id=user.id)
                if not db_txs:
                    warnings.append("No transactions recorded yet; spending metrics and cash-flow forecasts are unavailable.")
                else:
                    phase1_txns = [
                        Transaction(
                            date=tx.date,
                            amount=tx.amount,
                            transaction_type=tx.transaction_type,
                            category=tx.category,
                            description=tx.description,
                        )
                        for tx in db_txs
                    ]
                    summary = calculate_financial_summary(phase1_txns)

                    cat_totals: Dict[str, Decimal] = {}
                    for tx in db_txs:
                        if tx.transaction_type == TransactionType.expense:
                            c_name = tx.category or "other"
                            cat_totals[c_name] = cat_totals.get(c_name, Decimal("0.00")) + tx.amount
                    top_cats = {
                        k: str(v)
                        for k, v in sorted(cat_totals.items(), key=lambda item: item[1], reverse=True)[:5]
                    }

                    tot_inc = Decimal(str(summary.total_income))
                    tot_exp = Decimal(str(summary.total_expenses))
                    net_sav = Decimal(str(summary.net_cash_flow))
                    sav_rate = (
                        ((net_sav / tot_inc) * Decimal("100.00")).quantize(Decimal("0.01"))
                        if tot_inc > Decimal("0.00")
                        else Decimal("0.00")
                    )

                    spend_dict: Dict[str, Any] = {
                        "total_income": str(summary.total_income),
                        "total_expenses": str(summary.total_expenses),
                        "net_savings": str(summary.net_cash_flow),
                        "savings_rate_percentage": str(sav_rate),
                        "transaction_count": summary.transaction_count,
                        "top_spending_categories": top_cats,
                    }

                    # Cash flow forecast
                    prof_cfg = self.profile_repo.get_emergency_fund_config(user_id=user.id)
                    cur_cash = (
                        Decimal(str(prof_cfg["emergency_fund_balance"]))
                        if prof_cfg and prof_cfg.get("emergency_fund_balance") is not None
                        else Decimal("0.00")
                    )
                    forecast_res = generate_cash_flow_forecast(
                        transactions=db_txs,
                        current_balance=cur_cash,
                        forecast_start_date=datetime.now(timezone.utc).date(),
                        min_cash_buffer=Decimal("0.00"),
                    )
                    spend_dict["forecast_min_balance"] = str(forecast_res.get("minimum_projected_balance", "0.00"))
                    spend_dict["forecast_lowest_date"] = str(forecast_res.get("lowest_balance_date", ""))
                    f_warns = forecast_res.get("warnings", [])
                    spend_dict["forecast_liquidity_warning"] = f_warns[0] if f_warns else None

                    verified_data["spending_and_cash_flow"] = spend_dict
            except Exception as e:
                warnings.append(f"Spending analysis encountered partial data issue: {str(e)}")

        # 2. Emergency Fund
        if "emergency_fund" in domains:
            try:
                db_txs = self.tx_repo.all(user_id=user.id)
                prof_cfg = self.profile_repo.get_emergency_fund_config(user_id=user.id)
                if prof_cfg:
                    raw_bal = prof_cfg.get("emergency_fund_balance")
                    cur_cash = Decimal(str(raw_bal)) if raw_bal is not None else None
                    essential_cats = prof_cfg.get("essential_categories", list(DEFAULT_ESSENTIAL_CATEGORIES))
                    window = int(prof_cfg.get("analysis_window_months", 12))
                else:
                    cur_cash = None
                    essential_cats = list(DEFAULT_ESSENTIAL_CATEGORIES)
                    window = 12

                ef_res = calculate_emergency_fund_analysis(
                    transactions=db_txs,
                    emergency_fund_balance=cur_cash,
                    essential_categories=essential_cats,
                    analysis_window_months=window,
                )
                verified_data["emergency_fund"] = {
                    "available_savings": str(ef_res.get("emergency_fund_balance") or "0.00"),
                    "monthly_essential_expenses": str(ef_res.get("average_monthly_essential_expenses", "0.00")),
                    "months_of_coverage": str(ef_res.get("months_of_coverage") or "0.0"),
                    "target_3_months": str(ef_res.get("three_month_target", "0.00")),
                    "shortfall_3_months": str(ef_res.get("shortfall_three_month") or "0.00"),
                    "target_6_months": str(ef_res.get("six_month_target", "0.00")),
                    "shortfall_6_months": str(ef_res.get("shortfall_six_month") or "0.00"),
                    "target_status": ef_res.get("balance_status", "unknown"),
                }
                if ef_res.get("warnings"):
                    warnings.extend(ef_res["warnings"])
            except Exception as e:
                warnings.append(f"Emergency fund analysis unavailable: {str(e)}")

        # 3. Portfolio & Modern Portfolio Theory
        if "portfolio_risk_and_allocation" in domains or "rebalancing_and_drift" in domains:
            try:
                portfolios = self.portfolio_repo.list_portfolios(user_id=user.id)
                target_port = None
                if portfolio_id:
                    target_port = next((p for p in portfolios if p.id == portfolio_id), None)
                elif portfolios:
                    target_port = portfolios[0]

                if not target_port:
                    warnings.append("No investment portfolios found for user; portfolio risk and allocation metrics are unavailable.")
                else:
                    val = calculate_portfolio_valuation(target_port)
                    alloc_breakdown = {
                        item.asset_class: str(item.allocation_percentage)
                        for item in val.asset_class_breakdown
                    }
                    port_dict: Dict[str, Any] = {
                        "portfolio_id": target_port.id,
                        "portfolio_name": target_port.name,
                        "base_currency": val.base_currency,
                        "total_priced_value": str(val.priced_holdings_value),
                        "total_cost_basis": str(val.cost_basis_priced),
                        "unrealized_gain_loss": str(val.unrealized_gain_loss),
                        "unrealized_gain_loss_percentage": str(val.unrealized_gain_loss_percentage),
                        "total_holdings_count": val.total_holdings_count,
                        "unpriced_holdings_count": val.unpriced_holdings_count,
                        "asset_class_allocation": alloc_breakdown,
                    }

                    # Fetch latest MPT optimization run if one exists
                    opt_runs = self.portfolio_repo.list_optimization_runs(target_port.id, user_id=user.id)
                    if opt_runs:
                        latest_opt = opt_runs[-1]
                        port_dict["latest_optimization"] = {
                            "strategy": latest_opt.strategy,
                            "expected_return": f"{float(latest_opt.expected_return)*100:.2f}%",
                            "expected_volatility": f"{float(latest_opt.expected_volatility)*100:.2f}%",
                            "sharpe_ratio": str(latest_opt.sharpe_ratio),
                            "optimal_weights": {k: str(v) for k, v in latest_opt.weights.items()},
                        }

                    verified_data["portfolio_risk_and_allocation"] = port_dict
                    warnings.extend(val.warnings)

                    # 4. Drift and Rebalancing
                    if "rebalancing_and_drift" in domains:
                        target_alloc = self.portfolio_repo.get_target_allocation(target_port.id, user_id=user.id)
                        drift_res = calculate_portfolio_drift(target_port, target_alloc)
                        drift_dict: Dict[str, Any] = {
                            "drift_threshold_percentage_points": str(drift_res.drift_threshold_percentage_points),
                            "portfolio_exceeds_threshold": drift_res.portfolio_exceeds_threshold,
                            "max_drift_percentage_points": str(drift_res.max_drift_percentage_points),
                            "drifted_classes": drift_res.drifted_classes,
                        }
                        if target_alloc:
                            try:
                                rebal_res = calculate_rebalancing_analysis(target_port, target_alloc)
                                drift_dict["illustrative_rebalancing_trades"] = [
                                    {
                                        "asset_class": t.asset_class,
                                        "action": t.action,
                                        "trade_amount": str(t.trade_amount),
                                    }
                                    for t in rebal_res.trades
                                    if t.action in {"BUY", "SELL"}
                                ]
                            except Exception:
                                pass
                        verified_data["rebalancing_and_drift"] = drift_dict
                        warnings.extend(drift_res.warnings)
            except Exception as e:
                warnings.append(f"Portfolio context collection encountered an issue: {str(e)}")

        # 5. Investment Goals
        if "investment_goals" in domains:
            try:
                goals = self.portfolio_repo.list_goals(user_id=user.id)
                goals_list = []
                for g in goals:
                    exp_ret = g.expected_annual_return
                    req_override = GoalProjectionRequest()
                    if exp_ret is not None and exp_ret > Decimal("1.00"):
                        req_override = GoalProjectionRequest(expected_annual_return=exp_ret / Decimal("100.00"))
                    proj = calculate_goal_projection(g, req_override, portfolio=g.portfolio)
                    goals_list.append({
                        "id": g.id,
                        "name": g.name,
                        "target_amount": str(g.target_amount),
                        "target_date": g.target_date.isoformat(),
                        "remaining_months": proj.remaining_months,
                        "current_amount": str(proj.current_amount),
                        "progress_percentage": str(proj.progress_percentage),
                        "planned_monthly_contribution": str(proj.planned_monthly_contribution),
                        "required_monthly_contribution": str(proj.required_monthly_contribution),
                        "status_assessment": proj.status_assessment,
                    })
                verified_data["investment_goals"] = goals_list
                if not goals:
                    warnings.append("No active investment goals configured.")
            except Exception as e:
                warnings.append(f"Goals context retrieval issue: {str(e)}")

        # 6. Financial News & FinBERT Sentiment
        if "financial_news" in domains:
            try:
                from app.news.aggregation import MarketSentimentAggregator
                from app.news.relevance import PortfolioNewsRelevanceMatcher
                from app.db.repositories.news_repo import SQLNewsRepository

                news_repo = SQLNewsRepository(self.session)
                articles = news_repo.list_articles(limit=25)

                if not articles:
                    warnings.append("No financial news articles currently ingested.")
                else:
                    aggregator = MarketSentimentAggregator(self.session)
                    summary = aggregator.aggregate(time_window="24h")

                    matcher = PortfolioNewsRelevanceMatcher(self.session)
                    matches = matcher.match_articles(articles, user=user, portfolio_id=portfolio_id)

                    matched_list = [
                        {
                            "title": m.article_title,
                            "canonical_url": m.canonical_url,
                            "source_name": m.source_name,
                            "sentiment_label": m.sentiment_label,
                            "sentiment_score": m.sentiment_score,
                            "matched_entity": m.matched_entity,
                            "match_confidence": m.match_confidence,
                        }
                        for m in matches[:6]
                    ]

                    verified_data["financial_news"] = {
                        "overall_sentiment_label": summary.overall_sentiment_label,
                        "average_sentiment_score": str(round(summary.average_sentiment_score, 4)),
                        "total_articles": summary.total_articles,
                        "positive_percentage": str(round(summary.positive_percentage, 2)),
                        "negative_percentage": str(round(summary.negative_percentage, 2)),
                        "neutral_percentage": str(round(summary.neutral_percentage, 2)),
                        "time_window": summary.time_window,
                        "portfolio_matched_articles": matched_list,
                    }
                    if summary.warnings:
                        warnings.extend(summary.warnings)
            except Exception as e:
                warnings.append(f"Financial news context retrieval issue: {str(e)}")

        # 7. Stress Testing & Stochastic Simulations (Phase 13)
        if "stress_test_and_simulation" in domains:
            try:
                from app.stress_testing import SCENARIO_PRESETS
                verified_data["stress_testing_capabilities"] = {
                    "available_macro_presets": [
                        {"id": k, "name": v["name"], "description": v["description"]}
                        for k, v in SCENARIO_PRESETS.items()
                    ],
                    "analytical_principles": [
                        "Stress tests are deterministic linear impact models and not market predictions.",
                        "Monte Carlo projections use Geometric Brownian Motion to estimate probability distributions, not guaranteed outcomes.",
                        "Backtests utilize historical price replay with anti-lookahead bias enforcement and transaction costs.",
                    ],
                }
            except Exception as e:
                warnings.append(f"Simulation context retrieval issue: {str(e)}")

        # Filter duplicate warnings
        unique_warnings = list(dict.fromkeys(warnings))

        return ValidatedFinancialContext(
            user_id=user.id,
            as_of_date=today_iso,
            domains_retrieved=sorted(list(domains)),
            verified_data=verified_data,
            missing_data_warnings=unique_warnings,
        )
