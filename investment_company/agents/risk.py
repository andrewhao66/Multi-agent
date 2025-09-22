"""Risk management agent."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np

from .base import AgentReport, AnalysisContext


@dataclass
class RiskOfficer:
    max_weight_per_asset: float = 0.2
    max_sector_exposure: float = 0.5
    target_volatility: float = 0.3
    name: str = "Risk Officer"

    def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        price = context.price_history
        volatility = price["close"].pct_change().std() * np.sqrt(252)
        volatility_penalty = np.clip((volatility - self.target_volatility) / self.target_volatility, 0, 1)
        score = float(np.clip(0.5 - volatility_penalty, -1.0, 1.0))
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
