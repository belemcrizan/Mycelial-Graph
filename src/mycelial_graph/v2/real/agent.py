from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .actions import (
    EDIT_CODE,
    ESCALATE,
    EXECUTE_TEST,
    INSPECT_FAILURE,
    READ_FILE,
    REASON,
    RETRIEVE_CONTEXT,
    SEARCH_REPOSITORY,
    STOP,
    VERIFY,
    ActionLog,
)
from .controller import ComputeEnvelope, decide_stop, envelope_for
from .hypothesize import propose_repairs
from .tasks import RealCodingTask, TestOutcome, grade_source
from .workspace import TaskWorkspace


@dataclass
class AgentResult:
    passed: bool
    stop_reason: str
    log: ActionLog
    used_known_fix: bool = False

    def to_payload(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "stop_reason": self.stop_reason,
            "used_known_fix": self.used_known_fix,
            "actions": [rec.to_dict() for rec in self.log.records],
            "tokens": self.log.total_tokens,
            "tool_calls": self.log.tool_calls,
            "ledger": self.log.ledger.to_dict(),
        }


def _grade(workspace: TaskWorkspace) -> TestOutcome:
    return grade_source(
        workspace.read(workspace.source_path.name),
        workspace.read(workspace.test_path.name),
        source_name=workspace.source_path.name,
    )


def _budget_left(envelope: ComputeEnvelope, log: ActionLog) -> float:
    return float(envelope.token_budget - log.total_tokens)


def run_local_agent(task: RealCodingTask, policy: str) -> AgentResult:
    envelope: ComputeEnvelope = envelope_for(policy)
    workspace = TaskWorkspace(task)
    log = ActionLog()
    passed = False
    halt = "BUDGET_EXHAUSTED"
    tests_seen = 0
    edits_tried = 0
    try:
        source = workspace.read(workspace.source_path.name)
        log.record(READ_FILE, source)
        log.record(SEARCH_REPOSITORY, workspace.search("def "))
        test_source = workspace.read(workspace.test_path.name)
        log.record(RETRIEVE_CONTEXT, test_source)

        outcome = _grade(workspace)
        tests_seen += 1
        log.record(EXECUTE_TEST, outcome.message or "passed")
        if outcome.passed:
            passed = True
            halt = "QUALITY_SUFFICIENT"
        else:
            log.record(INSPECT_FAILURE, f"{outcome.exception_type}:{outcome.message}")
            halt_now = decide_stop(
                envelope,
                passed=False,
                budget_left=_budget_left(envelope, log),
                tests_seen=tests_seen,
                edits_tried=edits_tried,
            )
            if halt_now:
                halt = halt_now
            elif not envelope.allow_edit:
                halt = "MARGINAL_COMPUTE_NOT_WORTH_IT"
            else:
                queue = propose_repairs(workspace.read(workspace.source_path.name), outcome)
                log.record(REASON, "; ".join(item.bug_class for item in queue) or "no_hypothesis")
                escalated = False
                while queue and log.n_actions < envelope.max_actions and log.total_tokens < envelope.token_budget:
                    halt_now = decide_stop(
                        envelope,
                        passed=False,
                        budget_left=_budget_left(envelope, log),
                        tests_seen=tests_seen,
                        edits_tried=edits_tried,
                    )
                    if halt_now:
                        halt = halt_now
                        break
                    hypothesis = queue.pop(0)
                    if envelope.allow_escalate and edits_tried >= 1 and not escalated:
                        log.record(ESCALATE, hypothesis.bug_class)
                        escalated = True
                    workspace.write_source(hypothesis.source)
                    edits_tried += 1
                    log.record(EDIT_CODE, f"{hypothesis.bug_class}\n{hypothesis.source}")
                    outcome = _grade(workspace)
                    tests_seen += 1
                    log.record(VERIFY, outcome.message or "passed")
                    if outcome.passed:
                        passed = True
                        halt = "QUALITY_SUFFICIENT"
                        break
                    log.record(INSPECT_FAILURE, f"{outcome.exception_type}:{outcome.message}")
                else:
                    if not passed and halt == "BUDGET_EXHAUSTED" and not queue:
                        halt = "NO_FEASIBLE_ACTION"

        if passed:
            halt = "QUALITY_SUFFICIENT"
        log.record(STOP, halt)
        return AgentResult(passed=passed, stop_reason=halt, log=log)
    finally:
        workspace.close()
