from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np

from ...environment.graph import LayeredDAG
from ..ledger import ResourceObservation


@dataclass(frozen=True)
class ResourceDecision:
    path: tuple[int, ...]
    edge_ids: tuple[int, ...]
    exploratory_edges: int
    edge_scores: tuple[float, ...]
    router_candidates: int
    mvc: float
    prune_count: int
    transfer_l1: float


class ResourceAgent(ABC):
    name: str

    def __init__(self, rng: np.random.Generator) -> None:
        self.rng = rng

    @abstractmethod
    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        graph: LayeredDAG,
        decision: ResourceDecision,
        observations: list[ResourceObservation],
        step: int,
        budget_cap: float,
    ) -> None:
        raise NotImplementedError
