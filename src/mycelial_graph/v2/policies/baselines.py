from __future__ import annotations

import numpy as np

from ...agents._routing import greedy_local_route, stochastic_local_route
from ...environment.graph import LayeredDAG
from ..ledger import ResourceObservation
from ..types import ControllerConfig
from .base import ResourceAgent, ResourceDecision


def _fixed_class_score(graph: LayeredDAG, preferred_alt: int) -> callable:
    from ..environment.roles import alternative_index, layer_index

    def score(edge_id: int) -> float:
        edge = graph.edges[edge_id]
        if layer_index(graph, edge.target) in {0, len(graph.layers) - 1}:
            return 1.0
        alt = alternative_index(graph, edge.target)
        return 3.0 if alt == preferred_alt else (1.0 if alt == 1 else 0.2)

    return score


class AlwaysHighCompute(ResourceAgent):
    name = "always_high_compute"

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decision = greedy_local_route(graph, self.rng, _fixed_class_score(graph, 2))
        candidates = sum(len(graph.outgoing[node]) for node in graph.outgoing)
        return ResourceDecision(
            decision.path, decision.edge_ids, 0, decision.edge_scores, candidates, 0.0, 0, 0.0
        )

    def update(self, graph, decision, observations, step, budget_cap) -> None:
        return None


class AlwaysLowCompute(ResourceAgent):
    name = "always_low_compute"

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decision = greedy_local_route(graph, self.rng, _fixed_class_score(graph, 0))
        candidates = sum(len(graph.outgoing[node]) for node in graph.outgoing)
        return ResourceDecision(
            decision.path, decision.edge_ids, 0, decision.edge_scores, candidates, 0.0, 0, 0.0
        )

    def update(self, graph, decision, observations, step, budget_cap) -> None:
        return None


class FixedBudgetAgent(ResourceAgent):
    name = "fixed_budget"

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decision = greedy_local_route(graph, self.rng, _fixed_class_score(graph, 1))
        candidates = sum(len(graph.outgoing[node]) for node in graph.outgoing)
        return ResourceDecision(
            decision.path, decision.edge_ids, 0, decision.edge_scores, candidates, 0.0, 0, 0.0
        )

    def update(self, graph, decision, observations, step, budget_cap) -> None:
        return None


class RandomRouter(ResourceAgent):
    name = "random_router"

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decision = stochastic_local_route(graph, self.rng, lambda _: 1.0, 1.0, 1.0)
        candidates = sum(len(graph.outgoing[node]) for node in graph.outgoing)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            decision.exploratory_edges,
            decision.edge_scores,
            candidates,
            0.0,
            0,
            0.0,
        )

    def update(self, graph, decision, observations, step, budget_cap) -> None:
        return None


class EpsilonGreedyQuality(ResourceAgent):
    name = "epsilon_greedy"

    def __init__(self, config: ControllerConfig, edge_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.config = config
        self.quality_hat = np.full(edge_count, 0.5)
        self.counts = np.zeros(edge_count, dtype=int)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decision = stochastic_local_route(
            graph,
            self.rng,
            lambda edge_id: float(self.quality_hat[edge_id]),
            max(self.config.temperature, 0.05),
            0.15,
        )
        candidates = sum(len(graph.outgoing[node]) for node in graph.outgoing)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            decision.exploratory_edges,
            decision.edge_scores,
            candidates,
            0.0,
            0,
            0.0,
        )

    def update(
        self,
        graph: LayeredDAG,
        decision: ResourceDecision,
        observations: list[ResourceObservation],
        step: int,
        budget_cap: float,
    ) -> None:
        for obs in observations:
            self.counts[obs.edge_id] += 1
            n = self.counts[obs.edge_id]
            self.quality_hat[obs.edge_id] += (obs.quality - self.quality_hat[obs.edge_id]) / n


class V1EdgeOnlyTransplant(ResourceAgent):
    """Quality-only mycelial conductance; ignores cost. Control for V1 identity."""

    name = "v1_edge_only"

    def __init__(self, config: ControllerConfig, edge_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.config = config
        self.conductance = np.full(edge_count, config.initial_conductance)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decay = 1.0 - self.config.temporal_decay
        self.conductance = self.config.initial_conductance + (
            self.conductance - self.config.initial_conductance
        ) * decay
        decision = stochastic_local_route(
            graph,
            self.rng,
            lambda edge_id: float(self.conductance[edge_id]),
            self.config.temperature,
            self.config.exploration_probability,
        )
        candidates = sum(len(graph.outgoing[node]) for node in graph.outgoing)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            decision.exploratory_edges,
            decision.edge_scores,
            candidates,
            0.0,
            0,
            0.0,
        )

    def update(
        self,
        graph: LayeredDAG,
        decision: ResourceDecision,
        observations: list[ResourceObservation],
        step: int,
        budget_cap: float,
    ) -> None:
        for obs in observations:
            delta = obs.quality - 0.5
            self.conductance[obs.edge_id] = np.clip(
                self.conductance[obs.edge_id] + self.config.learning_rate * delta,
                self.config.minimum_conductance,
                self.config.maximum_conductance,
            )
