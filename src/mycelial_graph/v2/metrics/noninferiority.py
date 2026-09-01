from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class AbsoluteBootstrap:
    estimate: float
    confidence_low: float
    confidence_high: float
    one_sided_lower_bound: float
    one_sided_upper_bound: float
    samples: int


def paired_absolute_effect(
    treatment: np.ndarray,
    control: np.ndarray,
    bootstrap_samples: int,
    confidence_level: float,
    seed: int = 20260831,
) -> AbsoluteBootstrap:
    if treatment.shape != control.shape or treatment.ndim != 1 or len(treatment) < 2:
        raise ValueError("Paired samples must be 1-D and have at least two pairs.")
    estimate = float(np.mean(treatment) - np.mean(control))
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(treatment), size=(bootstrap_samples, len(treatment)))
    effects = np.mean(treatment[indices], axis=1) - np.mean(control[indices], axis=1)
    alpha = 1.0 - confidence_level
    low, high = np.quantile(effects, [alpha / 2.0, 1.0 - alpha / 2.0])
    return AbsoluteBootstrap(
        estimate=estimate,
        confidence_low=float(low),
        confidence_high=float(high),
        one_sided_lower_bound=float(np.quantile(effects, 1.0 - confidence_level)),
        one_sided_upper_bound=float(np.quantile(effects, confidence_level)),
        samples=bootstrap_samples,
    )
