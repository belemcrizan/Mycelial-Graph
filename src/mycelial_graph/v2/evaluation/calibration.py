from __future__ import annotations

import numpy as np


def brier_score(probabilities: np.ndarray, outcomes: np.ndarray) -> float:
    if len(probabilities) == 0:
        return float("nan")
    return float(np.mean((probabilities - outcomes) ** 2))


def expected_calibration_error(
    probabilities: np.ndarray,
    outcomes: np.ndarray,
    bins: int = 10,
) -> float:
    if len(probabilities) == 0:
        return float("nan")
    probabilities = np.clip(np.asarray(probabilities, dtype=float), 0.0, 1.0)
    outcomes = np.asarray(outcomes, dtype=float)
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    n = len(probabilities)
    for low, high in zip(edges[:-1], edges[1:]):
        mask = (probabilities >= low) & (probabilities < high if high < 1.0 else probabilities <= high)
        if not np.any(mask):
            continue
        acc = float(np.mean(outcomes[mask]))
        conf = float(np.mean(probabilities[mask]))
        ece += (float(np.count_nonzero(mask)) / n) * abs(acc - conf)
    return float(ece)


def ranking_accuracy(predicted: np.ndarray, observed: np.ndarray) -> float:
    """Fraction of pairs with concordant sign of additional-compute benefit."""
    if len(predicted) == 0:
        return float("nan")
    pred_pos = predicted > 0
    obs_pos = observed > 0
    return float(np.mean(pred_pos == obs_pos))
