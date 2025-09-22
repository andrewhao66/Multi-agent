"""Utility helpers for numeric operations that gracefully degrade without NumPy."""
from __future__ import annotations

from math import isfinite, sqrt, tanh
from typing import Iterable


def clamp(value: float, lower: float, upper: float) -> float:
    """Clamp ``value`` between ``lower`` and ``upper``.

    This mirrors ``numpy.clip`` but relies only on the standard library.
    """
    if value < lower:
        return lower
    if value > upper:
        return upper
    return value


def is_finite_number(value: float) -> bool:
    """Return ``True`` if ``value`` is a finite real number."""
    return isinstance(value, (int, float)) and isfinite(value)


def safe_mean(values: Iterable[float]) -> float:
    """Compute the arithmetic mean of ``values`` ignoring non-finite entries."""
    cleaned = [float(v) for v in values if is_finite_number(v)]
    if not cleaned:
        return 0.0
    return sum(cleaned) / len(cleaned)


__all__ = [
    "clamp",
    "is_finite_number",
    "safe_mean",
    "sqrt",
    "tanh",
]
