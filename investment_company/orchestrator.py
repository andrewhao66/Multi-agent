"""High level orchestration for the multi-agent investment workflow."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .agents.base import AnalysisContext
from .agents.fundamental import FundamentalAnalyst
from .agents.portfolio import PortfolioManager
from .agents.risk import RiskOfficer
from .agents.sentiment import SentimentAnalyst
from .agents.technical import TechnicalAnalyst
from .data import download_price_history, fetch_fundamental_snapshot, fetch_recent_news
from .reports import backtest_portfolio


@dataclass
class InvestmentMeeting:
    symbols: Iterable[str]
    start: str
    end: str
    agents: List = field(default_factory=lambda: [
        TechnicalAnalyst(),
        FundamentalAnalyst(),
        SentimentAnalyst(),
        RiskOfficer(),
    ])
    portfolio_manager: PortfolioManager = field(default_factory=PortfolioManager)

    def run(self) -> Dict[str, Dict]:
        price_data = download_price_history(self.symbols, start=self.start, end=self.end)
        decisions: Dict[str, Dict] = {}
        for symbol, data in price_data.items():
            context = AnalysisContext(
                symbol=symbol,
                price_history=data.history,
                indicators=data.indicators,
                fundamentals=fetch_fundamental_snapshot(symbol),
                news=fetch_recent_news(symbol),
            )
            reports = [agent.analyze(context) for agent in self.agents]
            decision = self.portfolio_manager.synthesize(reports, context)
            backtest = backtest_portfolio(decision, data)
            decision["backtest"] = backtest.__dict__
            decisions[symbol] = decision
        return decisions
