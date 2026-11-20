"""
Explainable Insights Service for Phase 9.

Generates deterministic, structured financial health insights across spending,
emergency funds, investment goals, portfolio risk, and rebalancing drift.
Every insight is strictly grounded in deterministic calculations from Phases 1–8.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.ai.financial_context import FinancialContextService, ValidatedFinancialContext
from app.db.models import UserModel


@dataclass
class InsightItem:
    """A single domain-level explainable financial insight."""
    domain: str
    title: str
    severity: str  # "positive", "info", "warning", "alert"
    summary: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FinancialHealthReport:
    """Consolidated financial health assessment across all user data."""
    generated_at: str
    user_id: str
    overall_status: str  # "healthy", "attention_needed", "critical", "insufficient_data"
    executive_summary: str
    insights: List[InsightItem] = field(default_factory=list)
    missing_data_warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "user_id": self.user_id,
            "overall_status": self.overall_status,
            "executive_summary": self.executive_summary,
            "insights": [i.to_dict() for i in self.insights],
            "missing_data_warnings": self.missing_data_warnings,
        }


class FinancialInsightsService:
    """Deterministic insight generation engine based on validated financial context."""

    def __init__(self, session: Session):
        self.session = session
        self.context_service = FinancialContextService(session)

    def generate_report(
        self,
        user: UserModel,
        portfolio_id: Optional[str] = None,
    ) -> FinancialHealthReport:
        """Generate a complete financial health report with domain insights."""
        # Query context across all core domains
        all_domains_query = "spending emergency fund goals portfolio rebalance"
        context = self.context_service.build_context(
            user=user,
            question=all_domains_query,
            portfolio_id=portfolio_id,
        )

        insights: List[InsightItem] = []
        data = context.verified_data

        # 1. Spending and Cash Flow Insight
        if "spending_and_cash_flow" in data:
            s_insight = self._evaluate_spending(data["spending_and_cash_flow"])
            if s_insight:
                insights.append(s_insight)

        # 2. Emergency Fund Insight
        if "emergency_fund" in data:
            ef_insight = self._evaluate_emergency_fund(data["emergency_fund"])
            if ef_insight:
                insights.append(ef_insight)

        # 3. Investment Goals Insight
        if "investment_goals" in data:
            goals_insight = self._evaluate_goals(data["investment_goals"])
            if goals_insight:
                insights.append(goals_insight)

        # 4. Portfolio Risk Insight
        if "portfolio_risk_and_allocation" in data:
            port_insight = self._evaluate_portfolio(data["portfolio_risk_and_allocation"])
            if port_insight:
                insights.append(port_insight)

        # 5. Rebalancing & Drift Insight
        if "rebalancing_and_drift" in data:
            drift_insight = self._evaluate_drift(data["rebalancing_and_drift"])
            if drift_insight:
                insights.append(drift_insight)

        # Overall Status Determination
        overall_status, exec_summary = self._synthesize_overall_status(
            insights=insights,
            warnings=context.missing_data_warnings,
        )

        now_iso = datetime.now(timezone.utc).isoformat()
        return FinancialHealthReport(
            generated_at=now_iso,
            user_id=user.id,
            overall_status=overall_status,
            executive_summary=exec_summary,
            insights=insights,
            missing_data_warnings=context.missing_data_warnings,
        )

    # -----------------------------------------------------------------------
    # Domain Evaluators
    # -----------------------------------------------------------------------

    def _evaluate_spending(self, s_data: Dict[str, Any]) -> Optional[InsightItem]:
        net_savings = Decimal(s_data.get("net_savings", "0.00"))
        savings_rate = Decimal(s_data.get("savings_rate_percentage", "0.00"))
        total_income = Decimal(s_data.get("total_income", "0.00"))
        total_expenses = Decimal(s_data.get("total_expenses", "0.00"))
        top_cats = s_data.get("top_spending_categories", {})
        forecast_warning = s_data.get("forecast_liquidity_warning")

        metrics = {
            "total_income": str(total_income),
            "total_expenses": str(total_expenses),
            "net_savings": str(net_savings),
            "savings_rate_percentage": str(savings_rate),
            "top_categories": top_cats,
        }

        recs = []
        if net_savings < Decimal("0.00"):
            severity = "alert"
            title = "Negative Monthly Net Savings Detected"
            summary = (
                f"Expenses ({total_expenses}) currently exceed income ({total_income}), "
                f"resulting in a deficit of {abs(net_savings)}."
            )
            recs.append("Review discretionary spending categories to eliminate monthly cash deficit.")
        elif forecast_warning:
            severity = "warning"
            title = "Cash Flow Liquidity Warning in 30-Day Forecast"
            summary = (
                f"While recorded savings rate is {savings_rate}%, the 30-day cash flow projection "
                f"warns: {forecast_warning}."
            )
            recs.append("Maintain higher liquid checking balances before scheduled bill obligations.")
        elif savings_rate < Decimal("20.00"):
            severity = "warning"
            title = "Savings Rate Below Target Benchmark"
            summary = (
                f"Your current savings rate is {savings_rate}%. A standard financial benchmark "
                f"aims for at least 20% of net income saved or invested."
            )
            recs.append("Explore trimming secondary spending categories to boost savings rate towards 20%.")
        else:
            severity = "positive"
            title = "Healthy Savings Rate and Cash Flow"
            summary = (
                f"Your savings rate is strong at {savings_rate}%, generating {net_savings} in net monthly savings."
            )
            recs.append("Consider funneling surplus monthly cash into emergency reserves or targeted investment SIPs.")

        # Top category concentration check
        if top_cats and total_expenses > Decimal("0.00"):
            top_cat_name, top_cat_amt = next(iter(top_cats.items()))
            top_pct = (Decimal(str(top_cat_amt)) / total_expenses) * Decimal("100.0")
            if top_pct > Decimal("45.00"):
                recs.append(
                    f"Concentration alert: '{top_cat_name}' accounts for {top_pct:.1f}% of total expenses."
                )

        return InsightItem(
            domain="spending_and_cash_flow",
            title=title,
            severity=severity,
            summary=summary,
            metrics=metrics,
            recommendations=recs,
        )

    def _evaluate_emergency_fund(self, ef_data: Dict[str, Any]) -> Optional[InsightItem]:
        available = Decimal(ef_data.get("available_savings", "0.00"))
        months_coverage = Decimal(ef_data.get("months_of_coverage", "0.0"))
        monthly_exp = Decimal(ef_data.get("monthly_essential_expenses", "0.00"))
        target_3 = Decimal(ef_data.get("target_3_months", "0.00"))
        target_6 = Decimal(ef_data.get("target_6_months", "0.00"))
        shortfall_3 = Decimal(ef_data.get("shortfall_3_months", "0.00"))
        shortfall_6 = Decimal(ef_data.get("shortfall_6_months", "0.00"))

        metrics = {
            "available_savings": str(available),
            "monthly_essential_expenses": str(monthly_exp),
            "months_of_coverage": str(months_coverage),
            "target_3_months": str(target_3),
            "shortfall_3_months": str(shortfall_3),
            "target_6_months": str(target_6),
            "shortfall_6_months": str(shortfall_6),
        }

        recs = []
        if months_coverage < Decimal("1.0"):
            severity = "alert"
            title = "Critical Emergency Reserve Deficiency"
            summary = (
                f"You currently have only {months_coverage} months of essential expense coverage "
                f"({available} vs {target_3} for a minimal 3-month buffer). Shortfall is {shortfall_3}."
            )
            recs.append("Prioritize building a 3-month emergency fund in high-yield liquid accounts before aggressive equity investing.")
            recs.append(f"Allocating {round(shortfall_3 / Decimal('6.0'), 2)} monthly would close the 3-month gap in 6 months.")
        elif months_coverage < Decimal("3.0"):
            severity = "warning"
            title = "Emergency Fund Below 3-Month Minimum"
            summary = (
                f"Current coverage is {months_coverage} months ({available}). "
                f"A minimum 3-month reserve requires {target_3} (shortfall of {shortfall_3})."
            )
            recs.append("Increase liquid monthly savings until the 3-month threshold is satisfied.")
        elif months_coverage < Decimal("6.0"):
            severity = "info"
            title = "Adequate 3-Month Reserve, Below 6-Month Target"
            summary = (
                f"Current coverage is {months_coverage} months, satisfying the 3-month minimum "
                f"but trailing the 6-month resilience target by {shortfall_6}."
            )
            recs.append("Gradually scale reserves toward the 6-month target of " + str(target_6) + ".")
        else:
            severity = "positive"
            title = "Robust Emergency Fund Coverage"
            summary = (
                f"Your emergency cushion covers {months_coverage} months of essential expenses, "
                f"fully meeting the 6-month resilience standard."
            )
            recs.append("Maintain this liquid balance; surplus savings can now be directed toward wealth generation goals.")

        return InsightItem(
            domain="emergency_fund",
            title=title,
            severity=severity,
            summary=summary,
            metrics=metrics,
            recommendations=recs,
        )

    def _evaluate_goals(self, goals_data: List[Dict[str, Any]]) -> Optional[InsightItem]:
        if not goals_data:
            return InsightItem(
                domain="investment_goals",
                title="No Active Financial Goals Defined",
                severity="info",
                summary="You have not created any structured investment goals yet.",
                metrics={"active_goals_count": 0},
                recommendations=["Create specific goals (e.g., retirement, down payment) to enable progress tracking and SIP calculations."],
            )

        total_goals = len(goals_data)
        behind_count = 0
        ahead_count = 0
        total_shortfall_monthly = Decimal("0.00")

        for g in goals_data:
            status = g.get("status_assessment", "")
            if status == "behind":
                behind_count += 1
            elif status == "ahead":
                ahead_count += 1

            planned_sip = Decimal(str(g.get("planned_monthly_contribution", "0.00")))
            req_sip = Decimal(str(g.get("required_monthly_contribution", "0.00")))
            if req_sip > planned_sip:
                total_shortfall_monthly += (req_sip - planned_sip)

        metrics = {
            "total_goals_count": total_goals,
            "goals_behind": behind_count,
            "goals_ahead": ahead_count,
            "total_monthly_sip_shortfall": str(total_shortfall_monthly),
        }

        recs = []
        if behind_count > 0:
            severity = "warning"
            title = f"{behind_count} of {total_goals} Investment Goals Trailing Target Pace"
            summary = (
                f"{behind_count} goals are currently behind schedule. An aggregate additional "
                f"SIP of {total_shortfall_monthly}/mo is required to reach targets on schedule."
            )
            recs.append("Increase monthly SIP contributions for trailing goals or extend their target horizon dates.")
        else:
            severity = "positive"
            title = "All Active Investment Goals on Schedule"
            summary = f"All {total_goals} tracked goals are currently pacing at or ahead of required milestones."
            recs.append("Continue current monthly SIP schedule and perform quarterly glide-path checkups.")

        return InsightItem(
            domain="investment_goals",
            title=title,
            severity=severity,
            summary=summary,
            metrics=metrics,
            recommendations=recs,
        )

    def _evaluate_portfolio(self, port_data: Dict[str, Any]) -> Optional[InsightItem]:
        total_val = Decimal(port_data.get("total_priced_value", "0.00"))
        gain_loss = Decimal(port_data.get("unrealized_gain_loss", "0.00"))
        gain_loss_pct = Decimal(port_data.get("unrealized_gain_loss_percentage", "0.00"))
        unpriced = port_data.get("unpriced_holdings_count", 0)
        alloc = port_data.get("asset_class_allocation", {})
        latest_opt = port_data.get("latest_optimization")

        metrics = {
            "portfolio_name": port_data.get("portfolio_name"),
            "total_priced_value": str(total_val),
            "unrealized_gain_loss": str(gain_loss),
            "unrealized_gain_loss_percentage": str(gain_loss_pct),
            "unpriced_holdings_count": unpriced,
            "asset_allocation": alloc,
        }

        recs = []
        if total_val == Decimal("0.00"):
            return InsightItem(
                domain="portfolio_risk_and_allocation",
                title="Portfolio Empty or Unpriced",
                severity="info",
                summary="Portfolio has no priced holdings recorded.",
                metrics=metrics,
                recommendations=["Record holdings and ensure market price history is populated."],
            )

        if unpriced > 0:
            recs.append(f"Ensure recent market quotes are uploaded for {unpriced} unpriced assets.")

        if latest_opt:
            sharpe = latest_opt.get("sharpe_ratio")
            vol = latest_opt.get("expected_volatility")
            exp_ret = latest_opt.get("expected_return")
            metrics["latest_mpt_sharpe"] = sharpe
            metrics["latest_mpt_volatility"] = vol
            metrics["latest_mpt_expected_return"] = exp_ret

        if gain_loss >= Decimal("0.00"):
            severity = "positive"
            title = f"Portfolio in Positive Territory (+{gain_loss_pct}%)"
            summary = (
                f"Current portfolio value is {total_val} with unrealized gain of {gain_loss} (+{gain_loss_pct}%)."
            )
        else:
            severity = "warning"
            title = f"Portfolio Showing Unrealized Loss ({gain_loss_pct}%)"
            summary = (
                f"Current portfolio value is {total_val} with unrealized loss of {gain_loss} ({gain_loss_pct}%)."
            )
            recs.append("Review long-term asset allocation targets before making emotional liquidation decisions.")

        if alloc:
            # Check for extreme concentration in a single asset class (> 80%)
            for ac, pct in alloc.items():
                if Decimal(str(pct)) > Decimal("80.00"):
                    recs.append(f"High concentration risk: '{ac}' comprises {pct}% of your portfolio.")

        return InsightItem(
            domain="portfolio_risk_and_allocation",
            title=title,
            severity=severity,
            summary=summary,
            metrics=metrics,
            recommendations=recs,
        )

    def _evaluate_drift(self, drift_data: Dict[str, Any]) -> Optional[InsightItem]:
        exceeds = drift_data.get("portfolio_exceeds_threshold", False)
        max_drift = Decimal(str(drift_data.get("max_drift_percentage_points", "0.00")))
        threshold = Decimal(str(drift_data.get("drift_threshold_percentage_points", "5.00")))
        drifted_classes = drift_data.get("drifted_classes", [])
        trades = drift_data.get("illustrative_rebalancing_trades", [])

        metrics = {
            "portfolio_exceeds_threshold": exceeds,
            "max_drift_percentage_points": str(max_drift),
            "drift_threshold_percentage_points": str(threshold),
            "drifted_classes": drifted_classes,
            "trade_actions_count": len(trades),
        }

        recs = []
        if exceeds:
            severity = "warning"
            title = f"Portfolio Drift ({max_drift}%) Exceeds {threshold}% Threshold"
            summary = (
                f"Allocation drift has breached your {threshold}% threshold in: {', '.join(drifted_classes)}. "
                f"Max drift observed is {max_drift}%."
            )
            recs.append("Consider executing recommended rebalancing trades to realign with target risk profile.")
            if trades:
                recs.append(f"Review {len(trades)} illustrative rebalancing transactions calculated by the engine.")
        else:
            severity = "positive"
            title = "Portfolio Allocation Within Rebalancing Tolerance"
            summary = (
                f"Current allocation drift (max {max_drift}%) is safely within the {threshold}% boundary."
            )
            recs.append("No immediate rebalancing trades are required.")

        return InsightItem(
            domain="rebalancing_and_drift",
            title=title,
            severity=severity,
            summary=summary,
            metrics=metrics,
            recommendations=recs,
        )

    # -----------------------------------------------------------------------
    # Report Synthesis
    # -----------------------------------------------------------------------

    def _synthesize_overall_status(
        self,
        insights: List[InsightItem],
        warnings: List[str],
    ) -> tuple[str, str]:
        """Determine aggregate health tier and concise executive summary."""
        if not insights and warnings:
            return (
                "insufficient_data",
                "Limited data recorded. Please record transactions and portfolio holdings to generate a complete assessment.",
            )

        alert_count = sum(1 for i in insights if i.severity == "alert")
        warning_count = sum(1 for i in insights if i.severity == "warning")
        positive_count = sum(1 for i in insights if i.severity == "positive")

        if alert_count > 0:
            status = "critical"
            exec_summary = (
                f"Action required: {alert_count} critical alert(s) detected across your finances. "
                "Immediate attention recommended for emergency reserves or cash deficits."
            )
        elif warning_count > 0:
            status = "attention_needed"
            exec_summary = (
                f"Fair financial foundation with {warning_count} area(s) needing attention "
                "(such as portfolio drift, savings rate, or goal SIP shortfall)."
            )
        else:
            status = "healthy"
            exec_summary = (
                "Strong financial standing: spending is controlled, reserves are intact, "
                "and investment allocations are well within risk parameters."
            )

        return status, exec_summary
