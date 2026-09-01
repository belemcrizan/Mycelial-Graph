from __future__ import annotations

import numpy as np

from ..types import ControllerConfig, UtilityConfig


def routing_utility(
    quality: float,
    token_norm: float,
    cost_norm: float,
    latency_norm: float,
    risk: float,
    failed: float,
    state_norm: float,
    utility: UtilityConfig,
    cost_aware: bool,
) -> float:
    if not cost_aware:
        return float(quality)
    return float(
        quality
        - utility.lambda_tokens * token_norm
        - utility.lambda_cost * cost_norm
        - utility.lambda_latency * latency_norm
        - utility.lambda_risk * risk
        - utility.lambda_failure * failed
        - utility.lambda_state * state_norm
    )


def update_conductance(
    conductance: np.ndarray,
    edge_ids: tuple[int, ...],
    targets: np.ndarray,
    demand: np.ndarray,
    waste: np.ndarray,
    config: ControllerConfig,
    cord_enabled: bool,
) -> np.ndarray:
    updated = conductance * (1.0 - config.temporal_decay)
    demand_term = demand if cord_enabled else np.zeros_like(demand)
    for edge_id, target in zip(edge_ids, targets):
        updated[edge_id] += config.learning_rate * (float(target) - 0.5)
        updated[edge_id] += 0.05 * float(demand_term[edge_id])
        updated[edge_id] -= 0.08 * float(waste[edge_id])
    return np.clip(updated, config.minimum_conductance, config.maximum_conductance)
