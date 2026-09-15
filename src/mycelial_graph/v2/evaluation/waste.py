from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

LEDGER_SCHEMA_VERSION = "v2.1-waste-1"


@dataclass(frozen=True)
class WasteBreakdown:
    """Non-overlapping token buckets plus named proxies.

    Proxies are not causal token labels. They must not be summed into
    `accounted_total` unless they are already exclusive ledger fields.
    """

    ledger_schema_version: str
    input_tokens: int
    output_tokens: int
    reasoning_tokens: int
    retrieval_tokens: int
    verification_tokens: int
    tool_tokens: int
    summarization_tokens: int
    router_tokens: int
    state_overhead_tokens: int
    accounted_total: int
    # Proxies (not added into accounted_total)
    unique_context_tokens: int
    reingested_context_tokens: int
    unused_retrieval_tokens: int
    successful_trajectory_tokens: int
    cacheable_tokens: int
    cache_hit_equivalent_tokens: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def decompose_waste(ledger: dict[str, Any], *, success: bool, retrieval_used: bool) -> WasteBreakdown:
    input_tokens = int(ledger.get("input_tokens", 0))
    output_tokens = int(ledger.get("output_tokens", 0))
    reasoning = int(ledger.get("reasoning_tokens", 0))
    retrieval = int(ledger.get("retrieval_tokens", 0))
    verification = int(ledger.get("verification_tokens", 0))
    tool = int(ledger.get("tool_tokens", 0))
    summarization = int(ledger.get("summarization_tokens", 0))
    router = int(ledger.get("router_tokens", 0))
    state = int(ledger.get("state_overhead_tokens", 0))
    accounted = (
        input_tokens
        + output_tokens
        + reasoning
        + retrieval
        + verification
        + tool
        + summarization
        + router
        + state
    )
    unique_context = max(0, retrieval // 2 + input_tokens)
    reingested = max(0, retrieval - unique_context)
    unused_retrieval = 0 if retrieval_used else retrieval
    successful = accounted if success else 0
    cacheable = unique_context
    return WasteBreakdown(
        ledger_schema_version=LEDGER_SCHEMA_VERSION,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        reasoning_tokens=reasoning,
        retrieval_tokens=retrieval,
        verification_tokens=verification,
        tool_tokens=tool,
        summarization_tokens=summarization,
        router_tokens=router,
        state_overhead_tokens=state,
        accounted_total=accounted,
        unique_context_tokens=unique_context,
        reingested_context_tokens=reingested,
        unused_retrieval_tokens=unused_retrieval,
        successful_trajectory_tokens=successful,
        cacheable_tokens=cacheable,
        cache_hit_equivalent_tokens=0,
    )


def waste_identity_ok(breakdown: WasteBreakdown, ledger_total: int) -> bool:
    return breakdown.accounted_total == int(ledger_total)
