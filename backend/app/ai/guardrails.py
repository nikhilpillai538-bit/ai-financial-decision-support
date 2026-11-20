"""
Grounding, Anti-Hallucination, and Guardrails Service for Phase 9.

Ensures LLM prompts are injection-resistant, responses are strictly grounded
in verified financial facts, and a deterministic fallback is always available
when the LLM is unconfigured, times out, or returns invalid output.
"""

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set

from app.ai.financial_context import ValidatedFinancialContext


# ---------------------------------------------------------------------------
# Prompt Injection Filtering
# ---------------------------------------------------------------------------

SUSPICIOUS_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions",
    r"system\s*prompt",
    r"you\s+are\s+now\s+(an?\s+)?unrestricted",
    r"bypass\s+all\s+filters",
    r"override\s+system\s+rules",
    r"jailbreak",
    r"act\s+as\s+DAN",
    r"pretend\s+you\s+have\s+no\s+rules",
]

COMPILED_SUSPICIOUS = [re.compile(p, re.IGNORECASE) for p in SUSPICIOUS_PATTERNS]


def sanitize_user_input(question: str) -> str:
    """
    Sanitize user input to neutralize prompt injection while preserving valid queries.
    """
    cleaned = question.strip()
    for pattern in COMPILED_SUSPICIOUS:
        cleaned = pattern.sub("[filtered_directive]", cleaned)
    return cleaned


# ---------------------------------------------------------------------------
# Grounded System Prompt
# ---------------------------------------------------------------------------

FINANCIAL_ASSISTANT_SYSTEM_PROMPT = """You are an AI-Powered Financial Decision Support Assistant for an authenticated personal finance system.

Your core mission is to help the user understand their finances, interpret portfolio analytics, evaluate risks, and make informed financial decisions.

ABSOLUTE OPERATIONAL CONSTRAINTS:
1. SOURCE OF TRUTH: All authoritative calculations (balances, cash flow, emergency funds, MPT risk metrics, SIP math, drift, rebalancing) are deterministically computed by the backend engine and supplied in the verified context below.
2. ZERO INVENTED NUMBERS: You must NEVER invent, assume, extrapolate, or hallucinate financial numbers, account balances, stock prices, or historical returns.
3. MISSING DATA TRANSPARENCY: If a user asks about a metric or domain that is not present in the verified context, state clearly and concisely that the metric is unavailable in their financial profile.
4. NO FIDUCIARY OR GUARANTEE CLAIMS: Never promise guaranteed returns, claim zero risk, or provide formal tax/legal/regulated investment advice. Always maintain an objective decision-support tone.
5. NO UNAUTHORIZED MUTATION: You are an analytical and conversational advisor. You cannot execute trades, transfer money, or modify account settings.

OUTPUT FORMAT REQUIREMENTS:
You MUST respond with a single, valid JSON object (enclosed in ```json ... ``` or as raw JSON) with the following exact keys:
{
  "answer": "Detailed, markdown-formatted explanation addressing the user's question directly using verified facts.",
  "cited_domains": ["list", "of", "domains", "used"],
  "key_metrics_cited": {"metric_name": "metric_value"},
  "limitations_or_missing_data": ["any data gaps or caveats mentioned"],
  "suggested_follow_ups": ["2 to 3 relevant follow-up questions the user might ask next"],
  "disclaimer": "Educational and decision-support guidance only. Not financial, tax, or legal advice."
}
"""


def build_assistant_system_prompt(context: ValidatedFinancialContext) -> str:
    """Combine base prompt instructions with the grounded financial context."""
    grounded_context_text = context.to_grounded_text()
    return f"{FINANCIAL_ASSISTANT_SYSTEM_PROMPT}\n\n{grounded_context_text}"


# ---------------------------------------------------------------------------
# Structured Output Schema
# ---------------------------------------------------------------------------

@dataclass
class GuardedAssistantResponse:
    """Structured, verified response from the financial assistant."""
    answer: str
    cited_domains: List[str] = field(default_factory=list)
    key_metrics_cited: Dict[str, Any] = field(default_factory=dict)
    limitations_or_missing_data: List[str] = field(default_factory=list)
    suggested_follow_ups: List[str] = field(default_factory=list)
    disclaimer: str = (
        "Educational and decision-support guidance only. "
        "Not formal financial, legal, or tax advice. Market investments are subject to risk."
    )
    is_fallback: bool = False
    provider_name: str = "mock"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Response Post-Validation & Normalization
# ---------------------------------------------------------------------------

def parse_and_validate_llm_response(
    raw_text: str,
    context: ValidatedFinancialContext,
    provider_name: str,
) -> GuardedAssistantResponse:
    """
    Parse LLM output JSON, validate schema keys, verify cited domains, and enforce guardrails.
    If parsing fails, falls back gracefully to a deterministic response.
    """
    cleaned_text = raw_text.strip()

    # Extract JSON if wrapped in markdown code blocks
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned_text)
    if json_match:
        cleaned_text = json_match.group(1).strip()

    try:
        parsed = json.loads(cleaned_text)
        if not isinstance(parsed, dict):
            return build_deterministic_fallback(
                context=context,
                reason="LLM response was not a JSON dictionary",
                provider_name=provider_name,
            )

        answer = parsed.get("answer")
        if not answer or not isinstance(answer, str):
            answer = parsed.get("summary") or parsed.get("explanation") or raw_text

        # Validate cited domains against context
        valid_domains = set(context.domains_retrieved)
        raw_cited = parsed.get("cited_domains", [])
        if isinstance(raw_cited, list):
            cited_domains = [d for d in raw_cited if isinstance(d, str) and d in valid_domains]
        else:
            cited_domains = list(valid_domains)

        key_metrics = parsed.get("key_metrics_cited", {})
        if not isinstance(key_metrics, dict):
            key_metrics = {}

        limitations = parsed.get("limitations_or_missing_data", [])
        if not isinstance(limitations, list):
            limitations = []
        # Always merge context warnings
        for w in context.missing_data_warnings:
            if w not in limitations:
                limitations.append(w)

        follow_ups = parsed.get("suggested_follow_ups", [])
        if not isinstance(follow_ups, list) or not follow_ups:
            follow_ups = _generate_default_follow_ups(cited_domains)

        disclaimer = parsed.get(
            "disclaimer",
            "Educational and decision-support guidance only. Not financial, tax, or legal advice.",
        )

        # Enforce anti-hallucination check for guaranteed returns
        guarantee_check = re.search(r"\b(guaranteed\s+return|risk-free\s+return|promise\s+\d+%)\b", answer, re.IGNORECASE)
        if guarantee_check:
            answer += "\n\n*(Note: Investment market returns cannot be guaranteed and past performance does not guarantee future results.)*"

        return GuardedAssistantResponse(
            answer=answer,
            cited_domains=cited_domains if cited_domains else list(valid_domains),
            key_metrics_cited=key_metrics,
            limitations_or_missing_data=limitations,
            suggested_follow_ups=follow_ups[:3],
            disclaimer=disclaimer,
            is_fallback=False,
            provider_name=provider_name,
        )

    except (json.JSONDecodeError, Exception):
        # Fall back gracefully to structured deterministic response
        return build_deterministic_fallback(
            context=context,
            reason="LLM response JSON parsing error",
            raw_text=raw_text,
            provider_name=provider_name,
        )


# ---------------------------------------------------------------------------
# Deterministic Fallback Generator
# ---------------------------------------------------------------------------

def build_deterministic_fallback(
    context: ValidatedFinancialContext,
    reason: str = "LLM unavailable or unconfigured",
    raw_text: Optional[str] = None,
    provider_name: str = "fallback",
) -> GuardedAssistantResponse:
    """
    Generate an authoritative, completely deterministic fallback answer directly
    from the verified financial context. Guarantees the system never fails to respond.
    """
    sections = []
    sections.append("### Financial Decision Support Summary (Authoritative Engine)")

    if raw_text and len(raw_text.strip()) > 30:
        # Include partial text if helpful
        sections.append(f"*{reason}. Provided deterministic synthesis below.*")
    else:
        sections.append(f"*{reason}. Financial analytics synthesized from verified profile records.*")

    data = context.verified_data

    # 1. Spending and Cash Flow
    if "spending_and_cash_flow" in data:
        s = data["spending_and_cash_flow"]
        sections.append(
            f"\n**Spending & Cash Flow:**\n"
            f"- Total Recorded Income: {s.get('total_income', '0.00')}\n"
            f"- Total Recorded Expenses: {s.get('total_expenses', '0.00')}\n"
            f"- Net Savings: {s.get('net_savings', '0.00')} (Savings Rate: {s.get('savings_rate_percentage', '0.00')}%)\n"
            f"- Recorded Transactions: {s.get('transaction_count', 0)}"
        )
        if s.get("top_spending_categories"):
            top_cat_str = ", ".join(f"{k}: {v}" for k, v in list(s["top_spending_categories"].items())[:3])
            sections.append(f"- Top Categories: {top_cat_str}")
        if s.get("forecast_liquidity_warning"):
            sections.append(f"- ⚠️ Cash Flow Warning: {s.get('forecast_liquidity_warning')}")

    # 2. Emergency Fund
    if "emergency_fund" in data:
        ef = data["emergency_fund"]
        sections.append(
            f"\n**Emergency Fund Status:**\n"
            f"- Available Liquid Savings: {ef.get('available_savings', '0.00')}\n"
            f"- Current Coverage: {ef.get('months_of_coverage', '0.0')} months "
            f"(Monthly Essential Expenses: {ef.get('monthly_essential_expenses', '0.00')})\n"
            f"- Recommended 3-Month Buffer: {ef.get('target_3_months', '0.00')} "
            f"(Shortfall: {ef.get('shortfall_3_months', '0.00')})\n"
            f"- Recommended 6-Month Buffer: {ef.get('target_6_months', '0.00')} "
            f"(Shortfall: {ef.get('shortfall_6_months', '0.00')})"
        )

    # 3. Portfolio & Risk
    if "portfolio_risk_and_allocation" in data:
        p = data["portfolio_risk_and_allocation"]
        sections.append(
            f"\n**Portfolio & Risk:**\n"
            f"- Portfolio: {p.get('portfolio_name')} ({p.get('base_currency')})\n"
            f"- Total Priced Value: {p.get('total_priced_value', '0.00')}\n"
            f"- Unrealized Gain/Loss: {p.get('unrealized_gain_loss', '0.00')} "
            f"({p.get('unrealized_gain_loss_percentage', '0.00')}%)"
        )
        if p.get("latest_optimization"):
            opt = p["latest_optimization"]
            sections.append(
                f"- MPT Expected Return: {opt.get('expected_return')}, "
                f"Volatility: {opt.get('expected_volatility')}, "
                f"Sharpe Ratio: {opt.get('sharpe_ratio')}"
            )

    # 4. Rebalancing & Drift
    if "rebalancing_and_drift" in data:
        d = data["rebalancing_and_drift"]
        sections.append(
            f"\n**Portfolio Drift & Rebalancing:**\n"
            f"- Drift Threshold: {d.get('drift_threshold_percentage_points', '5.00')}%\n"
            f"- Threshold Exceeded: {'Yes' if d.get('portfolio_exceeds_threshold') else 'No'} "
            f"(Max Drift: {d.get('max_drift_percentage_points', '0.00')}%)"
        )

    # 5. Investment Goals
    if "investment_goals" in data:
        g_list = data["investment_goals"]
        sections.append(f"\n**Investment Goals:**")
        if not g_list:
            sections.append("- No active investment goals found.")
        else:
            for g in g_list:
                sections.append(
                    f"- '{g.get('name')}': Target {g.get('target_amount')} by {g.get('target_date')} "
                    f"(Progress: {g.get('progress_percentage')}%, Status: {g.get('status_assessment')})"
                )

    # 6. Financial News & Sentiment
    if "financial_news" in data:
        n = data["financial_news"]
        sections.append(
            f"\n**Financial News & Sentiment:**\n"
            f"- Market Sentiment: {n.get('overall_sentiment_label', 'neutral').upper()} "
            f"(Score: {n.get('average_sentiment_score', '0.00')})\n"
            f"- Positive: {n.get('positive_percentage')}%, Negative: {n.get('negative_percentage')}%, Neutral: {n.get('neutral_percentage')}%\n"
            f"- Analyzed Articles: {n.get('total_articles', 0)}"
        )
        matched = n.get("portfolio_matched_articles", [])
        if matched:
            sections.append("- Portfolio-Matched News:")
            for m in matched[:3]:
                sections.append(f"  * {m.get('title')} ({m.get('source_name')}, {m.get('sentiment_label')})")

    answer = "\n".join(sections)
    follow_ups = _generate_default_follow_ups(context.domains_retrieved)

    return GuardedAssistantResponse(
        answer=answer,
        cited_domains=context.domains_retrieved,
        key_metrics_cited={
            k: (v.get("total_income") if isinstance(v, dict) else len(v))
            for k, v in context.verified_data.items()
        },
        limitations_or_missing_data=list(context.missing_data_warnings),
        suggested_follow_ups=follow_ups[:3],
        disclaimer=(
            "Educational and decision-support guidance only. "
            "Not financial, tax, or legal advice. Deterministic engine fallback response."
        ),
        is_fallback=True,
        provider_name=provider_name,
    )


def _generate_default_follow_ups(domains: List[str]) -> List[str]:
    """Generate contextual follow-up questions based on domains."""
    follow_ups = []
    if "emergency_fund" in domains:
        follow_ups.append("How much should I save monthly to reach my 6-month emergency fund target?")
    if "portfolio_risk_and_allocation" in domains or "rebalancing_and_drift" in domains:
        follow_ups.append("What rebalancing trades are recommended to restore my target allocation?")
    if "investment_goals" in domains:
        follow_ups.append("What will my goal corpus be if I increase my monthly SIP by 5,000?")
    if "spending_and_cash_flow" in domains:
        follow_ups.append("What is my lowest projected cash balance over the next 30 days?")
    if "financial_news" in domains:
        follow_ups.append("Which recent financial news headlines relate directly to my portfolio?")

    if not follow_ups:
        follow_ups = [
            "What is my current savings rate?",
            "Is my emergency fund adequate?",
            "What is my portfolio asset allocation?",
        ]
    return follow_ups
