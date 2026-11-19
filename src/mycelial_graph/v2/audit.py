from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any


TOKEN_BUCKET_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cached_tokens",
    "reasoning_tokens",
    "estimated_tokens",
    "router_tokens",
    "verification_tokens",
    "tool_tokens",
    "retrieval_tokens",
    "summarization_tokens",
    "memory_tokens",
    "retry_tokens",
    "recovery_overhead_tokens",
    "state_overhead_tokens",
)


def audit_resource_traces(output_directory: str | Path) -> dict[str, Any]:
    """Recompute all token buckets, costs, latencies, and step counts from traces vs trial ledgers."""
    output = Path(output_directory).resolve()
    mismatches = []
    checked = 0
    for raw in sorted((output / "raw").rglob("*.json")):
        payload = json.loads(raw.read_text(encoding="utf-8"))
        for result in payload["scientific_payload"]["results"]:
            trace_path = output / result["trace_ref"]
            total = 0
            router = 0
            cost_sum = 0.0
            latency_sum = 0.0
            steps = 0
            bucket_sums = {field: 0 for field in TOKEN_BUCKET_FIELDS}
            with gzip.open(trace_path, "rt", encoding="utf-8") as stream:
                for line in stream:
                    record = json.loads(line)
                    steps += 1
                    rec_total = int(record["total_tokens"])
                    total += rec_total
                    router += int(record["router_tokens"])
                    cost_sum += float(record.get("monetary_cost", 0.0))
                    latency_sum += float(record.get("latency_ms", 0.0))
                    usage = record.get("token_usage") or {}
                    if int(usage.get("total_tokens", rec_total)) != rec_total:
                        mismatches.append(
                            {
                                "trial_id": result["trial_id"],
                                "step": record.get("step"),
                                "field": "token_usage.total_tokens",
                                "trace_record_total": rec_total,
                                "token_usage_total": usage.get("total_tokens"),
                            }
                        )
                    for field in TOKEN_BUCKET_FIELDS:
                        bucket_sums[field] += int(usage.get(field, 0))
            ledger = result["ledger"]
            checked += 1
            if total != int(ledger["total_tokens"]):
                mismatches.append(
                    {
                        "trial_id": result["trial_id"],
                        "field": "total_tokens",
                        "trace_total": total,
                        "ledger_total": ledger["total_tokens"],
                    }
                )
            if router != int(ledger["router_tokens"]):
                mismatches.append(
                    {
                        "trial_id": result["trial_id"],
                        "field": "router_tokens",
                        "trace": router,
                        "ledger": ledger["router_tokens"],
                    }
                )
            for field in TOKEN_BUCKET_FIELDS:
                if field in ledger and bucket_sums[field] != int(ledger[field]):
                    mismatches.append(
                        {
                            "trial_id": result["trial_id"],
                            "field": field,
                            "trace": bucket_sums[field],
                            "ledger": ledger[field],
                        }
                    )
            if steps != int(ledger.get("steps", steps)):
                mismatches.append(
                    {
                        "trial_id": result["trial_id"],
                        "field": "steps",
                        "trace": steps,
                        "ledger": ledger.get("steps"),
                    }
                )
            if abs(cost_sum - float(ledger.get("monetary_cost", 0.0))) > 1e-6:
                mismatches.append(
                    {
                        "trial_id": result["trial_id"],
                        "field": "monetary_cost",
                        "trace": cost_sum,
                        "ledger": ledger.get("monetary_cost"),
                    }
                )
            if abs(latency_sum - float(ledger.get("latency_ms", 0.0))) > 1e-5:
                mismatches.append(
                    {
                        "trial_id": result["trial_id"],
                        "field": "latency_ms",
                        "trace": latency_sum,
                        "ledger": ledger.get("latency_ms"),
                    }
                )
    return {
        "checked_trials": checked,
        "mismatches": mismatches,
        "ok": not mismatches,
    }
