from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from mycelial_graph.v2.ledger.tokens import TokenUsage


READ_FILE = "read_file"
SEARCH_REPOSITORY = "search_repository"
RETRIEVE_CONTEXT = "retrieve_context"
REASON = "reason"
EXECUTE_TEST = "execute_test"
INSPECT_FAILURE = "inspect_failure"
EDIT_CODE = "edit_code"
VERIFY = "verify"
ESCALATE = "escalate_model_context"
STOP = "stop"

ACTION_COSTS: dict[str, str] = {
    READ_FILE: "input_tokens",
    SEARCH_REPOSITORY: "retrieval_tokens",
    RETRIEVE_CONTEXT: "retrieval_tokens",
    REASON: "reasoning_tokens",
    EXECUTE_TEST: "tool_tokens",
    INSPECT_FAILURE: "tool_tokens",
    EDIT_CODE: "output_tokens",
    VERIFY: "verification_tokens",
    ESCALATE: "router_tokens",
    STOP: "router_tokens",
}


def count_tokens(text: str) -> int:
    """Whitespace proxy with a floor of 1. Not a provider tokenizer."""
    return max(1, len(text.split()))


def context_id_for(*blobs: str) -> str:
    digest = hashlib.sha256("\n".join(blobs).encode("utf-8")).hexdigest()
    return f"ctx-{digest[:16]}"


@dataclass(frozen=True)
class ActionRecord:
    action_id: str
    context_id: str
    name: str
    summary: str
    tokens: int
    usage: TokenUsage

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "context_id": self.context_id,
            "name": self.name,
            "summary": self.summary,
            "tokens": self.tokens,
            "usage": self.usage.to_dict(),
        }


class ActionLog:
    def __init__(self) -> None:
        self.records: list[ActionRecord] = []
        self._seq = 0
        self.ledger = TokenUsage()

    def record(self, name: str, payload: str, extra: int = 0) -> ActionRecord:
        self._seq += 1
        field = ACTION_COSTS[name]
        n = count_tokens(payload) + extra
        usage = TokenUsage(**{field: n})
        self.ledger = self.ledger.merged(usage)
        rec = ActionRecord(
            action_id=f"act-{self._seq:04d}",
            context_id=context_id_for(name, payload),
            name=name,
            summary=payload[:240],
            tokens=n,
            usage=usage,
        )
        self.records.append(rec)
        return rec

    @property
    def n_actions(self) -> int:
        return self._seq

    @property
    def total_tokens(self) -> int:
        return self.ledger.total_tokens

    @property
    def tool_calls(self) -> int:
        return sum(1 for rec in self.records if rec.name not in {REASON, STOP})
