"""License gates. Adapters must not silently process forbidden or unknown redistribution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LicenseState(str, Enum):
    ALLOWED = "ALLOWED"
    GATED = "GATED"
    FORBIDDEN = "FORBIDDEN"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class LicenseRecord:
    source_id: str
    license_name: str
    state: LicenseState
    redistribution_allowed: bool
    commercial_use: str
    notes: str
    retrieved_at_utc: str
    source_url: str


# Snapshot of public cards inspected 2026-09-14. Re-check before any download.
KNOWN_SOURCES: dict[str, LicenseRecord] = {
    "lmsys-chat-1m": LicenseRecord(
        source_id="lmsys-chat-1m",
        license_name="LMSYS-Chat-1M Dataset License Agreement",
        state=LicenseState.GATED,
        redistribution_allowed=False,
        commercial_use="conditional_on_agreement",
        notes="Hugging Face gated dataset. Do not commit raw conversations. Adapter-only until a local gated copy exists.",
        retrieved_at_utc="2026-09-14T00:00:00Z",
        source_url="https://huggingface.co/datasets/lmsys/lmsys-chat-1m",
    ),
    "chatbot-arena-conversations": LicenseRecord(
        source_id="chatbot-arena-conversations",
        license_name="prompts CC-BY-4.0; model outputs CC-BY-NC-4.0",
        state=LicenseState.GATED,
        redistribution_allowed=False,
        commercial_use="prompts_yes_outputs_no",
        notes="Split license. Do not redistribute model outputs in this repository.",
        retrieved_at_utc="2026-09-14T00:00:00Z",
        source_url="https://huggingface.co/datasets/lmsys/chatbot_arena_conversations",
    ),
    "arena-human-preference-55k": LicenseRecord(
        source_id="arena-human-preference-55k",
        license_name="Apache-2.0 on dataset card (lmarena-ai/arena-human-preference-55k); re-check upstream content terms",
        state=LicenseState.GATED,
        redistribution_allowed=False,
        commercial_use="card_says_apache_but_contains_third_party_model_outputs",
        notes="Card license is not permission to commit the corpus. Adapter-only.",
        retrieved_at_utc="2026-09-14T00:00:00Z",
        source_url="https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k",
    ),
    "routellm-code": LicenseRecord(
        source_id="routellm-code",
        license_name="Apache-2.0",
        state=LicenseState.ALLOWED,
        redistribution_allowed=True,
        commercial_use="yes_for_code",
        notes="Applies to lm-sys/RouteLLM software, not automatically to every HF dataset it uses.",
        retrieved_at_utc="2026-09-14T00:00:00Z",
        source_url="https://github.com/lm-sys/RouteLLM",
    ),
    "routellm-gpt4-dataset": LicenseRecord(
        source_id="routellm-gpt4-dataset",
        license_name="Apache-2.0 on Hugging Face card",
        state=LicenseState.GATED,
        redistribution_allowed=False,
        commercial_use="card_apache_recheck_gpt4_terms",
        notes="Do not commit the dataset. Judge labels may inherit model-output restrictions.",
        retrieved_at_utc="2026-09-14T00:00:00Z",
        source_url="https://huggingface.co/datasets/routellm/gpt4_dataset",
    ),
    "routerarena-code": LicenseRecord(
        source_id="routerarena-code",
        license_name="Apache-2.0",
        state=LicenseState.ALLOWED,
        redistribution_allowed=True,
        commercial_use="yes_for_code",
        notes="RouteWorks/RouterArena software license. Dataset license is not assumed identical.",
        retrieved_at_utc="2026-09-14T00:00:00Z",
        source_url="https://github.com/RouteWorks/RouterArena",
    ),
    "synthetic-fixture": LicenseRecord(
        source_id="synthetic-fixture",
        license_name="Apache-2.0 (this repository)",
        state=LicenseState.ALLOWED,
        redistribution_allowed=True,
        commercial_use="yes",
        notes="Local synthetic fixtures for adapter tests. Not external evidence.",
        retrieved_at_utc="2026-09-14T00:00:00Z",
        source_url="https://github.com/belemcrizan/Mycelial-Graph",
    ),
}


def require_transform_allowed(source_id: str, *, for_redistribution: bool) -> LicenseRecord:
    record = KNOWN_SOURCES.get(source_id)
    if record is None:
        raise PermissionError(f"Unknown source {source_id!r}: treat as UNKNOWN and refuse silent processing.")
    if record.state == LicenseState.UNKNOWN:
        raise PermissionError(f"Source {source_id} has UNKNOWN license state.")
    if record.state == LicenseState.FORBIDDEN:
        raise PermissionError(f"Source {source_id} is FORBIDDEN.")
    if for_redistribution and not record.redistribution_allowed:
        raise PermissionError(
            f"Source {source_id} may not be redistributed from this repository. Keep adapter-only."
        )
    return record
