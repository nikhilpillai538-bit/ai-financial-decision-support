"""
Modern Portfolio Theory (MPT) Optimization Engine for Phase 7.

Implements deterministic numerical optimization algorithms using NumPy:
- Global Minimum Volatility Portfolio
- Maximum Sharpe Ratio (Tangency) Portfolio
- Target-Return Constrained Portfolio
- Custom Asset Weight Bounds
- Efficient Frontier Curve Tracing
- Rebalancing Action & Value Generator
- Explainable Optimization Reports
"""

from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import numpy as np

from app.db.models import PortfolioModel, TargetAllocationModel
from app.historical_data import MarketDataMatrix
from app.optimization_schemas import (
    AssetClassOptimizationSummary,
    EfficientFrontierPoint,
    OptimizationRequest,
    OptimizationStrategy,
    OptimizedHoldingAllocation,
    PortfolioOptimizationResponse,
)
from app.portfolio_schemas import quantize_decimal
from app.portfolio_valuation import calculate_portfolio_valuation


# ---------------------------------------------------------------------------
# Mathematical Projection & Numerical Solvers
# ---------------------------------------------------------------------------

def project_onto_bounded_simplex(
    v: np.ndarray,
    lower: np.ndarray,
    upper: np.ndarray,
    tol: float = 1e-9,
    max_iter: int = 100,
) -> np.ndarray:
    """Exact projection of vector v onto the bounded probability simplex:
    sum(w) = 1.0, lower <= w <= upper.
    """
    low = np.min(v - upper)
    high = np.max(v - lower)

    for _ in range(max_iter):
        mid = (low + high) / 2.0
        w = np.clip(v - mid, lower, upper)
        s = np.sum(w)
        if abs(s - 1.0) < tol:
            return w
        if s > 1.0:
            low = mid
        else:
            high = mid

    return np.clip(v - (low + high) / 2.0, lower, upper)


def portfolio_performance(
    weights: np.ndarray,
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float,
) -> Tuple[float, float, float]:
    """Calculate annualized expected return, volatility, and Sharpe ratio.

    Returns:
        Tuple of (expected_return, expected_volatility, sharpe_ratio).
    """
    ret = float(np.dot(weights, mean_returns))
    vol = float(np.sqrt(np.dot(weights, cov_matrix @ weights)))
    sharpe = float((ret - risk_free_rate) / vol) if vol > 1e-9 else 0.0
    return ret, vol, sharpe


def optimize_min_volatility(
    cov_matrix: np.ndarray,
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
    max_iter: int = 1000,
    tol: float = 1e-8,
) -> np.ndarray:
    """Find portfolio weights that minimize portfolio volatility subject to weight bounds:
    min 0.5 * w^T Sigma w  s.t. sum(w) = 1, lower <= w <= upper.
    """
    n = cov_matrix.shape[0]
    # Initial point: midpoint of bounds projected onto simplex
    w = project_onto_bounded_simplex(np.ones(n) / n, lower_bounds, upper_bounds)
    
    # Lipschitz constant of gradient is spectral norm of Sigma
    spectral_norm = np.linalg.norm(cov_matrix, 2)
    step = 1.0 / max(spectral_norm, 1e-4)

    for _ in range(max_iter):
        grad = cov_matrix @ w
        w_next = project_onto_bounded_simplex(w - step * grad, lower_bounds, upper_bounds)
        if np.linalg.norm(w_next - w) < tol:
            break
        w = w_next

    return w


def optimize_max_sharpe(
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float,
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
    max_iter: int = 1000,
    tol: float = 1e-8,
) -> Tuple[np.ndarray, bool, Optional[str]]:
    """Find portfolio weights that maximize the Sharpe ratio.

    Returns:
        Tuple of (optimal_weights, was_max_sharpe_valid, optional_fallback_reason).
    """
    excess_returns = mean_returns - risk_free_rate
    max_excess = np.max(excess_returns)

    # Condition: If no asset's expected return exceeds the risk-free rate,
    # the tangency portfolio does not exist in the positive risk-return quadrant.
    if max_excess <= 0:
        min_vol_w = optimize_min_volatility(cov_matrix, lower_bounds, upper_bounds)
        reason = (
            f"All asset expected returns are less than or equal to the risk-free rate ({risk_free_rate * 100:.2f}%). "
            "A positive risk premium cannot be achieved; defaulting to the Minimum Volatility portfolio."
        )
        return min_vol_w, False, reason

    n = len(mean_returns)
    w = project_onto_bounded_simplex(np.ones(n) / n, lower_bounds, upper_bounds)
    step = 0.05

    for _ in range(max_iter):
        ret = np.dot(w, mean_returns)
        vol = np.sqrt(np.dot(w, cov_matrix @ w))
        if vol < 1e-9:
            break

        # Analytical gradient of Sharpe ratio S(w) = (R - rf) / sigma:
        # grad = (mean_returns / vol) - ((ret - rf) / (vol^3)) * (cov_matrix @ w)
        grad = (mean_returns / vol) - ((ret - risk_free_rate) / (vol ** 3)) * (cov_matrix @ w)

        # Gradient ascent to maximize Sharpe
        w_next = project_onto_bounded_simplex(w + step * grad, lower_bounds, upper_bounds)
        if np.linalg.norm(w_next - w) < tol:
            break
        w = w_next

    return w, True, None


def optimize_target_return(
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
    target_return: float,
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
    max_iter: int = 1000,
    tol: float = 1e-7,
) -> Tuple[np.ndarray, bool, Optional[str]]:
    """Find minimum volatility portfolio that achieves at least target_return."""
    min_possible_ret = np.min(mean_returns)
    max_possible_ret = np.max(mean_returns)

    if target_return > max_possible_ret:
        # Cannot achieve target return
        max_idx = np.argmax(mean_returns)
        w = np.zeros(len(mean_returns))
        w[max_idx] = 1.0
        reason = (
            f"Target return ({target_return * 100:.2f}%) exceeds the maximum individual asset "
            f"expected return ({max_possible_ret * 100:.2f}%). Allocated to maximum return asset."
        )
        return w, False, reason

    # Augmented Lagrangian method for target return constraint: w^T mu >= target_return
    n = len(mean_returns)
    w = project_onto_bounded_simplex(np.ones(n) / n, lower_bounds, upper_bounds)
    
    spectral_norm = float(np.linalg.norm(cov_matrix, 2))
    base_step = 1.0 / max(spectral_norm, 1e-4)

    lambda_mult = 0.0
    rho = 100.0

    for _ in range(40):
        step = min(base_step, 0.02)
        for _ in range(50):
            ret = float(np.dot(w, mean_returns))
            deficit = target_return - ret
            # Dual penalty gradient
            grad = cov_matrix @ w - (lambda_mult + rho * max(0.0, deficit)) * mean_returns
            w_next = project_onto_bounded_simplex(w - step * grad, lower_bounds, upper_bounds)
            if np.linalg.norm(w_next - w) < tol:
                w = w_next
                break
            w = w_next

        ret = float(np.dot(w, mean_returns))
        deficit = target_return - ret
        if deficit <= 1e-4:
            break
        lambda_mult += rho * deficit
        rho = min(rho * 2.0, 1e6)

    return w, True, None


def trace_efficient_frontier(
    mean_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_free_rate: float,
    symbols: List[str],
    lower_bounds: np.ndarray,
    upper_bounds: np.ndarray,
    n_points: int = 15,
) -> List[EfficientFrontierPoint]:
    """Generate discrete points along the Markowitz efficient frontier."""
    # Find min volatility portfolio return
    w_min = optimize_min_volatility(cov_matrix, lower_bounds, upper_bounds)
    min_ret, _, _ = portfolio_performance(w_min, mean_returns, cov_matrix, risk_free_rate)
    max_ret = float(np.max(mean_returns))

    if min_ret >= max_ret:
        # Flat returns
        r, v, s = portfolio_performance(w_min, mean_returns, cov_matrix, risk_free_rate)
        return [
            EfficientFrontierPoint(
                expected_return=quantize_decimal(Decimal(str(r)), 4),
                expected_volatility=quantize_decimal(Decimal(str(v)), 4),
                sharpe_ratio=quantize_decimal(Decimal(str(s)), 4),
                weights={sym: quantize_decimal(Decimal(str(w_min[i])), 4) for i, sym in enumerate(symbols)},
            )
        ]

    target_returns = np.linspace(min_ret, max_ret, n_points)
    points: List[EfficientFrontierPoint] = []

    for tr in target_returns:
        w_pt, _, _ = optimize_target_return(mean_returns, cov_matrix, tr, lower_bounds, upper_bounds)
        r, v, s = portfolio_performance(w_pt, mean_returns, cov_matrix, risk_free_rate)
        weights_dict = {
            sym: quantize_decimal(Decimal(str(max(0.0, w_pt[i]))), 4)
            for i, sym in enumerate(symbols)
        }
        points.append(
            EfficientFrontierPoint(
                expected_return=quantize_decimal(Decimal(str(r)), 4),
                expected_volatility=quantize_decimal(Decimal(str(v)), 4),
                sharpe_ratio=quantize_decimal(Decimal(str(s)), 4),
                weights=weights_dict,
            )
        )

    # Sort frontier by increasing volatility
    points.sort(key=lambda p: p.expected_volatility)
    return points


# ---------------------------------------------------------------------------
# High-Level Portfolio Optimization Orchestrator
# ---------------------------------------------------------------------------

def run_mpt_optimization(
    portfolio: PortfolioModel,
    target_allocation: Optional[TargetAllocationModel],
    market_data: MarketDataMatrix,
    request: OptimizationRequest,
    run_id: Optional[str] = None,
) -> PortfolioOptimizationResponse:
    """Execute Modern Portfolio Theory optimization and compile an explainable response."""
    symbols = market_data.symbols
    n_assets = len(symbols)
    rf = float(request.risk_free_rate)

    # 1. Parse Weight Constraints
    lower_bounds = np.full(n_assets, float(request.min_weight))
    upper_bounds = np.full(n_assets, float(request.max_weight))

    if request.asset_bounds:
        for sym, bound in request.asset_bounds.items():
            sym_upper = sym.strip().upper()
            if sym_upper in symbols:
                idx = symbols.index(sym_upper)
                lower_bounds[idx] = float(bound.min_weight)
                upper_bounds[idx] = float(bound.max_weight)

    warnings: List[str] = list(market_data.warnings)
    assumptions: List[str] = [
        "Modern Portfolio Theory assumes historical returns and covariances are representative of future distribution parameters.",
        "Asset returns are assumed to follow a multivariate normal distribution.",
        f"Annualized calculations use a standard {252} trading-day convention.",
        f"The risk-free rate is assumed to be constant at {rf * 100:.2f}% per annum.",
        "Optimization is executed under a long-only constraint (no short selling or leverage).",
    ]

    # 2. Execute Strategy Optimization
    strategy = request.strategy
    if strategy == OptimizationStrategy.MIN_VOLATILITY:
        optimal_w = optimize_min_volatility(market_data.cov_matrix, lower_bounds, upper_bounds)
        methodology = (
            "Markowitz Global Minimum Volatility: Solved for weights that minimize annualized portfolio variance "
            "subject to simplex and asset-level allocation constraints."
        )
    elif strategy == OptimizationStrategy.MAX_SHARPE:
        optimal_w, valid, reason = optimize_max_sharpe(
            market_data.mean_returns, market_data.cov_matrix, rf, lower_bounds, upper_bounds
        )
        if not valid and reason:
            warnings.append(reason)
            methodology = (
                "Maximum Sharpe Ratio (Fallback to Minimum Volatility): "
                "Because excess returns were non-positive, minimum volatility was generated."
            )
        else:
            methodology = (
                "Markowitz Tangency Portfolio (Maximum Sharpe Ratio): Solved for the optimal allocation on the "
                f"Capital Allocation Line that maximizes risk-adjusted return over the risk-free rate of {rf * 100:.2f}%."
            )
    elif strategy == OptimizationStrategy.TARGET_RETURN:
        tr = float(request.target_return or Decimal("0.12"))
        optimal_w, valid, reason = optimize_target_return(
            market_data.mean_returns, market_data.cov_matrix, tr, lower_bounds, upper_bounds
        )
        if not valid and reason:
            warnings.append(reason)
        methodology = (
            f"Target Return Optimization: Solved for the minimum-variance portfolio that satisfies an annualized "
            f"target return threshold of {tr * 100:.2f}%."
        )
    else:  # USER_CONSTRAINED
        optimal_w = optimize_min_volatility(market_data.cov_matrix, lower_bounds, upper_bounds)
        methodology = (
            "User-Constrained Portfolio: Solved for minimum variance within user-defined minimum and maximum weight bounds."
        )

    # Clean small floating point artifacts
    optimal_w = np.maximum(0.0, optimal_w)
    optimal_w = optimal_w / np.sum(optimal_w)

    # 3. Calculate Performance Metrics
    opt_ret, opt_vol, opt_sharpe = portfolio_performance(optimal_w, market_data.mean_returns, market_data.cov_matrix, rf)

    # 4. Map to Current Portfolio Holdings & Valuation
    valuation = calculate_portfolio_valuation(portfolio)
    total_port_value = valuation.priced_holdings_value

    holdings_by_symbol = {}
    for h in portfolio.holdings or []:
        if h.asset and h.asset.symbol:
            holdings_by_symbol[h.asset.symbol.upper()] = h

    allocations: List[OptimizedHoldingAllocation] = []
    class_curr_weights: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    class_opt_weights: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))

    # Compute current weights in the universe of optimized assets
    curr_w_vector = np.zeros(n_assets)
    for i, sym in enumerate(symbols):
        h = holdings_by_symbol.get(sym)
        if h and h.current_price is not None and total_port_value > Decimal("0"):
            h_val = Decimal(str(h.quantity)) * Decimal(str(h.current_price))
            curr_w = h_val / total_port_value
            curr_w_vector[i] = float(curr_w)

    curr_ret, curr_vol, curr_sharpe = None, None, None
    vol_reduction_pct, sharpe_improvement = None, None

    if np.sum(curr_w_vector) > 0:
        # Normalize current weights to sum to 1.0 for fair mathematical comparison
        normalized_curr_w = curr_w_vector / np.sum(curr_w_vector)
        c_ret, c_vol, c_sharpe = portfolio_performance(normalized_curr_w, market_data.mean_returns, market_data.cov_matrix, rf)
        curr_ret = quantize_decimal(Decimal(str(c_ret)), 4)
        curr_vol = quantize_decimal(Decimal(str(c_vol)), 4)
        curr_sharpe = quantize_decimal(Decimal(str(c_sharpe)), 4)

        if c_vol > 0:
            diff_vol = Decimal(str((c_vol - opt_vol) / c_vol)) * Decimal("100")
            vol_reduction_pct = quantize_decimal(diff_vol, 2)
        diff_sharpe = Decimal(str(opt_sharpe - c_sharpe))
        sharpe_improvement = quantize_decimal(diff_sharpe, 4)

    # 5. Build Rebalancing Allocations
    for i, sym in enumerate(symbols):
        h = holdings_by_symbol.get(sym)
        asset_id = h.asset_id if h else "unknown"
        asset_name = h.asset.name if (h and h.asset) else sym
        asset_class = (h.asset.asset_class if (h and h.asset) else "equity").lower()

        c_weight = quantize_decimal(Decimal(str(curr_w_vector[i])), 4)
        o_weight = quantize_decimal(Decimal(str(optimal_w[i])), 4)
        w_delta = quantize_decimal(o_weight - c_weight, 4)

        c_val = quantize_decimal(c_weight * total_port_value, 2)
        t_val = quantize_decimal(o_weight * total_port_value, 2)
        trade_amount = quantize_decimal(abs(w_delta) * total_port_value, 2)

        if w_delta > Decimal("0.0050"):
            action = "BUY"
        elif w_delta < Decimal("-0.0050"):
            action = "SELL"
        else:
            action = "HOLD"

        allocations.append(
            OptimizedHoldingAllocation(
                asset_id=asset_id,
                symbol=sym,
                name=asset_name,
                asset_class=asset_class,
                current_weight=c_weight,
                optimal_weight=o_weight,
                weight_delta=w_delta,
                current_value=c_val,
                target_value=t_val,
                action=action,
                trade_amount=trade_amount,
            )
        )

        class_curr_weights[asset_class] += c_weight
        class_opt_weights[asset_class] += o_weight

    # 6. Asset Class Aggregates vs Target Allocation
    target_weights: Dict[str, Decimal] = {}
    if target_allocation and not target_allocation.is_draft:
        target_weights = {
            k.lower(): quantize_decimal(Decimal(str(v)) / Decimal("100"), 4)
            for k, v in target_allocation.targets.items()
        }

    all_classes = set(class_curr_weights.keys()).union(class_opt_weights.keys()).union(target_weights.keys())
    asset_class_summary: List[AssetClassOptimizationSummary] = []
    for ac in sorted(all_classes):
        cw = class_curr_weights.get(ac, Decimal("0.0000"))
        ow = class_opt_weights.get(ac, Decimal("0.0000"))
        tw = target_weights.get(ac)
        asset_class_summary.append(
            AssetClassOptimizationSummary(
                asset_class=ac,
                current_weight=cw,
                optimal_weight=ow,
                target_allocation_weight=tw,
                weight_delta=quantize_decimal(ow - cw, 4),
            )
        )

    # 7. Trace Efficient Frontier
    frontier: List[EfficientFrontierPoint] = []
    if request.include_efficient_frontier:
        frontier = trace_efficient_frontier(
            market_data.mean_returns,
            market_data.cov_matrix,
            rf,
            symbols,
            lower_bounds,
            upper_bounds,
            n_points=15,
        )

    return PortfolioOptimizationResponse(
        portfolio_id=portfolio.id,
        portfolio_name=portfolio.name,
        base_currency=portfolio.base_currency,
        strategy=strategy.value if hasattr(strategy, "value") else str(strategy),
        risk_free_rate=quantize_decimal(Decimal(str(rf)), 4),
        expected_return=quantize_decimal(Decimal(str(opt_ret)), 4),
        expected_volatility=quantize_decimal(Decimal(str(opt_vol)), 4),
        sharpe_ratio=quantize_decimal(Decimal(str(opt_sharpe)), 4),
        current_portfolio_return=curr_ret,
        current_portfolio_volatility=curr_vol,
        current_portfolio_sharpe=curr_sharpe,
        volatility_reduction_percentage=vol_reduction_pct,
        sharpe_improvement=sharpe_improvement,
        total_portfolio_value=total_port_value,
        allocations=allocations,
        asset_class_summary=asset_class_summary,
        efficient_frontier=frontier,
        observation_count=market_data.observation_count,
        start_date=market_data.start_date,
        end_date=market_data.end_date,
        methodology=methodology,
        assumptions=assumptions,
        warnings=warnings,
        run_id=run_id,
    )
