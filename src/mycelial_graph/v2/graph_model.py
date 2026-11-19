"""Explicit computational graph model G = (V, E, S, B, H) for Mycelial-Graph V2.

Preserves full compatibility with V1/V2 ``LayeredDAG`` while making component
roles, adaptive state ``S``, hard resource budgets ``B``, and observed health
signals ``H`` first-class, inspectable objects with invariant checks.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

import numpy as np

from ..environment.graph import Edge, LayeredDAG
from .environment.roles import alternative_index, edge_role, layer_index
from .ledger.tokens import ResourceObservation
from .resources.reservation import BudgetReservation

CANONICAL_COMPONENT_ROLES = (
    "source",
    "prompt",
    "retriever",
    "model",
    "tool",
    "memory",
    "validator",
    "guardrail",
    "fallback",
    "output_processor",
    "sink",
)


@dataclass(frozen=True)
class ComponentSpec:
    """Vertex v in V representing an AI pipeline operator."""

    id: int
    name: str
    role: str
    layer: int
    tier: int = 0
    is_guardrail: bool = False
    is_fallback: bool = False


@dataclass
class AdaptiveState:
    """Adaptive graph state S: conductances, structural memory, retraction mask, corridor budgets."""

    conductance: np.ndarray
    node_memory: np.ndarray
    retraction_evidence: np.ndarray
    retracted: np.ndarray
    corridor_budget: np.ndarray
    degradation_memory: np.ndarray


@dataclass
class HealthSignals:
    """Observed health & uncertainty monitor H with surprise and negative-transfer diagnostics."""

    edge_count: int
    node_count: int
    ewma_alpha: float = 0.22
    shock_alpha: float = 0.55
    surprise_z_threshold: float = 2.5
    discrepancy_scale: float = 0.12
    quality_hat: np.ndarray = field(init=False)
    quality_var: np.ndarray = field(init=False)
    token_hat: np.ndarray = field(init=False)
    cost_hat: np.ndarray = field(init=False)
    latency_hat: np.ndarray = field(init=False)
    fail_hat: np.ndarray = field(init=False)
    edge_counts: np.ndarray = field(init=False)
    node_quality_hat: np.ndarray = field(init=False)
    node_cost_hat: np.ndarray = field(init=False)
    node_fail_hat: np.ndarray = field(init=False)
    node_counts: np.ndarray = field(init=False)
    shock_flags: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.quality_hat = np.full(self.edge_count, 0.65, dtype=float)
        self.quality_var = np.full(self.edge_count, 0.025, dtype=float)
        self.token_hat = np.full(self.edge_count, 180.0, dtype=float)
        self.cost_hat = np.full(self.edge_count, 0.15, dtype=float)
        self.latency_hat = np.full(self.edge_count, 160.0, dtype=float)
        self.fail_hat = np.full(self.edge_count, 0.05, dtype=float)
        self.edge_counts = np.zeros(self.edge_count, dtype=int)
        self.node_quality_hat = np.full(self.node_count, 0.65, dtype=float)
        self.node_cost_hat = np.full(self.node_count, 0.15, dtype=float)
        self.node_fail_hat = np.full(self.node_count, 0.05, dtype=float)
        self.node_counts = np.zeros(self.node_count, dtype=int)
        self.shock_flags = np.zeros(self.edge_count, dtype=bool)

    def uncertainty(self, edge_id: int) -> float:
        n = int(self.edge_counts[edge_id])
        prior_std = 0.22 / np.sqrt(n + 1.0)
        emp_std = float(np.sqrt(max(self.quality_var[edge_id], 1e-6)))
        return float(0.6 * prior_std + 0.4 * emp_std)

    def observe(
        self,
        obs: ResourceObservation,
        target_node: int,
        *,
        shock_memory_enabled: bool = True,
    ) -> bool:
        """Update edge and component health estimates; return True if a shock surprise fired."""
        e = obs.edge_id
        self.edge_counts[e] += 1
        n = self.edge_counts[e]
        fail_val = 0.0 if obs.success else 1.0
        tokens = float(obs.token_usage.path_tokens)

        std_before = float(np.sqrt(max(self.quality_var[e], 1e-4)))
        q_surprise = abs(obs.quality - self.quality_hat[e]) / std_before if n > 2 else 0.0
        c_surprise = (
            abs(obs.monetary_cost - self.cost_hat[e]) / max(0.05, 0.5 * self.cost_hat[e])
            if n > 2
            else 0.0
        )
        is_shock = bool(
            shock_memory_enabled
            and n > 2
            and (q_surprise > self.surprise_z_threshold or c_surprise > self.surprise_z_threshold or (not obs.success and self.fail_hat[e] < 0.20))
        )
        self.shock_flags[e] = is_shock

        alpha = 1.0 if n == 1 else (self.shock_alpha if is_shock else max(self.ewma_alpha, 1.0 / n))
        diff = obs.quality - self.quality_hat[e]
        self.quality_hat[e] += alpha * diff
        self.quality_var[e] = (1.0 - alpha) * self.quality_var[e] + alpha * (diff * diff)
        self.token_hat[e] += alpha * (tokens - self.token_hat[e])
        self.cost_hat[e] += alpha * (obs.monetary_cost - self.cost_hat[e])
        self.latency_hat[e] += alpha * (obs.latency_ms - self.latency_hat[e])
        self.fail_hat[e] += alpha * (fail_val - self.fail_hat[e])

        self.node_counts[target_node] += 1
        n_node = self.node_counts[target_node]
        alpha_node = 1.0 if n_node == 1 else (self.shock_alpha if is_shock else max(self.ewma_alpha, 1.0 / n_node))
        self.node_quality_hat[target_node] += alpha_node * (obs.quality - self.node_quality_hat[target_node])
        self.node_cost_hat[target_node] += alpha_node * (obs.monetary_cost - self.node_cost_hat[target_node])
        self.node_fail_hat[target_node] += alpha_node * (fail_val - self.node_fail_hat[target_node])
        return is_shock

    def anastomosis_gate(self, target_node: int, incoming_edges: tuple[int, ...], max_mix: float = 0.45) -> float:
        """Discrepancy-gated structural sharing weight in [0, max_mix].

        When observed incoming edges into ``target_node`` agree (shared component
        degradation or health), pooling approaches ``max_mix`` so unobserved sibling
        transitions learn immediately. When observed incoming edges disagree strongly
        (edge-specific degradation), discrepancy suppresses pooling toward 0 to block
        negative transfer.
        """
        visited = [e for e in incoming_edges if self.edge_counts[e] > 0]
        if not visited or self.node_counts[target_node] == 0:
            return 0.0
        if len(visited) == 1:
            # Moderate cautious transfer from first observed incident edge to unvisited siblings.
            return float(0.55 * max_mix)
        vals = np.array([self.quality_hat[e] for e in visited], dtype=float)
        discrepancy = float(np.max(np.abs(vals - np.mean(vals))))
        cost_vals = np.array([self.cost_hat[e] for e in visited], dtype=float)
        cost_spread = float(np.std(cost_vals) / max(0.05, float(np.mean(cost_vals))))
        total_disc = discrepancy + 0.25 * cost_spread
        return float(max_mix * np.exp(-((total_disc / max(self.discrepancy_scale, 1e-4)) ** 2)))


@dataclass(frozen=True)
class ComputationalGraph:
    """Structure-aware computational graph G = (V, E, S, B, H) with DAG & connectivity invariants."""

    dag: LayeredDAG
    components: Mapping[int, ComponentSpec]
    incoming: Mapping[int, tuple[int, ...]]

    def __post_init__(self) -> None:
        object.__setattr__(self, "components", MappingProxyType(dict(self.components)))
        object.__setattr__(
            self,
            "incoming",
            MappingProxyType({int(k): tuple(v) for k, v in self.incoming.items()}),
        )
        self.validate_invariants()

    @property
    def source(self) -> int:
        return self.dag.source

    @property
    def sink(self) -> int:
        return self.dag.sink

    @property
    def node_count(self) -> int:
        return len(self.components)

    @property
    def edge_count(self) -> int:
        return len(self.dag.edges)

    def outgoing_edges(self, node_id: int) -> tuple[int, ...]:
        return self.dag.outgoing.get(node_id, ())

    def validate_invariants(self) -> None:
        if self.source not in self.components or self.sink not in self.components:
            raise ValueError("Graph must contain both source and sink components.")
        if self.source == self.sink:
            raise ValueError("Source and sink must be distinct.")
        # Verify topological acyclicity via Kahn's algorithm and source->sink reachability.
        indegree = {node: 0 for node in self.components}
        adj: dict[int, list[int]] = {node: [] for node in self.components}
        for edge in self.dag.edges:
            if edge.source not in self.components or edge.target not in self.components:
                raise ValueError(f"Edge {edge.id} endpoints must belong to V.")
            if edge.source == edge.target:
                raise ValueError(f"Self-loop on node {edge.source} violates DAG invariant.")
            adj[edge.source].append(edge.target)
            indegree[edge.target] += 1
        queue = deque([n for n, d in indegree.items() if d == 0])
        visited = 0
        while queue:
            u = queue.popleft()
            visited += 1
            for v in adj[u]:
                indegree[v] -= 1
                if indegree[v] == 0:
                    queue.append(v)
        if visited != len(self.components):
            raise ValueError("ComputationalGraph contains a cycle; DAG invariant violated.")
        if not self.has_feasible_path():
            raise ValueError("ComputationalGraph has no feasible path from source to sink.")

    def has_feasible_path(self, active_edge_mask: np.ndarray | None = None) -> bool:
        """Return True iff at least one active path connects source to sink."""
        seen = {self.source}
        queue = deque([self.source])
        while queue:
            u = queue.popleft()
            if u == self.sink:
                return True
            for edge_id in self.dag.outgoing.get(u, ()):
                if active_edge_mask is not None and not bool(active_edge_mask[edge_id]):
                    continue
                v = self.dag.edges[edge_id].target
                if v not in seen:
                    seen.add(v)
                    queue.append(v)
        return False

    @classmethod
    def from_layered_dag(cls, dag: LayeredDAG) -> "ComputationalGraph":
        components: dict[int, ComponentSpec] = {}
        incoming_lists: dict[int, list[int]] = {}
        role_by_internal_depth = {
            0: "retriever",
            1: "model",
            2: "validator",
            3: "tool",
            4: "guardrail",
        }
        last_layer = len(dag.layers) - 1
        for l_idx, layer in enumerate(dag.layers):
            for pos, node_id in enumerate(layer):
                incoming_lists[node_id] = []
                if l_idx == 0:
                    role = "source"
                elif l_idx == last_layer:
                    role = "sink"
                else:
                    role = role_by_internal_depth.get(l_idx - 1, "memory")
                is_guard = role in {"validator", "guardrail"} and pos > 0
                is_fb = pos == 0 and role in {"model", "retriever", "tool"}
                components[node_id] = ComponentSpec(
                    id=node_id,
                    name=f"{role}_{l_idx}_{pos}",
                    role=role,
                    layer=l_idx,
                    tier=pos,
                    is_guardrail=is_guard,
                    is_fallback=is_fb,
                )
        for edge in dag.edges:
            incoming_lists.setdefault(edge.target, []).append(edge.id)
        return cls(
            dag=dag,
            components=components,
            incoming={k: tuple(v) for k, v in incoming_lists.items()},
        )

    @classmethod
    def heterogeneous_pipeline(cls, layer_widths: tuple[int, ...] = (2, 3, 3, 2)) -> "ComputationalGraph":
        """Build a general heterogeneous pipeline DAG with arbitrary per-stage widths."""
        if not layer_widths or any(w < 1 for w in layer_widths):
            raise ValueError("All internal layer widths must be >= 1.")
        layers: list[tuple[int, ...]] = [(0,)]
        next_id = 1
        for width in layer_widths:
            layer = tuple(range(next_id, next_id + width))
            layers.append(layer)
            next_id += width
        sink = next_id
        layers.append((sink,))

        edges: list[Edge] = []
        outgoing: dict[int, list[int]] = {node: [] for layer in layers for node in layer}
        edge_lookup: dict[tuple[int, int], int] = {}
        for left, right in zip(layers[:-1], layers[1:]):
            for u in left:
                for v in right:
                    eid = len(edges)
                    edges.append(Edge(eid, u, v))
                    outgoing[u].append(eid)
                    edge_lookup[(u, v)] = eid
        dag = LayeredDAG(
            layers=tuple(layers),
            edges=tuple(edges),
            outgoing={node: tuple(ids) for node, ids in outgoing.items()},
            edge_lookup=edge_lookup,
        )
        return cls.from_layered_dag(dag)


def new_budget_state(cap: float) -> BudgetReservation:
    return BudgetReservation(cap=float(cap))


_ = (alternative_index, edge_role, layer_index)
