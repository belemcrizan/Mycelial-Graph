from __future__ import annotations

from collections.abc import Callable

import numpy as np

from ...agents._routing import greedy_local_route, stochastic_local_route
from ...environment.graph import LayeredDAG
from ..environment.roles import alternative_index, edge_role, layer_index
from ..ledger import ResourceObservation
from ..types import ConstraintConfig, ControllerConfig, UtilityConfig
from .base import ResourceAgent, ResourceDecision


def _visited_candidates(graph: LayeredDAG, path: tuple[int, ...]) -> int:
    return sum(len(graph.outgoing[node]) for node in path[:-1])


def _fixed_class_score(graph: LayeredDAG, preferred_alt: int) -> Callable[[int], float]:
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
        preferred = 2 if graph.layers and len(graph.layers[1]) > 2 else len(graph.layers[1]) - 1
        decision = greedy_local_route(graph, self.rng, _fixed_class_score(graph, preferred))
        candidates = _visited_candidates(graph, decision.path)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            0,
            decision.edge_scores,
            candidates,
            0.0,
            0,
            0.0,
            decision_mode="static_high",
        )

    def update(self, graph, decision, observations, step, budget_cap) -> None:
        return None


class AlwaysLowCompute(ResourceAgent):
    name = "always_low_compute"

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decision = greedy_local_route(graph, self.rng, _fixed_class_score(graph, 0))
        candidates = _visited_candidates(graph, decision.path)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            0,
            decision.edge_scores,
            candidates,
            0.0,
            0,
            0.0,
            decision_mode="static_low",
        )

    def update(self, graph, decision, observations, step, budget_cap) -> None:
        return None


class FixedBudgetAgent(ResourceAgent):
    name = "fixed_budget"

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decision = greedy_local_route(graph, self.rng, _fixed_class_score(graph, 1))
        candidates = _visited_candidates(graph, decision.path)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            0,
            decision.edge_scores,
            candidates,
            0.0,
            0,
            0.0,
            decision_mode="static_medium",
        )

    def update(self, graph, decision, observations, step, budget_cap) -> None:
        return None


class RandomRouter(ResourceAgent):
    name = "random_router"

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decision = stochastic_local_route(graph, self.rng, lambda _: 1.0, 1.0, 1.0)
        candidates = _visited_candidates(graph, decision.path)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            decision.exploratory_edges,
            decision.edge_scores,
            candidates,
            0.0,
            0,
            0.0,
            decision_mode="random_uniform",
        )

    def update(self, graph, decision, observations, step, budget_cap) -> None:
        return None


class RandomFeasibleRouter(ResourceAgent):
    """Uniform random routing over safety- and budget-feasible candidates."""

    name = "random_feasible"

    def __init__(
        self,
        constraints: ConstraintConfig,
        total_steps: int,
        edge_count: int,
        rng: np.random.Generator,
    ) -> None:
        super().__init__(rng)
        self.constraints = constraints
        self.total_steps = max(total_steps, 1)
        self.token_hat = np.full(edge_count, 160.0, dtype=float)
        self.fail_hat = np.full(edge_count, 0.05, dtype=float)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        steps_left = max(self.total_steps - step, 1)
        step_budget = budget_cap / float(steps_left) if budget_cap > 2500.0 else budget_cap
        node = graph.source
        path = [node]
        edges: list[int] = []
        scores: list[float] = []
        evaluated = 0
        fallback_reason: str | None = None
        spent_est = 0.0
        while node != graph.sink:
            cands = list(graph.outgoing[node])
            evaluated += len(cands)
            feasible = cands
            if self.constraints.mandatory_verification and cands and edge_role(graph, cands[0]) == "verification":
                non_skip = [e for e in feasible if alternative_index(graph, graph.edges[e].target) > 0]
                if non_skip:
                    feasible = non_skip
            safe = [e for e in feasible if self.fail_hat[e] <= self.constraints.max_risk]
            if safe:
                feasible = safe
            elif len(feasible) > 1:
                fallback_reason = "max_risk_guardrail"
                feasible = [min(feasible, key=lambda e: float(self.fail_hat[e]))]
            affordable = [e for e in feasible if spent_est + self.token_hat[e] <= max(step_budget, 25.0)]
            if affordable:
                feasible = affordable
            elif feasible:
                fallback_reason = fallback_reason or "budget_cap_downgrade"
                feasible = [min(feasible, key=lambda e: float(self.token_hat[e]))]
            chosen = int(self.rng.choice(feasible))
            edges.append(chosen)
            scores.append(1.0 / max(len(feasible), 1))
            spent_est += float(self.token_hat[chosen])
            node = graph.edges[chosen].target
            path.append(node)
        return ResourceDecision(
            tuple(path),
            tuple(edges),
            len(edges),
            tuple(scores),
            evaluated,
            0.0,
            0,
            0.0,
            estimated_tokens=spent_est,
            decision_mode="random_feasible",
            fallback_reason=fallback_reason,
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        for obs in observations:
            self.token_hat[obs.edge_id] = 0.8 * self.token_hat[obs.edge_id] + 0.2 * obs.token_usage.path_tokens
            fail = 0.0 if obs.success else 1.0
            self.fail_hat[obs.edge_id] = 0.8 * self.fail_hat[obs.edge_id] + 0.2 * fail


class EpsilonGreedyQuality(ResourceAgent):
    name = "epsilon_greedy"

    def __init__(self, config: ControllerConfig, edge_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.config = config
        self.quality_hat = np.full(edge_count, 0.55)
        self.counts = np.zeros(edge_count, dtype=int)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decision = stochastic_local_route(
            graph,
            self.rng,
            lambda edge_id: float(self.quality_hat[edge_id]),
            max(self.config.temperature, 0.05),
            0.15,
        )
        candidates = _visited_candidates(graph, decision.path)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            decision.exploratory_edges,
            decision.edge_scores,
            candidates,
            0.0,
            0,
            0.0,
            decision_mode="epsilon_greedy",
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
            alpha = max(0.15, 1.0 / self.counts[obs.edge_id])
            self.quality_hat[obs.edge_id] += alpha * (obs.quality - self.quality_hat[obs.edge_id])


class V1EdgeOnlyTransplant(ResourceAgent):
    """Quality-only mycelial conductance; ignores cost. Control for V1 edge-only identity."""

    name = "v1_edge_only"

    def __init__(self, config: ControllerConfig, edge_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.config = config
        self.conductance: np.ndarray = np.full(edge_count, config.initial_conductance, dtype=float)

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
        candidates = _visited_candidates(graph, decision.path)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            decision.exploratory_edges,
            decision.edge_scores,
            candidates,
            0.0,
            0,
            0.0,
            decision_mode="v1_edge_conductance",
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


class V1NodeOnlyTransplant(ResourceAgent):
    """Faithful V1 node-only comparator (quality-only, ungated node state)."""

    name = "v1_node_only"

    def __init__(self, config: ControllerConfig, node_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.config = config
        self.source_effect = np.zeros(node_count, dtype=float)
        self.target_effect = np.zeros(node_count, dtype=float)

    def _score(self, graph: LayeredDAG, edge_id: int) -> float:
        edge = graph.edges[edge_id]
        return float(
            self.config.initial_conductance
            + self.source_effect[edge.source]
            + self.target_effect[edge.target]
        )

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decay = 1.0 - self.config.temporal_decay
        self.source_effect *= decay
        self.target_effect *= decay
        decision = stochastic_local_route(
            graph,
            self.rng,
            lambda eid: self._score(graph, eid),
            self.config.temperature,
            self.config.exploration_probability,
        )
        candidates = _visited_candidates(graph, decision.path)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            decision.exploratory_edges,
            decision.edge_scores,
            candidates,
            0.0,
            0,
            0.0,
            decision_mode="v1_node_only",
        )

    def update(self, graph: LayeredDAG, decision: ResourceDecision, observations: list[ResourceObservation], step: int, budget_cap: float) -> None:
        lr = 0.14
        self.source_effect *= 0.998
        self.target_effect *= 0.998
        for obs in observations:
            edge = graph.edges[obs.edge_id]
            err = float(obs.quality) - float(np.clip(self._score(graph, obs.edge_id), 0.0, 1.0))
            self.source_effect[edge.source] += lr * err / 2.0
            self.target_effect[edge.target] += lr * err / 2.0
        self.source_effect -= np.mean(self.source_effect)
        self.target_effect -= np.mean(self.target_effect)


class V1HierarchicalTransplant(ResourceAgent):
    """Faithful V1 hierarchical node+edge comparator preserved for V2 vs V1 evaluation."""

    name = "v1_hierarchical"

    def __init__(
        self,
        config: ControllerConfig,
        node_count: int,
        edge_count: int,
        rng: np.random.Generator,
    ) -> None:
        super().__init__(rng)
        self.config = config
        self.source_effect = np.zeros(node_count, dtype=float)
        self.target_effect = np.zeros(node_count, dtype=float)
        self.interaction = np.zeros(edge_count, dtype=float)

    def _score(self, graph: LayeredDAG, edge_id: int) -> float:
        edge = graph.edges[edge_id]
        return float(
            self.config.initial_conductance
            + self.source_effect[edge.source]
            + self.target_effect[edge.target]
            + self.interaction[edge_id]
        )

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        decay = 1.0 - self.config.temporal_decay
        self.source_effect *= decay
        self.target_effect *= decay
        self.interaction *= decay
        decision = stochastic_local_route(
            graph,
            self.rng,
            lambda eid: self._score(graph, eid),
            self.config.temperature,
            self.config.exploration_probability,
        )
        candidates = _visited_candidates(graph, decision.path)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            decision.exploratory_edges,
            decision.edge_scores,
            candidates,
            0.0,
            0,
            0.0,
            decision_mode="v1_hierarchical",
        )

    def update(self, graph: LayeredDAG, decision: ResourceDecision, observations: list[ResourceObservation], step: int, budget_cap: float) -> None:
        self.source_effect *= 0.998
        self.target_effect *= 0.998
        self.interaction *= 0.998
        for obs in observations:
            edge = graph.edges[obs.edge_id]
            err = float(obs.quality) - float(np.clip(self._score(graph, obs.edge_id), 0.0, 1.0))
            self.source_effect[edge.source] += 0.14 * err / 2.0
            self.target_effect[edge.target] += 0.14 * err / 2.0
            self.interaction[obs.edge_id] += 0.10 * err
        self.source_effect -= np.mean(self.source_effect)
        self.target_effect -= np.mean(self.target_effect)
        self.interaction -= np.mean(self.interaction)


class ResourceAwareHeuristic(ResourceAgent):
    """Non-biological resource-aware greedy heuristic (EWMA utility-per-resource + budget cap)."""

    name = "resource_heuristic"

    def __init__(
        self,
        utility: UtilityConfig,
        constraints: ConstraintConfig,
        total_steps: int,
        edge_count: int,
        rng: np.random.Generator,
    ) -> None:
        super().__init__(rng)
        self.utility = utility
        self.constraints = constraints
        self.total_steps = max(total_steps, 1)
        self.q_hat = np.full(edge_count, 0.65, dtype=float)
        self.t_hat = np.full(edge_count, 180.0, dtype=float)
        self.c_hat = np.full(edge_count, 0.15, dtype=float)
        self.l_hat = np.full(edge_count, 160.0, dtype=float)
        self.f_hat = np.full(edge_count, 0.05, dtype=float)
        self.counts = np.zeros(edge_count, dtype=int)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        steps_left = max(self.total_steps - step, 1)
        step_budget = budget_cap / float(steps_left) if budget_cap > 2500.0 else budget_cap
        u = self.utility
        node = graph.source
        path = [node]
        edges: list[int] = []
        scores: list[float] = []
        evaluated = 0
        spent_est = 0.0
        while node != graph.sink:
            cands = list(graph.outgoing[node])
            evaluated += len(cands)
            feasible = [e for e in cands if self.f_hat[e] <= self.constraints.max_risk] or cands
            if self.constraints.mandatory_verification and feasible and edge_role(graph, feasible[0]) == "verification":
                non_skip = [e for e in feasible if alternative_index(graph, graph.edges[e].target) > 0]
                if non_skip:
                    feasible = non_skip
            affordable = [e for e in feasible if spent_est + self.t_hat[e] <= max(step_budget, 25.0)]
            if affordable:
                feasible = affordable
            else:
                feasible = [min(feasible, key=lambda e: float(self.t_hat[e]))]

            def edge_val(eid: int) -> float:
                bonus = 0.04 if self.counts[eid] == 0 else 0.0
                return float(
                    self.q_hat[eid]
                    - u.lambda_tokens * (self.t_hat[eid] / 1000.0)
                    - u.lambda_cost * (self.c_hat[eid] / 2.5)
                    - u.lambda_latency * (self.l_hat[eid] / 1000.0)
                    - u.lambda_risk * self.f_hat[eid]
                    + bonus
                )

            cand_scores = np.array([edge_val(e) for e in feasible], dtype=float)
            best_idx = int(self.rng.choice(np.flatnonzero(np.isclose(cand_scores, np.max(cand_scores)))))
            chosen = feasible[best_idx]
            edges.append(chosen)
            scores.append(float(cand_scores[best_idx]))
            spent_est += float(self.t_hat[chosen])
            node = graph.edges[chosen].target
            path.append(node)
        return ResourceDecision(
            tuple(path),
            tuple(edges),
            0,
            tuple(scores),
            evaluated,
            0.0,
            0,
            0.0,
            estimated_utility=float(np.mean(scores)) if scores else 0.0,
            estimated_tokens=spent_est,
            decision_mode="resource_heuristic",
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        for obs in observations:
            self.counts[obs.edge_id] += 1
            alpha = 0.25 if self.counts[obs.edge_id] > 1 else 1.0
            self.q_hat[obs.edge_id] += alpha * (obs.quality - self.q_hat[obs.edge_id])
            self.t_hat[obs.edge_id] += alpha * (obs.token_usage.path_tokens - self.t_hat[obs.edge_id])
            self.c_hat[obs.edge_id] += alpha * (obs.monetary_cost - self.c_hat[obs.edge_id])
            self.l_hat[obs.edge_id] += alpha * (obs.latency_ms - self.l_hat[obs.edge_id])
            fail = 0.0 if obs.success else 1.0
            self.f_hat[obs.edge_id] += alpha * (fail - self.f_hat[obs.edge_id])
