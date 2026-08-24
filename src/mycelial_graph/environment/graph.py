from __future__ import annotations

from dataclasses import dataclass
from itertools import product


@dataclass(frozen=True)
class Edge:
    id: int
    source: int
    target: int


@dataclass(frozen=True)
class LayeredDAG:
    layers: tuple[tuple[int, ...], ...]
    edges: tuple[Edge, ...]
    outgoing: dict[int, tuple[int, ...]]
    edge_lookup: dict[tuple[int, int], int]

    @property
    def source(self) -> int:
        return self.layers[0][0]

    @property
    def sink(self) -> int:
        return self.layers[-1][0]

    @property
    def node_count(self) -> int:
        return sum(len(layer) for layer in self.layers)

    @classmethod
    def complete_layered(cls, internal_layers: int, alternatives: int) -> "LayeredDAG":
        layers: list[tuple[int, ...]] = [(0,)]
        next_node = 1
        for _ in range(internal_layers):
            layer = tuple(range(next_node, next_node + alternatives))
            layers.append(layer)
            next_node += alternatives
        layers.append((next_node,))

        edges: list[Edge] = []
        outgoing: dict[int, list[int]] = {node: [] for layer in layers for node in layer}
        edge_lookup: dict[tuple[int, int], int] = {}
        for left, right in zip(layers[:-1], layers[1:]):
            for source in left:
                for target in right:
                    edge_id = len(edges)
                    edges.append(Edge(edge_id, source, target))
                    outgoing[source].append(edge_id)
                    edge_lookup[(source, target)] = edge_id
        return cls(
            layers=tuple(layers),
            edges=tuple(edges),
            outgoing={node: tuple(ids) for node, ids in outgoing.items()},
            edge_lookup=edge_lookup,
        )

    def all_paths(self) -> tuple[tuple[int, ...], ...]:
        internal = self.layers[1:-1]
        return tuple(
            (self.source, *selection, self.sink)
            for selection in product(*internal)
        )

    def path_edges(self, path: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(self.edge_lookup[(u, v)] for u, v in zip(path[:-1], path[1:]))

    def incident_edges(self, node: int) -> tuple[int, ...]:
        return tuple(
            edge.id for edge in self.edges if edge.source == node or edge.target == node
        )

