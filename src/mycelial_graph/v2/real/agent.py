from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from mycelial_graph.v2.resources import BudgetReservation

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
    count_tokens,
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


def _record_guarded(wallet: BudgetReservation, log: ActionLog, name: str, payload: str) -> bool:
    cost = float(count_tokens(payload))
    if not wallet.can_afford(cost):
        return False
    wallet.reserve(cost)
    wallet.commit(cost, cost)
    log.record(name, payload)
    return True


def run_local_agent(task: RealCodingTask, policy: str) -> AgentResult:
    envelope: ComputeEnvelope = envelope_for(policy)
    wallet = BudgetReservation(cap=float(envelope.token_budget))
    workspace = TaskWorkspace(task)
    log = ActionLog()
    passed = False
    halt = "BUDGET_EXHAUSTED"
    tests_seen = 0
    edits_tried = 0
    try:
        source = workspace.read(workspace.source_path.name)
        if not _record_guarded(wallet, log, READ_FILE, source):
            log.record(STOP, halt, charge_tokens=False)
            return AgentResult(passed=False, stop_reason=halt, log=log)

        if not _record_guarded(wallet, log, SEARCH_REPOSITORY, workspace.search("def ")):
            log.record(STOP, halt, charge_tokens=False)
            return AgentResult(passed=False, stop_reason=halt, log=log)

        test_source = workspace.read(workspace.test_path.name)
        if not _record_guarded(wallet, log, RETRIEVE_CONTEXT, test_source):
            log.record(STOP, halt, charge_tokens=False)
            return AgentResult(passed=False, stop_reason=halt, log=log)

        outcome = _grade(workspace)
        tests_seen += 1
        if not _record_guarded(wallet, log, EXECUTE_TEST, outcome.message or "passed"):
            log.record(STOP, halt, charge_tokens=False)
            return AgentResult(passed=False, stop_reason=halt, log=log)

        if outcome.passed:
            passed = True
            halt = "QUALITY_SUFFICIENT"
        else:
            if not _record_guarded(wallet, log, INSPECT_FAILURE, f"{outcome.exception_type}:{outcome.message}"):
                log.record(STOP, halt, charge_tokens=False)
                return AgentResult(passed=False, stop_reason=halt, log=log)

            halt_now = decide_stop(
                envelope,
                passed=False,
                budget_left=wallet.remaining,
                tests_seen=tests_seen,
                edits_tried=edits_tried,
            )
            if halt_now:
                halt = halt_now
            elif not envelope.allow_edit:
                halt = "MARGINAL_COMPUTE_NOT_WORTH_IT"
            else:
                queue = propose_repairs(workspace.read(workspace.source_path.name), outcome)
                reason_payload = "; ".join(item.bug_class for item in queue) or "no_hypothesis"
                if not _record_guarded(wallet, log, REASON, reason_payload):
                    halt = "BUDGET_EXHAUSTED"
                else:
                    escalated = False
                    while queue and log.n_actions < envelope.max_actions and wallet.remaining > 0:
                        halt_now = decide_stop(
                            envelope,
                            passed=False,
                            budget_left=wallet.remaining,
                            tests_seen=tests_seen,
                            edits_tried=edits_tried,
                        )
                        if halt_now:
                            halt = halt_now
                            break
                        hypothesis = queue.pop(0)
                        if envelope.allow_escalate and edits_tried >= 1 and not escalated:
                            if not _record_guarded(wallet, log, ESCALATE, hypothesis.bug_class):
                                halt = "BUDGET_EXHAUSTED"
                                break
                            escalated = True
                        edit_payload = f"{hypothesis.bug_class}\n{hypothesis.source}"
                        if not _record_guarded(wallet, log, EDIT_CODE, edit_payload):
                            halt = "BUDGET_EXHAUSTED"
                            break
                        workspace.write_source(hypothesis.source)
                        edits_tried += 1
                        outcome = _grade(workspace)
                        tests_seen += 1
                        if not _record_guarded(wallet, log, VERIFY, outcome.message or "passed"):
                            halt = "BUDGET_EXHAUSTED"
                            break
                        if outcome.passed:
                            passed = True
                            halt = "QUALITY_SUFFICIENT"
                            break
                        if not _record_guarded(wallet, log, INSPECT_FAILURE, f"{outcome.exception_type}:{outcome.message}"):
                            halt = "BUDGET_EXHAUSTED"
                            break
                    else:
                        if not passed and halt == "BUDGET_EXHAUSTED" and not queue:
                            halt = "NO_FEASIBLE_ACTION"

        if passed:
            halt = "QUALITY_SUFFICIENT"
        if not _record_guarded(wallet, log, STOP, halt):
            log.record(STOP, halt, charge_tokens=False)
        return AgentResult(passed=passed, stop_reason=halt, log=log)
    finally:
        workspace.close()
