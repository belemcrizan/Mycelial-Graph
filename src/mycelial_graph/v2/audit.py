from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any


def audit_resource_traces(output_directory: str | Path) -> dict[str, Any]:
    """Recompute token totals from traces and compare to trial ledgers."""
    output = Path(output_directory).resolve()
    mismatches = []
    checked = 0
    for raw in sorted((output / "raw").rglob("*.json")):
        payload = json.loads(raw.read_text(encoding="utf-8"))
        for result in payload["scientific_payload"]["results"]:
            trace_path = output / result["trace_ref"]
            total = 0
            router = 0
            with gzip.open(trace_path, "rt", encoding="utf-8") as stream:
                for line in stream:
                    record = json.loads(line)
                    total += int(record["total_tokens"])
                    router += int(record["router_tokens"])
            ledger = result["ledger"]
            checked += 1
            if total != ledger["total_tokens"]:
                mismatches.append(
                    {
                        "trial_id": result["trial_id"],
                        "trace_total": total,
                        "ledger_total": ledger["total_tokens"],
                    }
                )
            if router != ledger["router_tokens"]:
                mismatches.append(
                    {
                        "trial_id": result["trial_id"],
                        "field": "router_tokens",
                        "trace": router,
                        "ledger": ledger["router_tokens"],
                    }
                )
    return {
        "checked_trials": checked,
        "mismatches": mismatches,
        "ok": not mismatches,
    }
