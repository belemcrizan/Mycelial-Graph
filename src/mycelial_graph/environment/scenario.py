from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np

from ..types import ExperimentConfig
from .graph import LayeredDAG


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    seed: int
    rho: float
    graph: LayeredDAG
    base_edge_means: np.ndarray
    post_edge_means: np.ndarray
    potential_rewards: np.ndarray
    optimal_pre_path: tuple[int, ...]
    optimal_post_path: tuple[int, ...]
    optimal_pre_utility: float
    optimal_post_utility: float
    shock_vector: np.ndarray
    shock_node: int
    interaction_edge: int
    pre_shock_steps: int
    post_shock_steps: int

    def expected_edge_rewards(self, step: int) -> np.ndarray:
        return self.base_edge_means if step < self.pre_shock_steps else self.post_edge_means

    def expected_path_utility(self, edge_ids: tuple[int, ...], step: int) -> float:
        return float(np.mean(self.expected_edge_rewards(step)[list(edge_ids)]))

    def realized_edge_rewards(self, edge_ids: tuple[int, ...], step: int) -> np.ndarray:
        return self.potential_rewards[step, list(edge_ids)].copy()

    def realized_path_utility(self, edge_ids: tuple[int, ...], step: int) -> float:
        return float(np.mean(self.realized_edge_rewards(edge_ids, step)))

    def oracle_expected_utility(self, step: int) -> float:
        return self.optimal_pre_utility if step < self.pre_shock_steps else self.optimal_post_utility

    def scientific_hash(self) -> str:
        payload = {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "rho": self.rho,
            "base": self.base_edge_means.round(12).tolist(),
            "post": self.post_edge_means.round(12).tolist(),
            "rewards": self.potential_rewards.round(12).tolist(),
            "pre_path": self.optimal_pre_path,
            "post_path": self.optimal_post_path,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


def _path_utilities(graph: LayeredDAG, edge_means: np.ndarray) -> list[tuple[float, tuple[int, ...]]]:
    scored = []
    for path in graph.all_paths():
        edge_ids = graph.path_edges(path)
        scored.append((float(np.mean(edge_means[list(edge_ids)])), path))
    return sorted(scored, key=lambda item: item[0], reverse=True)


def _normalised_pattern(size: int, indices: tuple[int, ...]) -> np.ndarray:
    pattern = np.zeros(size, dtype=float)
    pattern[list(indices)] = 1.0
    norm = float(np.linalg.norm(pattern))
    if norm == 0:
        raise ValueError("A shock pattern cannot be empty.")
    return pattern / norm


def generate_scenario_family(config: ExperimentConfig, seed: int) -> dict[float, Scenario]:
    """Generate a rho family sharing topology, base means, and potential noise.

    The node and interaction patterns have disjoint support, so the L2 norm of
    the total shock stays equal to ``shock_magnitude`` for every rho. A candidate
    base world is admitted only when every configured rho has certified optima.
    """
    graph = LayeredDAG.complete_layered(
        config.graph.internal_layers,
        config.graph.alternatives_per_layer,
    )
    root = np.random.SeedSequence(seed)
    parameter_ss, noise_ss = root.spawn(2)
    rng = np.random.default_rng(parameter_ss)
    noise_rng = np.random.default_rng(noise_ss)
    edge_count = len(graph.edges)

    for attempt in range(config.environment.max_generation_attempts):
        # A narrow range keeps alternatives competitive and makes recovery observable.
        base = np.clip(0.62 + rng.normal(0.0, 0.035, edge_count), 0.45, 0.80)
        pre_rank = _path_utilities(graph, base)
        pre_best, pre_path = pre_rank[0]
        if pre_best - pre_rank[1][0] < config.environment.optimum_margin:
            continue

        middle_index = 1 + config.graph.internal_layers // 2
        shock_node = pre_path[middle_index]
        node_support = graph.incident_edges(shock_node)
        pre_edges = graph.path_edges(pre_path)
        disjoint_pre_edges = tuple(edge for edge in pre_edges if edge not in node_support)
        if not disjoint_pre_edges:
            continue
        interaction_edge = disjoint_pre_edges[0]
        node_pattern = _normalised_pattern(edge_count, node_support)
        interaction_pattern = _normalised_pattern(edge_count, (interaction_edge,))
        candidates: dict[float, tuple[np.ndarray, np.ndarray, float, tuple[int, ...]]] = {}
        family_valid = True
        for rho in config.environment.rho_values:
            shock = -config.environment.shock_magnitude * (
                np.sqrt(rho) * node_pattern + np.sqrt(1.0 - rho) * interaction_pattern
            )
            post = np.clip(base + shock, 0.02, 0.98)
            if not np.allclose(post - base, shock, atol=1e-12, rtol=0.0):
                family_valid = False
                break
            post_rank = _path_utilities(graph, post)
            post_best, post_path = post_rank[0]
            if (
                post_path == pre_path
                or post_best - post_rank[1][0] < config.environment.optimum_margin
            ):
                family_valid = False
                break
            candidates[rho] = (shock, post, post_best, post_path)
        if not family_valid:
            continue

        noise = noise_rng.normal(
            0.0,
            config.environment.reward_noise_std,
            (config.horizon.total_steps, edge_count),
        )
        family: dict[float, Scenario] = {}
        for rho, (shock, post, post_best, post_path) in candidates.items():
            expected = np.vstack(
                [
                    np.repeat(base[None, :], config.horizon.pre_shock_steps, axis=0),
                    np.repeat(post[None, :], config.horizon.post_shock_steps, axis=0),
                ]
            )
            potential = np.clip(expected + noise, 0.0, 1.0)
            scenario_id = f"{config.experiment_id}-rho{rho:.2f}-seed{seed}"
            family[rho] = Scenario(
                scenario_id=scenario_id,
                seed=seed,
                rho=rho,
                graph=graph,
                base_edge_means=base.copy(),
                post_edge_means=post,
                potential_rewards=potential,
                optimal_pre_path=pre_path,
                optimal_post_path=post_path,
                optimal_pre_utility=pre_best,
                optimal_post_utility=post_best,
                shock_vector=shock,
                shock_node=shock_node,
                interaction_edge=interaction_edge,
                pre_shock_steps=config.horizon.pre_shock_steps,
                post_shock_steps=config.horizon.post_shock_steps,
            )
        return family
    raise RuntimeError(
        f"Could not generate a certified scenario family after "
        f"{config.environment.max_generation_attempts} attempts."
    )


def generate_scenario(config: ExperimentConfig, seed: int, rho: float) -> Scenario:
    if rho not in config.environment.rho_values:
        raise ValueError(f"rho={rho} is not part of the configured frozen grid.")
    return generate_scenario_family(config, seed)[rho]
