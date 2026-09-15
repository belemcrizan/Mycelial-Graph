from __future__ import annotations

import numpy as np

from ...agents._routing import greedy_local_route
from ...environment.graph import LayeredDAG
from ..biology.voc import estimate_voc, should_allocate
from ..environment.roles import alternative_index, edge_role
from ..ledger import ResourceObservation
from ..types import ControllerConfig, UtilityConfig
from .base import ResourceAgent, ResourceDecision


def _candidates(graph: LayeredDAG) -> int:
    return sum(len(graph.outgoing[node]) for node in graph.outgoing)


class ThompsonSamplingQuality(ResourceAgent):
    """Gaussian Thompson sampling on per-edge quality. Cost-unaware unless lambda>0."""

    name = "thompson_sampling"

    def __init__(self, config: ControllerConfig, utility: UtilityConfig, edge_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.config = config
        self.utility = utility
        self.mean = np.full(edge_count, 0.55)
        self.sq = np.full(edge_count, 0.05)
        self.counts = np.zeros(edge_count, dtype=int)
        self.token_hat = np.full(edge_count, 200.0)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        std = np.sqrt(self.sq / np.maximum(self.counts, 1))
        samples = self.rng.normal(self.mean, std)

        def score(edge_id: int) -> float:
            return float(samples[edge_id] - self.utility.lambda_tokens * self.token_hat[edge_id] / 1000.0)

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path, decision.edge_ids, 0, decision.edge_scores, _candidates(graph), 0.0, 0, 0.0
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        for obs in observations:
            n = self.counts[obs.edge_id]
            n1 = n + 1
            delta = obs.quality - self.mean[obs.edge_id]
            self.mean[obs.edge_id] += delta / n1
            self.sq[obs.edge_id] += delta * (obs.quality - self.mean[obs.edge_id])
            self.token_hat[obs.edge_id] += (obs.token_usage.path_tokens - self.token_hat[obs.edge_id]) / n1
            self.counts[obs.edge_id] = n1


class CostSensitiveContextualBandit(ResourceAgent):
    """Linear score on observable hats: Q - λT - λC. Features are local, not oracle."""

    name = "cost_sensitive_bandit"

    def __init__(self, utility: UtilityConfig, edge_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.utility = utility
        self.quality_hat = np.full(edge_count, 0.55)
        self.token_hat = np.full(edge_count, 200.0)
        self.cost_hat = np.full(edge_count, 0.2)
        self.counts = np.zeros(edge_count, dtype=int)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        def score(edge_id: int) -> float:
            return float(
                self.quality_hat[edge_id]
                - self.utility.lambda_tokens * self.token_hat[edge_id] / 1000.0
                - self.utility.lambda_cost * self.cost_hat[edge_id] / 2.5
            )

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path, decision.edge_ids, 0, decision.edge_scores, _candidates(graph), 0.0, 0, 0.0
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        for obs in observations:
            self.counts[obs.edge_id] += 1
            n = self.counts[obs.edge_id]
            self.quality_hat[obs.edge_id] += (obs.quality - self.quality_hat[obs.edge_id]) / n
            self.token_hat[obs.edge_id] += (obs.token_usage.path_tokens - self.token_hat[obs.edge_id]) / n
            self.cost_hat[obs.edge_id] += (obs.monetary_cost - self.cost_hat[obs.edge_id]) / n


class StructuredSWUCBResource(ResourceAgent):
    """Sliding-window UCB on the same node-edge indices used by V1 SW-UCB."""

    name = "structured_sw_ucb"

    def __init__(self, config: ControllerConfig, edge_count: int, rng: np.random.Generator, window: int = 12) -> None:
        super().__init__(rng)
        self.config = config
        self.window = window
        self.history: list[list[float]] = [[] for _ in range(edge_count)]

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        def score(edge_id: int) -> float:
            window = self.history[edge_id][-self.window :]
            if not window:
                return 1.0
            mean = float(np.mean(window))
            bonus = np.sqrt(2.0 * np.log(max(step, 1) + 1.0) / len(window))
            return mean + bonus

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path, decision.edge_ids, 0, decision.edge_scores, _candidates(graph), 0.0, 0, 0.0
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        for obs in observations:
            self.history[obs.edge_id].append(obs.quality)
            if len(self.history[obs.edge_id]) > self.window * 4:
                self.history[obs.edge_id] = self.history[obs.edge_id][-self.window :]


class UncertaintyThresholdRouter(ResourceAgent):
    """Escalate compute class when posterior std exceeds a threshold."""

    name = "uncertainty_threshold"

    def __init__(self, edge_count: int, rng: np.random.Generator, threshold: float = 0.12) -> None:
        super().__init__(rng)
        self.threshold = threshold
        self.mean = np.full(edge_count, 0.55)
        self.counts = np.zeros(edge_count, dtype=int)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        uncertain = float(np.mean(1.0 / np.sqrt(self.counts + 1.0))) > self.threshold
        preferred = 2 if uncertain else 0

        def score(edge_id: int) -> float:
            alt = alternative_index(graph, graph.edges[edge_id].target)
            return 3.0 if alt == preferred else 0.4

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path, decision.edge_ids, 0, decision.edge_scores, _candidates(graph), 0.0, 0, 0.0
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        for obs in observations:
            self.counts[obs.edge_id] += 1
            n = self.counts[obs.edge_id]
            self.mean[obs.edge_id] += (obs.quality - self.mean[obs.edge_id]) / n


class AdaptiveEarlyStop(ResourceAgent):
    """Fixed standard model; skip verification when VOC difference is non-positive."""

    name = "adaptive_early_stop"

    def __init__(self, utility: UtilityConfig, edge_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.utility = utility
        self.quality_hat = np.full(edge_count, 0.55)
        self.token_hat = np.full(edge_count, 200.0)
        self.last_mvc = 0.0

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        verify_ids = [edge.id for edge in graph.edges if edge_role(graph, edge.id) == "verification"]
        if len(verify_ids) >= 2:
            skip = min(verify_ids)
            spend = max(verify_ids)
            voc = estimate_voc(
                self.quality_hat[spend] - self.quality_hat[skip],
                max(self.token_hat[spend] - self.token_hat[skip], 1.0),
                self.utility.lambda_tokens,
            )
            self.last_mvc = voc.ratio
            prefer_skip = not should_allocate(voc, 0.0, use_difference=True)
        else:
            prefer_skip = False

        def score(edge_id: int) -> float:
            role = edge_role(graph, edge_id)
            alt = alternative_index(graph, graph.edges[edge_id].target)
            if role == "model":
                return 3.0 if alt == 1 else 0.2
            if role == "verification":
                if prefer_skip:
                    return 3.0 if edge_id == min(verify_ids) else 0.1
                return 3.0 if edge_id == max(verify_ids) else 0.1
            return 1.0

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            0,
            decision.edge_scores,
            _candidates(graph),
            self.last_mvc,
            0,
            0.0,
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        for obs in observations:
            self.quality_hat[obs.edge_id] = 0.8 * self.quality_hat[obs.edge_id] + 0.2 * obs.quality
            self.token_hat[obs.edge_id] = 0.8 * self.token_hat[obs.edge_id] + 0.2 * obs.token_usage.path_tokens


class LagrangianBudgetAllocator(ResourceAgent):
    """Dual ascent on a token budget; primal score is quality minus dual * tokens."""

    name = "lagrangian_budget"

    def __init__(self, edge_count: int, rng: np.random.Generator, target_tokens: float = 400.0) -> None:
        super().__init__(rng)
        self.target_tokens = target_tokens
        self.dual = 0.0
        self.quality_hat = np.full(edge_count, 0.55)
        self.token_hat = np.full(edge_count, 200.0)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        def score(edge_id: int) -> float:
            return float(self.quality_hat[edge_id] - self.dual * self.token_hat[edge_id] / 1000.0)

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path, decision.edge_ids, 0, decision.edge_scores, _candidates(graph), 0.0, 0, 0.0
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        used = 0.0
        for obs in observations:
            self.quality_hat[obs.edge_id] = 0.85 * self.quality_hat[obs.edge_id] + 0.15 * obs.quality
            self.token_hat[obs.edge_id] = 0.85 * self.token_hat[obs.edge_id] + 0.15 * obs.token_usage.path_tokens
            used += obs.token_usage.path_tokens
        self.dual = max(0.0, self.dual + 0.002 * (used - self.target_tokens))


class StaticCascade(ResourceAgent):
    """Cheap then escalate to frontier if last quality was below a floor."""

    name = "static_cascade"

    def __init__(self, rng: np.random.Generator, floor: float = 0.62) -> None:
        super().__init__(rng)
        self.floor = floor
        self.last_quality = 1.0

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        preferred = 2 if self.last_quality < self.floor else 0

        def score(edge_id: int) -> float:
            alt = alternative_index(graph, graph.edges[edge_id].target)
            return 3.0 if alt == preferred else 0.3

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path, decision.edge_ids, 0, decision.edge_scores, _candidates(graph), 0.0, 0, 0.0
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        if observations:
            self.last_quality = float(np.mean([obs.quality for obs in observations]))
