from __future__ import annotations

from dataclasses import dataclass

from ...environment.graph import LayeredDAG


RETRIEVER_LAYER = 1
MODEL_LAYER = 2
VERIFY_LAYER = 3


def layer_index(graph: LayeredDAG, node: int) -> int:
    for index, layer in enumerate(graph.layers):
        if node in layer:
            return index
    raise KeyError(node)


def alternative_index(graph: LayeredDAG, node: int) -> int:
    layer = graph.layers[layer_index(graph, node)]
    return layer.index(node)


def edge_role(graph: LayeredDAG, edge_id: int) -> str:
    edge = graph.edges[edge_id]
    source_layer = layer_index(graph, edge.source)
    if source_layer == 0:
        return "retrieval"
    if source_layer == RETRIEVER_LAYER:
        return "model"
    if source_layer == MODEL_LAYER:
        return "verification"
    return "output"


def compute_class(graph: LayeredDAG, edge_id: int) -> str:
    """Map alternative index to a compute class used by baselines."""
    edge = graph.edges[edge_id]
    alt = alternative_index(graph, edge.target) if layer_index(graph, edge.target) not in {0, len(graph.layers) - 1} else 0
    names = ("cheap", "standard", "frontier")
    if alt >= len(names):
        return "frontier"
    return names[alt]


@dataclass(frozen=True)
class ClassMeans:
    quality: float
    tokens: float
    latency_ms: float
    fail_prob: float
    price_per_1k: float
