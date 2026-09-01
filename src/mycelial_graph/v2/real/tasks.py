from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4] / "experiments" / "v2_1" / "real_smoke"


@dataclass(frozen=True)
class RealCodingTask:
    task_id: str
    source_path: Path
    test_path: Path
    fixed_source: str

    def read_source(self) -> str:
        return self.source_path.read_text(encoding="utf-8")

    def read_test(self) -> str:
        return self.test_path.read_text(encoding="utf-8")


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


def grade_task(task: RealCodingTask, *, apply_fix: bool) -> bool:
    namespace: dict[str, object] = {}
    source = task.fixed_source if apply_fix else task.read_source()
    exec(compile(source, str(task.source_path), "exec"), namespace, namespace)
    test_source = task.read_test()
    try:
        exec(compile(test_source, str(task.test_path), "exec"), namespace, namespace)
    except AssertionError:
        return False
    except Exception:
        return False
    return True
