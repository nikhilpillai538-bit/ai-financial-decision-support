"""
Unit tests for historical market-data ingestion, parsing, returns, and covariance calculations.
"""

from datetime import date as ISODate
from decimal import Decimal

import numpy as np
import pytest

from app.historical_data import (
    parse_historical_prices_csv,
    prepare_market_data_matrix,
)
from app.optimization_schemas import HistoricalPriceRow


class TestHistoricalDataParser:
    """Tests for parse_historical_prices_csv."""

    def test_valid_csv_parsing(self):
        csv_data = """date,symbol,adjusted_close
2025-01-02,TCS,3850.50
2025-01-03,TCS,3862.00
2025-01-02,INFY,1820.00
2025-01-03,INFY,1835.50
"""
        rows, errors = parse_historical_prices_csv(csv_data)
        assert len(errors) == 0
        assert len(rows) == 4
        assert rows[0].symbol == "TCS"
        assert rows[0].date == ISODate(2025, 1, 2)
        assert rows[0].adjusted_close == Decimal("3850.5000")

    def test_empty_csv_reported(self):
        rows, errors = parse_historical_prices_csv("")
        assert len(rows) == 0
        assert any("empty" in e.lower() for e in errors)

    def test_missing_column_reported(self):
        csv_data = """date,symbol\n2025-01-02,TCS\n"""
        rows, errors = parse_historical_prices_csv(csv_data)
        assert len(rows) == 0
        assert any("missing required" in e.lower() for e in errors)

    def test_invalid_date_and_negative_price_reported(self):
        csv_data = """date,symbol,adjusted_close
invalid-date,TCS,100.0
2025-01-02,TCS,-50.0
2025-01-03,TCS,0.0
2025-01-04,TCS,120.0
"""
        rows, errors = parse_historical_prices_csv(csv_data)
        assert len(rows) == 1
        assert rows[0].date == ISODate(2025, 1, 4)
        assert len(errors) == 3


class TestMarketDataMatrixPreparation:
    """Tests for prepare_market_data_matrix."""

    def _generate_synthetic_prices(self, n_days: int = 30) -> list[HistoricalPriceRow]:
        rows = []
        base_tcs = 3000.0
        base_infy = 1500.0

        for i in range(1, n_days + 1):
            dt = ISODate(2025, 1, i if i <= 28 else 28)
            # Simulated drift
            p_tcs = base_tcs * (1 + 0.001 * i)
            p_infy = base_infy * (1 + 0.0015 * i)

            rows.append(HistoricalPriceRow(date=dt, symbol="TCS", adjusted_close=Decimal(str(round(p_tcs, 2)))))
            rows.append(HistoricalPriceRow(date=dt, symbol="INFY", adjusted_close=Decimal(str(round(p_infy, 2)))))
        return rows

    def test_market_data_matrix_success(self):
        # 30 unique dates
        rows = []
        for d in range(1, 31):
            dt = ISODate(2025, 1 if d <= 28 else 2, d if d <= 28 else d - 28)
            rows.append(HistoricalPriceRow(date=dt, symbol="TCS", adjusted_close=Decimal(str(3000 + d * 5))))
            rows.append(HistoricalPriceRow(date=dt, symbol="INFY", adjusted_close=Decimal(str(1500 + d * 3))))

        matrix = prepare_market_data_matrix(rows, required_symbols=["TCS", "INFY"], min_observations=20)

        assert matrix.symbols == ["TCS", "INFY"]
        assert matrix.observation_count == 29  # 30 price dates yield 29 daily returns
        assert len(matrix.mean_returns) == 2
        assert matrix.cov_matrix.shape == (2, 2)
        assert matrix.cov_matrix[0, 0] > 0
        assert matrix.cov_matrix[1, 1] > 0

    def test_missing_required_symbol_raises_error(self):
        rows = [
            HistoricalPriceRow(date=ISODate(2025, 1, 2), symbol="TCS", adjusted_close=Decimal("3000")),
        ]
        with pytest.raises(ValueError) as exc:
            prepare_market_data_matrix(rows, required_symbols=["TCS", "RELIANCE"], min_observations=5)
        assert "missing for required" in str(exc.value)

    def test_insufficient_observations_raises_error(self):
        # Only 5 days provided when 20 required
        rows = []
        for d in range(1, 6):
            dt = ISODate(2025, 1, d)
            rows.append(HistoricalPriceRow(date=dt, symbol="TCS", adjusted_close=Decimal(str(3000 + d))))
            rows.append(HistoricalPriceRow(date=dt, symbol="INFY", adjusted_close=Decimal(str(1500 + d))))

        with pytest.raises(ValueError) as exc:
            prepare_market_data_matrix(rows, required_symbols=["TCS", "INFY"], min_observations=20)
        assert "below the required minimum" in str(exc.value)

    def test_covariance_shrinkage_on_singular_matrix(self):
        # Create identical price series (perfect collinearity, singular covariance)
        rows = []
        for d in range(1, 25):
            dt = ISODate(2025, 1, d)
            rows.append(HistoricalPriceRow(date=dt, symbol="A", adjusted_close=Decimal(str(100 + d))))
            rows.append(HistoricalPriceRow(date=dt, symbol="B", adjusted_close=Decimal(str(100 + d))))

        matrix = prepare_market_data_matrix(rows, required_symbols=["A", "B"], min_observations=15)
        # Should apply shrinkage and remain positive definite
        min_eig = np.min(np.linalg.eigvalsh(matrix.cov_matrix))
        assert min_eig > 0
        assert matrix.was_regularized is True
