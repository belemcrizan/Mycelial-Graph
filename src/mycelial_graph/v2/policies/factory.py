from __future__ import annotations

import numpy as np

from ...environment.graph import LayeredDAG
from ..types import V2ExperimentConfig
from .base import ResourceAgent
from .baselines import (
    AlwaysHighCompute,
    AlwaysLowCompute,
    EpsilonGreedyQuality,
    FixedBudgetAgent,
    RandomRouter,
    V1EdgeOnlyTransplant,
)
from .controller import MycelialResourceController


def create_resource_agent(
    name: str,
    config: V2ExperimentConfig,
    graph: LayeredDAG,
    rng: np.random.Generator,
) -> ResourceAgent:
    edges = len(graph.edges)
    if name == "always_high_compute":
        return AlwaysHighCompute(rng)
    if name == "always_low_compute":
        return AlwaysLowCompute(rng)
    if name == "fixed_budget":
        return FixedBudgetAgent(rng)
    if name == "random_router":
        return RandomRouter(rng)
    if name == "epsilon_greedy":
        return EpsilonGreedyQuality(config.controller, edges, rng)
    if name == "v1_edge_only":
        return V1EdgeOnlyTransplant(config.controller, edges, rng)
    flags = {
        "v2_mycelial": {},
        "v2_no_pruning": {"pruning": False},
        "v2_no_transfer": {"transfer": False},
        "v2_no_cord": {"cord": False},
        "v2_no_cost_awareness": {"cost_aware": False},
        "v2_no_branching": {},
        "v2_no_anastomosis": {},
        "v2_no_uncertainty": {},
        "v2_static_topology": {},
        "v2_no_shock_memory": {},
    }
    if name in flags:
        agent = MycelialResourceController(config, edges, rng, **flags[name])
        agent.name = name
        return agent
    raise ValueError(f"Unknown V2 method: {name}")
