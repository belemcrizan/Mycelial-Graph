from __future__ import annotations

import numpy as np

from ..environment.graph import LayeredDAG
from ..types import MycelialConfig
from ._routing import stochastic_local_route
from .base import Agent, AgentDecision


class NodeOnlyAgent(Agent):
    """Ablation that shares all state through source and target nodes."""

    name = "node_only"

    def __init__(self, config: MycelialConfig, node_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.config = config
        self.source_effect = np.zeros(node_count, dtype=float)
        self.target_effect = np.zeros(node_count, dtype=float)

    def _project(self) -> None:
        self.source_effect -= np.mean(self.source_effect)
        self.target_effect -= np.mean(self.target_effect)

    def _score(self, graph: LayeredDAG, edge_id: int) -> float:
        edge = graph.edges[edge_id]
        return float(
            self.config.initial_conductance
            + self.source_effect[edge.source]
            + self.target_effect[edge.target]
        )

    def choose(self, graph: LayeredDAG, step: int) -> AgentDecision:
        decay = 1.0 - self.config.temporal_decay
        self.source_effect *= decay
        self.target_effect *= decay
        c = self.config
        return stochastic_local_route(
            graph,
            self.rng,
            lambda edge_id: self._score(graph, edge_id),
            c.temperature,
            c.exploration_probability,
        )

    def update(
        self,
        graph: LayeredDAG,
        decision: AgentDecision,
        rewards: np.ndarray,
        step: int,
    ) -> None:
        c = self.config
        self.source_effect *= 1.0 - c.shrinkage
        self.target_effect *= 1.0 - c.shrinkage
        for edge_id, reward in zip(decision.edge_ids, rewards):
            edge = graph.edges[edge_id]
            error = float(reward) - np.clip(self._score(graph, edge_id), 0.0, 1.0)
            self.source_effect[edge.source] += c.node_learning_rate * error / 2.0
            self.target_effect[edge.target] += c.node_learning_rate * error / 2.0
        self._project()

