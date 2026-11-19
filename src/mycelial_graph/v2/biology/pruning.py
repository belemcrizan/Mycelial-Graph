from __future__ import annotations

from typing import Mapping

import numpy as np

from ..types import ControllerConfig


def prune_score(
    resource_burden: float,
    redundancy: float,
    fail_rate: float,
    marginal_utility: float,
) -> float:
    """Inefficiency evidence score combining resource burden, redundancy, failure, and net utility."""
    return float(resource_burden + redundancy + fail_rate - marginal_utility)


def update_prune_evidence(
    evidence: np.ndarray,
    observations: np.ndarray,
    scores: np.ndarray,
    config: ControllerConfig,
    enabled: bool,
    *,
    observed_edges: tuple[int, ...] | None = None,
    outgoing_map: Mapping[int, tuple[int, ...]] | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Observation-gated cytoplasmic retraction with strict connectivity preservation.

    - Evidence increments only when an edge is actually observed (if ``observed_edges`` is given),
      preventing phantom pruning during unvisited steps.
    - Evidence is capped at ``2 * prune_persistence`` so retracted corridors remain recoverable
      under subsequent environmental shifts.
    - When ``outgoing_map`` is supplied, at least one outgoing transition (lowest prune score)
      is guaranteed to remain active at every node so source->sink connectivity never collapses.
    """
    if not enabled:
        return np.zeros_like(evidence), np.zeros(len(evidence), dtype=bool)
    next_evidence = evidence.copy()
    observed_set = set(observed_edges) if observed_edges is not None else None
    max_evidence = max(config.prune_persistence * 2, config.prune_persistence + 1)

    for edge_id, score in enumerate(scores):
        if observations[edge_id] < config.min_prune_observations:
            continue
        if observed_set is None or edge_id in observed_set:
            if score > config.prune_threshold:
                next_evidence[edge_id] = min(max_evidence, int(next_evidence[edge_id]) + 1)
            else:
                next_evidence[edge_id] = max(0, int(next_evidence[edge_id]) - 1)

    pruned = next_evidence >= config.prune_persistence
    if outgoing_map is not None:
        for _, siblings in outgoing_map.items():
            if siblings and all(bool(pruned[eid]) for eid in siblings):
                best_keeper = min(siblings, key=lambda eid: float(scores[eid]))
                pruned[best_keeper] = False
                next_evidence[best_keeper] = max(0, config.prune_persistence - 1)
    return next_evidence, pruned
