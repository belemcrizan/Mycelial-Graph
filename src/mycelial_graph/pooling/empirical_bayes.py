"""James–Stein / empirical-Bayes shrinkage for the isolated pooling protocol.

This module is not a V1 method. It must not be imported by MG-EXP-V1 runners.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ShrinkageState:
    grand_mean: float
    between_var: float
    within_var: float
    lambdas: np.ndarray
    pooled_means: np.ndarray


def james_stein_means(observations: np.ndarray, known_var: float) -> ShrinkageState:
    """observations: shape (K, n) Gaussian samples around arm means.

    CLASSIFICATION: this is a standard positive-part James–Stein estimator for
    known observation variance, not a theorem about Mycelial recovery time.
    """
    if observations.ndim != 2:
        raise ValueError("observations must have shape (K, n)")
    k, n = observations.shape
    if k < 3:
        raise ValueError("James–Stein requires K>=3.")
    if n < 1 or known_var <= 0:
        raise ValueError("Need n>=1 and known_var>0.")
    means = observations.mean(axis=1)
    grand = float(means.mean())
    centered = means - grand
    ss = float(np.dot(centered, centered))
    sigma2 = known_var / n
    shrink = min(1.0, max(0.0, 1.0 - ((k - 2) * sigma2) / max(ss, 1e-18)))
    lambdas = np.full(k, shrink)
    pooled = grand + (1.0 - shrink) * centered
    residual = observations - means[:, None]
    within = float(residual.var(ddof=1)) if observations.size > k else known_var
    between = max(0.0, float(means.var(ddof=1)) - sigma2)
    return ShrinkageState(grand, between, within, lambdas, pooled)


def pooling_weight_from_variances(between_var: float, within_var: float) -> float:
    """Classic random-effects weight toward the grand mean: within / (within + between).

    High between-edge variance -> less pooling (weight toward local).
    """
    if within_var < 0 or between_var < 0:
        raise ValueError("variances must be non-negative")
    denom = within_var + between_var
    if denom == 0:
        return 0.5
    return float(within_var / denom)
