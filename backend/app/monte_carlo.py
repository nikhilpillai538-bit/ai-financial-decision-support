"""
Monte Carlo Wealth & Goal Simulator for Phase 13.

Generates thousands of stochastic multi-year investment paths using vectorized
Geometric Brownian Motion (GBM) with:
- Configurable simulation horizon (1 to 360 months)
- Bounded computational trajectory paths (100 to 5,000 runs)
- Optional random seed for deterministic reproducibility and testing
- Exact zero-volatility edge case handling (collapse to deterministic compounding)
- Monthly contribution deposits (ordinary annuity compounding)
- Time-series percentile fan curves (5th, 25th, 50th, 75th, 95th percentiles)
- Objective goal success probability estimation
"""

from decimal import Decimal
import math
from typing import Dict, List, Optional, Tuple

import numpy as np

from app.db.models import PortfolioModel
from app.portfolio_schemas import quantize_decimal
from app.portfolio_valuation import calculate_portfolio_valuation
from app.simulation_schemas import (
    MonteCarloPercentilePoint,
    MonteCarloRequest,
    MonteCarloResponse,
    TerminalWealthStats,
)


def run_monte_carlo_simulation(
    request: MonteCarloRequest,
    portfolio: Optional[PortfolioModel] = None,
) -> MonteCarloResponse:
    """Execute a vectorized Monte Carlo simulation of future portfolio wealth."""
    warnings: List[str] = []
    assumptions: List[str] = [
        "Asset returns are modeled via Geometric Brownian Motion (log-normal distribution).",
        "Expected return and volatility parameters are assumed constant across the simulation horizon.",
        "Monthly contributions are deposited at the beginning of each period.",
        "Simulations exclude taxes, inflation deflation, and transaction slippage.",
    ]
    disclaimers: List[str] = [
        "Monte Carlo results are probabilistic mathematical models, not guarantees of future wealth.",
        "Real-world financial distributions often exhibit fat tails and kurtosis not captured by standard normal models.",
    ]

    # 1. Resolve Initial Value
    initial_v = float(request.initial_value)
    if portfolio is not None:
        val = calculate_portfolio_valuation(portfolio)
        if val.priced_holdings_value > Decimal("0.00"):
            initial_v = float(val.priced_holdings_value)
            if val.unpriced_holdings_count > 0:
                warnings.append(
                    f"{val.unpriced_holdings_count} unpriced holdings were excluded from initial portfolio valuation."
                )

    if initial_v <= 0:
        raise ValueError("Initial portfolio value must be greater than zero.")

    monthly_contrib = float(request.monthly_contribution)
    horizon_m = request.horizon_months
    n_sims = request.num_simulations

    # 2. Resolve Expected Return and Volatility
    ann_ret_pct: float
    ann_vol_pct: float

    if request.expected_annual_return_pct is not None:
        ann_ret_pct = float(request.expected_annual_return_pct)
    else:
        # Default moderate expected return
        ann_ret_pct = 10.0
        warnings.append("Expected annual return was not specified; defaulted to 10.0% p.a.")

    if request.annual_volatility_pct is not None:
        ann_vol_pct = float(request.annual_volatility_pct)
    else:
        # Default moderate volatility
        ann_vol_pct = 15.0
        warnings.append("Annual volatility was not specified; defaulted to 15.0% p.a.")

    if ann_vol_pct < 0:
        raise ValueError("Annual volatility percentage cannot be negative.")

    # 3. Vectorized Geometric Brownian Motion Computation
    dt = 1.0 / 12.0  # Monthly time step
    mu = ann_ret_pct / 100.0
    sigma = ann_vol_pct / 100.0

    # Itô drift: alpha = (mu - 0.5 * sigma^2) * dt
    alpha = (mu - 0.5 * (sigma ** 2)) * dt
    beta = sigma * math.sqrt(dt)

    # Initialize random state with optional seed for exact deterministic reproducibility
    rng = np.random.RandomState(request.seed) if request.seed is not None else np.random.RandomState()

    if abs(sigma) < 1e-9:
        # Zero-volatility edge case: purely deterministic ordinary annuity compounding
        Z = np.zeros((n_sims, horizon_m), dtype=np.float64)
    else:
        Z = rng.normal(loc=0.0, scale=1.0, size=(n_sims, horizon_m))

    # Monthly return multipliers: F = exp(alpha + beta * Z)
    monthly_multipliers = np.exp(alpha + beta * Z)

    # Matrix to store wealth paths: shape (num_simulations, horizon_months + 1)
    wealth = np.zeros((n_sims, horizon_m + 1), dtype=np.float64)
    wealth[:, 0] = initial_v

    for t in range(1, horizon_m + 1):
        # Deposit monthly contribution at start of period, then apply period return
        wealth[:, t] = (wealth[:, t - 1] + monthly_contrib) * monthly_multipliers[:, t - 1]
        # Floor at 0 (cannot have negative wealth in limited liability investment)
        wealth[:, t] = np.maximum(wealth[:, t], 0.0)

    # 4. Generate Percentile Trajectory
    # To keep payload responsive for multi-year horizons, sample milestone points:
    # Always include month 0, month 1, and every 3rd month (or all months if horizon <= 60)
    step_size = 1 if horizon_m <= 60 else (3 if horizon_m <= 180 else 6)
    sampled_months = list(range(0, horizon_m + 1, step_size))
    if sampled_months[-1] != horizon_m:
        sampled_months.append(horizon_m)

    percentile_curve: List[MonteCarloPercentilePoint] = []
    num_samples_to_save = min(5, n_sims)

    for m in sampled_months:
        col = wealth[:, m]
        p5 = float(np.percentile(col, 5))
        p25 = float(np.percentile(col, 25))
        p50 = float(np.percentile(col, 50))
        p75 = float(np.percentile(col, 75))
        p95 = float(np.percentile(col, 95))
        sample_paths = [float(wealth[i, m]) for i in range(num_samples_to_save)]

        percentile_curve.append(
            MonteCarloPercentilePoint(
                month=m,
                year=round(m / 12.0, 2),
                p5=quantize_decimal(Decimal(str(p5)), places=2),
                p25=quantize_decimal(Decimal(str(p25)), places=2),
                p50=quantize_decimal(Decimal(str(p50)), places=2),
                p75=quantize_decimal(Decimal(str(p75)), places=2),
                p95=quantize_decimal(Decimal(str(p95)), places=2),
                sample_paths=[quantize_decimal(Decimal(str(sp)), places=2) for sp in sample_paths],
            )
        )

    # 5. Terminal Wealth Statistics
    terminal_col = wealth[:, horizon_m]
    term_mean = float(np.mean(terminal_col))
    term_median = float(np.median(terminal_col))
    term_std = float(np.std(terminal_col, ddof=1)) if n_sims > 1 else 0.0
    term_p5 = float(np.percentile(terminal_col, 5))
    term_p25 = float(np.percentile(terminal_col, 25))
    term_p75 = float(np.percentile(terminal_col, 75))
    term_p95 = float(np.percentile(terminal_col, 95))
    term_min = float(np.min(terminal_col))
    term_max = float(np.max(terminal_col))

    terminal_stats = TerminalWealthStats(
        mean=quantize_decimal(Decimal(str(term_mean)), places=2),
        median=quantize_decimal(Decimal(str(term_median)), places=2),
        std_dev=quantize_decimal(Decimal(str(term_std)), places=2),
        p5=quantize_decimal(Decimal(str(term_p5)), places=2),
        p25=quantize_decimal(Decimal(str(term_p25)), places=2),
        p75=quantize_decimal(Decimal(str(term_p75)), places=2),
        p95=quantize_decimal(Decimal(str(term_p95)), places=2),
        min=quantize_decimal(Decimal(str(term_min)), places=2),
        max=quantize_decimal(Decimal(str(term_max)), places=2),
    )

    # 6. Goal Achievement Probability
    goal_prob_pct: Optional[Decimal] = None
    target_amt_dec: Optional[Decimal] = None
    if request.target_amount is not None:
        target_amt_dec = quantize_decimal(request.target_amount, places=2)
        target_val = float(request.target_amount)
        successes = int(np.sum(terminal_col >= target_val))
        prob = (successes / n_sims) * 100.0
        goal_prob_pct = quantize_decimal(Decimal(str(prob)), places=2)

    clean_warnings = list(dict.fromkeys(warnings))

    return MonteCarloResponse(
        initial_value=quantize_decimal(Decimal(str(initial_v)), places=2),
        monthly_contribution=quantize_decimal(Decimal(str(monthly_contrib)), places=2),
        horizon_months=horizon_m,
        num_simulations=n_sims,
        annual_return_assumed_pct=quantize_decimal(Decimal(str(ann_ret_pct)), places=2),
        annual_volatility_assumed_pct=quantize_decimal(Decimal(str(ann_vol_pct)), places=2),
        target_amount=target_amt_dec,
        goal_success_probability_pct=goal_prob_pct,
        terminal_wealth=terminal_stats,
        percentile_trajectory=percentile_curve,
        warnings=clean_warnings,
        assumptions=assumptions,
        disclaimers=disclaimers,
    )
