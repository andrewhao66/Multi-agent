"""Portfolio manager agent that synthesizes reports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .base import AgentReport, AnalysisContext
from ..utils import clamp, is_finite_number, safe_mean


@dataclass
class PortfolioManager:
    name: str = "Portfolio Manager"
    max_gross_exposure: float = 1.0
    min_confidence: float = 0.1

    def synthesize(self, reports: List[Dict[str, Any]], context: AnalysisContext) -> Dict[str, Any]:
        if not reports:
            raise ValueError("Portfolio manager requires at least one agent report")

        scores = []
        for report in reports:
            score = report.get("score")
            if is_finite_number(score):
                scores.append(float(score))
            else:
                scores.append(0.0)

        avg_score = float(safe_mean(scores))
        weight = float(clamp(avg_score, 0.0, 1.0) * min(0.25, 0.5 - abs(avg_score - 0.5)))

        if avg_score < self.min_confidence:
            orders: List[Dict[str, Any]] = []
            notes = "Confidence below threshold; holding cash"
        else:
            risk_metadata = next((r for r in reports if r["agent"] == "Risk Officer"), None)
            max_weight = risk_metadata.get("metadata", {}).get("max_weight", 0.2) if risk_metadata else 0.2
            weight = float(clamp(avg_score, 0.0, 1.0) * max_weight)
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
