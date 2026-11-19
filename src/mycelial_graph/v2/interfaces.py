"""Protocol-oriented interfaces for Mycelial-Graph V2.

Separates graph representation, routing policies, component health monitoring,
resource accounting, execution tracing, and provider adapters so the simulator
remains 100% self-contained and offline-testable while exposing clean seams
for future real-system adapters. No production-readiness claim is made here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

import numpy as np

from .ledger.tokens import ResourceObservation, TokenUsage


@runtime_checkable
class GraphEngine(Protocol):
    """Directed acyclic computational graph G = (V, E, S, B, H)."""

    @property
    def source(self) -> int: ...

    @property
    def sink(self) -> int: ...

    def outgoing_edges(self, node_id: int) -> tuple[int, ...]: ...

    def has_feasible_path(self, active_edge_mask: np.ndarray | None = None) -> bool: ...


@runtime_checkable
class ComponentHealthMonitor(Protocol):
    """Tracks recency-weighted component & edge health, uncertainty, and shock signals."""

    def observe(self, obs: ResourceObservation, target_node: int, step: int) -> float: ...

    def anastomosis_weight(self, target_node: int, sibling_edges: tuple[int, ...]) -> float: ...


@runtime_checkable
class ResourceLedger(Protocol):
    """Audit-grade resource ledger tracking tokens, calls, latency, cost, and retries."""

    @property
    def total_tokens(self) -> int: ...

    def to_dict(self) -> dict[str, Any]: ...


@runtime_checkable
class RoutingPolicy(Protocol):
    """Adaptive or baseline routing policy over a computational graph."""

    name: str

    def choose(self, graph: Any, step: int, budget_cap: float) -> Any: ...

    def update(
        self,
        graph: Any,
        decision: Any,
        observations: list[ResourceObservation],
        step: int,
        budget_cap: float,
    ) -> None: ...


@runtime_checkable
class TraceRecorder(Protocol):
    """Deterministic structured execution trace writer."""

    def record(self, step_record: Any) -> None: ...


@dataclass(frozen=True)
class AdapterRequest:
    task_id: str
    component_id: str
    component_role: str
    prompt_tokens_budget: int
    payload: str


@dataclass(frozen=True)
class AdapterResponse:
    component_id: str
    output_text: str
    token_usage: TokenUsage
    latency_ms: float
    monetary_cost: float
    success: bool
    validated_utility: float


@runtime_checkable
class ProviderAdapter(Protocol):
    """Clean boundary between graph execution and external LLM/tool/retriever providers."""

    def invoke(self, request: AdapterRequest) -> AdapterResponse: ...


class DeterministicMockProvider:
    """Deterministic, zero-network, zero-cost mock provider for integration testing."""

    def __init__(
        self,
        *,
        seed: int = 0,
        base_quality: float = 0.80,
        tokens_per_call: int = 120,
        price_per_1k: float = 0.15,
        latency_ms: float = 95.0,
        failure_rate: float = 0.02,
    ) -> None:
        self._rng = np.random.default_rng(seed)
        self.base_quality = base_quality
        self.tokens_per_call = tokens_per_call
        self.price_per_1k = price_per_1k
        self.latency_ms = latency_ms
        self.failure_rate = failure_rate

    def invoke(self, request: AdapterRequest) -> AdapterResponse:
        success = bool(self._rng.random() >= self.failure_rate)
        allowed = max(1, min(self.tokens_per_call, request.prompt_tokens_budget))
        in_tok = int(round(0.45 * allowed))
        out_tok = max(0, allowed - in_tok)
        usage = (
            TokenUsage(retrieval_tokens=allowed)
            if request.component_role in {"retriever", "retrieval"}
            else TokenUsage(verification_tokens=allowed)
            if request.component_role in {"validator", "guardrail", "verification"}
            else TokenUsage(tool_tokens=allowed)
            if request.component_role == "tool"
            else TokenUsage(memory_tokens=allowed)
            if request.component_role == "memory"
            else TokenUsage(input_tokens=in_tok, output_tokens=out_tok)
        )
        raw_q = float(np.clip(self.base_quality + self._rng.normal(0.0, 0.03), 0.0, 1.0))
        utility = raw_q if success else raw_q * 0.25
        cost = (usage.path_tokens / 1000.0) * self.price_per_1k
        return AdapterResponse(
            component_id=request.component_id,
            output_text=f"mock:{request.component_role}:{request.task_id}:ok={success}",
            token_usage=usage,
            latency_ms=float(max(1.0, self.latency_ms * (1.0 + self._rng.normal(0.0, 0.05)))),
            monetary_cost=cost,
            success=success,
            validated_utility=utility,
        )
