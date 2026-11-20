"""
Deterministic Portfolio Stress-Testing Engine for Phase 13.

Simulates the immediate financial impact of macroeconomic crisis scenarios and custom
percentage shocks on an investor's portfolio holdings, calculating granular asset-level
and asset-class contributions to total losses without relying on stochastic assumptions.
"""

from collections import defaultdict
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from app.db.models import PortfolioHoldingModel, PortfolioModel
from app.portfolio_schemas import quantize_decimal
from app.portfolio_valuation import calculate_portfolio_valuation
from app.simulation_schemas import (
    AssetClassShockResult,
    CustomHoldingInput,
    CustomShock,
    HoldingShockResult,
    StressTestRequest,
    StressTestResponse,
    _q2,
)

# ---------------------------------------------------------------------------
# Predefined Macroeconomic Shock Scenarios
# ---------------------------------------------------------------------------

SCENARIO_PRESETS: Dict[str, Dict[str, Any]] = {
    "equity_market_crash": {
        "name": "Global Equity Market Crash",
        "description": "Severe market-wide equity contraction (-25%) with modest flight-to-safety into government bonds (+3%).",
        "asset_class_shocks": {
            "equity": Decimal("-25.0"),
            "fixed_income": Decimal("3.0"),
            "cash": Decimal("0.0"),
            "alternatives": Decimal("-10.0"),
            "commodities": Decimal("-15.0"),
            "real_estate": Decimal("-15.0"),
            "crypto": Decimal("-40.0"),
        },
    },
    "bond_market_decline": {
        "name": "Rapid Interest Rate Hike & Bond Slump",
        "description": "Sudden 200+ bps central bank rate hike driving broad bond duration losses (-12%) and growth stock pressure (-8%).",
        "asset_class_shocks": {
            "fixed_income": Decimal("-12.0"),
            "equity": Decimal("-8.0"),
            "cash": Decimal("2.0"),
            "alternatives": Decimal("-5.0"),
            "commodities": Decimal("-5.0"),
            "real_estate": Decimal("-10.0"),
            "crypto": Decimal("-15.0"),
        },
    },
    "stagflation_shock": {
        "name": "Stagflation Crisis (High Inflation + Low Growth)",
        "description": "Commodity price explosion (+25%) coupled with simultaneous equity (-20%) and fixed-income (-15%) sell-offs.",
        "asset_class_shocks": {
            "equity": Decimal("-20.0"),
            "fixed_income": Decimal("-15.0"),
            "commodities": Decimal("25.0"),
            "cash": Decimal("-5.0"),
            "alternatives": Decimal("0.0"),
            "real_estate": Decimal("-5.0"),
            "crypto": Decimal("-25.0"),
        },
    },
    "tech_sector_rout": {
        "name": "Tech & Growth Valuation Multiple Compression",
        "description": "Aggressive multiple re-rating heavily hitting technology equities (-35%) with minor spillover to broad equities (-12%).",
        "asset_class_shocks": {
            "equity": Decimal("-15.0"),
            "fixed_income": Decimal("2.0"),
            "cash": Decimal("0.0"),
            "alternatives": Decimal("-8.0"),
            "commodities": Decimal("-2.0"),
            "real_estate": Decimal("-4.0"),
            "crypto": Decimal("-30.0"),
        },
        "symbol_shocks": {
            "INFY.NS": Decimal("-35.0"),
            "TCS.NS": Decimal("-32.0"),
            "TECHM.NS": Decimal("-35.0"),
            "WIPRO.NS": Decimal("-35.0"),
            "AAPL": Decimal("-30.0"),
            "MSFT": Decimal("-28.0"),
            "NVDA": Decimal("-40.0"),
            "GOOGL": Decimal("-28.0"),
        },
    },
    "covid_liquidity_shock": {
        "name": "Acute Liquidity Freeze & Sudden Lockdowns",
        "description": "Acute cross-asset liquidity crunch mirroring March 2020: Equities -30%, Real Estate -20%, Commodities -35%.",
        "asset_class_shocks": {
            "equity": Decimal("-30.0"),
            "real_estate": Decimal("-20.0"),
            "commodities": Decimal("-35.0"),
            "fixed_income": Decimal("-5.0"),
            "cash": Decimal("0.0"),
            "alternatives": Decimal("-20.0"),
            "crypto": Decimal("-45.0"),
        },
    },
}


def _normalize_asset_class(raw_class: Optional[str]) -> str:
    """Normalize asset class string to standard lowercase key."""
    if not raw_class:
        return "equity"
    s = raw_class.strip().lower().replace(" ", "_").replace("-", "_")
    if s in {"fixedincome", "bond", "debt", "bonds"}:
        return "fixed_income"
    if s in {"stocks", "stock", "shares"}:
        return "equity"
    if s in {"realestate", "reit", "property"}:
        return "real_estate"
    if s in {"commodity", "gold", "silver", "metals"}:
        return "commodities"
    if s in {"crypto_currency", "cryptocurrency", "bitcoin"}:
        return "crypto"
    return s


def run_portfolio_stress_test(
    request: StressTestRequest,
    portfolio: Optional[PortfolioModel] = None,
) -> StressTestResponse:
    """Execute a deterministic stress test on a portfolio or custom holdings basket."""
    warnings: List[str] = []
    assumptions: List[str] = [
        "Stress test models an instantaneous single-period price shock across holdings.",
        "Constant correlation assumption: historical asset relationships are held fixed during the shock.",
        "Liquidity, bid-ask spread expansion, and slippage on potential forced sales are not included.",
    ]
    disclaimers: List[str] = [
        "Hypothetical stress-test results are illustrative analytical estimates, not forecasts, predictions, or guarantees.",
        "Actual market crises involve complex dynamic feedback loops, liquidity evaporation, and divergence from modeled scenarios.",
    ]

    # 1. Resolve Scenario Details & Shocks
    scenario_key = request.scenario.strip().lower()
    preset = SCENARIO_PRESETS.get(scenario_key)

    asset_class_shocks: Dict[str, Decimal] = {}
    symbol_shocks: Dict[str, Decimal] = {}
    scenario_name = request.name or (preset["name"] if preset else f"Custom Scenario ({scenario_key})")
    description = preset["description"] if preset else "User-defined custom shock scenario."

    if preset:
        asset_class_shocks.update(preset.get("asset_class_shocks", {}))
        symbol_shocks.update(preset.get("symbol_shocks", {}))

    # Apply user overrides from custom_shocks if provided
    if request.custom_shocks:
        for cs in request.custom_shocks:
            if cs.symbol:
                symbol_shocks[cs.symbol.strip().upper()] = cs.shock_percentage
            elif cs.asset_class:
                norm_cls = _normalize_asset_class(cs.asset_class)
                asset_class_shocks[norm_cls] = cs.shock_percentage

    # 2. Extract and Validate Holdings
    holdings_to_stress: List[Tuple[str, str, str, Decimal]] = []  # (symbol, name, asset_class, value)

    if portfolio is not None:
        if not portfolio.holdings:
            raise ValueError(f"Portfolio '{portfolio.name}' has no active holdings to stress test.")

        for h in portfolio.holdings:
            sym = h.asset.symbol.upper() if h.asset else "UNKNOWN"
            name = h.asset.name if h.asset else sym
            raw_cls = h.asset.asset_class if h.asset else "equity"
            asset_cls = _normalize_asset_class(raw_cls)

            # Check price availability
            price = h.current_price
            if price is None or price <= Decimal("0.00"):
                warnings.append(
                    f"Holding '{sym}' ({float(h.quantity):.4f} units) has no current market price recorded. "
                    "This unpriced exposure cannot be shocked and was excluded from stress calculations."
                )
                continue

            holding_val = quantize_decimal(h.quantity * price, places=2)
            if holding_val > Decimal("0.00"):
                holdings_to_stress.append((sym, name, asset_cls, holding_val))

    elif request.custom_holdings:
        for ch in request.custom_holdings:
            sym = ch.symbol.strip().upper()
            asset_cls = _normalize_asset_class(ch.asset_class)
            val = quantize_decimal(ch.current_value, places=2)
            if val > Decimal("0.00"):
                holdings_to_stress.append((sym, sym, asset_cls, val))

    else:
        raise ValueError("Either a valid portfolio_id or custom_holdings must be provided.")

    if not holdings_to_stress:
        raise ValueError("No priced holdings available for stress testing after evaluating inputs.")

    # 3. Calculate Stressed Values per Holding
    baseline_portfolio_val = sum(val for _, _, _, val in holdings_to_stress)
    holding_results: List[HoldingShockResult] = []

    # Intermediate structures for asset class aggregation
    class_baseline: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    class_stressed: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    class_shock_applied: Dict[str, Decimal] = {}

    total_abs_change = Decimal("0.00")

    for sym, name, asset_cls, base_val in holdings_to_stress:
        # Determine shock %: symbol shock takes precedence, then asset class shock, then 0.0%
        if sym in symbol_shocks:
            shock_pct = symbol_shocks[sym]
        elif asset_cls in asset_class_shocks:
            shock_pct = asset_class_shocks[asset_cls]
        else:
            shock_pct = Decimal("0.00")
            warnings.append(
                f"No specific shock defined for asset class '{asset_cls}' (symbol '{sym}'). Shock rate defaulted to 0.0%."
            )

        shock_factor = Decimal("1.00") + (shock_pct / Decimal("100.00"))
        # Floor value at 0 (holding value cannot be negative in linear stress test)
        stressed_val = quantize_decimal(max(Decimal("0.00"), base_val * shock_factor), places=2)
        abs_change = quantize_decimal(stressed_val - base_val, places=2)
        total_abs_change += abs_change

        class_baseline[asset_cls] += base_val
        class_stressed[asset_cls] += stressed_val
        class_shock_applied[asset_cls] = shock_pct

        holding_results.append(
            HoldingShockResult(
                symbol=sym,
                asset_name=name,
                asset_class=asset_cls,
                baseline_value=base_val,
                shock_percentage=quantize_decimal(shock_pct, places=2),
                stressed_value=stressed_val,
                absolute_change=abs_change,
                contribution_to_loss_pct=Decimal("0.00"),  # Computed below
            )
        )

    stressed_portfolio_val = baseline_portfolio_val + total_abs_change
    portfolio_pct_change = quantize_decimal(
        (total_abs_change / baseline_portfolio_val) * Decimal("100.00")
        if baseline_portfolio_val > Decimal("0.00")
        else Decimal("0.00"),
        places=2,
    )

    # 4. Compute Loss / Gain Contributions
    for hr in holding_results:
        if abs(total_abs_change) > Decimal("0.001"):
            hr.contribution_to_loss_pct = quantize_decimal(
                (hr.absolute_change / total_abs_change) * Decimal("100.00"),
                places=2,
            )
        else:
            hr.contribution_to_loss_pct = Decimal("0.00")

    # 5. Build Asset Class Breakdown
    class_results: List[AssetClassShockResult] = []
    for cls_name, base_cval in sorted(class_baseline.items()):
        stress_cval = class_stressed[cls_name]
        abs_c_change = stress_cval - base_cval
        shock_applied = class_shock_applied.get(cls_name, Decimal("0.00"))

        base_weight = quantize_decimal(
            (base_cval / baseline_portfolio_val) * Decimal("100.00")
            if baseline_portfolio_val > 0
            else Decimal("0.00"),
            places=2,
        )
        stress_weight = quantize_decimal(
            (stress_cval / stressed_portfolio_val) * Decimal("100.00")
            if stressed_portfolio_val > 0
            else Decimal("0.00"),
            places=2,
        )
        c_contrib = quantize_decimal(
            (abs_c_change / total_abs_change) * Decimal("100.00")
            if abs(total_abs_change) > Decimal("0.001")
            else Decimal("0.00"),
            places=2,
        )

        class_results.append(
            AssetClassShockResult(
                asset_class=cls_name,
                baseline_value=quantize_decimal(base_cval, places=2),
                baseline_weight_pct=base_weight,
                shock_percentage=quantize_decimal(shock_applied, places=2),
                stressed_value=quantize_decimal(stress_cval, places=2),
                stressed_weight_pct=stress_weight,
                absolute_change=quantize_decimal(abs_c_change, places=2),
                contribution_to_loss_pct=c_contrib,
            )
        )

    # Deduplicate any duplicate warning messages
    clean_warnings = list(dict.fromkeys(warnings))

    return StressTestResponse(
        scenario_name=scenario_name,
        description=description,
        baseline_portfolio_value=quantize_decimal(baseline_portfolio_val, places=2),
        stressed_portfolio_value=quantize_decimal(stressed_portfolio_val, places=2),
        absolute_change=quantize_decimal(total_abs_change, places=2),
        percentage_change=portfolio_pct_change,
        holdings_breakdown=holding_results,
        asset_class_breakdown=class_results,
        warnings=clean_warnings,
        assumptions=assumptions,
        disclaimers=disclaimers,
    )
