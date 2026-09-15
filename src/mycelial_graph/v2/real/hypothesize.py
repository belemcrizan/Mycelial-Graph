from __future__ import annotations

import ast
from dataclasses import dataclass

from .tasks import TestOutcome


@dataclass(frozen=True)
class RepairHypothesis:
    bug_class: str
    source: str
    rationale: str


def _functions(tree: ast.AST) -> list[ast.FunctionDef]:
    return [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]


def _empty_guard_source(source: str) -> str | None:
    tree = ast.parse(source)
    funcs = _functions(tree)
    if len(funcs) != 1 or not funcs[0].args.args:
        return None
    func = funcs[0]
    arg = func.args.args[0].arg
    body = "\n    ".join(ast.unparse(stmt) for stmt in func.body)
    if f"if not {arg}:" in ast.unparse(func):
        return None
    return f"def {func.name}({arg}):\n    if not {arg}:\n        return None\n    {body}\n"


def _shifted_return_source(source: str, delta: int) -> str | None:
    tree = ast.parse(source)
    funcs = _functions(tree)
    if len(funcs) != 1:
        return None
    func = funcs[0]
    if len(func.body) != 1 or not isinstance(func.body[0], ast.Return) or func.body[0].value is None:
        return None
    expr = ast.unparse(func.body[0].value)
    args = ", ".join(a.arg for a in func.args.args)
    op = f"{expr} + {delta}" if delta > 0 else f"{expr} - {abs(delta)}"
    return f"def {func.name}({args}):\n    return {op}\n"


def propose_repairs(source: str, outcome: TestOutcome) -> list[RepairHypothesis]:
    """Propose edits from observed failures. Never consults a gold patch."""
    candidates: list[RepairHypothesis] = []
    if outcome.exception_type == "IndexError":
        guarded = _empty_guard_source(source)
        if guarded and guarded != source:
            candidates.append(RepairHypothesis("empty_access", guarded, "IndexError on access; try empty guard"))
    if outcome.exception_type == "AssertionError":
        expects_none = outcome.expected in {"None", "none"} or "None" in outcome.message
        if expects_none:
            guarded = _empty_guard_source(source)
            if guarded and guarded != source:
                candidates.append(
                    RepairHypothesis("empty_guard_none", guarded, "Assertion expects None on empty input")
                )
        else:
            for delta, label in ((-1, "off_by_one_minus"), (1, "off_by_one_plus")):
                shifted = _shifted_return_source(source, delta)
                if shifted and shifted != source:
                    candidates.append(
                        RepairHypothesis(label, shifted, f"numeric mismatch; try return shift {delta}")
                    )
    seen: set[str] = set()
    unique: list[RepairHypothesis] = []
    for item in candidates:
        if item.source in seen:
            continue
        seen.add(item.source)
        unique.append(item)
    return unique
