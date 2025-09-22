"""Backtesting utilities and reporting helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd

from .data import PriceData


@dataclass
class BacktestReport:
    start: str
    end: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    cumulative_returns: Dict[str, float]


def backtest_portfolio(decision: Dict, data: PriceData) -> BacktestReport:
    orders = decision.get("orders", [])
    weights = {order["symbol"]: order.get("weight", 0.0) for order in orders if order.get("action") == "buy"}
    if not weights:
        weights = {decision.get("symbol"): 0.0}

    price = data.history["close"].copy()
    returns = price.pct_change().fillna(0.0)
    cumulative = (1 + returns).cumprod()

    weight = sum(weights.values())
    portfolio_curve = 1 + weight * (cumulative - 1)

    total_return = float(portfolio_curve.iloc[-1] - 1)
    periods_per_year = 252
    if getattr(returns.index, "freq", None) == "W":
        periods_per_year = 52
    avg_return = returns.mean() * periods_per_year * weight
    volatility = returns.std() * np.sqrt(periods_per_year) * max(weight, 1e-9)
    sharpe = float(avg_return / volatility) if volatility else 0.0

    rolling_max = portfolio_curve.cummax()
    drawdown = (portfolio_curve - rolling_max) / rolling_max
    max_drawdown = float(drawdown.min()) if not drawdown.empty else 0.0

    report = BacktestReport(
        start=str(price.index[0].date()),
        end=str(price.index[-1].date()),
        total_return=total_return,
        annualized_return=float(avg_return),
        sharpe_ratio=sharpe,
        max_drawdown=max_drawdown,
        cumulative_returns={"portfolio": float(portfolio_curve.iloc[-1] - 1)},
    )
    return report
