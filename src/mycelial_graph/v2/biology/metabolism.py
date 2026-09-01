from __future__ import annotations

import numpy as np


def assert_budget_conserved(budget: np.ndarray, cap: float, atol: float = 1e-6) -> None:
    if not np.isfinite(budget).all():
        raise AssertionError("Budget contains non-finite values.")
    if abs(float(budget.sum()) - cap) > atol * max(1.0, cap):
        raise AssertionError(
            f"Budget conservation failed: sum={float(budget.sum())} cap={cap}"
        )
