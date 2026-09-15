"""Append-only scientific experiment ledger."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED = (
    "experiment_id",
    "protocol",
    "commit",
    "config",
    "seeds",
    "dataset",
    "status",
    "start",
    "finish",
    "result_classification",
    "artifact_location",
    "invalidations",
    "amendments",
    "notes",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def append_entry(path: str | Path, entry: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in REQUIRED if key not in entry]
    if missing:
        raise ValueError(f"Ledger entry missing fields: {missing}")
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing = destination.read_text(encoding="utf-8").splitlines()
        for line in existing:
            if not line.strip():
                continue
            previous = json.loads(line)
            if previous.get("experiment_id") == entry["experiment_id"] and previous.get("status") == "sealed":
                raise ValueError("Refusing to append a duplicate sealed experiment_id.")
    record = dict(entry)
    record["ledger_appended_at_utc"] = _now()
    with destination.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")
    return record


def read_ledger(path: str | Path) -> list[dict[str, Any]]:
    destination = Path(path)
    if not destination.exists():
        return []
    return [json.loads(line) for line in destination.read_text(encoding="utf-8").splitlines() if line.strip()]
