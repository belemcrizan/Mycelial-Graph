"""Seal V1 confirmatory evidence into version control and the scientific ledger.

`outputs/` is not version controlled, so the canonical confirmatory artifacts are copied into
`experiments/v1/artifacts/confirmatory/` with their hashes, and one append-only ledger entry
records the execution. Nothing is interpreted, recomputed, or rewritten here.

Usage:
    python scripts/seal_v1_confirmatory.py --output outputs/confirmatory
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mycelial_graph.science.ledger import append_entry  # noqa: E402

SEALED = ROOT / "experiments" / "v1" / "artifacts" / "confirmatory"
LEDGER = ROOT / "research" / "ledger" / "ledger.jsonl"
COPIED = ("manifest.json", "REPORT.md", "processed/analysis.json")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/confirmatory")
    args = parser.parse_args()

    output = (ROOT / args.output).resolve()
    analysis_path = output / "processed" / "analysis.json"
    if not analysis_path.exists():
        print(f"ERROR: no confirmatory analysis at {analysis_path}", file=sys.stderr)
        return 2
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    if analysis.get("run_kind") != "confirmatory":
        print(f"ERROR: run_kind is {analysis.get('run_kind')!r}, refusing to seal.", file=sys.stderr)
        return 2

    SEALED.mkdir(parents=True, exist_ok=True)
    hashes: dict[str, str] = {}
    for relative in COPIED:
        source = output / relative
        if not source.exists():
            print(f"ERROR: missing artifact {source}", file=sys.stderr)
            return 2
        destination = SEALED / Path(relative).name
        shutil.copy2(source, destination)
        hashes[relative] = sha256_file(destination)

    figures_source = output / "figures"
    if figures_source.exists():
        figures_destination = SEALED / "figures"
        figures_destination.mkdir(exist_ok=True)
        for figure in sorted(figures_source.glob("*.png")):
            shutil.copy2(figure, figures_destination / figure.name)
            hashes[f"figures/{figure.name}"] = sha256_file(figures_destination / figure.name)

    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    result_state = analysis.get("result_state") or {}
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True, encoding="utf-8"
    ).strip()

    summary = {
        "protocol_version": manifest["protocol_version"],
        "experiment_id": manifest["experiment_id"],
        "sealed_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "code_revision_at_execution": manifest["code_revision"],
        "code_revision_at_seal": commit,
        "config_hash": manifest["config_hash"],
        "seeds_file_sha256": manifest["seeds_file_sha256"],
        "scientific_job_count": manifest["scientific_job_count"],
        "environment": manifest["environment"],
        "result_state": result_state,
        "primary_contrast": analysis["primary_contrast"],
        "noninferiority_contrast": analysis["noninferiority_contrast"],
        "decision_gate": analysis["decision_gate"],
        "frozen_contrast_integrity": analysis["frozen_contrast_integrity"],
        "sealed_artifact_sha256": hashes,
        "claim_boundary": analysis["claim_boundary"],
        "reproduction_status": "internal / automated; no independent external reproduction",
    }
    (SEALED / "CONFIRMATORY_EVIDENCE.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    append_entry(
        LEDGER,
        {
            "experiment_id": manifest["experiment_id"],
            "protocol": manifest["protocol_version"],
            "commit": manifest["code_revision"],
            "config": "experiments/v1/config.confirmatory.yaml",
            "seeds": "experiments/v1/seeds.confirmatory.txt",
            "dataset": "synthetic-v1-simulator",
            "status": "sealed",
            "start": None,
            "finish": summary["sealed_at_utc"],
            "result_classification": result_state.get("state", "UNKNOWN"),
            "artifact_location": "experiments/v1/artifacts/confirmatory/",
            "invalidations": [],
            "amendments": ["AMENDMENT_001.md", "AMENDMENT_002.md"],
            "notes": (
                "V1 confirmatory executed under CONFIRMATORY_FREEZE.json with no post-pilot "
                "tuning. Claim boundary: rho=0.50 primary contrast and rho=0 safety gate only."
            ),
        },
    )
    print(json.dumps({"sealed": str(SEALED.relative_to(ROOT)), "result_state": result_state}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
