from __future__ import annotations

import numpy as np

from ...agents._routing import stochastic_local_route
from ...environment.graph import LayeredDAG
from ..biology import (
    assert_budget_conserved,
    budget_l1_shift,
    marginal_value,
    prune_score,
    routing_utility,
    should_spend,
    translocate,
    update_conductance,
    update_prune_evidence,
)
from ..environment.roles import alternative_index, edge_role
from ..ledger import ResourceObservation
from ..types import V2ExperimentConfig
from .base import ResourceAgent, ResourceDecision

TOKEN_SCALE = 1000.0
COST_SCALE = 2.5
LATENCY_SCALE = 1000.0


class MycelialResourceController(ResourceAgent):
    name = "v2_mycelial"

    def __init__(
        self,
        config: V2ExperimentConfig,
        edge_count: int,
        rng: np.random.Generator,
        *,
        pruning: bool = True,
        transfer: bool = True,
        cord: bool = True,
        cost_aware: bool = True,
    ) -> None:
        super().__init__(rng)
        self.config = config
        self.pruning_enabled = pruning
        self.transfer_enabled = transfer
        self.cord_enabled = cord
        self.cost_aware = cost_aware
        c = config.controller
        self.conductance = np.full(edge_count, c.initial_conductance)
        self.budget = np.full(edge_count, 1.0)
        self.quality_hat = np.full(edge_count, 0.55)
        self.token_hat = np.full(edge_count, 200.0)
        self.cost_hat = np.full(edge_count, 0.2)
        self.latency_hat = np.full(edge_count, 200.0)
        self.fail_hat = np.full(edge_count, 0.08)
        self.counts = np.zeros(edge_count, dtype=int)
        self.prune_evidence = np.zeros(edge_count, dtype=int)
        self.pruned = np.zeros(edge_count, dtype=bool)
        self.last_path: tuple[int, ...] | None = None
        self.last_switch_step = -10_000
        self.last_prune_count = 0
        self.last_transfer_l1 = 0.0
        self.last_mvc = 0.0

    def _score(self, graph: LayeredDAG, edge_id: int, step: int) -> float:
        c = self.config.controller
        u = self.config.utility
        if self.pruned[edge_id]:
            base = c.minimum_conductance
        else:
            token_norm = float(self.token_hat[edge_id] / TOKEN_SCALE)
            cost_norm = float(self.cost_hat[edge_id] / COST_SCALE)
            lat_norm = float(self.latency_hat[edge_id] / LATENCY_SCALE)
            util = routing_utility(
                float(self.quality_hat[edge_id]),
                token_norm,
                cost_norm,
                lat_norm,
                float(self.fail_hat[edge_id]),
                float(self.fail_hat[edge_id]),
                0.0,
                u,
                self.cost_aware,
            )
            base = 0.5 * float(self.conductance[edge_id]) + 0.5 * util
            if self.last_path is not None and edge_id in set(
                graph.path_edges(self.last_path)
            ):
                base += c.hysteresis
            if (
                self.last_path is not None
                and step - self.last_switch_step < u.switch_cooldown
            ):
                if edge_id not in set(graph.path_edges(self.last_path)):
                    base -= u.switching_penalty
        return float(base)

    def _apply_mvc_verification(self, graph: LayeredDAG, step: int) -> None:
        """Bias skip vs verify using MVC, subject to hard constraints."""
        verify_sources = [
            node
            for node, outgoing in graph.outgoing.items()
            if outgoing and edge_role(graph, outgoing[0]) == "verification"
        ]
        if not verify_sources:
            self.last_mvc = 0.0
            return
        node = verify_sources[0]
        candidates = graph.outgoing[node]
        skip = min(candidates, key=lambda e: alternative_index(graph, graph.edges[e].target))
        spend = max(candidates, key=lambda e: alternative_index(graph, graph.edges[e].target))
        gain = float(self.quality_hat[spend] - self.quality_hat[skip])
        extra = float(max(self.token_hat[spend] - self.token_hat[skip], 1.0))
        mvc = marginal_value(gain, extra)
        self.last_mvc = mvc
        spend_ok = should_spend(
            mvc,
            self.config.utility.mvc_threshold,
            float(self.quality_hat[skip]),
            float(self.fail_hat[skip]),
            self.config.constraints,
        )
        if not spend_ok:
            self.conductance[skip] = min(
                self.config.controller.maximum_conductance,
                self.conductance[skip] + 0.08,
            )

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        self.budget = translocate(
            self.budget,
            np.maximum(self.conductance, self.config.controller.minimum_conductance),
            float(budget_cap),
            self.config.controller,
            self.transfer_enabled,
        )
        assert_budget_conserved(self.budget, float(budget_cap), atol=1e-5)
        self._apply_mvc_verification(graph, step)
        decision = stochastic_local_route(
            graph,
            self.rng,
            lambda edge_id: self._score(graph, edge_id, step),
            self.config.controller.temperature,
            self.config.controller.exploration_probability,
        )
        if self.last_path is not None and decision.path != self.last_path:
            self.last_switch_step = step
        self.last_path = decision.path
        candidates = sum(len(graph.outgoing[node]) for node in graph.outgoing)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            decision.exploratory_edges,
            decision.edge_scores,
            candidates,
            self.last_mvc,
            int(self.last_prune_count),
            self.last_transfer_l1,
        )

    def update(
        self,
        graph: LayeredDAG,
        decision: ResourceDecision,
        observations: list[ResourceObservation],
        step: int,
        budget_cap: float,
    ) -> None:
        targets = []
        waste = np.zeros(len(self.conductance))
        demand = np.zeros(len(self.conductance))
        for obs in observations:
            self.counts[obs.edge_id] += 1
            n = self.counts[obs.edge_id]
            self.quality_hat[obs.edge_id] += (obs.quality - self.quality_hat[obs.edge_id]) / n
            tokens = obs.token_usage.path_tokens
            self.token_hat[obs.edge_id] += (tokens - self.token_hat[obs.edge_id]) / n
            self.cost_hat[obs.edge_id] += (obs.monetary_cost - self.cost_hat[obs.edge_id]) / n
            self.latency_hat[obs.edge_id] += (obs.latency_ms - self.latency_hat[obs.edge_id]) / n
            fail = 0.0 if obs.success else 1.0
            self.fail_hat[obs.edge_id] += (fail - self.fail_hat[obs.edge_id]) / n
            token_norm = tokens / TOKEN_SCALE
            cost_norm = obs.monetary_cost / COST_SCALE
            util = routing_utility(
                obs.quality,
                token_norm,
                cost_norm,
                obs.latency_ms / LATENCY_SCALE,
                fail,
                fail,
                0.0,
                self.config.utility,
                self.cost_aware,
            )
            targets.append(util)
            waste[obs.edge_id] = max(0.0, token_norm - obs.quality)
            demand[obs.edge_id] = 1.0
        self.conductance = update_conductance(
            self.conductance,
            decision.edge_ids,
            np.array(targets, dtype=float),
            demand,
            waste,
            self.config.controller,
            self.cord_enabled,
        )
        scores = np.zeros(len(self.conductance))
        for edge_id in range(len(self.conductance)):
            token_norm = float(self.token_hat[edge_id] / TOKEN_SCALE)
            redundancy = 0.0
            source = graph.edges[edge_id].source
            siblings = graph.outgoing.get(source, ())
            if siblings:
                best = max(float(self.quality_hat[other]) for other in siblings)
                redundancy = max(0.0, best - float(self.quality_hat[edge_id]))
            scores[edge_id] = prune_score(
                token_norm,
                redundancy,
                float(self.fail_hat[edge_id]),
                float(self.quality_hat[edge_id] - self.config.utility.lambda_tokens * token_norm),
            )
        before = self.budget.copy()
        self.prune_evidence, pruned = update_prune_evidence(
            self.prune_evidence,
            self.counts,
            scores,
            self.config.controller,
            self.pruning_enabled,
        )
        self.pruned = pruned
        if self.pruning_enabled:
            self.conductance[pruned] = self.config.controller.minimum_conductance
        self.last_prune_count = int(np.count_nonzero(self.pruned))
        weights = self.conductance * np.maximum(self.quality_hat, 0.05)
        weights[self.pruned] = self.config.controller.minimum_conductance
        self.budget = translocate(
            self.budget, weights, float(budget_cap), self.config.controller, self.transfer_enabled
        )
        self.last_transfer_l1 = budget_l1_shift(before, self.budget)
        assert_budget_conserved(self.budget, float(budget_cap), atol=1e-5)
