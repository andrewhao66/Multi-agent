"""News and sentiment analyst agent."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict

import numpy as np

from .base import AgentReport, AnalysisContext

POSITIVE_KEYWORDS = {
    "beats",
    "growth",
    "surge",
    "outperform",
    "bullish",
    "upgrade",
    "strong",
    "record",
}

NEGATIVE_KEYWORDS = {
    "miss",
    "decline",
    "drop",
    "lawsuit",
    "bearish",
    "downgrade",
    "weak",
    "fraud",
    "risk",
}


def _score_headline(headline: str) -> float:
    words = headline.lower().split()
    counts = Counter(words)
    pos_hits = sum(counts.get(word, 0) for word in POSITIVE_KEYWORDS)
    neg_hits = sum(counts.get(word, 0) for word in NEGATIVE_KEYWORDS)
    if pos_hits == neg_hits == 0:
        return 0.0
    return (pos_hits - neg_hits) / max(pos_hits + neg_hits, 1)


@dataclass
class SentimentAnalyst:
    name: str = "Sentiment Analyst"

    def analyze(self, context: AnalysisContext) -> Dict[str, Any]:
        news_items = context.news or []
        if not news_items:
            report = AgentReport(
                agent=self.name,
                symbol=context.symbol,
                score=0.0,
                rationale="No recent news",
                metadata={"news_count": 0},
            )
            return report.__dict__

        scores = []
        processed = []
        for item in news_items:
            title = item.get("title") or ""
            summary = item.get("summary") or ""
            combined = f"{title} {summary}".strip()
            if not combined:
                continue
            score = _score_headline(combined)
            scores.append(score)
            processed.append({"title": title, "score": score})

        if not scores:
            avg_score = 0.0
        else:
            avg_score = float(np.tanh(np.mean(scores)))

        rationale = f"Average sentiment score {avg_score:.2f} based on {len(processed)} articles"
        report = AgentReport(
            agent=self.name,
            symbol=context.symbol,
            score=avg_score,
            rationale=rationale,
            metadata={"articles": processed},
        )
        return report.__dict__
