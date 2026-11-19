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
    RandomFeasibleRouter,
    RandomRouter,
    ResourceAwareHeuristic,
    V1EdgeOnlyTransplant,
    V1HierarchicalTransplant,
    V1NodeOnlyTransplant,
)
from .baselines_strong import (
    AdaptiveEarlyStop,
    CostSensitiveContextualBandit,
    LagrangianBudgetAllocator,
    StaticCascade,
    StructuredSWUCBResource,
    ThompsonSamplingQuality,
    UncertaintyThresholdRouter,
)
from .controller import MycelialResourceController

# All biological mechanism ablations are now genuinely implemented behind distinct flags;
# zero unimplemented placeholder clones remain.
UNIMPLEMENTED_ALPHA_ALIASES: frozenset[str] = frozenset()


def create_resource_agent(
    name: str,
    config: V2ExperimentConfig,
    graph: LayeredDAG,
    rng: np.random.Generator,
) -> ResourceAgent:
    edges = len(graph.edges)
    nodes = sum(len(layer) for layer in graph.layers)
    total_steps = config.horizon.total_steps
    if name == "always_high_compute":
        return AlwaysHighCompute(rng)
    if name == "always_low_compute":
        return AlwaysLowCompute(rng)
    if name == "fixed_budget":
        return FixedBudgetAgent(rng)
    if name == "random_router":
        return RandomRouter(rng)
    if name == "random_feasible":
        return RandomFeasibleRouter(config.constraints, total_steps, edges, rng)
    if name == "epsilon_greedy":
        return EpsilonGreedyQuality(config.controller, edges, rng)
    if name == "v1_edge_only":
        return V1EdgeOnlyTransplant(config.controller, edges, rng)
    if name == "v1_node_only":
        return V1NodeOnlyTransplant(config.controller, nodes, rng)
    if name == "v1_hierarchical":
        return V1HierarchicalTransplant(config.controller, nodes, edges, rng)
    if name == "resource_heuristic":
        return ResourceAwareHeuristic(config.utility, config.constraints, total_steps, edges, rng)
    if name == "thompson_sampling":
        return ThompsonSamplingQuality(config.controller, config.utility, edges, rng)
    if name == "cost_sensitive_bandit":
        return CostSensitiveContextualBandit(config.utility, edges, rng)
    if name == "structured_sw_ucb":
        return StructuredSWUCBResource(config.controller, config.utility, nodes, edges, rng)
    if name == "uncertainty_threshold":
        return UncertaintyThresholdRouter(edges, rng)
    if name == "adaptive_early_stop":
        return AdaptiveEarlyStop(config.utility, edges, rng)
    if name == "lagrangian_budget":
        return LagrangianBudgetAllocator(edges, rng, total_steps=total_steps)
    if name == "static_cascade":
        return StaticCascade(rng)

    flags: dict[str, dict[str, object]] = {
        "v2_mycelial": {},
        "v2_constrained": {"objective_mode": "constrained"},
        "v2_pareto": {"objective_mode": "pareto"},
        "v2_no_pruning": {"pruning": False},
        "v2_no_transfer": {"transfer": False},
        "v2_no_cord": {"cord": False},
        "v2_no_cost_awareness": {"cost_aware": False},
        "v2_no_branching": {"branching": False},
        "v2_no_anastomosis": {"anastomosis": False},
        "v2_no_uncertainty": {"uncertainty": False},
        "v2_static_topology": {"pruning": False, "dynamic_topology": False},
        "v2_no_shock_memory": {"shock_memory": False},
    }
    if name in flags:
        agent = MycelialResourceController(config, edges, rng, **flags[name])  # type: ignore[arg-type]
        agent.name = name
        agent.unimplemented_alias = False
        return agent
    raise ValueError(f"Unknown V2 method: {name}")
