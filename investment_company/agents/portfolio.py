"""Portfolio manager agent that synthesizes reports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from .base import AgentReport, AnalysisContext


@dataclass
class PortfolioManager:
    name: str = "Portfolio Manager"
    max_gross_exposure: float = 1.0
    min_confidence: float = 0.1

    def synthesize(self, reports: List[Dict[str, Any]], context: AnalysisContext) -> Dict[str, Any]:
        if not reports:
            raise ValueError("Portfolio manager requires at least one agent report")

        scores = np.array([report["score"] for report in reports])
        avg_score = float(np.mean(scores))
        weight = float(np.clip(avg_score, 0, 1) * min(0.25, 0.5 - np.abs(avg_score - 0.5)))

        if avg_score < self.min_confidence:
            orders: List[Dict[str, Any]] = []
            notes = "Confidence below threshold; holding cash"
        else:
            risk_metadata = next((r for r in reports if r["agent"] == "Risk Officer"), None)
            max_weight = risk_metadata.get("metadata", {}).get("max_weight", 0.2) if risk_metadata else 0.2
            weight = float(np.clip(avg_score, 0, 1) * max_weight)
            orders = [
                {
                    "symbol": context.symbol,
                    "action": "buy" if avg_score > 0 else "hold",
                    "weight": round(weight, 4),
                    "entry_rule": "SMA20>SMA50 & MACD histogram positive",
                    "stop": 0.08,
                    "take_profit": 0.2,
                    "rationale": "; ".join(r["rationale"] for r in reports if r["rationale"]),
                }
            ]
            notes = "Diversify across sectors; keep tech exposure <50%"

        decision = {
            "as_of": str(context.price_history.index[-1].date()),
            "symbol": context.symbol,
            "composite_score": avg_score,
            "orders": orders,
            "max_gross_exposure": self.max_gross_exposure,
            "notes": notes,
            "agent_reports": reports,
        }
        return decision
