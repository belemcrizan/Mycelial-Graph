"""Conservative scientific collector. Default is dry-run; paid live calls require explicit flags."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .hashing import sha256_json
from .schemas import validate_collector_record

COLLECTOR_VERSION = "MG-COLLECTOR-0.1.0"


@dataclass(frozen=True)
class CollectorLimits:
    dry_run: bool = True
    max_cost: float = 0.0
    max_requests: int = 0
    max_duration_seconds: float = 1.0
    authorize_spend: bool = False


class CollectorSafetyError(RuntimeError):
    pass


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def collect_workload(
    prompts: list[dict[str, Any]],
    endpoints: list[dict[str, Any]],
    limits: CollectorLimits,
) -> dict[str, Any]:
    if not limits.dry_run and not limits.authorize_spend:
        raise CollectorSafetyError("Live collection requires authorize_spend=True in addition to dry_run=False.")
    if not limits.dry_run and limits.max_cost <= 0:
        raise CollectorSafetyError("Live collection requires a positive max_cost cap.")
    if limits.max_requests < 0:
        raise CollectorSafetyError("max_requests must be non-negative.")
    started = time.perf_counter()
    records: list[dict[str, Any]] = []
    skipped_reason: list[str] = []
    request_count = 0
    estimated_cost = 0.0
    for prompt in prompts:
        for endpoint in endpoints:
            elapsed = time.perf_counter() - started
            if elapsed > limits.max_duration_seconds:
                skipped_reason.append("max_duration")
                break
            if limits.max_requests and request_count >= limits.max_requests:
                skipped_reason.append("max_requests")
                break
            unit_cost = float(endpoint.get("estimated_cost", 0.0))
            if estimated_cost + unit_cost > limits.max_cost and not limits.dry_run:
                skipped_reason.append("max_cost")
                break
            request_count += 1
            if limits.dry_run:
                record = {
                    "timestamp_utc": _now_utc(),
                    "prompt_id": str(prompt.get("prompt_id") or ""),
                    "task_type": prompt.get("task_type"),
                    "provider": str(endpoint.get("provider") or ""),
                    "model": str(endpoint.get("model") or ""),
                    "model_version": endpoint.get("model_version"),
                    "endpoint": endpoint.get("endpoint"),
                    "latency": None,
                    "time_to_first_token": None,
                    "tokens_input": None,
                    "tokens_output": None,
                    "router_tokens": None,
                    "cost": 0.0,
                    "success": False,
                    "error_type": "dry_run_no_network",
                    "http_status": None,
                    "timeout": False,
                    "retry_count": 0,
                    "quality_score": None,
                    "judge_score": None,
                    "region_if_known": endpoint.get("region"),
                    "collector_version": COLLECTOR_VERSION,
                    "dry_run": True,
                    "clock": "local_collector_utc",
                }
            else:
                raise CollectorSafetyError("Paid live HTTP execution is not implemented in this version.")
            validate_collector_record(record)
            record["record_sha256"] = sha256_json({k: v for k, v in record.items() if k != "record_sha256"})
            records.append(record)
        else:
            continue
        break
    return {
        "collector_version": COLLECTOR_VERSION,
        "limits": {
            "dry_run": limits.dry_run,
            "max_cost": limits.max_cost,
            "max_requests": limits.max_requests,
            "max_duration_seconds": limits.max_duration_seconds,
            "authorize_spend": limits.authorize_spend,
        },
        "n_records": len(records),
        "skipped": sorted(set(skipped_reason)),
        "records": records,
        "warning": "Do not interpret collector latency as provider degradation without clock and path diagnostics.",
    }
