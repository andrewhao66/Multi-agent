"""Technical analyst agent implementation."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Dict

from pandas import isna

from .base import AgentReport, AnalysisContext
from ..utils import clamp


@dataclass
class TechnicalAnalyst:
    name: str = "Technical Analyst"

    def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        price = context.price_history
        indicators = context.indicators

        if price is None or getattr(price, "empty", False):
            report = AgentReport(
                agent=self.name,
                symbol=context.symbol,
                score=0.0,
                rationale="No price history available",
                metadata={},
            )
            return report.__dict__

        insufficient_history = False
        attrs: Dict[str, Any] = {}
        if indicators is not None:
            potential_attrs = getattr(indicators, "attrs", {})
            if isinstance(potential_attrs, dict):
                attrs = potential_attrs
                insufficient_history = bool(attrs.get("insufficient_history", False))

        if indicators is None or getattr(indicators, "empty", True) or insufficient_history:
            price_points = len(price) if price is not None else 0
            rationale = "Insufficient price history to compute indicators"
            report = AgentReport(
                agent=self.name,
                symbol=context.symbol,
                score=0.0,
                rationale=rationale,
                metadata={
                    "indicators_available": False,
                    "price_points": price_points,
                    "required_points": attrs.get("min_required"),
                },
            )
            return report.__dict__

        latest = price.iloc[-1]
        latest_ind = indicators.iloc[-1]

        trend_score = 0.0
        rationale_parts = []

        sma_fast = latest_ind.get("sma_20")
        sma_slow = latest_ind.get("sma_50")
        if sma_fast is not None and sma_slow is not None and not (isna(sma_fast) or isna(sma_slow)):
            if sma_fast > sma_slow:
                trend_score += 0.3
                rationale_parts.append("SMA20 above SMA50")
            else:
                trend_score -= 0.3
                rationale_parts.append("SMA20 below SMA50")

        macd_hist = latest_ind.get("macd_hist")
        if macd_hist is not None and not isna(macd_hist):
            if macd_hist > 0:
                trend_score += 0.2
                rationale_parts.append("MACD histogram positive")
            else:
                trend_score -= 0.2
                rationale_parts.append("MACD histogram negative")

        rsi = latest_ind.get("rsi")
        if rsi is not None and not isna(rsi):
            if 45 <= rsi <= 70:
                trend_score += 0.2
                rationale_parts.append(f"RSI neutral-positive ({rsi:.1f})")
            elif rsi < 35:
                trend_score -= 0.1
                rationale_parts.append(f"RSI oversold ({rsi:.1f})")
            elif rsi > 75:
                trend_score -= 0.2
                rationale_parts.append(f"RSI overbought ({rsi:.1f})")

        bb_upper = latest_ind.get("bb_upper")
        bb_lower = latest_ind.get("bb_lower")
        close = latest["close"]
        if (
            bb_upper is not None
            and bb_lower is not None
            and not (isna(bb_upper) or isna(bb_lower))
        ):
            if close < bb_lower:
                trend_score += 0.1
                rationale_parts.append("Price near Bollinger lower band")
            elif close > bb_upper:
                trend_score -= 0.1
                rationale_parts.append("Price near Bollinger upper band")

        returns = price["close"].pct_change().dropna()
        if returns.empty:
            volatility = 0.0
        else:
            volatility = float(returns.std(ddof=0) * sqrt(252))
        volatility_score = clamp(0.2 - volatility, -0.2, 0.2)
        trend_score += volatility_score
        rationale_parts.append(f"Annualized volatility {volatility:.2f}")

        score = float(clamp(trend_score, -1.0, 1.0))
        report = AgentReport(
            agent=self.name,
            symbol=context.symbol,
            score=score,
            rationale="; ".join(rationale_parts),
            metadata={
                "close": float(close),
                "volatility": float(volatility),
                "latest_indicators": latest_ind.to_dict(),
            },
        )
        return report.__dict__
