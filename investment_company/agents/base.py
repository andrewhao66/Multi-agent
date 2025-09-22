"""Base classes shared by all agents."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Protocol


class Agent(Protocol):
    """Protocol for all agents participating in the investment workflow."""

    name: str

    def analyze(self, context: "AnalysisContext") -> Dict[str, Any]:
        ...


@dataclass
class AnalysisContext:
    """Bundle that contains price, indicator and meta information."""

    symbol: str
    price_history: Any
    indicators: Any
    fundamentals: Dict[str, Any]
    news: Any


@dataclass
class AgentReport:
    """Normalized report returned by each agent."""

    agent: str
    symbol: str
    score: float
    rationale: str
    metadata: Dict[str, Any]
