from __future__ import annotations

import numpy as np

from ..types import ControllerConfig


def prune_score(cost_norm: float, redundancy: float, fail_rate: float, marginal_utility: float) -> float:
    return float(cost_norm + redundancy + fail_rate - marginal_utility)


def update_prune_evidence(
    evidence: np.ndarray,
    observations: np.ndarray,
    scores: np.ndarray,
    config: ControllerConfig,
    enabled: bool,
) -> tuple[np.ndarray, np.ndarray]:
    if not enabled:
        return evidence, np.zeros(len(evidence), dtype=bool)
    next_evidence = evidence.copy()
    pruned = np.zeros(len(evidence), dtype=bool)
    for edge_id, score in enumerate(scores):
        if observations[edge_id] < config.min_prune_observations:
            continue
        if score > config.prune_threshold:
            next_evidence[edge_id] += 1
        else:
            next_evidence[edge_id] = max(0, next_evidence[edge_id] - 1)
        if next_evidence[edge_id] >= config.prune_persistence:
            pruned[edge_id] = True
    return next_evidence, pruned
