"""Risk management agent."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any, Dict

from .base import AgentReport, AnalysisContext
from ..utils import clamp


@dataclass
class RiskOfficer:
    max_weight_per_asset: float = 0.2
    max_sector_exposure: float = 0.5
    target_volatility: float = 0.3
    name: str = "Risk Officer"

    def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        price = context.price_history
        if price is None or getattr(price, "empty", False):
            volatility = 0.0
        else:
            returns = price["close"].pct_change()
            valid_returns = returns.dropna()
            if valid_returns.empty:
                volatility = 0.0
            else:
                volatility = float(valid_returns.std(ddof=0) * sqrt(252))

        if self.target_volatility > 0:
            raw_penalty = (volatility - self.target_volatility) / self.target_volatility
        else:
            raw_penalty = 0.0
        volatility_penalty = clamp(raw_penalty, 0.0, 1.0)
        score = float(clamp(0.5 - volatility_penalty, -1.0, 1.0))
        rationale = f"Annualized volatility {volatility:.2f}; penalty {volatility_penalty:.2f}"
        report = AgentReport(
            agent=self.name,
            symbol=context.symbol,
            score=score,
            rationale=rationale,
            metadata={
                "max_weight": self.max_weight_per_asset,
                "max_sector_exposure": self.max_sector_exposure,
                "volatility": float(volatility),
            },
        )
        return report.__dict__
