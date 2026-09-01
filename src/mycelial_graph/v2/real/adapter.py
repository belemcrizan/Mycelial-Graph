from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .agent import run_local_agent
from .shadow import shadow_recommend
from .tasks import RealCodingTask, default_smoke_tasks


@dataclass(frozen=True)
class RealRunResult:
    task_id: str
    policy: str
    passed: bool
    tokens: int
    tool_calls: int
    latency_ms: float
    stop_reason: str
    shadow: dict[str, Any] | None
    used_known_fix: bool
    actions: tuple[dict[str, Any], ...]
    ledger: dict[str, Any]


def run_real_task(task: RealCodingTask, policy: str, *, shadow: bool = False) -> RealRunResult:
    """Matched-scaffold local runner. No network, no provider keys, no gold-patch injection.

    Quality is executable: tests run against the agent's edited workspace copy.
    """
    result = run_local_agent(task, policy)
    payload = result.to_payload()
    shadow_payload = None
    if shadow:
        rec = shadow_recommend(task, payload["tokens"], result.passed)
        shadow_payload = rec.to_dict()
    return RealRunResult(
        task_id=task.task_id,
        policy=policy,
        passed=result.passed,
        tokens=payload["tokens"],
        tool_calls=payload["tool_calls"],
        latency_ms=5.0 * max(1, payload["tool_calls"]),
        stop_reason=result.stop_reason,
        shadow=shadow_payload,
        used_known_fix=False,
        actions=tuple(payload["actions"]),
        ledger=payload["ledger"],
    )


def run_real_smoke(policies: tuple[str, ...] = ("always_high_compute", "always_low_compute", "v2_mycelial")) -> dict[str, Any]:
    tasks = default_smoke_tasks()
    rows = [run_real_task(task, policy, shadow=True).__dict__ for task in tasks for policy in policies]
    return {
        "protocol": "MG-EXP-V2.1-A-REAL-AGENT",
        "n_tasks": len(tasks),
        "policies": list(policies),
        "results": rows,
        "claim_boundary": (
            "Local fixture tasks with an autonomous read/test/edit loop and executable tests. "
            "This is not SWE-bench and does not use a known gold patch. "
            "Do not claim real coding-agent token reduction from this smoke run."
        ),
    }
