from __future__ import annotations

import numpy as np

from ..types import DecisionRecord, HorizonConfig


def sustained_recovery_time(
    records: list[DecisionRecord],
    horizon: HorizonConfig,
) -> tuple[int | None, int, bool]:
    post = records[horizon.pre_shock_steps :]
    utilities = np.array([record.expected_utility for record in post], dtype=float)
    oracle = np.array([record.oracle_expected_utility for record in post], dtype=float)
    ratios = np.divide(utilities, oracle, out=np.zeros_like(utilities), where=oracle > 0)
    trailing = horizon.recovery_trailing_window
    confirmation = horizon.recovery_confirmation_window
    threshold = horizon.recovery_utility_fraction

    moving = np.full(len(ratios), np.nan, dtype=float)
    for end in range(trailing - 1, len(ratios)):
        moving[end] = float(np.mean(ratios[end - trailing + 1 : end + 1]))
    for end in range(trailing - 1, len(ratios) - confirmation + 1):
        confirmation_slice = moving[end : end + confirmation]
        if np.all(np.isfinite(confirmation_slice)) and np.all(confirmation_slice >= threshold):
            recovery_time = end + 1
            return recovery_time, recovery_time, True
    return None, horizon.post_shock_steps, False


def post_shock_dynamic_regret(records: list[DecisionRecord], horizon: HorizonConfig) -> float:
    post = records[horizon.pre_shock_steps :]
    return float(
        sum(max(record.oracle_expected_utility - record.expected_utility, 0.0) for record in post)
    )

