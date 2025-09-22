"""Fundamental analyst agent implementation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from .base import AgentReport, AnalysisContext
from ..utils import clamp


@dataclass
class FundamentalAnalyst:
    name: str = "Fundamental Analyst"

    def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        fundamentals = context.fundamentals or {}
        score = 0.0
        rationale = []

        pe = fundamentals.get("pe_ratio")
        if pe is not None:
            if 0 < pe < 25:
                score += 0.25
                rationale.append(f"PE attractive at {pe:.1f}")
            elif pe >= 40:
                score -= 0.15
                rationale.append(f"PE elevated at {pe:.1f}")

        pb = fundamentals.get("pb_ratio")
        if pb is not None:
            if pb < 4:
                score += 0.1
                rationale.append(f"PB reasonable at {pb:.1f}")
            elif pb > 8:
                score -= 0.1
                rationale.append(f"PB high at {pb:.1f}")

        dividend_yield = fundamentals.get("dividend_yield")
        if dividend_yield is not None:
            score += min(dividend_yield * 5, 0.1)
            rationale.append(f"Dividend yield {dividend_yield:.2%}")

        debt_to_asset = fundamentals.get("debt_to_asset")
        if debt_to_asset is not None:
            if debt_to_asset < 0.6:
                score += 0.15
                rationale.append(f"Leverage manageable ({debt_to_asset:.2f})")
            else:
                score -= 0.15
                rationale.append(f"Leverage high ({debt_to_asset:.2f})")

        esg = fundamentals.get("esg_score")
        if esg is not None:
            adjustment = clamp((esg - 50) / 200, -0.05, 0.1)
            score += adjustment
            rationale.append(f"ESG score {esg:.1f}")

        score = float(clamp(score, -1.0, 1.0))
        report = AgentReport(
            agent=self.name,
            symbol=context.symbol,
            score=score,
            rationale="; ".join(rationale) if rationale else "Limited fundamentals available",
            metadata=fundamentals,
        )
        return report.__dict__
