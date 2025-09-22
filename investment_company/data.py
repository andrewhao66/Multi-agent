"""Data utilities for the multi-agent investment project."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

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
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start, end=end, interval=interval, auto_adjust=False)
        if hist.empty:
            raise ValueError(f"No data returned for {symbol}")
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


def fetch_recent_news(symbol: str, limit: int = 20) -> List[Dict[str, str]]:
    """Return recent news metadata from yfinance for ``symbol``."""

    ticker = yf.Ticker(symbol)
    news = ticker.news or []
    return news[:limit]
