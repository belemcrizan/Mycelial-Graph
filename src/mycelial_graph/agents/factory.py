from __future__ import annotations

import numpy as np

from ..environment.graph import LayeredDAG
from ..types import ExperimentConfig
from .base import Agent
from .edge_only import EdgeOnlyAgent
from .hierarchical import HierarchicalAgent
from .node_only import NodeOnlyAgent
from .structured_sw_ucb import StructuredSWUCBAgent


def create_agent(
    name: str,
    config: ExperimentConfig,
    graph: LayeredDAG,
    rng: np.random.Generator,
) -> Agent:
    if name == "edge_only":
        return EdgeOnlyAgent(config.mycelial, len(graph.edges), rng)
    if name == "node_only":
        return NodeOnlyAgent(config.mycelial, graph.node_count, rng)
    if name == "hierarchical":
        return HierarchicalAgent(
            config.mycelial,
            graph.node_count,
            len(graph.edges),
            rng,
        )
    if name == "structured_sw_ucb":
        return StructuredSWUCBAgent(
            config.structured_sw_ucb,
            graph.node_count,
            len(graph.edges),
            rng,
        )
    raise ValueError(f"Unknown method: {name}")
