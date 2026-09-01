from __future__ import annotations

import numpy as np

from ...types import HorizonConfig


def sustained_quality_recovery(
    expected_quality: list[float],
    oracle: list[float],
    horizon: HorizonConfig,
) -> tuple[int | None, int, bool]:
    post_q = np.array(expected_quality[horizon.pre_shock_steps :], dtype=float)
    post_o = np.array(oracle[horizon.pre_shock_steps :], dtype=float)
    ratios = np.divide(post_q, post_o, out=np.zeros_like(post_q), where=post_o > 0)
    trailing = horizon.recovery_trailing_window
    confirmation = horizon.recovery_confirmation_window
    threshold = horizon.recovery_utility_fraction
    moving = np.full(len(ratios), np.nan)
    for end in range(trailing - 1, len(ratios)):
        moving[end] = float(np.mean(ratios[end - trailing + 1 : end + 1]))
    for end in range(trailing - 1, len(ratios) - confirmation + 1):
        window = moving[end : end + confirmation]
        if np.all(np.isfinite(window)) and np.all(window >= threshold):
            recovery = end + 1
            return recovery, recovery, True
    return None, horizon.post_shock_steps, False
