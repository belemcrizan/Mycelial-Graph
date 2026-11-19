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
    """Redistribute budget across corridors while conserving ``cap`` and honoring ``floor``.

    Uses exact floor-first surplus allocation: each corridor receives ``floor``, and only
    the remaining ``cap - n * floor`` is mixed toward normalized positive weights.
    """
    n = max(len(budget), 1)
    if cap <= 0.0 or len(budget) == 0:
        return np.zeros_like(budget, dtype=float)
    floor_frac = float(np.clip(config.floor_budget_fraction, 0.0, 0.95))
    floor = floor_frac * cap / n
    surplus = max(0.0, cap - floor * len(budget))
    if surplus <= 1e-12:
        return np.full(len(budget), cap / len(budget), dtype=float)

    prev_excess = np.maximum(budget.astype(float) - floor, 0.0)
    prev_sum = float(prev_excess.sum())
    if prev_sum > 1e-12:
        prev_surplus_alloc = surplus * (prev_excess / prev_sum)
    else:
        prev_surplus_alloc = np.full(len(budget), surplus / len(budget), dtype=float)

    if not enabled:
        return floor + prev_surplus_alloc

    positive = np.maximum(weights.astype(float), 1e-9)
    target_surplus_alloc = surplus * (positive / float(positive.sum()))
    mix = float(np.clip(config.transfer_mix, 0.0, 1.0))
    allocated = floor + (1.0 - mix) * prev_surplus_alloc + mix * target_surplus_alloc
    return allocated


def budget_l1_shift(before: np.ndarray, after: np.ndarray) -> float:
    return float(np.abs(after - before).sum() / 2.0)
