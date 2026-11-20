"""
Historical market-data ingestion, validation, and returns processing service for Phase 7.

Parses time series price data, aligns trading observations across instruments,
calculates annualized returns, and computes regularized covariance matrices using pandas and NumPy.
"""

import csv
from dataclasses import dataclass
from datetime import date as DateType, datetime
from decimal import Decimal
import io
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

from app.optimization_schemas import HistoricalPriceRow


@dataclass
class MarketDataMatrix:
    """Prepared numerical time series matrix for portfolio optimization."""

    symbols: List[str]
    mean_returns: np.ndarray
    cov_matrix: np.ndarray
    start_date: DateType
    end_date: DateType
    observation_count: int
    was_regularized: bool
    warnings: List[str]


def parse_historical_prices_csv(
    csv_text: str,
) -> Tuple[List[HistoricalPriceRow], List[str]]:
    """Parse and validate historical price CSV content.

    Expected CSV columns: date, symbol, adjusted_close (or price).
    Returns:
        Tuple of (valid_rows, error_messages)
    """
    valid_rows: List[HistoricalPriceRow] = []
    errors: List[str] = []

    if not csv_text or not csv_text.strip():
        errors.append("CSV content is empty.")
        return valid_rows, errors

    f = io.StringIO(csv_text.strip())
    reader = csv.reader(f)

    try:
        header = next(reader, None)
    except Exception as e:
        errors.append(f"Could not parse CSV header: {e}")
        return valid_rows, errors

    if not header:
        errors.append("CSV file has no headers.")
        return valid_rows, errors

    # Normalize header names
    header_norm = [h.strip().lower() for h in header]
    col_map: Dict[str, int] = {}
    for idx, col in enumerate(header_norm):
        if col in {"date", "trade_date", "timestamp"}:
            col_map["date"] = idx
        elif col in {"symbol", "ticker", "instrument"}:
            col_map["symbol"] = idx
        elif col in {"adjusted_close", "adj_close", "close", "price"}:
            col_map["price"] = idx

    for required in ["date", "symbol", "price"]:
        if required not in col_map:
            errors.append(f"Missing required CSV column for '{required}'. Expected date, symbol, adjusted_close.")
            return valid_rows, errors

    date_idx = col_map["date"]
    sym_idx = col_map["symbol"]
    price_idx = col_map["price"]

    for row_num, row in enumerate(reader, start=2):
        if not row or not any(field.strip() for field in row):
            continue

        if len(row) <= max(date_idx, sym_idx, price_idx):
            errors.append(f"Row {row_num}: insufficient columns (found {len(row)}).")
            continue

        raw_date = row[date_idx].strip()
        raw_symbol = row[sym_idx].strip().upper()
        raw_price = row[price_idx].strip()

        # Validate date
        try:
            parsed_date = DateType.fromisoformat(raw_date)
        except ValueError:
            errors.append(f"Row {row_num}: invalid date format '{raw_date}'. Expected YYYY-MM-DD.")
            continue

        # Validate symbol
        if not raw_symbol:
            errors.append(f"Row {row_num}: symbol cannot be blank.")
            continue

        # Validate price
        try:
            parsed_price = Decimal(raw_price)
            if parsed_price <= Decimal("0"):
                errors.append(f"Row {row_num}: price must be positive. Received '{raw_price}'.")
                continue
        except Exception:
            errors.append(f"Row {row_num}: invalid numeric price '{raw_price}'.")
            continue

        valid_rows.append(
            HistoricalPriceRow(
                date=parsed_date,
                symbol=raw_symbol,
                adjusted_close=parsed_price,
            )
        )

    return valid_rows, errors


def prepare_market_data_matrix(
    price_records: List[HistoricalPriceRow],
    required_symbols: List[str],
    min_observations: int = 20,
    annual_trading_days: int = 252,
) -> MarketDataMatrix:
    """Transform historical price observations into aligned returns and covariance matrices.

    Args:
        price_records: List of parsed HistoricalPriceRow models.
        required_symbols: List of instrument symbols that must be present in the portfolio.
        min_observations: Minimum aligned trading days required.
        annual_trading_days: Number of trading days in a year (default 252).

    Raises:
        ValueError: If observations are insufficient or required symbols are missing.
    """
    warnings: List[str] = []

    if not price_records:
        raise ValueError("No historical price observations provided.")

    clean_symbols = [s.strip().upper() for s in required_symbols]
    if len(clean_symbols) < 2:
        raise ValueError(f"At least 2 distinct symbols required for portfolio optimization. Received: {clean_symbols}")

    # Build DataFrame
    data = [
        {"date": r.date, "symbol": r.symbol.upper(), "price": float(r.adjusted_close)}
        for r in price_records
    ]
    df = pd.DataFrame(data)

    # Check that each required symbol exists in the dataset
    dataset_symbols = set(df["symbol"].unique())
    missing_symbols = [s for s in clean_symbols if s not in dataset_symbols]
    if missing_symbols:
        raise ValueError(
            f"Historical price data is missing for required portfolio instruments: {missing_symbols}. "
            "All portfolio assets must have historical price time series."
        )

    # Pivot to Date x Symbol table
    pivoted = df[df["symbol"].isin(clean_symbols)].pivot_table(
        index="date", columns="symbol", values="price", aggfunc="last"
    )
    pivoted = pivoted[clean_symbols]  # Preserve exact symbol ordering

    # Handle sparse data: drop dates where any symbol is missing
    initial_dates = len(pivoted)
    # Forward-fill gaps of up to 1 day for non-overlapping exchange holidays
    pivoted = pivoted.ffill(limit=1).dropna()
    aligned_obs = len(pivoted)

    if aligned_obs < min_observations:
        raise ValueError(
            f"Aligned historical observations count ({aligned_obs}) is below the required "
            f"minimum ({min_observations} trading days). Please provide a longer price history."
        )

    if aligned_obs < initial_dates:
        dropped = initial_dates - aligned_obs
        warnings.append(
            f"{dropped} non-common trading dates were dropped during multi-asset date alignment."
        )

    # Calculate daily simple returns
    returns = pivoted.pct_change().dropna()
    returns_count = len(returns)

    start_date = pivoted.index[0]
    end_date = pivoted.index[-1]

    # Annualized mean returns: mu = mean_daily * 252
    mean_daily = returns.mean().values
    mean_returns = mean_daily * annual_trading_days

    # Annualized covariance matrix: Sigma = cov_daily * 252
    cov_daily = returns.cov().values
    cov_matrix = cov_daily * annual_trading_days

    # Covariance Regularization / Positive-Definiteness Verification
    was_regularized = False
    min_eigenval = np.min(np.linalg.eigvalsh(cov_matrix))
    if min_eigenval <= 1e-6:
        # Apply Ledoit-Wolf diagonal shrinkage regularization: Sigma_reg = (1 - alpha) * Sigma + alpha * F
        diag_mean = np.trace(cov_matrix) / len(clean_symbols)
        shrinkage_intensity = 0.01
        cov_matrix = (1.0 - shrinkage_intensity) * cov_matrix + shrinkage_intensity * diag_mean * np.eye(len(clean_symbols))
        was_regularized = True
        warnings.append(
            "Covariance matrix was ill-conditioned or non-positive definite; "
            "diagonal shrinkage regularization was applied to guarantee numerical stability."
        )

    return MarketDataMatrix(
        symbols=clean_symbols,
        mean_returns=mean_returns,
        cov_matrix=cov_matrix,
        start_date=start_date,
        end_date=end_date,
        observation_count=returns_count,
        was_regularized=was_regularized,
        warnings=warnings,
    )
