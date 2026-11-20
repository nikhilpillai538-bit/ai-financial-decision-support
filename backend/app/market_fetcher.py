"""
Market data auto-fetcher module using Yahoo Finance (yfinance).

Enables automatic ingestion of historical daily adjusted closing prices
and live quotes for Indian (NSE/BSE) and global assets (e.g., RELIANCE.NS, TCS.NS, AAPL).
"""

from datetime import date as DateType, datetime, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf

from app.optimization_schemas import HistoricalPriceRow

logger = logging.getLogger(__name__)

CURATED_PRESETS = [
    {
        "id": "nifty_top5",
        "name": "Nifty 50 Top 5 (India)",
        "description": "Reliance, TCS, HDFC Bank, Infosys, ICICI Bank",
        "symbols": ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"],
    },
    {
        "id": "india_banking",
        "name": "Banking & Financials (India)",
        "description": "HDFC Bank, ICICI Bank, SBI, Kotak Bank, Axis Bank",
        "symbols": ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"],
    },
    {
        "id": "india_it",
        "name": "IT & Software Leaders (India)",
        "description": "TCS, Infosys, HCL Tech, Wipro, Tech Mahindra",
        "symbols": ["TCS.NS", "INFY.NS", "HCLTECH.NS", "WIPRO.NS", "TECHM.NS"],
    },
    {
        "id": "us_tech_megacap",
        "name": "US Megacap Tech",
        "description": "Apple, Microsoft, Alphabet, Amazon, Nvidia",
        "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
    },
    {
        "id": "india_etfs",
        "name": "Index & Gold ETFs (India)",
        "description": "Nifty BeES, Gold BeES, Junior BeES, Silver BeES",
        "symbols": ["NIFTYBEES.NS", "GOLDBEES.NS", "JUNIORBEES.NS", "SILVERBEES.NS"],
    },
]


def normalize_symbol(symbol: str) -> str:
    """Normalize symbol string for Yahoo Finance lookup."""
    clean = symbol.strip().upper()
    return clean


def fetch_yahoo_historical_data(
    symbols: List[str],
    period: str = "1y",
    interval: str = "1d",
) -> Tuple[List[HistoricalPriceRow], List[str], List[str]]:
    """Download daily adjusted closing prices from Yahoo Finance.

    Args:
        symbols: List of ticker symbols (e.g. ['RELIANCE.NS', 'TCS.NS', 'AAPL']).
        period: Valid yfinance period ('1mo', '3mo', '6mo', '1y', '2y', '5y', 'max').
        interval: Data interval ('1d', '1wk', '1mo').

    Returns:
        Tuple of (price_rows, successful_symbols, failed_symbols)
    """
    clean_symbols = list(dict.fromkeys(normalize_symbol(s) for s in symbols if s.strip()))
    if not clean_symbols:
        return [], [], []

    valid_periods = {"5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "max"}
    if period not in valid_periods:
        period = "1y"

    try:
        # Download multi-ticker historical data with auto_adjust=True
        df = yf.download(
            tickers=clean_symbols,
            period=period,
            interval=interval,
            auto_adjust=True,
            progress=False,
            group_by="column",
        )
    except Exception as exc:
        logger.error("Failed to download historical prices from Yahoo Finance: %s", exc)
        return [], [], clean_symbols

    if df is None or df.empty:
        return [], [], clean_symbols

    # Extract Close series/dataframe
    if "Close" not in df:
        return [], [], clean_symbols

    close_data = df["Close"]
    price_rows: List[HistoricalPriceRow] = []
    symbol_point_counts: Dict[str, int] = {s: 0 for s in clean_symbols}

    if isinstance(close_data, pd.Series):
        # Single ticker case where Close returned as Series
        single_sym = clean_symbols[0]
        for dt, val in close_data.items():
            if pd.isna(val):
                continue
            try:
                date_obj = dt.date() if hasattr(dt, "date") else DateType.fromisoformat(str(dt)[:10])
                price_val = Decimal(str(round(float(val), 4)))
                if price_val > Decimal("0.0000"):
                    price_rows.append(
                        HistoricalPriceRow(
                            date=date_obj,
                            symbol=single_sym,
                            adjusted_close=price_val,
                        )
                    )
                    symbol_point_counts[single_sym] = symbol_point_counts.get(single_sym, 0) + 1
            except Exception:
                continue

    elif isinstance(close_data, pd.DataFrame):
        # Multiple tickers or single ticker returned as DataFrame
        for col_name in close_data.columns:
            sym_key = str(col_name).strip().upper()
            series = close_data[col_name]
            for dt, val in series.items():
                if pd.isna(val):
                    continue
                try:
                    date_obj = dt.date() if hasattr(dt, "date") else DateType.fromisoformat(str(dt)[:10])
                    price_val = Decimal(str(round(float(val), 4)))
                    if price_val > Decimal("0.0000"):
                        price_rows.append(
                            HistoricalPriceRow(
                                date=date_obj,
                                symbol=sym_key,
                                adjusted_close=price_val,
                            )
                        )
                        symbol_point_counts[sym_key] = symbol_point_counts.get(sym_key, 0) + 1
                except Exception:
                    continue

    successful_symbols = [s for s, count in symbol_point_counts.items() if count > 0]
    failed_symbols = [s for s, count in symbol_point_counts.items() if count == 0]

    # Sort rows chronologically
    price_rows.sort(key=lambda r: (r.symbol, r.date))

    return price_rows, successful_symbols, failed_symbols


def fetch_live_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch current market quote for a single symbol using Yahoo Finance.

    Returns dict with keys: symbol, last_price, currency, change, change_percent, etc.
    """
    clean_sym = normalize_symbol(symbol)
    try:
        ticker = yf.Ticker(clean_sym)
        fast_info = getattr(ticker, "fast_info", None)

        last_price = None
        currency = "INR" if clean_sym.endswith((".NS", ".BO")) else "USD"
        previous_close = None

        if fast_info is not None:
            try:
                last_price = fast_info.last_price
            except Exception:
                pass
            try:
                currency = fast_info.currency or currency
            except Exception:
                pass
            try:
                previous_close = fast_info.previous_close
            except Exception:
                pass

        # Fallback to history(period="1d") if fast_info last_price is missing
        if last_price is None or pd.isna(last_price):
            hist = ticker.history(period="2d")
            if not hist.empty and "Close" in hist:
                last_price = float(hist["Close"].iloc[-1])
                if len(hist) > 1:
                    previous_close = float(hist["Close"].iloc[-2])

        if last_price is None or pd.isna(last_price) or float(last_price) <= 0:
            return None

        price_dec = Decimal(str(round(float(last_price), 4)))
        prev_dec = Decimal(str(round(float(previous_close), 4))) if previous_close else None

        change = None
        change_pct = None
        if prev_dec and prev_dec > 0:
            change = price_dec - prev_dec
            change_pct = round(((price_dec - prev_dec) / prev_dec) * Decimal("100"), 2)

        return {
            "symbol": clean_sym,
            "last_price": price_dec,
            "currency": currency,
            "previous_close": prev_dec,
            "change": change,
            "change_percent": change_pct,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        logger.warning("Could not fetch live quote for %s: %s", clean_sym, exc)
        return None


def fetch_live_quotes(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch current market quotes for multiple symbols."""
    results: Dict[str, Dict[str, Any]] = {}
    for sym in symbols:
        quote = fetch_live_quote(sym)
        if quote:
            results[quote["symbol"]] = quote
    return results
