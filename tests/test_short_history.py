"""Regression tests for handling very short price histories."""
from __future__ import annotations

import math
import unittest

import pandas as pd

from investment_company.agents.base import AnalysisContext
from investment_company.agents.portfolio import PortfolioManager
from investment_company.agents.risk import RiskOfficer
from investment_company.agents.technical import TechnicalAnalyst
from investment_company.data import PriceData, compute_indicators


class ShortHistoryTests(unittest.TestCase):
    def setUp(self) -> None:
        index = pd.date_range("2024-01-01", periods=3, freq="D")
        history = pd.DataFrame(
            {
                "open": [100.0, 101.0, 102.0],
                "high": [101.0, 102.0, 103.0],
                "low": [99.0, 100.0, 101.0],
                "close": [100.0, 101.0, 102.0],
                "volume": [1_000_000, 1_100_000, 1_200_000],
            },
            index=index,
        )
        indicators = compute_indicators(history)
        self.price_data = PriceData(history=history, indicators=indicators)
        self.context = AnalysisContext(
            symbol="TEST",
            price_history=history,
            indicators=indicators,
            fundamentals={},
            news=[],
        )

    def test_compute_indicators_marks_insufficient_history(self) -> None:
        indicators = self.price_data.indicators
        self.assertTrue(indicators.attrs.get("insufficient_history"))
        self.assertEqual(indicators.attrs.get("observations"), 3)

    def test_technical_analyst_returns_neutral_report(self) -> None:
        report = TechnicalAnalyst().analyze(self.context)
        self.assertEqual(report["score"], 0.0)
        self.assertIn("Insufficient price history", report["rationale"])
        self.assertFalse(report["metadata"].get("indicators_available"))

    def test_risk_officer_handles_sparse_history(self) -> None:
        report = RiskOfficer().analyze(self.context)
        self.assertTrue(math.isfinite(report["score"]))
        self.assertIn("volatility", report["metadata"])
        self.assertEqual(report["metadata"]["volatility"], 0.0)

    def test_portfolio_manager_avoids_nan_allocation(self) -> None:
        tech_report = TechnicalAnalyst().analyze(self.context)
        risk_report = RiskOfficer().analyze(self.context)
        other_report = {
            "agent": "Mock Analyst",
            "symbol": "TEST",
            "score": float("nan"),
            "rationale": "",
            "metadata": {},
        }
        reports = [tech_report, risk_report, other_report]
        decision = PortfolioManager().synthesize(reports, self.context)
        self.assertTrue(math.isfinite(decision["composite_score"]))
        self.assertEqual(decision["orders"], [])
        self.assertEqual(decision["max_gross_exposure"], 1.0)


if __name__ == "__main__":
    unittest.main()
