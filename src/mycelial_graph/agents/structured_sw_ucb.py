from __future__ import annotations

from collections import deque

import numpy as np

from ..environment.graph import LayeredDAG
from ..types import UCBConfig
from ._routing import greedy_local_route
from .base import Agent, AgentDecision


class StructuredSWUCBAgent(Agent):
    """Sliding-window linear UCB with the same node-edge representation."""

    name = "structured_sw_ucb"

    def __init__(
        self,
        config: UCBConfig,
        node_count: int,
        edge_count: int,
        rng: np.random.Generator,
    ) -> None:
        super().__init__(rng)
        self.config = config
        self.node_count = node_count
        self.edge_count = edge_count
        self.dimension = 2 * node_count + edge_count
        self.observations: deque[tuple[np.ndarray, float]] = deque(
            maxlen=config.window_size
        )
        self.theta = np.zeros(self.dimension, dtype=float)
        self.inverse = np.eye(self.dimension, dtype=float) / config.ridge

    def _feature(self, graph: LayeredDAG, edge_id: int) -> np.ndarray:
        edge = graph.edges[edge_id]
        x = np.zeros(self.dimension, dtype=float)
        x[edge.source] = 1.0
        x[self.node_count + edge.target] = 1.0
        x[2 * self.node_count + edge_id] = 1.0
        return x / np.sqrt(3.0)

    def _fit(self) -> None:
        a = self.config.ridge * np.eye(self.dimension, dtype=float)
        b = np.zeros(self.dimension, dtype=float)
        for x, reward in self.observations:
            a += np.outer(x, x)
            b += x * reward
        self.inverse = np.linalg.inv(a)
        self.theta = self.inverse @ b

    def _score(self, graph: LayeredDAG, edge_id: int) -> float:
        x = self._feature(graph, edge_id)
        mean = float(x @ self.theta)
        uncertainty = float(np.sqrt(max(x @ self.inverse @ x, 0.0)))
        return mean + self.config.uncertainty_bonus * uncertainty

    def choose(self, graph: LayeredDAG, step: int) -> AgentDecision:
        self._fit()
        return greedy_local_route(
            graph,
            self.rng,
            lambda edge_id: self._score(graph, edge_id),
        )

    def update(
        self,
        graph: LayeredDAG,
        decision: AgentDecision,
        rewards: np.ndarray,
        step: int,
    ) -> None:
        for edge_id, reward in zip(decision.edge_ids, rewards):
            self.observations.append((self._feature(graph, edge_id), float(reward)))

