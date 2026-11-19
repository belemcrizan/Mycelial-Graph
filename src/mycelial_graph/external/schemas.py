"""JSON Schema-like required-field contracts for external records."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Iterable

ROUTING_REQUIRED = (
    "record_id",
    "timestamp_utc",
    "prompt_id",
    "model_a",
    "model_b",
    "winner",
    "source_id",
    "source_version",
    "license_state",
)

INCIDENT_REQUIRED = (
    "incident_id",
    "provider",
    "service",
    "incident_start_utc",
    "status",
    "source",
    "retrieved_at_utc",
    "source_version",
)

LOGGED_BANDIT_REQUIRED = (
    "timestamp_utc",
    "context_id",
    "action",
    "reward",
    "propensity",
    "policy_version",
)

COLLECTOR_REQUIRED = (
    "timestamp_utc",
    "prompt_id",
    "provider",
    "model",
    "success",
    "collector_version",
    "dry_run",
)


class SchemaError(ValueError):
    pass


def require_fields(record: dict[str, Any], required: Iterable[str], *, kind: str) -> list[str]:
    missing = [name for name in required if name not in record or record[name] in (None, "")]
    if missing:
        raise SchemaError(f"{kind} missing required fields: {missing}")
    return []


def validate_routing_record(record: dict[str, Any]) -> dict[str, Any]:
    require_fields(record, ROUTING_REQUIRED, kind="routing_record")
    winner = record["winner"]
    if winner not in {"model_a", "model_b", "tie", "tie_both_bad", "unknown"}:
        raise SchemaError(f"unsupported winner {winner!r}")
    return record


def parse_iso_utc(text: str, *, field_name: str = "timestamp") -> datetime:
    cleaned = str(text).strip()
    if cleaned.endswith("Z"):
        cleaned = cleaned[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(cleaned)
    except ValueError as exc:
        raise SchemaError(f"{field_name} is not valid ISO-8601: {text!r}") from exc
    if parsed.tzinfo is None:
        raise SchemaError(f"{field_name} must include an explicit timezone (prefer UTC Z).")
    return parsed.astimezone(timezone.utc)


def _finite_number(value: Any, *, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        try:
            if isinstance(value, bool):
                raise TypeError("boolean is not a numeric value")
            num = float(value)
        except (TypeError, ValueError) as exc:
            raise SchemaError(f"{field_name} must be a finite number") from exc
    else:
        num = float(value)
    if not math.isfinite(num):
        raise SchemaError(f"{field_name} must be finite")
    return num


def validate_incident_record(record: dict[str, Any]) -> dict[str, Any]:
    require_fields(record, INCIDENT_REQUIRED, kind="incident_record")
    start_dt = parse_iso_utc(str(record["incident_start_utc"]), field_name="incident_start_utc")
    parse_iso_utc(str(record["retrieved_at_utc"]), field_name="retrieved_at_utc")
    end = record.get("incident_end_utc")
    if end not in (None, ""):
        end_dt = parse_iso_utc(str(end), field_name="incident_end_utc")
        if end_dt < start_dt:
            raise SchemaError("incident_end_utc precedes incident_start_utc")
    return record


def validate_logged_bandit(record: dict[str, Any]) -> dict[str, Any]:
    require_fields(record, LOGGED_BANDIT_REQUIRED, kind="logged_bandit")
    _finite_number(record["reward"], field_name="reward")
    propensity = _finite_number(record["propensity"], field_name="propensity")
    if not 0.0 <= propensity <= 1.0:
        raise SchemaError("propensity must be in [0, 1]")
    return record


def validate_collector_record(record: dict[str, Any]) -> dict[str, Any]:
    require_fields(record, COLLECTOR_REQUIRED, kind="collector_record")
    if not isinstance(record["dry_run"], bool):
        raise SchemaError("dry_run must be boolean")
    return record
