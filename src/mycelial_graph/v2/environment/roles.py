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
    """Assign heterogeneous AI operator role to each transition layer.

    Preserves exact 3-layer mapping (retrieval -> model -> verification -> output)
    while supporting 2-layer and 4..6-layer pipelines cleanly.
    """
    edge = graph.edges[edge_id]
    source_layer = layer_index(graph, edge.source)
    last_internal = len(graph.layers) - 2
    if source_layer == last_internal:
        return "output"
    if len(graph.layers) == 5:
        if source_layer == 0:
            return "retrieval"
        if source_layer == RETRIEVER_LAYER:
            return "model"
        return "verification"
    if len(graph.layers) == 4:
        return "model" if source_layer == 0 else "verification"
    # Depth >= 4 internal layers: prompt -> retrieval -> model -> [tool/memory...] -> verification -> output
    if source_layer == 0:
        return "prompt"
    if source_layer == 1:
        return "retrieval"
    if source_layer == 2:
        return "model"
    if source_layer == last_internal - 1:
        return "verification"
    return "tool" if source_layer % 2 == 1 else "memory"


def compute_class(graph: LayeredDAG, edge_id: int) -> str:
    """Map alternative index to a compute class used by baselines."""
    edge = graph.edges[edge_id]
    alt = (
        alternative_index(graph, edge.target)
        if layer_index(graph, edge.target) not in {0, len(graph.layers) - 1}
        else 0
    )
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
