from __future__ import annotations

from dataclasses import dataclass

from mycelial_graph.v2.biology.stop import stop_reason
from mycelial_graph.v2.biology.voc import estimate_voc, should_allocate
from mycelial_graph.v2.types import UtilityConfig


def _utility(envelope: ComputeEnvelope) -> UtilityConfig:
    return UtilityConfig(
        lambda_tokens=envelope.lambda_resource,
        lambda_cost=0.0,
        lambda_latency=0.0,
        lambda_risk=0.0,
        lambda_failure=0.0,
        lambda_state=0.0,
        mvc_threshold=envelope.voc_threshold,
        switching_penalty=0.0,
        switch_cooldown=0,
    )


@dataclass(frozen=True)
class ComputeEnvelope:
    policy: str
    max_actions: int
    token_budget: int
    allow_edit: bool
    allow_escalate: bool
    allow_test: bool
    lambda_resource: float
    voc_threshold: float


def envelope_for(policy: str) -> ComputeEnvelope:
    if policy == "always_low_compute":
        return ComputeEnvelope(policy, 8, 80, False, False, True, 0.35, 0.0)
    if policy == "fixed_budget":
        return ComputeEnvelope(policy, 10, 140, True, False, True, 0.35, 0.0)
    if policy == "adaptive_early_stop":
        return ComputeEnvelope(policy, 12, 220, True, False, True, 0.45, 0.0)
    if policy == "v2_mycelial":
        return ComputeEnvelope(policy, 16, 280, True, True, True, 0.25, 0.0)
    return ComputeEnvelope(policy, 20, 400, True, True, True, 0.05, 0.0)


def decide_stop(
    envelope: ComputeEnvelope,
    *,
    passed: bool,
    budget_left: float,
    tests_seen: int,
    edits_tried: int,
) -> str | None:
    if passed:
        return "QUALITY_SUFFICIENT"
    if budget_left <= 0:
        return "BUDGET_EXHAUSTED"
    if not envelope.allow_edit and tests_seen:
        return "MARGINAL_COMPUTE_NOT_WORTH_IT"
    extra = 24.0
    voc = estimate_voc(1.0 if not passed else 0.0, extra, envelope.lambda_resource)
    reason = stop_reason(budget_left, voc.ratio, _utility(envelope), passed)
    if reason == "budget_exhausted":
        return "BUDGET_EXHAUSTED"
    if envelope.policy in {"v2_mycelial", "adaptive_early_stop"} and edits_tried >= 1:
        if not should_allocate(voc, envelope.voc_threshold) and not envelope.allow_escalate:
            return "MARGINAL_COMPUTE_NOT_WORTH_IT"
        if reason == "low_marginal_value":
            return "MARGINAL_COMPUTE_NOT_WORTH_IT"
    return None
