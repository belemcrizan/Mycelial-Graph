from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BootstrapResult:
    estimate: float
    confidence_low: float
    confidence_high: float
    one_sided_upper_bound: float
    bootstrap_tail_probability: float
    samples: int


def paired_relative_effect(
    treatment: np.ndarray,
    control: np.ndarray,
    bootstrap_samples: int,
    confidence_level: float,
    seed: int = 20260824,
    null_margin: float = 0.0,
) -> BootstrapResult:
    if treatment.shape != control.shape or treatment.ndim != 1:
        raise ValueError("Paired samples must be one-dimensional and have equal shape.")
    if len(treatment) < 2:
        raise ValueError("At least two paired trials are required.")
    estimate = float((np.mean(treatment) - np.mean(control)) / np.mean(control))
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(treatment), size=(bootstrap_samples, len(treatment)))
    treatment_means = np.mean(treatment[indices], axis=1)
    control_means = np.mean(control[indices], axis=1)
    effects = np.divide(
        treatment_means - control_means,
        control_means,
        out=np.zeros_like(treatment_means),
        where=control_means != 0,
    )
    alpha = 1.0 - confidence_level
    low, high = np.quantile(effects, [alpha / 2.0, 1.0 - alpha / 2.0])
    upper = float(np.quantile(effects, confidence_level))
    tail_probability = float(
        (np.count_nonzero(effects >= null_margin) + 1) / (len(effects) + 1)
    )
    return BootstrapResult(
        estimate=estimate,
        confidence_low=float(low),
        confidence_high=float(high),
        one_sided_upper_bound=upper,
        bootstrap_tail_probability=tail_probability,
        samples=bootstrap_samples,
    )
