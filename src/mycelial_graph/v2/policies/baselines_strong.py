from __future__ import annotations

from collections import deque

import numpy as np

from ...agents._routing import greedy_local_route
from ...environment.graph import LayeredDAG
from ..biology.voc import TOKEN_SCALE, estimate_token_voc, should_allocate
from ..environment.roles import alternative_index, edge_role
from ..ledger import ResourceObservation
from ..types import ControllerConfig, UtilityConfig
from .base import ResourceAgent, ResourceDecision


def _visited_candidates(graph: LayeredDAG, path: tuple[int, ...]) -> int:
    return sum(len(graph.outgoing[node]) for node in path[:-1])


class ThompsonSamplingQuality(ResourceAgent):
    """Discounted Gaussian Thompson sampling on per-edge net utility."""

    name = "thompson_sampling"

    def __init__(self, config: ControllerConfig, utility: UtilityConfig, edge_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.config = config
        self.utility = utility
        self.mean = np.full(edge_count, 0.65)
        self.var = np.full(edge_count, 0.04)
        self.eff_counts = np.zeros(edge_count, dtype=float)
        self.token_hat = np.full(edge_count, 180.0)
        self.cost_hat = np.full(edge_count, 0.15)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        std = np.sqrt(self.var / np.maximum(self.eff_counts + 1.0, 1.0))
        samples = self.rng.normal(self.mean, std)

        def score(edge_id: int) -> float:
            return float(
                samples[edge_id]
                - self.utility.lambda_tokens * (self.token_hat[edge_id] / TOKEN_SCALE)
                - self.utility.lambda_cost * (self.cost_hat[edge_id] / 2.5)
            )

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            0,
            decision.edge_scores,
            _visited_candidates(graph, decision.path),
            0.0,
            0,
            0.0,
            decision_mode="thompson_sampling",
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        self.eff_counts *= 0.96
        for obs in observations:
            e = obs.edge_id
            self.eff_counts[e] += 1.0
            alpha = max(0.20, 1.0 / self.eff_counts[e])
            diff = obs.quality - self.mean[e]
            self.mean[e] += alpha * diff
            self.var[e] = max(1e-4, (1.0 - alpha) * self.var[e] + alpha * (diff * diff))
            self.token_hat[e] += alpha * (obs.token_usage.path_tokens - self.token_hat[e])
            self.cost_hat[e] += alpha * (obs.monetary_cost - self.cost_hat[e])


class CostSensitiveContextualBandit(ResourceAgent):
    """Recency-weighted cost-sensitive bandit: Q_hat - lambda_T*T_hat - lambda_C*C_hat + UCB."""

    name = "cost_sensitive_bandit"

    def __init__(self, utility: UtilityConfig, edge_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.utility = utility
        self.quality_hat = np.full(edge_count, 0.65)
        self.token_hat = np.full(edge_count, 180.0)
        self.cost_hat = np.full(edge_count, 0.15)
        self.counts = np.zeros(edge_count, dtype=int)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        def score(edge_id: int) -> float:
            bonus = 0.08 / np.sqrt(self.counts[edge_id] + 1.0)
            return float(
                self.quality_hat[edge_id]
                - self.utility.lambda_tokens * (self.token_hat[edge_id] / TOKEN_SCALE)
                - self.utility.lambda_cost * (self.cost_hat[edge_id] / 2.5)
                + bonus
            )

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            0,
            decision.edge_scores,
            _visited_candidates(graph, decision.path),
            0.0,
            0,
            0.0,
            decision_mode="cost_sensitive_bandit",
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        for obs in observations:
            e = obs.edge_id
            self.counts[e] += 1
            alpha = max(0.22, 1.0 / self.counts[e])
            self.quality_hat[e] += alpha * (obs.quality - self.quality_hat[e])
            self.token_hat[e] += alpha * (obs.token_usage.path_tokens - self.token_hat[e])
            self.cost_hat[e] += alpha * (obs.monetary_cost - self.cost_hat[e])


class StructuredSWUCBResource(ResourceAgent):
    """True structured sliding-window linear UCB over V1 node+edge features (centered prior)."""

    name = "structured_sw_ucb"

    def __init__(
        self,
        config: ControllerConfig,
        utility: UtilityConfig,
        node_count: int,
        edge_count: int,
        rng: np.random.Generator,
        window_steps: int = 16,
    ) -> None:
        super().__init__(rng)
        self.config = config
        self.utility = utility
        self.node_count = node_count
        self.edge_count = edge_count
        self.dimension = node_count + edge_count  # target-node + edge-interaction features
        self.window_steps = window_steps
        self.step_history: deque[list[tuple[np.ndarray, float]]] = deque(maxlen=window_steps)
        self.theta = np.zeros(self.dimension, dtype=float)
        self.inverse = np.eye(self.dimension, dtype=float)

    def _feature(self, graph: LayeredDAG, edge_id: int) -> np.ndarray:
        edge = graph.edges[edge_id]
        x = np.zeros(self.dimension, dtype=float)
        x[edge.target] = 1.0
        x[self.node_count + edge_id] = 1.0
        return x / np.sqrt(2.0)

    def _fit(self) -> None:
        ridge = 1.0
        a = ridge * np.eye(self.dimension, dtype=float)
        b = np.zeros(self.dimension, dtype=float)
        for step_obs in self.step_history:
            for x, centered_reward in step_obs:
                a += np.outer(x, x)
                b += x * centered_reward
        self.inverse = np.linalg.inv(a)
        self.theta = self.inverse @ b

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        self._fit()

        def score(edge_id: int) -> float:
            x = self._feature(graph, edge_id)
            mean = 0.55 + float(x @ self.theta)
            unc = float(np.sqrt(max(float(x @ self.inverse @ x), 0.0)))
            return mean + 0.30 * unc

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            0,
            decision.edge_scores,
            _visited_candidates(graph, decision.path),
            0.0,
            0,
            0.0,
            decision_mode="structured_sw_ucb",
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        step_items: list[tuple[np.ndarray, float]] = []
        for obs in observations:
            net = (
                obs.quality
                - self.utility.lambda_tokens * (obs.token_usage.path_tokens / TOKEN_SCALE)
                - self.utility.lambda_cost * (obs.monetary_cost / 2.5)
            )
            step_items.append((self._feature(graph, obs.edge_id), float(net - 0.55)))
        self.step_history.append(step_items)


class UncertaintyThresholdRouter(ResourceAgent):
    """Escalate compute tier when active task quality residual/uncertainty exceeds threshold."""

    name = "uncertainty_threshold"

    def __init__(self, edge_count: int, rng: np.random.Generator, threshold: float = 0.14) -> None:
        super().__init__(rng)
        self.threshold = threshold
        self.mean = np.full(edge_count, 0.65)
        self.residual_ewma = 0.20
        self.counts = np.zeros(edge_count, dtype=int)

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        # Warm-up across tiers in steps 0..2, then adaptively escalate only when residual uncertainty is high.
        if step < 3:
            preferred = step % min(3, len(graph.layers[1]))
        else:
            preferred = 2 if self.residual_ewma > self.threshold else 1 if self.residual_ewma > 0.07 else 0
            preferred = min(preferred, len(graph.layers[1]) - 1)

        def score(edge_id: int) -> float:
            target = graph.edges[edge_id].target
            if target in {graph.source, graph.sink}:
                return 1.0
            alt = alternative_index(graph, target)
            return 3.0 if alt == preferred else 0.4

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            0,
            decision.edge_scores,
            _visited_candidates(graph, decision.path),
            0.0,
            0,
            0.0,
            uncertainty=float(self.residual_ewma),
            decision_mode="uncertainty_escalation",
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        errs = []
        for obs in observations:
            e = obs.edge_id
            self.counts[e] += 1
            err = abs(obs.quality - self.mean[e]) + (0.25 if not obs.success else 0.0)
            errs.append(err)
            alpha = max(0.20, 1.0 / self.counts[e])
            self.mean[e] += alpha * (obs.quality - self.mean[e])
        if errs:
            self.residual_ewma = 0.75 * self.residual_ewma + 0.25 * float(np.mean(errs))


class AdaptiveEarlyStop(ResourceAgent):
    """Standard model tier; dynamically decides skip vs verify at the active model node via normalized VOC."""

    name = "adaptive_early_stop"

    def __init__(self, utility: UtilityConfig, edge_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.utility = utility
        self.quality_hat = np.full(edge_count, 0.65)
        # Initialize verification lift priors realistically so initial probe occurs before settling.
        self.token_hat = np.full(edge_count, 140.0)
        self.counts = np.zeros(edge_count, dtype=int)
        self.last_mvc = 0.0

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        node = graph.source
        path = [node]
        selected_edges: list[int] = []
        selected_scores: list[float] = []
        evaluated = 0
        self.last_mvc = 0.0

        while node != graph.sink:
            cands = graph.outgoing[node]
            evaluated += len(cands)
            if len(cands) == 1:
                chosen = cands[0]
                selected_scores.append(1.0)
            else:
                role = edge_role(graph, cands[0])
                if role == "verification":
                    skip = min(cands, key=lambda e: alternative_index(graph, graph.edges[e].target))
                    spend = max(cands, key=lambda e: alternative_index(graph, graph.edges[e].target))
                    # Ensure both skip and spend are probed at least once before locking a stop decision.
                    if self.counts[skip] == 0:
                        chosen = skip
                        selected_scores.append(2.0)
                    elif self.counts[spend] == 0:
                        chosen = spend
                        selected_scores.append(2.0)
                    else:
                        dq = float(self.quality_hat[spend] - self.quality_hat[skip])
                        dt = max(float(self.token_hat[spend] - self.token_hat[skip]), 1.0)
                        voc = estimate_token_voc(dq, dt, self.utility.lambda_tokens)
                        self.last_mvc = voc.ratio
                        chosen = spend if should_allocate(voc, 0.0, use_difference=True) else skip
                        selected_scores.append(float(voc.difference))
                else:
                    target_tier = min(1, len(cands) - 1)
                    matching = [e for e in cands if alternative_index(graph, graph.edges[e].target) == target_tier]
                    chosen = matching[0] if matching else cands[0]
                    selected_scores.append(3.0)
            selected_edges.append(chosen)
            node = graph.edges[chosen].target
            path.append(node)

        return ResourceDecision(
            tuple(path),
            tuple(selected_edges),
            0,
            tuple(selected_scores),
            evaluated,
            float(self.last_mvc),
            0,
            0.0,
            decision_mode="adaptive_early_stop",
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        for obs in observations:
            e = obs.edge_id
            self.counts[e] += 1
            alpha = 1.0 if self.counts[e] == 1 else 0.25
            self.quality_hat[e] = (1.0 - alpha) * self.quality_hat[e] + alpha * obs.quality
            self.token_hat[e] = (1.0 - alpha) * self.token_hat[e] + alpha * obs.token_usage.path_tokens


class LagrangianBudgetAllocator(ResourceAgent):
    """Primal-dual online allocator adapting dual price to remaining per-step budget_cap."""

    name = "lagrangian_budget"

    def __init__(
        self,
        edge_count: int,
        rng: np.random.Generator,
        total_steps: int = 60,
        target_tokens: float = 420.0,
    ) -> None:
        super().__init__(rng)
        self.total_steps = max(total_steps, 1)
        self.default_target_tokens = target_tokens
        self.dual = 0.20
        self.quality_hat = np.full(edge_count, 0.65)
        self.token_hat = np.full(edge_count, 180.0)
        self.counts = np.zeros(edge_count, dtype=int)

    def _step_target(self, step: int, budget_cap: float) -> float:
        steps_left = max(self.total_steps - step, 1)
        cap_per_step = budget_cap / float(steps_left) if budget_cap > 2500.0 else budget_cap
        return float(min(self.default_target_tokens, max(60.0, 0.90 * cap_per_step)))

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        def score(edge_id: int) -> float:
            bonus = 0.04 if self.counts[edge_id] == 0 else 0.0
            return float(self.quality_hat[edge_id] - self.dual * (self.token_hat[edge_id] / TOKEN_SCALE) + bonus)

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            0,
            decision.edge_scores,
            _visited_candidates(graph, decision.path),
            0.0,
            0,
            0.0,
            decision_mode="lagrangian_primal_dual",
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap: float) -> None:
        used = 0.0
        for obs in observations:
            e = obs.edge_id
            self.counts[e] += 1
            alpha = 1.0 if self.counts[e] == 1 else 0.22
            self.quality_hat[e] = (1.0 - alpha) * self.quality_hat[e] + alpha * obs.quality
            self.token_hat[e] = (1.0 - alpha) * self.token_hat[e] + alpha * obs.token_usage.path_tokens
            used += obs.token_usage.path_tokens
        target = self._step_target(step, budget_cap)
        self.dual = float(np.clip(self.dual + 0.0015 * (used - target), 0.0, 5.0))


class StaticCascade(ResourceAgent):
    """Cheap tier first; escalate to standard/frontier if last step quality fell below floor."""

    name = "static_cascade"

    def __init__(self, rng: np.random.Generator, floor: float = 0.66) -> None:
        super().__init__(rng)
        self.floor = floor
        self.last_quality = 1.0

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        preferred = min(2, len(graph.layers[1]) - 1) if self.last_quality < self.floor else 0

        def score(edge_id: int) -> float:
            target = graph.edges[edge_id].target
            if target in {graph.source, graph.sink}:
                return 1.0
            alt = alternative_index(graph, target)
            return 3.0 if alt == preferred else 0.3

        decision = greedy_local_route(graph, self.rng, score)
        return ResourceDecision(
            decision.path,
            decision.edge_ids,
            0,
            decision.edge_scores,
            _visited_candidates(graph, decision.path),
            0.0,
            0,
            0.0,
            decision_mode="static_cascade",
        )

    def update(self, graph, decision, observations: list[ResourceObservation], step, budget_cap) -> None:
        if observations:
            self.last_quality = float(np.mean([obs.quality for obs in observations]))
