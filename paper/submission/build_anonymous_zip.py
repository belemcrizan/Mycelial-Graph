"""Build an anonymized supplementary ZIP for TMLR.

Usage:
    python paper/submission/build_anonymous_zip.py
"""

from __future__ import annotations

import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "paper" / "submission" / "anonymous_supplement.zip"

IDENTIFYING = re.compile(
    r"Crizan Belem Ribeiro|belemcrizan|belem@|Área de Trabalho|OneDrive",
    re.IGNORECASE,
)

INCLUDE_PREFIXES = (
    "src/",
    "tests/",
    "scripts/",
    "experiments/v1/",
    "paper/tmlr/",
    "paper/CLAIM_MAP.yaml",
    "docs/claim_evidence_matrix.yaml",
    "research/state.json",
    "research/runtime.json",
    "reproduce_confirmatory.py",
    "pyproject.toml",
    "requirements.lock.txt",
    "LICENSE",
    "CONFIRMATORY_RUNBOOK.md",
    "experiments/v1/EXPERIMENT_PROTOCOL_V1.md",
    "experiments/v1/ANALYSIS_PLAN.md",
    "experiments/v1/HYPOTHESIS_MATRIX.md",
)

EXCLUDE_PARTS = {
    "paper/tmlr/fancyhdr.sty",
    "paper/tmlr/math_commands.tex",
    "paper/tmlr/README.md",
}


def keep(relative: str) -> bool:
    posix = relative.replace("\\", "/")
    if "__pycache__" in posix or posix.endswith((".pyc", ".pyo")):
        return False
    if posix in EXCLUDE_PARTS:
        return False
    if posix.startswith("experiments/v1/artifacts/confirmatory/figures/"):
        return True
    return posix.startswith(INCLUDE_PREFIXES) or posix in {
        "reproduce_confirmatory.py",
        "pyproject.toml",
        "requirements.lock.txt",
        "LICENSE",
        "CONFIRMATORY_RUNBOOK.md",
        "paper/CLAIM_MAP.yaml",
        "docs/claim_evidence_matrix.yaml",
        "research/state.json",
        "research/runtime.json",
    }


def scrub(relative: str, data: bytes) -> bytes:
    if relative.replace("\\", "/").endswith((".png", ".pdf", ".gz", ".zip", ".bst", ".pyc")):
        return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    text = re.sub(r"[A-Za-z]:\\+Users\\+[^\\s\"']+", "ANONYMIZED_PATH", text)
    text = re.sub(r"Users\\\\[^\\]+", r"Users\\\\anonymous", text)
    text = re.sub(r"/home/[^/\s\"']+", "ANONYMIZED_PATH", text)
    text = text.replace("Crizan Belem Ribeiro", "Anonymous Author")
    text = text.replace("belemcrizan", "anonymous")
    text = text.replace("https://github.com/anonymous/Mycelial-Graph", "ANONYMIZED")
    text = text.replace("https://github.com/belemcrizan/Mycelial-Graph", "ANONYMIZED")
    text = text.replace("Área de Trabalho", "ANONYMIZED")
    text = text.replace("OneDrive", "ANONYMIZED")
    if relative.replace("\\", "/") == "pyproject.toml":
        text = re.sub(r'authors = \[\{name = "[^"]*"\}\]', 'authors = [{name = "Anonymous"}]', text)
    return text.encode("utf-8")


def main() -> int:
    files: list[Path] = []
    for prefix in (
        ROOT / "src",
        ROOT / "tests",
        ROOT / "scripts",
        ROOT / "experiments" / "v1",
        ROOT / "paper" / "tmlr",
    ):
        files.extend(p for p in prefix.rglob("*") if p.is_file())
    for extra in (
        ROOT / "reproduce_confirmatory.py",
        ROOT / "pyproject.toml",
        ROOT / "requirements.lock.txt",
        ROOT / "LICENSE",
        ROOT / "CONFIRMATORY_RUNBOOK.md",
        ROOT / "paper" / "CLAIM_MAP.yaml",
        ROOT / "docs" / "claim_evidence_matrix.yaml",
        ROOT / "research" / "state.json",
        ROOT / "research" / "runtime.json",
        ROOT / "paper" / "submission" / "README_ANONYMOUS.md",
    ):
        if extra.exists():
            files.append(extra)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    identifying_hits: list[str] = []
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        readme = (ROOT / "paper" / "submission" / "README_ANONYMOUS.md").read_bytes()
        archive.writestr("README.md", readme)
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            if relative.endswith("README_ANONYMOUS.md"):
                continue
            if "__pycache__" in relative or relative.endswith((".pyc", ".pyo")):
                continue
            if not keep(relative) and not relative.startswith(("src/", "tests/", "scripts/", "experiments/v1/", "paper/tmlr/")):
                continue
            if relative.startswith("experiments/v1/") and "/raw/" in relative:
                continue
            data = scrub(relative, path.read_bytes())
            try:
                decoded = data.decode("utf-8")
            except UnicodeDecodeError:
                decoded = ""
            if decoded and IDENTIFYING.search(decoded) and not relative.endswith((".png", ".pdf")):
                identifying_hits.append(relative)
            archive.writestr(relative, data)
        archive.writestr(
            "ANONYMIZATION_NOTICE.txt",
            f"Anonymous TMLR supplementary build {datetime.now(timezone.utc).isoformat()}\n"
            "Identifying names and repository URLs were scrubbed. Scientific hashes were kept.\n",
        )
    if identifying_hits:
        print("Identifying strings remain in:", file=sys.stderr)
        for item in identifying_hits[:20]:
            print(" ", item, file=sys.stderr)
        return 2
    print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
