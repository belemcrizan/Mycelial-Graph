from __future__ import annotations

from collections.abc import Callable

import numpy as np

from ..environment.graph import LayeredDAG
from .base import AgentDecision, stable_softmax


def stochastic_local_route(
    graph: LayeredDAG,
    rng: np.random.Generator,
    score: Callable[[int], float],
    temperature: float,
    exploration_probability: float,
) -> AgentDecision:
    node = graph.source
    path = [node]
    selected_edges: list[int] = []
    scores: list[float] = []
    exploratory = 0
    while node != graph.sink:
        candidates = graph.outgoing[node]
        candidate_scores = np.array([score(edge_id) for edge_id in candidates], dtype=float)
        is_exploration = len(candidates) > 1 and rng.random() < exploration_probability
        if len(candidates) == 1:
            chosen_index = 0
        elif is_exploration:
            chosen_index = int(rng.integers(0, len(candidates)))
            exploratory += 1
        else:
            probabilities = stable_softmax(candidate_scores, temperature)
            chosen_index = int(rng.choice(len(candidates), p=probabilities))
        edge_id = candidates[chosen_index]
        edge = graph.edges[edge_id]
        selected_edges.append(edge_id)
        scores.append(float(candidate_scores[chosen_index]))
        path.append(edge.target)
        node = edge.target
    return AgentDecision(tuple(path), tuple(selected_edges), exploratory, tuple(scores))


def greedy_local_route(
    graph: LayeredDAG,
    rng: np.random.Generator,
    score: Callable[[int], float],
) -> AgentDecision:
    node = graph.source
    path = [node]
    selected_edges: list[int] = []
    scores: list[float] = []
    while node != graph.sink:
        candidates = graph.outgoing[node]
        candidate_scores = np.array([score(edge_id) for edge_id in candidates], dtype=float)
        best = np.flatnonzero(np.isclose(candidate_scores, np.max(candidate_scores)))
        chosen_index = int(rng.choice(best))
        edge_id = candidates[chosen_index]
        edge = graph.edges[edge_id]
        selected_edges.append(edge_id)
        scores.append(float(candidate_scores[chosen_index]))
        path.append(edge.target)
        node = edge.target
    return AgentDecision(tuple(path), tuple(selected_edges), 0, tuple(scores))

