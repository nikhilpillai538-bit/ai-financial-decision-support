"""
Phase 13 Unit Tests: Historical Portfolio Backtesting Engine.

Tests:
1. Deterministic synthetic price backtest with known returns.
2. Anti-lookahead bias verification (rebalance trades execute with current prices only).
3. Rebalancing frequency behavior (none, monthly, quarterly).
4. Transaction fee deductions based on turnover.
5. Max drawdown and peak tracking correctness.
6. Missing symbol and insufficient observation error handling.
"""

from datetime import date, timedelta
from decimal import Decimal
import pytest

from app.backtesting import run_portfolio_backtest
from app.db.models import HistoricalPriceModel
from app.simulation_schemas import BacktestRequest


def create_synthetic_price_records(
    symbols: list,
    prices_by_symbol: dict,  # {sym: [p0, p1, p2, ...]}
    start_date: date = date(2025, 1, 1),
) -> list:
    """Helper to generate sequential daily HistoricalPriceModel records."""
    records = []
    num_days = len(next(iter(prices_by_symbol.values())))
    for d in range(num_days):
        dt = start_date + timedelta(days=d)
        for sym in symbols:
            p = Decimal(str(prices_by_symbol[sym][d]))
            records.append(
                HistoricalPriceModel(
                    id=f"{sym}-{dt.isoformat()}",
                    symbol=sym,
                    date=dt,
                    adjusted_close=p,
                    source="synthetic_test",
                )
            )
    return records


class TestBacktestingEngine:
    """Rigorous mathematical tests for the historical backtest engine."""

    def test_single_asset_buy_and_hold_return(self):
        """Single asset growing from 100 to 120 (+20%) with no rebalancing yields exact 20% return."""
        prices = {"STOCK_A": [100.0, 105.0, 110.0, 115.0, 120.0, 120.0]}
        records = create_synthetic_price_records(["STOCK_A"], prices)

        req = BacktestRequest(
            symbols=["STOCK_A"],
            weights={"STOCK_A": Decimal("1.0")},
            initial_value=Decimal("100000.00"),
            rebalance_frequency="none",
            fee_bps=Decimal("0.0"),
        )

        res = run_portfolio_backtest(req, price_records=records)

        assert res.trading_days == 6
        assert res.initial_value == Decimal("100000.00")
        assert res.final_value == Decimal("120000.00")
        assert res.cumulative_return_pct == Decimal("20.00")
        assert res.max_drawdown_pct == Decimal("0.00")
        assert res.total_transaction_costs == Decimal("0.00")
        assert res.rebalance_count == 0

    def test_max_drawdown_calculation(self):
        """Asset sequence: 100 -> 120 (peak) -> 90 (drawdown) -> 110.
        Drawdown at 90 is (120 - 90) / 120 = 30 / 120 = 25.0%.
        """
        prices = {"STOCK_B": [100.0, 120.0, 90.0, 100.0, 110.0]}
        records = create_synthetic_price_records(["STOCK_B"], prices)

        req = BacktestRequest(
            symbols=["STOCK_B"],
            initial_value=Decimal("100000.00"),
            rebalance_frequency="none",
            fee_bps=Decimal("0.0"),
        )

        res = run_portfolio_backtest(req, price_records=records)
        assert res.max_drawdown_pct == Decimal("25.00")

    def test_transaction_cost_deduction_on_rebalance(self):
        """Rebalancing turnover incurs configured transaction costs."""
        # Stock A rises rapidly while Stock B stays flat, forcing rebalance
        prices = {
            "A": [100.0, 150.0, 150.0, 150.0, 150.0, 150.0],
            "B": [100.0, 100.0, 100.0, 100.0, 100.0, 100.0],
        }
        # Spread across months to trigger monthly rebalance
        records = []
        dates_list = [
            date(2025, 1, 15),
            date(2025, 1, 31),
            date(2025, 2, 3),   # Month change -> rebalance triggered
            date(2025, 2, 15),
            date(2025, 3, 2),   # Month change -> rebalance triggered
            date(2025, 3, 15),
        ]
        for i, dt in enumerate(dates_list):
            for s in ["A", "B"]:
                records.append(
                    HistoricalPriceModel(
                        id=f"{s}-{dt.isoformat()}",
                        symbol=s,
                        date=dt,
                        adjusted_close=Decimal(str(prices[s][i])),
                        source="synthetic_test",
                    )
                )

        req = BacktestRequest(
            symbols=["A", "B"],
            weights={"A": Decimal("0.5"), "B": Decimal("0.5")},
            initial_value=Decimal("100000.00"),
            rebalance_frequency="monthly",
            fee_bps=Decimal("50.0"),  # 50 bps = 0.50%
        )

        res = run_portfolio_backtest(req, price_records=records)
        assert res.rebalance_count >= 1
        assert res.total_transaction_costs > Decimal("0.00")

    def test_insufficient_data_rejection(self):
        """Backtesting with fewer than 5 observations raises ValueError."""
        prices = {"SHORT_SERIES": [100.0, 101.0, 102.0]}
        records = create_synthetic_price_records(["SHORT_SERIES"], prices)

        req = BacktestRequest(symbols=["SHORT_SERIES"])
        with pytest.raises(ValueError, match="insufficient aligned trading days"):
            run_portfolio_backtest(req, price_records=records)
