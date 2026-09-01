from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MethodPoint:
    method: str
    quality: float
    tokens: float
    cost: float
    latency: float


def dominates(left: MethodPoint, right: MethodPoint, atol: float = 1e-12) -> bool:
    """True if left is at least as good on all inverted-cost axes and better on one."""
    not_worse = (
        left.quality + atol >= right.quality
        and left.tokens - atol <= right.tokens
        and left.cost - atol <= right.cost
        and left.latency - atol <= right.latency
    )
    better = (
        left.quality > right.quality + atol
        or left.tokens < right.tokens - atol
        or left.cost < right.cost - atol
        or left.latency < right.latency - atol
    )
    return not_worse and better


def nondominated(points: list[MethodPoint]) -> list[MethodPoint]:
    return [
        point
        for point in points
        if not any(dominates(other, point) for other in points if other.method != point.method)
    ]
