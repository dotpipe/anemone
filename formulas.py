"""Production-ready formula utilities.

This module provides typed, validated implementations of small
formula functions previously kept as examples.
"""
from typing import Union

Number = Union[int, float]


def _ensure_number(x: Number, name: str) -> float:
    if not isinstance(x, (int, float)):
        raise TypeError(f"{name} must be a number (int or float)")
    return float(x)


def deltau(Q: Number, W: Number) -> float:
    """Compute ΔU = Q - W.

    Args:
        Q: Heat added (number).
        W: Work done (number).

    Returns:
        The change in internal energy as a float.
    """
    q = _ensure_number(Q, "Q")
    w = _ensure_number(W, "W")
    return q - w


def deltau_half(Q: Number, W: Number) -> float:
    """Compute (ΔU) / 2.

    Uses the validated `deltau` implementation.
    """
    return deltau(Q, W) / 2.0


def s(n: int) -> int:
    """Compute S = n*(n+1)/2 for non-negative integers.

    Args:
        n: Non-negative integer.

    Returns:
        The triangular number as an integer.
    """
    if not isinstance(n, int):
        raise TypeError("n must be an int")
    if n < 0:
        raise ValueError("n must be non-negative")
    return n * (n + 1) // 2


# User-friendly PascalCase wrappers kept for compatibility with examples
def FirstLawThermoDynamics(Q: Number, W: Number) -> float:
    """PascalCase wrapper for the First Law: returns ΔU = Q - W"""
    return deltau(Q, W)


def FirstLawThermoDynamics_half(Q: Number, W: Number) -> float:
    """Return (ΔU)/2 = (Q - W)/2"""
    return deltau_half(Q, W)


__all__ = [
    "deltau",
    "deltau_half",
    "s",
    "FirstLawThermoDynamics",
    "FirstLawThermoDynamics_half",
]
