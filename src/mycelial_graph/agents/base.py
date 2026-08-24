from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from ..environment.graph import LayeredDAG


@dataclass(frozen=True)
class AgentDecision:
    path: tuple[int, ...]
    edge_ids: tuple[int, ...]
    exploratory_edges: int
    edge_scores: tuple[float, ...]


class Agent(ABC):
    name: str

    def __init__(self, rng: np.random.Generator) -> None:
        self.rng = rng

    @abstractmethod
    def choose(self, graph: LayeredDAG, step: int) -> AgentDecision:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        graph: LayeredDAG,
        decision: AgentDecision,
        rewards: np.ndarray,
        step: int,
    ) -> None:
        raise NotImplementedError


def stable_softmax(values: np.ndarray, temperature: float) -> np.ndarray:
    scaled = values / temperature
    scaled -= np.max(scaled)
    exp = np.exp(scaled)
    return exp / np.sum(exp)

