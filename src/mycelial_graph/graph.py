"""Typed layered DAG and hard-policy boundary for Mycelial Graph V0."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


class GraphError(ValueError):
    pass


class NoFeasiblePathError(RuntimeError):
    pass


@dataclass(frozen=True)
class Component:
    id: str
    layer: str
    quality: float
    latency_ms: float
    cost_usd: float
    reliability: float
    load: float
    scored: bool = True


@dataclass(frozen=True)
class Edge:
    id: str
    source: str
    target: str


@dataclass(frozen=True)
class HardPolicy:
    """Non-negotiable constraints applied before any soft routing score."""

    blocked_components: frozenset[str]
    max_component_cost_usd: float

    @classmethod
    def from_config(cls, data: dict[str, Any]) -> "HardPolicy":
        return cls(
            blocked_components=frozenset(data.get("blocked_components", [])),
            max_component_cost_usd=float(data["max_component_cost_usd"]),
        )

    def permits(self, component: Component) -> bool:
        if component.id in {"source", "sink"}:
            return True
        return (
            component.id not in self.blocked_components
            and component.cost_usd <= self.max_component_cost_usd
        )


class LayeredGraph:
    def __init__(
        self,
        components: dict[str, Component],
        edges: Iterable[Edge],
        layer_order: tuple[tuple[str, ...], ...],
    ) -> None:
        self.components = dict(components)
        self.edges = {edge.id: edge for edge in edges}
        self.layer_order = layer_order
        self.source = "source"
        self.sink = "sink"
        self._outgoing: dict[str, list[Edge]] = {node: [] for node in components}
        for edge in self.edges.values():
            if edge.source not in components or edge.target not in components:
                raise GraphError(f"edge {edge.id} references an unknown node")
            self._outgoing[edge.source].append(edge)
        for outgoing in self._outgoing.values():
            outgoing.sort(key=lambda item: item.id)
        self._validate_layered_dag()

    @classmethod
    def from_config(cls, graph_data: dict[str, Any]) -> "LayeredGraph":
        components: dict[str, Component] = {
            "source": Component("source", "source", 1.0, 0.0, 0.0, 1.0, 0.0, False),
            "sink": Component("sink", "sink", 1.0, 0.0, 0.0, 1.0, 0.0, False),
        }
        ordered_layers: list[tuple[str, ...]] = []
        for layer in graph_data["layers"]:
            ids: list[str] = []
            for raw in layer["components"]:
                component = Component(
                    id=raw["id"],
                    layer=layer["name"],
                    quality=float(raw["quality"]),
                    latency_ms=float(raw["latency_ms"]),
                    cost_usd=float(raw["cost_usd"]),
                    reliability=float(raw["reliability"]),
                    load=float(raw["load"]),
                )
                components[component.id] = component
                ids.append(component.id)
            ordered_layers.append(tuple(ids))

        edges: list[Edge] = []
        previous = ("source",)
        for current in ordered_layers:
            for source in previous:
                for target in current:
                    edges.append(Edge(f"{source}__{target}", source, target))
            previous = current
        for source in previous:
            edges.append(Edge(f"{source}__sink", source, "sink"))
        return cls(components, edges, tuple(ordered_layers))

    def _validate_layered_dag(self) -> None:
        rank = {"source": -1, "sink": len(self.layer_order)}
        for index, layer in enumerate(self.layer_order):
            for node in layer:
                rank[node] = index
        for edge in self.edges.values():
            if rank[edge.target] != rank[edge.source] + 1:
                raise GraphError(f"edge {edge.id} skips or reverses a layer")
        if not self._outgoing[self.source]:
            raise GraphError("source has no outgoing edge")

    def outgoing(self, node_id: str, policy: HardPolicy) -> tuple[Edge, ...]:
        feasible = tuple(
            edge for edge in self._outgoing[node_id] if policy.permits(self.components[edge.target])
        )
        if node_id != self.sink and not feasible:
            raise NoFeasiblePathError(f"hard policy leaves no feasible edge from {node_id}")
        return feasible

    def all_paths(self, policy: HardPolicy) -> tuple[tuple[str, ...], ...]:
        paths: list[tuple[str, ...]] = []

        def visit(node: str, selected: tuple[str, ...]) -> None:
            if node == self.sink:
                paths.append(selected)
                return
            for edge in self.outgoing(node, policy):
                visit(edge.target, selected + (edge.id,))

        visit(self.source, ())
        return tuple(paths)

    @property
    def path_count(self) -> int:
        count = 1
        for layer in self.layer_order:
            count *= len(layer)
        return count

    def node_path(self, edge_path: Iterable[str]) -> tuple[str, ...]:
        nodes = [self.source]
        for edge_id in edge_path:
            nodes.append(self.edges[edge_id].target)
        return tuple(nodes)

