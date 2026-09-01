from __future__ import annotations

import numpy as np

from ..types import ControllerConfig


def translocate(
    budget: np.ndarray,
    weights: np.ndarray,
    cap: float,
    config: ControllerConfig,
    enabled: bool,
) -> np.ndarray:
    """Move budget toward weight shares while conserving the current cap."""
    n = max(len(budget), 1)
    floor = config.floor_budget_fraction * cap / n
    if cap <= 0:
        return np.zeros_like(budget)
    if enabled:
        positive = np.maximum(weights, 1e-9)
        share = cap * positive / positive.sum()
        mixed = (1.0 - config.transfer_mix) * budget + config.transfer_mix * share
    else:
        mixed = budget.copy()
    mixed = np.maximum(mixed, floor)
    mixed *= cap / mixed.sum()
    return mixed


def budget_l1_shift(before: np.ndarray, after: np.ndarray) -> float:
    return float(np.abs(after - before).sum() / 2.0)
