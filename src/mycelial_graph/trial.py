"""Immutable, pre-generated potential outcomes for fair policy comparison."""

from __future__ import annotations

import gzip
import hashlib
import json
import math
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .graph import Edge, HardPolicy, LayeredGraph


def _clip(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _stable_seed(*parts: object) -> int:
    payload = "|".join(str(part) for part in parts).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


@dataclass(frozen=True)
class LocalObservation:
    edge_id: str
    component_id: str
    quality: float
    latency_ms: float
    cost_usd: float
    failure: float
    load: float
    scored: bool


@dataclass(frozen=True)
class PathMetrics:
    quality: float
    latency_ms: float
    cost_usd: float
    failure: float
    load: float
    success: bool
    utility: float


class FrozenTrial:
    """A trial contains outcomes for every edge and time, but reveals only traversed edges."""

    def __init__(
        self,
        seed: int,
        graph: LayeredGraph,
        config: dict[str, Any],
        observations: dict[tuple[int, str], LocalObservation],
    ) -> None:
        self.seed = seed
        self.graph = graph
        self.config = config
        self._observations = observations
        self.steps = int(config["experiment"]["steps"])
        self.shock_step = int(config["experiment"]["shock_step"])
        self.digest = self._compute_digest()
        self.certification: dict[str, Any] = {}

    @classmethod
    def generate(cls, graph: LayeredGraph, config: dict[str, Any], seed: int) -> "FrozenTrial":
        observations: dict[tuple[int, str], LocalObservation] = {}
        for step in range(int(config["experiment"]["steps"])):
            for edge in graph.edges.values():
                observations[(step, edge.id)] = cls._sample_observation(
                    graph, edge, config, seed, step
                )
        trial = cls(seed, graph, config, observations)
        trial.certification = certify_trial(trial, HardPolicy.from_config(config["policy"]))
        return trial

    @staticmethod
    def _base_values(graph: LayeredGraph, edge: Edge, config: dict[str, Any], step: int) -> tuple[float, ...]:
        component = graph.components[edge.target]
        quality = component.quality
        latency = component.latency_ms
        cost = component.cost_usd
        reliability = component.reliability
        load = component.load
        shock = config["shock"]
        if step >= int(config["experiment"]["shock_step"]) and component.id == shock["component"]:
            quality *= float(shock["quality_multiplier"])
            latency *= float(shock["latency_multiplier"])
            cost *= float(shock["cost_multiplier"])
            reliability *= float(shock["reliability_multiplier"])
            load = max(load, float(shock["minimum_load"]))
        return quality, latency, cost, _clip(reliability, 0.0, 1.0), load

    @classmethod
    def _sample_observation(
        cls,
        graph: LayeredGraph,
        edge: Edge,
        config: dict[str, Any],
        seed: int,
        step: int,
    ) -> LocalObservation:
        component = graph.components[edge.target]
        quality, latency, cost, reliability, load = cls._base_values(graph, edge, config, step)
        if not component.scored:
            return LocalObservation(edge.id, component.id, 1.0, 0.0, 0.0, 0.0, 0.0, False)
        rng = random.Random(_stable_seed(seed, step, edge.id))
        quality = _clip(quality + rng.gauss(0.0, 0.025), 0.0, 1.0)
        latency = max(0.0, latency * math.exp(rng.gauss(0.0, 0.08)))
        cost = max(0.0, cost * math.exp(rng.gauss(0.0, 0.03)))
        failure = 1.0 if rng.random() > reliability else 0.0
        load = _clip(load + rng.gauss(0.0, 0.04), 0.0, 1.0)
        return LocalObservation(edge.id, component.id, quality, latency, cost, failure, load, True)

    def observation(self, step: int, edge_id: str) -> LocalObservation:
        return self._observations[(step, edge_id)]

    def observations_for(self, step: int, edge_ids: Iterable[str]) -> tuple[LocalObservation, ...]:
        return tuple(self.observation(step, edge_id) for edge_id in edge_ids)

    def expected_observation(self, step: int, edge_id: str) -> LocalObservation:
        edge = self.graph.edges[edge_id]
        component = self.graph.components[edge.target]
        quality, latency, cost, reliability, load = self._base_values(
            self.graph, edge, self.config, step
        )
        return LocalObservation(
            edge.id,
            component.id,
            quality,
            latency,
            cost,
            1.0 - reliability,
            load,
            component.scored,
        )

    def expected_for(self, step: int, edge_ids: Iterable[str]) -> tuple[LocalObservation, ...]:
        return tuple(self.expected_observation(step, edge_id) for edge_id in edge_ids)

    def _compute_digest(self) -> str:
        digest = hashlib.sha256()
        digest.update(str(self.seed).encode("ascii"))
        for key in sorted(self._observations):
            payload = json.dumps(asdict(self._observations[key]), sort_keys=True, separators=(",", ":"))
            digest.update(payload.encode("utf-8"))
        return digest.hexdigest()

    def save(self, path: str | Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "mycelial-graph-frozen-trial-v0",
            "seed": self.seed,
            "steps": self.steps,
            "shock_step": self.shock_step,
            "digest": self.digest,
            "certification": self.certification,
            "observations": [
                {"step": step, **asdict(observation)}
                for (step, _), observation in sorted(self._observations.items())
            ],
        }
        with gzip.open(target, "wt", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, separators=(",", ":"))
        return target


def local_reward(observation: LocalObservation, config: dict[str, Any]) -> float:
    if not observation.scored:
        return 0.0
    weights = config["reward"]
    exp = config["experiment"]
    latency = min(1.0, observation.latency_ms / float(exp["latency_normalizer_ms"]))
    cost = min(1.0, observation.cost_usd / float(exp["cost_normalizer_usd"]))
    return (
        float(weights["quality"]) * observation.quality
        - float(weights["latency"]) * latency
        - float(weights["cost"]) * cost
        - float(weights["failure"]) * observation.failure
        - float(weights["load"]) * observation.load
    )


def aggregate_path(
    observations: Iterable[LocalObservation],
    config: dict[str, Any],
    *,
    expected: bool = False,
) -> PathMetrics:
    scored = [observation for observation in observations if observation.scored]
    if not scored:
        raise ValueError("a path must contain at least one scored component")
    quality = sum(item.quality for item in scored) / len(scored)
    latency = sum(item.latency_ms for item in scored)
    cost = sum(item.cost_usd for item in scored)
    load = sum(item.load for item in scored) / len(scored)
    if expected:
        survival = math.prod(1.0 - item.failure for item in scored)
        failure = 1.0 - survival
    else:
        failure = max(item.failure for item in scored)
    exp = config["experiment"]
    # Fixed-length V0 paths use the mean of edge-local utilities. This keeps the
    # common evaluation objective aligned with the information available to a
    # local router while success and CPST remain end-to-end task metrics.
    utility = sum(local_reward(item, config) for item in scored) / len(scored)
    success = (
        failure < 0.5
        and quality >= float(exp["quality_threshold"])
        and latency <= float(exp["latency_sla_ms"])
    )
    return PathMetrics(quality, latency, cost, failure, load, success, utility)


def oracle_path(
    trial: FrozenTrial,
    step: int,
    policy: HardPolicy,
) -> tuple[tuple[str, ...], PathMetrics]:
    candidates = trial.graph.all_paths(policy)
    scored = [
        (path, aggregate_path(trial.expected_for(step, path), trial.config, expected=True))
        for path in candidates
    ]
    return max(scored, key=lambda item: (item[1].utility, item[0]))


def certify_trial(trial: FrozenTrial, policy: HardPolicy) -> dict[str, Any]:
    """Admit only trials with unique, separated pre/post optima and a real local change."""

    def rank(step: int) -> list[tuple[tuple[str, ...], PathMetrics]]:
        rows = [
            (path, aggregate_path(trial.expected_for(step, path), trial.config, expected=True))
            for path in trial.graph.all_paths(policy)
        ]
        return sorted(rows, key=lambda item: (item[1].utility, item[0]), reverse=True)

    before = rank(max(0, trial.shock_step - 1))
    after = rank(trial.shock_step)
    minimum_margin = float(trial.config["experiment"]["minimum_oracle_margin"])
    pre_margin = before[0][1].utility - before[1][1].utility
    post_margin = after[0][1].utility - after[1][1].utility
    if pre_margin < minimum_margin or post_margin < minimum_margin:
        raise ValueError(
            "trial rejected: oracle margin below minimum "
            f"(pre={pre_margin:.6f}, post={post_margin:.6f}, required={minimum_margin:.6f})"
        )
    shock_component = trial.config["shock"]["component"]
    pre_nodes = trial.graph.node_path(before[0][0])
    post_nodes = trial.graph.node_path(after[0][0])
    if shock_component not in pre_nodes:
        raise ValueError("trial rejected: the shocked component is not on the pre-shock optimum")
    if shock_component in post_nodes:
        raise ValueError("trial rejected: the shocked component remains on the post-shock optimum")
    shared = len(set(before[0][0]) & set(after[0][0])) / len(before[0][0])
    return {
        "pre_oracle_edges": list(before[0][0]),
        "post_oracle_edges": list(after[0][0]),
        "pre_oracle_nodes": list(pre_nodes),
        "post_oracle_nodes": list(post_nodes),
        "pre_oracle_utility": before[0][1].utility,
        "post_oracle_utility": after[0][1].utility,
        "pre_oracle_margin": pre_margin,
        "post_oracle_margin": post_margin,
        "shared_edge_fraction": shared,
        "shock_component_moves_out_of_optimum": True,
    }
