from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .shadow import ShadowDecision, shadow_recommend
from .tasks import RealCodingTask, default_smoke_tasks, grade_task


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


def run_real_task(task: RealCodingTask, policy: str, *, shadow: bool = False) -> RealRunResult:
    """Matched-scaffold local runner. No network and no provider keys.

    Quality is executable: the grader runs the task test. LLM-as-judge is not used.
    """
    traces: list[str] = []
    tokens = 40
    tool_calls = 0
    if policy in {"always_high_compute", "v2_mycelial", "adaptive_early_stop"}:
        traces.append(task.read_source())
        tokens += len(task.read_source().split())
        traces.append(task.read_test())
        tokens += len(task.read_test().split())
        tool_calls += 2
        passed = grade_task(task, apply_fix=True)
        tokens += 80
        tool_calls += 1
        stop_reason = "QUALITY_SUFFICIENT" if passed else "NO_FEASIBLE_ACTION"
    elif policy == "always_low_compute":
        traces.append(task.read_source())
        tokens += len(task.read_source().split())
        passed = grade_task(task, apply_fix=False)
        stop_reason = "MARGINAL_COMPUTE_NOT_WORTH_IT"
    else:
        traces.append(task.read_source())
        tokens += len(task.read_source().split())
        passed = grade_task(task, apply_fix=policy == "fixed_budget")
        tokens += 40 if policy == "fixed_budget" else 0
        stop_reason = "QUALITY_SUFFICIENT" if passed else "BUDGET_EXHAUSTED"
    shadow_payload = None
    if shadow:
        rec = shadow_recommend(task, tokens, passed)
        shadow_payload = rec.to_dict()
    return RealRunResult(
        task_id=task.task_id,
        policy=policy,
        passed=passed,
        tokens=tokens,
        tool_calls=tool_calls,
        latency_ms=5.0 * max(1, tool_calls),
        stop_reason=stop_reason,
        shadow=shadow_payload,
    )


def run_real_smoke(policies: tuple[str, ...] = ("always_high_compute", "always_low_compute", "v2_mycelial")) -> dict[str, Any]:
    tasks = default_smoke_tasks()
    rows = [run_real_task(task, policy, shadow=True).__dict__ for task in tasks for policy in policies]
    return {
        "protocol": "MG-EXP-V2.1-REAL-SMOKE",
        "n_tasks": len(tasks),
        "policies": list(policies),
        "results": rows,
        "claim_boundary": (
            "Local fixture tasks with executable tests. This is not SWE-bench. "
            "Do not claim real coding-agent token reduction from this smoke run."
        ),
    }
