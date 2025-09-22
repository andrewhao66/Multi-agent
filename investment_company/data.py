"""Data utilities for the multi-agent investment project."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf


@dataclass
class PriceData:
    """Container for OHLCV price data and convenience indicators."""

    history: pd.DataFrame
    indicators: pd.DataFrame

    @property
    def latest(self) -> pd.Series:
        return self.history.iloc[-1]


def download_price_history(
    symbols: Iterable[str],
    start: str,
    end: str,
    interval: str = "1d",
) -> Dict[str, PriceData]:
    """Download price history and compute common indicators.

    Parameters
    ----------
    symbols:
        Iterable of ticker symbols.
    start, end:
        ISO formatted date strings.
    interval:
        Resolution supported by yfinance (defaults to daily data).
    """

    data: Dict[str, PriceData] = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start, end=end, interval=interval, auto_adjust=False)
        except Exception:
            hist = pd.DataFrame()

        if hist is None or hist.empty:
            hist = _generate_mock_history(symbol=symbol, start=start, end=end, interval=interval)

        hist = hist.rename(columns=str.lower)
        indicators = compute_indicators(hist)
        data[symbol] = PriceData(history=hist, indicators=indicators)
    return data


def compute_indicators(history: pd.DataFrame, windows: Optional[List[int]] = None) -> pd.DataFrame:
    """Compute technical indicators such as SMAs, RSI and MACD."""

    if windows is None:
        windows = [5, 10, 20, 50, 100, 200]

    price = history["close"].copy()
    indicators: Dict[str, pd.Series] = {}

    for window in windows:
        indicators[f"sma_{window}"] = price.rolling(window=window, min_periods=window).mean()
        indicators[f"ema_{window}"] = price.ewm(span=window, adjust=False).mean()

    delta = price.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    roll_up = gain.ewm(alpha=1 / 14, adjust=False).mean()
    roll_down = loss.ewm(alpha=1 / 14, adjust=False).mean()
    rs = roll_up / roll_down
    indicators["rsi"] = 100 - (100 / (1 + rs))

    ema12 = price.ewm(span=12, adjust=False).mean()
    ema26 = price.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    indicators["macd"] = macd_line
    indicators["macd_signal"] = signal
    indicators["macd_hist"] = macd_line - signal

    bb_window = 20
    bb_std = price.rolling(window=bb_window, min_periods=bb_window).std()
    sma20 = indicators["sma_20"]
    indicators["bb_upper"] = sma20 + 2 * bb_std
    indicators["bb_lower"] = sma20 - 2 * bb_std

    df = pd.DataFrame(indicators, index=history.index)
    df = df.dropna(how="all")
    return df


def fetch_fundamental_snapshot(symbol: str) -> Dict[str, Optional[float]]:
    """Fetch a lightweight snapshot of fundamental metrics for ``symbol``."""

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.fast_info
        sustainability = getattr(ticker, "sustainability", None)
        pe_ratio = getattr(info, "trailing_pe", None)
        pb_ratio = getattr(info, "price_to_book", None)
        dividend_yield = getattr(info, "dividend_yield", None)

        metrics: Dict[str, Optional[float]] = {
            "market_cap": getattr(info, "market_cap", None),
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "dividend_yield": dividend_yield,
        }

        if sustainability is not None and not sustainability.empty:
            esg = sustainability.mean(numeric_only=True)
            metrics["esg_score"] = float(esg.mean())
        else:
            metrics["esg_score"] = None

        try:
            balance_sheet = ticker.balance_sheet
            if not balance_sheet.empty:
                debt = balance_sheet.loc["Long Term Debt"].iloc[0]
                assets = balance_sheet.loc["Total Assets"].iloc[0]
                metrics["debt_to_asset"] = float(debt / assets) if assets else None
        except Exception:  # pragma: no cover - yfinance optional fields
            metrics["debt_to_asset"] = None

        return metrics
    except Exception:
        return _mock_fundamental_snapshot(symbol)


def fetch_recent_news(symbol: str, limit: int = 20) -> List[Dict[str, str]]:
    """Return recent news metadata from yfinance for ``symbol``."""

    try:
        ticker = yf.Ticker(symbol)
        news = ticker.news or []
        return news[:limit]
    except Exception:
        return _mock_recent_news(symbol, limit)


def _generate_mock_history(symbol: str, start: str, end: str, interval: str) -> pd.DataFrame:
    """Generate deterministic mock OHLCV data when the API is unavailable."""

    if interval not in {"1d", "1wk", "1mo"}:
        raise ValueError(f"Unsupported interval '{interval}' for offline mode")

    freq_map = {"1d": "B", "1wk": "W-FRI", "1mo": "M"}
    index = pd.date_range(start=start, end=end, freq=freq_map[interval])
    if index.empty:
        raise ValueError("No dates generated for the requested range")

    seed = abs(hash((symbol, start, end, interval))) % (2**32)
    rng = np.random.default_rng(seed)
    steps = rng.normal(loc=0.001, scale=0.02, size=len(index))
    price = 100 * np.exp(np.cumsum(steps))
    high = price * (1 + rng.uniform(0, 0.02, size=len(index)))
    low = price * (1 - rng.uniform(0, 0.02, size=len(index)))
    open_ = price * (1 + rng.normal(0, 0.005, size=len(index)))
    close = price
    volume = rng.integers(1e6, 5e6, size=len(index))

    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=index,
    )


def _mock_fundamental_snapshot(symbol: str) -> Dict[str, Optional[float]]:
    """Fallback fundamental metrics derived from deterministic heuristics."""

    base = abs(hash(symbol)) % 1_000_000
    market_cap = float(1e9 + base * 1_000)
    pe_ratio = 10 + (base % 150) / 10
    pb_ratio = 1 + (base % 50) / 20
    dividend_yield = ((base % 300) / 3000) or None
    esg_score = 40 + (base % 30)
    debt_to_asset = ((base % 70) / 100)

    return {
        "market_cap": market_cap,
        "pe_ratio": pe_ratio,
        "pb_ratio": pb_ratio,
        "dividend_yield": dividend_yield,
        "esg_score": esg_score,
        "debt_to_asset": debt_to_asset,
    }


def _mock_recent_news(symbol: str, limit: int) -> List[Dict[str, str]]:
    """Produce placeholder news items when online retrieval fails."""

    now = datetime.utcnow()
    return [
        {
            "title": f"Offline headline {i+1} for {symbol}",
            "publisher": "MockWire",
            "link": f"https://example.com/{symbol}/{i+1}",
            "providerPublishTime": int(now.timestamp()) - i * 3600,
        }
        for i in range(limit)
    ]
