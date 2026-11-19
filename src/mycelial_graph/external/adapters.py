"""Deterministic adapters. Malformed records are returned as errors, never dropped silently."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any

from .hashing import sha256_json
from .licenses import require_transform_allowed
from .schemas import SchemaError, parse_iso_utc, validate_incident_record, validate_routing_record


def _first_present(raw: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in raw and raw[key] not in (None, ""):
            return raw[key]
    return None


def _utc(value: Any) -> str:
    if value is None or value == "":
        raise SchemaError("missing timestamp")
    if isinstance(value, bool):
        raise SchemaError("timestamp must not be boolean")
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            raise SchemaError("timestamp must be finite")
        return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat().replace("+00:00", "Z")
    parsed = parse_iso_utc(str(value), field_name="timestamp")
    return parsed.isoformat().replace("+00:00", "Z")


def adapt_arena_preference_row(
    raw: dict[str, Any],
    *,
    source_id: str,
    source_version: str,
    for_redistribution: bool = False,
) -> dict[str, Any]:
    license_record = require_transform_allowed(source_id, for_redistribution=for_redistribution)
    errors: list[str] = []
    try:
        winner = "unknown"
        if raw.get("winner") in {"model_a", "model_b", "tie", "tie_both_bad"}:
            winner = raw["winner"]
        elif int(raw.get("winner_model_a") or 0) == 1:
            winner = "model_a"
        elif int(raw.get("winner_model_b") or 0) == 1:
            winner = "model_b"
        elif int(raw.get("winner_tie") or 0) == 1:
            winner = "tie"
        timestamp = _first_present(raw, "timestamp_utc", "tstamp", "timestamp")
        record = {
            "record_id": str(_first_present(raw, "question_id", "id") or ""),
            "timestamp_utc": _utc(timestamp) if timestamp is not None else "",
            "prompt_id": str(raw.get("question_id") or raw.get("id") or ""),
            "model_a": str(raw.get("model_a") or ""),
            "model_b": str(raw.get("model_b") or ""),
            "winner": winner,
            "source_id": source_id,
            "source_version": source_version,
            "license_state": license_record.state.value,
            "task_category": raw.get("category") or raw.get("language") or None,
            "raw_parent_keys": sorted(raw.keys()),
        }
        if not record["timestamp_utc"]:
            # Preference corpora are often static battles; allow explicit unknown time.
            record["timestamp_utc"] = "1970-01-01T00:00:00Z"
            record["temporal_status"] = "UNORDERED_STATIC_BATTLE"
        else:
            record["temporal_status"] = "TIMESTAMPED"
        validate_routing_record(record)
        record["record_sha256"] = sha256_json({k: v for k, v in record.items() if k != "record_sha256"})
        return {"ok": True, "record": record, "errors": []}
    except (SchemaError, PermissionError, ValueError, TypeError) as exc:
        errors.append(str(exc))
        return {"ok": False, "record": None, "errors": errors, "raw_excerpt_keys": sorted(raw.keys())}


def adapt_incident_row(
    raw: dict[str, Any],
    *,
    source_id: str = "synthetic-fixture",
    for_redistribution: bool = False,
) -> dict[str, Any]:
    require_transform_allowed(source_id, for_redistribution=for_redistribution)
    try:
        start_raw = _first_present(raw, "incident_start", "incident_start_utc")
        end_raw = _first_present(raw, "incident_end_utc", "incident_end")
        rec_raw = _first_present(raw, "recovery_timestamp")
        record = {
            "incident_id": str(_first_present(raw, "incident_id", "id") or ""),
            "provider": str(raw.get("provider") or ""),
            "service": str(raw.get("service") or ""),
            "component": raw.get("component"),
            "incident_start_utc": _utc(start_raw),
            "incident_end_utc": _utc(end_raw) if end_raw is not None else None,
            "status": str(raw.get("status") or ""),
            "severity_if_available": raw.get("severity"),
            "affected_surface": raw.get("affected_surface"),
            "recovery_timestamp": _utc(rec_raw) if rec_raw is not None else None,
            "source": str(raw.get("source") or source_id),
            "retrieved_at_utc": _utc(raw.get("retrieved_at_utc") or "1970-01-01T00:00:00Z"),
            "source_version": str(raw.get("source_version") or "unspecified"),
            "annotation_role": "external_incident_annotation_not_causal_truth",
        }
        validate_incident_record(record)
        record["record_sha256"] = sha256_json({k: v for k, v in record.items() if k != "record_sha256"})
        return {"ok": True, "record": record, "errors": []}
    except (SchemaError, PermissionError, ValueError, TypeError) as exc:
        return {"ok": False, "record": None, "errors": [str(exc)], "raw_excerpt_keys": sorted(raw.keys())}


def deduplicate_by_id(records: list[dict[str, Any]], id_field: str) -> tuple[list[dict[str, Any]], list[str]]:
    seen: dict[str, dict[str, Any]] = {}
    duplicates: list[str] = []
    for record in records:
        key = str(record[id_field])
        if key in seen:
            duplicates.append(key)
            continue
        seen[key] = record
    return list(seen.values()), duplicates


def detect_overlapping_incidents(records: list[dict[str, Any]]) -> list[tuple[str, str]]:
    overlaps: list[tuple[str, str]] = []
    max_dt = datetime(9999, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
    ordered = sorted(
        records,
        key=lambda row: (
            row["provider"],
            row["service"],
            parse_iso_utc(str(row["incident_start_utc"]), field_name="incident_start_utc"),
        ),
    )
    for i, left in enumerate(ordered):
        left_end_raw = left.get("incident_end_utc")
        left_end = parse_iso_utc(str(left_end_raw), field_name="incident_end_utc") if left_end_raw else max_dt
        for right in ordered[i + 1 :]:
            if (left["provider"], left["service"]) != (right["provider"], right["service"]):
                continue
            right_start = parse_iso_utc(str(right["incident_start_utc"]), field_name="incident_start_utc")
            if right_start <= left_end:
                overlaps.append((left["incident_id"], right["incident_id"]))
            else:
                break
    return overlaps
