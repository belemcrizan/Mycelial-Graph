"""Frozen V0 routing policies.

The Mycelial policy updates only traversed edges from local feedback. The two
reference baselines are intentionally transparent engineering comparators; they
are not claimed to be publication-grade implementations.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Iterable

from .graph import Edge, HardPolicy, LayeredGraph
from .trial import LocalObservation, local_reward


@dataclass(frozen=True)
class Choice:
    edge_id: str
    mode: str


@dataclass(frozen=True)
class Decision:
    edge_ids: tuple[str, ...]
    choices: tuple[Choice, ...]
    primitive_operations: int


class Router:
    name = "router"

    def select(self, step: int, rng: random.Random) -> Decision:
        raise NotImplementedError

    def observe(
        self,
        step: int,
        decision: Decision,
        observations: Iterable[LocalObservation],
    ) -> None:
        raise NotImplementedError


def _weighted_choice(edges: tuple[Edge, ...], scores: list[float], rng: random.Random) -> Edge:
    maximum = max(scores)
    weights = [math.exp(score - maximum) for score in scores]
    threshold = rng.random() * sum(weights)
    cumulative = 0.0
    for edge, weight in zip(edges, weights):
        cumulative += weight
        if threshold <= cumulative:
            return edge
    return edges[-1]


class MycelialRouter(Router):
    name = "mycelial_v0"

    def __init__(self, graph: LayeredGraph, policy: HardPolicy, config: dict[str, Any]) -> None:
        self.graph = graph
        self.policy = policy
        self.config = config
        settings = config["mycelial"]
        self.decay = float(settings["temporal_decay"])
        self.eta = float(settings["plasticity"])
        self.xi = float(settings["exploration_reinforcement"])
        self.temperature = float(settings["temperature"])
        self.exploration = float(settings["explicit_exploration"])
        self.minimum = float(settings["min_conductance"])
        self.maximum = float(settings["max_conductance"])
        initial = float(settings["initial_conductance"])
        self.conductance = {edge_id: initial for edge_id in graph.edges}
        self.last_decay = {edge_id: 0 for edge_id in graph.edges}
        self.last_use: dict[str, int | None] = {edge_id: None for edge_id in graph.edges}
        self.last_feedback: dict[str, int | None] = {edge_id: None for edge_id in graph.edges}

    def _apply_decay(self, edge_id: str, step: int) -> None:
        elapsed = step - self.last_decay[edge_id]
        if elapsed > 0:
            self.conductance[edge_id] = max(
                self.minimum,
                self.conductance[edge_id] * ((1.0 - self.decay) ** elapsed),
            )
            self.last_decay[edge_id] = step

    def select(self, step: int, rng: random.Random) -> Decision:
        node = self.graph.source
        edges_selected: list[str] = []
        choices: list[Choice] = []
        operations = 0
        while node != self.graph.sink:
            candidates = self.graph.outgoing(node, self.policy)
            for edge in candidates:
                self._apply_decay(edge.id, step)
                operations += 1
            if len(candidates) == 1:
                chosen = candidates[0]
                mode = "single-edge-fallback"
            elif rng.random() < self.exploration:
                chosen = rng.choice(candidates)
                mode = "explicit-exploration"
            else:
                scores = [self.conductance[edge.id] / self.temperature for edge in candidates]
                chosen = _weighted_choice(candidates, scores, rng)
                mode = "conductance-softmax"
            edges_selected.append(chosen.id)
            choices.append(Choice(chosen.id, mode))
            self.last_use[chosen.id] = step
            node = chosen.target
        return Decision(tuple(edges_selected), tuple(choices), operations)

    def observe(
        self,
        step: int,
        decision: Decision,
        observations: Iterable[LocalObservation],
    ) -> None:
        choice_modes = {choice.edge_id: choice.mode for choice in decision.choices}
        for observation in observations:
            edge_id = observation.edge_id
            self._apply_decay(edge_id, step)
            reward = local_reward(observation, self.config)
            exploration = 1.0 if choice_modes[edge_id] == "explicit-exploration" else 0.0
            self.conductance[edge_id] = max(
                self.minimum,
                min(self.maximum, self.conductance[edge_id] + self.eta * reward + self.xi * exploration),
            )
            self.last_feedback[edge_id] = step


class StructuredSemiBanditRouter(Router):
    """Edge-level UCB with semi-bandit feedback and local graph traversal."""

    name = "structured_semi_bandit"

    def __init__(self, graph: LayeredGraph, policy: HardPolicy, config: dict[str, Any]) -> None:
        self.graph = graph
        self.policy = policy
        self.config = config
        self.c = float(config["baselines"]["semi_bandit_exploration"])
        self.count = {edge_id: 0 for edge_id in graph.edges}
        self.mean = {edge_id: 0.0 for edge_id in graph.edges}
        self.total_observations = 0

    def _score(self, edge_id: str) -> float:
        count = self.count[edge_id]
        if count == 0:
            return float("inf")
        return self.mean[edge_id] + self.c * math.sqrt(
            math.log(self.total_observations + 2.0) / count
        )

    def select(self, step: int, rng: random.Random) -> Decision:
        del step
        node = self.graph.source
        selected: list[str] = []
        choices: list[Choice] = []
        operations = 0
        while node != self.graph.sink:
            candidates = self.graph.outgoing(node, self.policy)
            scores = [self._score(edge.id) for edge in candidates]
            best = max(scores)
            tied = [edge for edge, score in zip(candidates, scores) if score == best]
            chosen = rng.choice(tied)
            selected.append(chosen.id)
            choices.append(Choice(chosen.id, "edge-ucb" if len(candidates) > 1 else "single-edge-fallback"))
            operations += len(candidates)
            node = chosen.target
        return Decision(tuple(selected), tuple(choices), operations)

    def observe(
        self,
        step: int,
        decision: Decision,
        observations: Iterable[LocalObservation],
    ) -> None:
        del step, decision
        for observation in observations:
            edge_id = observation.edge_id
            value = local_reward(observation, self.config)
            self.count[edge_id] += 1
            self.total_observations += 1
            count = self.count[edge_id]
            self.mean[edge_id] += (value - self.mean[edge_id]) / count


class ReactiveShortestPathRouter(Router):
    """Reactive best-path baseline with EWMA edge-weight updates."""

    name = "reactive_shortest_path"

    def __init__(self, graph: LayeredGraph, policy: HardPolicy, config: dict[str, Any]) -> None:
        self.graph = graph
        self.policy = policy
        self.config = config
        self.alpha = float(config["baselines"]["shortest_path_ewma"])
        self.estimate: dict[str, float] = {}
        for edge_id, edge in graph.edges.items():
            component = graph.components[edge.target]
            initial = LocalObservation(
                edge_id,
                component.id,
                component.quality,
                component.latency_ms,
                component.cost_usd,
                1.0 - component.reliability,
                component.load,
                component.scored,
            )
            self.estimate[edge_id] = local_reward(initial, config)

    def select(self, step: int, rng: random.Random) -> Decision:
        del step
        paths = self.graph.all_paths(self.policy)
        scores = [sum(self.estimate[edge_id] for edge_id in path) for path in paths]
        best = max(scores)
        tied = [path for path, score in zip(paths, scores) if abs(score - best) < 1e-12]
        path = rng.choice(tied)
        choices = tuple(Choice(edge_id, "reactive-best-path") for edge_id in path)
        operations = sum(len(path) for path in paths)
        return Decision(path, choices, operations)

    def observe(
        self,
        step: int,
        decision: Decision,
        observations: Iterable[LocalObservation],
    ) -> None:
        del step, decision
        for observation in observations:
            edge_id = observation.edge_id
            value = local_reward(observation, self.config)
            self.estimate[edge_id] = (
                (1.0 - self.alpha) * self.estimate[edge_id] + self.alpha * value
            )


def build_routers(
    graph: LayeredGraph,
    policy: HardPolicy,
    config: dict[str, Any],
) -> tuple[Router, ...]:
    return (
        MycelialRouter(graph, policy, config),
        StructuredSemiBanditRouter(graph, policy, config),
        ReactiveShortestPathRouter(graph, policy, config),
    )
