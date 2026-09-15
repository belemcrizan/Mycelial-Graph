from __future__ import annotations

import traceback
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4] / "experiments" / "v2_1" / "real_smoke"


@dataclass(frozen=True)
class RealCodingTask:
    task_id: str
    source_path: Path
    test_path: Path
    oracle_source: str

    def read_source(self) -> str:
        return self.source_path.read_text(encoding="utf-8")

    def read_test(self) -> str:
        return self.test_path.read_text(encoding="utf-8")


@dataclass(frozen=True)
class TestOutcome:
    passed: bool
    exception_type: str | None
    message: str
    traceback_text: str
    expected: str
    actual: str


def default_smoke_tasks() -> tuple[RealCodingTask, ...]:
    off = ROOT / "off_by_one"
    empty = ROOT / "empty_guard"
    return (
        RealCodingTask(
            "off_by_one",
            off / "src.py",
            off / "test_src.py",
            "def last_index(items):\n    return len(items) - 1\n",
        ),
        RealCodingTask(
            "empty_guard",
            empty / "src.py",
            empty / "test_src.py",
            "def first(items):\n    if not items:\n        return None\n    return items[0]\n",
        ),
    )


def grade_source(source: str, test_source: str, *, source_name: str = "src.py") -> TestOutcome:
    """Execute tests against the given source. Does not inject an oracle patch."""
    namespace: dict[str, object] = {}
    try:
        exec(compile(source, source_name, "exec"), namespace, namespace)
    except Exception as exc:
        return TestOutcome(False, type(exc).__name__, str(exc), traceback.format_exc(), "", "")
    try:
        exec(compile(test_source, "test_src.py", "exec"), namespace, namespace)
    except AssertionError as exc:
        expected, actual = _probe_assertion(namespace, test_source)
        return TestOutcome(
            False,
            "AssertionError",
            str(exc) or f"expected {expected!r} got {actual!r}",
            traceback.format_exc(),
            expected,
            actual,
        )
    except Exception as exc:
        return TestOutcome(False, type(exc).__name__, str(exc), traceback.format_exc(), "", "")
    return TestOutcome(True, None, "", "", "", "")


def _probe_assertion(namespace: dict[str, object], test_source: str) -> tuple[str, str]:
    import ast

    try:
        tree = ast.parse(test_source)
    except SyntaxError:
        return ("", "")
    for node in tree.body:
        if not isinstance(node, ast.Assert) or not isinstance(node.test, ast.Compare):
            continue
        left = node.test.left
        right = node.test.comparators[0]
        try:
            actual = eval(compile(ast.Expression(left), "probe", "eval"), namespace, namespace)
            expected = eval(compile(ast.Expression(right), "probe", "eval"), namespace, namespace)
        except Exception as exc:
            return (ast.unparse(right), type(exc).__name__)
        if actual != expected:
            return (repr(expected), repr(actual))
    return ("", "")
