from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

import numpy as np

from ...environment.graph import LayeredDAG
from ..ledger import ResourceObservation, TokenUsage
from ..types import V2ExperimentConfig
from .roles import (
    MODEL_LAYER,
    RETRIEVER_LAYER,
    VERIFY_LAYER,
    alternative_index,
    edge_role,
    layer_index,
)


DIFFICULTY_QUALITY = {
    "easy": (0.80, 0.83, 0.85),
    "medium": (0.58, 0.76, 0.86),
    "hard": (0.38, 0.64, 0.88),
    "very_hard": (0.28, 0.52, 0.90),
    "unknown": (0.50, 0.70, 0.84),
}

TOKEN_BY_CLASS = (90.0, 240.0, 920.0)
PRICE_BY_CLASS = (0.04, 0.18, 2.40)
LATENCY_BY_CLASS = (80.0, 220.0, 900.0)
FAIL_BY_CLASS = (0.08, 0.05, 0.04)
RETRIEVAL_TOKENS = (40.0, 90.0, 180.0)
VERIFY_TOKENS = (8.0, 140.0, 320.0)
VERIFY_QUALITY_LIFT = (0.00, 0.04, 0.07)


def _difficulty_for_seed(rng: np.random.Generator) -> str:
    return str(rng.choice(["easy", "medium", "hard"]))


@dataclass(frozen=True)
class ResourceScenario:
    scenario_id: str
    seed: int
    regime: str
    difficulty: str
    graph: LayeredDAG
    quality_means_pre: np.ndarray
    quality_means_post: np.ndarray
    token_means_pre: np.ndarray
    token_means_post: np.ndarray
    latency_means_pre: np.ndarray
    latency_means_post: np.ndarray
    fail_pre: np.ndarray
    fail_post: np.ndarray
    price_pre: np.ndarray
    price_post: np.ndarray
    quality_outcomes: np.ndarray
    token_outcomes: np.ndarray
    latency_outcomes: np.ndarray
    fail_uniforms: np.ndarray
    optimal_pre_path: tuple[int, ...]
    optimal_post_path: tuple[int, ...]
    optimal_pre_quality: float
    optimal_post_quality: float
    pre_shock_steps: int
    post_shock_steps: int
    budget_pre: int
    budget_post: int

    def quality_means(self, step: int) -> np.ndarray:
        return self.quality_means_pre if step < self.pre_shock_steps else self.quality_means_post

    def token_means(self, step: int) -> np.ndarray:
        return self.token_means_pre if step < self.pre_shock_steps else self.token_means_post

    def price(self, step: int) -> np.ndarray:
        return self.price_pre if step < self.pre_shock_steps else self.price_post

    def fail_prob(self, step: int) -> np.ndarray:
        return self.fail_pre if step < self.pre_shock_steps else self.fail_post

    def budget_cap(self, step: int) -> int:
        return self.budget_pre if step < self.pre_shock_steps else self.budget_post

    def expected_path_quality(self, edge_ids: tuple[int, ...], step: int) -> float:
        return float(np.mean(self.quality_means(step)[list(edge_ids)]))

    def oracle_quality(self, step: int) -> float:
        return self.optimal_pre_quality if step < self.pre_shock_steps else self.optimal_post_quality

    def observations(
        self, edge_ids: tuple[int, ...], step: int
    ) -> list[ResourceObservation]:
        observations = []
        for edge_id in edge_ids:
            tokens = int(self.token_outcomes[step, edge_id])
            usage = _usage_for_edge(self.graph, edge_id, tokens)
            quality = float(self.quality_outcomes[step, edge_id])
            success = bool(self.fail_uniforms[step, edge_id] >= self.fail_prob(step)[edge_id])
            if not success:
                quality *= 0.25
            price = float(self.price(step)[edge_id])
            monetary = (usage.total_tokens / 1000.0) * price
            observations.append(
                ResourceObservation(
                    edge_id=edge_id,
                    token_usage=usage,
                    latency_ms=float(self.latency_outcomes[step, edge_id]),
                    monetary_cost=monetary,
                    success=success,
                    quality=quality,
                    uncertainty=0.0,
                )
            )
        return observations

    def scientific_hash(self) -> str:
        payload = {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "regime": self.regime,
            "difficulty": self.difficulty,
            "q_pre": self.quality_means_pre.round(12).tolist(),
            "q_post": self.quality_means_post.round(12).tolist(),
            "tokens": self.token_outcomes.tolist(),
            "quality": self.quality_outcomes.round(12).tolist(),
            "pre_path": self.optimal_pre_path,
            "post_path": self.optimal_post_path,
            "budget_pre": self.budget_pre,
            "budget_post": self.budget_post,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return hashlib.sha256(encoded).hexdigest()


def _usage_for_edge(graph: LayeredDAG, edge_id: int, tokens: int) -> TokenUsage:
    role = edge_role(graph, edge_id)
    tokens = max(0, tokens)
    if role == "retrieval":
        return TokenUsage(retrieval_tokens=tokens)
    if role == "verification":
        return TokenUsage(verification_tokens=tokens)
    if role == "model":
        input_tokens = int(round(tokens * 0.35))
        reasoning = int(round(tokens * 0.25))
        output_tokens = max(0, tokens - input_tokens - reasoning)
        return TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            reasoning_tokens=reasoning,
        )
    return TokenUsage(summarization_tokens=tokens)


def _path_quality(graph: LayeredDAG, quality: np.ndarray) -> list[tuple[float, tuple[int, ...]]]:
    scored = []
    for path in graph.all_paths():
        edge_ids = graph.path_edges(path)
        scored.append((float(np.mean(quality[list(edge_ids)])), path))
    return sorted(scored, key=lambda item: item[0], reverse=True)


def _base_attributes(
    graph: LayeredDAG, difficulty: str
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n_edges = len(graph.edges)
    quality = np.zeros(n_edges)
    tokens = np.zeros(n_edges)
    latency = np.zeros(n_edges)
    fail = np.zeros(n_edges)
    price = np.zeros(n_edges)
    q_model = DIFFICULTY_QUALITY[difficulty]
    for edge in graph.edges:
        role = edge_role(graph, edge.id)
        alt = alternative_index(graph, edge.target) if layer_index(graph, edge.target) not in {0, len(graph.layers) - 1} else 0
        alt = min(alt, 2)
        if role == "retrieval":
            quality[edge.id] = 0.70 + 0.04 * alt
            tokens[edge.id] = RETRIEVAL_TOKENS[alt]
            latency[edge.id] = 40.0 + 40.0 * alt
            fail[edge.id] = 0.03
            price[edge.id] = 0.02
        elif role == "model":
            quality[edge.id] = q_model[alt]
            tokens[edge.id] = TOKEN_BY_CLASS[alt]
            latency[edge.id] = LATENCY_BY_CLASS[alt]
            fail[edge.id] = FAIL_BY_CLASS[alt]
            price[edge.id] = PRICE_BY_CLASS[alt]
        elif role == "verification":
            quality[edge.id] = 0.62 + VERIFY_QUALITY_LIFT[alt]
            tokens[edge.id] = VERIFY_TOKENS[alt]
            latency[edge.id] = 20.0 + 80.0 * alt
            fail[edge.id] = 0.02 if alt else 0.06
            price[edge.id] = 0.10 if alt else 0.0
        else:
            quality[edge.id] = 0.70
            tokens[edge.id] = 5.0
            latency[edge.id] = 10.0
            fail[edge.id] = 0.01
            price[edge.id] = 0.0
    return quality, tokens, latency, fail, price


def _apply_regime(
    graph: LayeredDAG,
    regime: str,
    quality: np.ndarray,
    tokens: np.ndarray,
    latency: np.ndarray,
    fail: np.ndarray,
    price: np.ndarray,
    magnitude: float,
    budget_pre: int,
    scarce: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, int]:
    q, t, ltn, f, p = quality.copy(), tokens.copy(), latency.copy(), fail.copy(), price.copy()
    budget_post = budget_pre
    frontier_model = [
        edge.id
        for edge in graph.edges
        if edge_role(graph, edge.id) == "model" and alternative_index(graph, edge.target) == 2
    ]
    if regime == "STATIC":
        return q, t, ltn, f, p, budget_post
    if regime == "DRIFT":
        q[frontier_model] -= 0.12 * magnitude
        p[frontier_model] *= 1.0 + 0.5 * magnitude
        return q, t, ltn, f, p, budget_post
    if regime == "PRICE_SHOCK":
        p[frontier_model] *= 1.0 + 3.5 * magnitude
        return q, t, ltn, f, p, budget_post
    if regime == "QUALITY_SHOCK":
        q[frontier_model] = np.clip(q[frontier_model] - 0.45 * magnitude, 0.02, 0.98)
        return q, t, ltn, f, p, budget_post
    if regime == "LATENCY_SHOCK":
        ltn[frontier_model] *= 1.0 + 4.0 * magnitude
        return q, t, ltn, f, p, budget_post
    if regime in {"OUTAGE", "CORRELATED_PROVIDER_FAILURE"}:
        q[frontier_model] = 0.05
        f[frontier_model] = 0.92
        return q, t, ltn, f, p, budget_post
    if regime == "RESOURCE_SCARCITY":
        budget_post = scarce
        return q, t, ltn, f, p, budget_post
    if regime == "MIXED_SHOCK":
        p[frontier_model] *= 1.0 + 2.5 * magnitude
        q[frontier_model] = np.clip(q[frontier_model] - 0.25 * magnitude, 0.02, 0.98)
        return q, t, ltn, f, p, budget_post
    if regime == "BURST_LOAD":
        t *= 1.0 + 0.8 * magnitude
        ltn *= 1.0 + 0.6 * magnitude
        return q, t, ltn, f, p, budget_post
    if regime == "ADVERSARIAL_COST":
        p *= 1.0 + 2.0 * magnitude
        t *= 1.0 + 0.4 * magnitude
        return q, t, ltn, f, p, budget_post
    if regime == "TASK_DIFFICULTY_SHIFT":
        q = np.clip(q - 0.18, 0.02, 0.98)
        return q, t, ltn, f, p, budget_post
    raise ValueError(f"Unknown regime: {regime}")


def generate_resource_scenario(
    config: V2ExperimentConfig, seed: int, regime: str
) -> ResourceScenario:
    graph = LayeredDAG.complete_layered(
        config.graph.internal_layers,
        config.graph.alternatives_per_layer,
    )
    root = np.random.SeedSequence(seed)
    parameter_ss, noise_ss = root.spawn(2)
    param_rng = np.random.default_rng(parameter_ss)
    noise_rng = np.random.default_rng(noise_ss)
    difficulty = _difficulty_for_seed(param_rng)
    n_edges = len(graph.edges)
    steps = config.horizon.total_steps

    quality_pre, token_pre, latency_pre, fail_pre, price_pre = _base_attributes(graph, difficulty)
    quality_pre = np.clip(quality_pre + param_rng.normal(0.0, 0.01, n_edges), 0.05, 0.95)

    quality_post, token_post, latency_post, fail_post, price_post, budget_post = _apply_regime(
        graph,
        regime,
        quality_pre,
        token_pre,
        latency_pre,
        fail_pre,
        price_pre,
        config.environment.shock_magnitude,
        config.resources.global_budget_tokens,
        config.resources.scarce_budget_tokens,
    )

    pre_rank = _path_quality(graph, quality_pre)
    post_rank = _path_quality(graph, quality_post)
    pre_best, pre_path = pre_rank[0]
    post_best, post_path = post_rank[0]

    q_noise = noise_rng.normal(0.0, config.environment.quality_noise_std, (steps, n_edges))
    t_noise = noise_rng.normal(0.0, config.environment.token_noise_std, (steps, n_edges))
    l_noise = noise_rng.normal(0.0, config.environment.latency_noise_std, (steps, n_edges))
    fail_u = noise_rng.random((steps, n_edges))

    expected_q = np.vstack(
        [
            np.repeat(quality_pre[None, :], config.horizon.pre_shock_steps, axis=0),
            np.repeat(quality_post[None, :], config.horizon.post_shock_steps, axis=0),
        ]
    )
    expected_t = np.vstack(
        [
            np.repeat(token_pre[None, :], config.horizon.pre_shock_steps, axis=0),
            np.repeat(token_post[None, :], config.horizon.post_shock_steps, axis=0),
        ]
    )
    expected_l = np.vstack(
        [
            np.repeat(latency_pre[None, :], config.horizon.pre_shock_steps, axis=0),
            np.repeat(latency_post[None, :], config.horizon.post_shock_steps, axis=0),
        ]
    )
    quality_outcomes = np.clip(expected_q + q_noise, 0.0, 1.0)
    token_outcomes = np.clip(np.round(expected_t * (1.0 + t_noise)), 1, 20000).astype(int)
    latency_outcomes = np.clip(expected_l * (1.0 + l_noise), 1.0, 20000.0)

    return ResourceScenario(
        scenario_id=f"{config.experiment_id}-{regime}-seed{seed}",
        seed=seed,
        regime=regime,
        difficulty=difficulty,
        graph=graph,
        quality_means_pre=quality_pre,
        quality_means_post=quality_post,
        token_means_pre=token_pre,
        token_means_post=token_post,
        latency_means_pre=latency_pre,
        latency_means_post=latency_post,
        fail_pre=fail_pre,
        fail_post=fail_post,
        price_pre=price_pre,
        price_post=price_post,
        quality_outcomes=quality_outcomes,
        token_outcomes=token_outcomes,
        latency_outcomes=latency_outcomes,
        fail_uniforms=fail_u,
        optimal_pre_path=pre_path,
        optimal_post_path=post_path,
        optimal_pre_quality=pre_best,
        optimal_post_quality=post_best,
        pre_shock_steps=config.horizon.pre_shock_steps,
        post_shock_steps=config.horizon.post_shock_steps,
        budget_pre=config.resources.global_budget_tokens,
        budget_post=budget_post,
    )


# Silence unused role constants if graph depth differs; they document the intended mapping.
_ = (RETRIEVER_LAYER, MODEL_LAYER, VERIFY_LAYER)
