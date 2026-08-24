from __future__ import annotations

import numpy as np

from ..environment.graph import LayeredDAG
from ..types import MycelialConfig
from ._routing import stochastic_local_route
from .base import Agent, AgentDecision


class EdgeOnlyAgent(Agent):
    """Original mycelial conductance: every edge learns independently."""

    name = "edge_only"

    def __init__(self, config: MycelialConfig, edge_count: int, rng: np.random.Generator) -> None:
        super().__init__(rng)
        self.config = config
        self.conductance = np.full(edge_count, config.initial_conductance, dtype=float)

    def _decay(self) -> None:
        c = self.config
        self.conductance = c.initial_conductance + (
            self.conductance - c.initial_conductance
        ) * (1.0 - c.temporal_decay)

    def choose(self, graph: LayeredDAG, step: int) -> AgentDecision:
        self._decay()
        c = self.config
        return stochastic_local_route(
            graph,
            self.rng,
            lambda edge_id: float(self.conductance[edge_id]),
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
        for edge_id, reward in zip(decision.edge_ids, rewards):
            delta = float(reward) - 0.5
            reinforcement = c.exploration_reinforcement if decision.exploratory_edges else 0.0
            self.conductance[edge_id] = np.clip(
                self.conductance[edge_id] + c.learning_rate * delta + reinforcement,
                c.minimum_conductance,
                c.maximum_conductance,
            )

