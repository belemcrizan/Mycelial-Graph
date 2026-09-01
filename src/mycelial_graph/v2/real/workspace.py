from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .tasks import RealCodingTask


class TaskWorkspace:
    """Isolated copy of a coding fixture. Edits never touch the repository tree."""

    def __init__(self, task: RealCodingTask) -> None:
        self.task = task
        self._tmp = tempfile.TemporaryDirectory(prefix=f"mycelial-{task.task_id}-")
        self.root = Path(self._tmp.name)
        self.source_path = self.root / task.source_path.name
        self.test_path = self.root / task.test_path.name
        shutil.copy2(task.source_path, self.source_path)
        shutil.copy2(task.test_path, self.test_path)

    def read(self, relative: str) -> str:
        path = self._resolve(relative)
        return path.read_text(encoding="utf-8")

    def write_source(self, contents: str) -> None:
        self.source_path.write_text(contents, encoding="utf-8")

    def search(self, query: str) -> str:
        hits: list[str] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if query in line:
                    hits.append(f"{path.name}:{lineno}:{line}")
        return "\n".join(hits) if hits else "(no matches)"

    def list_files(self) -> tuple[str, ...]:
        return tuple(sorted(p.name for p in self.root.iterdir() if p.is_file()))

    def close(self) -> None:
        self._tmp.cleanup()

    def _resolve(self, relative: str) -> Path:
        name = Path(relative).name
        if name == self.source_path.name:
            return self.source_path
        if name == self.test_path.name:
            return self.test_path
        raise FileNotFoundError(relative)
