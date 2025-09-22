"""Technical analyst agent implementation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

import numpy as np

from .base import AgentReport, AnalysisContext


@dataclass
class TechnicalAnalyst:
    name: str = "Technical Analyst"

    def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        price = context.price_history
        indicators = context.indicators
        latest = price.iloc[-1]
        latest_ind = indicators.iloc[-1]

        trend_score = 0.0
        rationale_parts = []

        sma_fast = latest_ind.get("sma_20")
        sma_slow = latest_ind.get("sma_50")
        if sma_fast is not None and sma_slow is not None:
            if sma_fast > sma_slow:
                trend_score += 0.3
                rationale_parts.append("SMA20 above SMA50")
            else:
                trend_score -= 0.3
                rationale_parts.append("SMA20 below SMA50")

        macd_hist = latest_ind.get("macd_hist")
        if macd_hist is not None:
            if macd_hist > 0:
                trend_score += 0.2
                rationale_parts.append("MACD histogram positive")
            else:
                trend_score -= 0.2
                rationale_parts.append("MACD histogram negative")

        rsi = latest_ind.get("rsi")
        if rsi is not None:
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
        if bb_upper is not None and bb_lower is not None:
            if close < bb_lower:
                trend_score += 0.1
                rationale_parts.append("Price near Bollinger lower band")
            elif close > bb_upper:
                trend_score -= 0.1
                rationale_parts.append("Price near Bollinger upper band")

        volatility = price["close"].pct_change().std() * np.sqrt(252)
        volatility_score = np.clip(0.2 - volatility, -0.2, 0.2)
        trend_score += volatility_score
        rationale_parts.append(f"Annualized volatility {volatility:.2f}")

        score = float(np.clip(trend_score, -1.0, 1.0))
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
