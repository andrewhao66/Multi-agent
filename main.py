"""Command line interface for running the multi-agent investment meeting."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from investment_company.orchestrator import InvestmentMeeting


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the multi-agent investment workflow")
    parser.add_argument("symbols", nargs="+", help="Ticker symbols to analyze")
    parser.add_argument("--start", default="2023-01-01", help="Start date for analysis")
    parser.add_argument("--end", default="2023-12-31", help="End date for analysis")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path to save the resulting decision JSON",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    meeting = InvestmentMeeting(symbols=args.symbols, start=args.start, end=args.end)
    decisions = meeting.run()
    if args.output:
        args.output.write_text(json.dumps(decisions, indent=2, ensure_ascii=False))
        print(f"Saved decisions to {args.output}")
    else:
        print(json.dumps(decisions, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
