"""Canonical one-command reproduction / verification of the frozen V1 confirmatory result.

Usage (from the repository root):

    python reproduce_confirmatory.py

This command does not retune, unfreeze, or reinterpret MG-EXP-V1. It verifies sealed
hashes, optionally recomputes the frozen analysis from local raw trials, and writes a
reproduction report. Full re-execution of 1940 trials is available with ``--full``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mycelial_graph.analysis.aggregate import analyze_results  # noqa: E402
from mycelial_graph.runner.trial import config_hash  # noqa: E402
from mycelial_graph.science.claim_invariants import audit_v1_invariants  # noqa: E402
from mycelial_graph.types import load_config  # noqa: E402
from mycelial_graph.validation import load_seeds, validate_config  # noqa: E402

SEALED = ROOT / "experiments" / "v1" / "artifacts" / "confirmatory"
EVIDENCE = SEALED / "CONFIRMATORY_EVIDENCE.json"
FREEZE = ROOT / "experiments" / "v1" / "artifacts" / "CONFIRMATORY_FREEZE.json"
MATRIX = ROOT / "docs" / "claim_evidence_matrix.yaml"
REPORT_PATH = ROOT / "experiments" / "v1" / "artifacts" / "diagnostics" / "REPRODUCTION_REPORT.md"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check(ok: bool, name: str, detail: str, failures: list[str]) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")
    if not ok:
        failures.append(f"{name}: {detail}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="outputs/confirmatory")
    parser.add_argument(
        "--full",
        action="store_true",
        help="Re-execute the frozen confirmatory experiment (minutes, not seconds).",
    )
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    started = time.perf_counter()
    failures: list[str] = []
    output = (ROOT / args.output).resolve()

    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    config = load_config(ROOT / "experiments" / "v1" / "config.confirmatory.yaml")
    seeds = load_seeds(ROOT / "experiments" / "v1" / "seeds.confirmatory.txt")
    seed_hash = sha256_file(ROOT / "experiments" / "v1" / "seeds.confirmatory.txt")

    check(len(seeds) == 97, "N", f"{len(seeds)}", failures)
    check(seed_hash == freeze["seeds_sha256"], "seeds_sha256", seed_hash, failures)
    check(config_hash(config) == freeze["confirmatory_config_hash"], "config_hash", config_hash(config), failures)
    check(validate_config(config) == [], "validate", "ok", failures)
    check(evidence["result_state"]["state"] == "REFUTED", "result_state", evidence["result_state"]["state"], failures)
    check(
        abs(float(evidence["primary_contrast"]["estimate"]) - 0.42112797022616655) < 1e-12,
        "primary_estimate",
        str(evidence["primary_contrast"]["estimate"]),
        failures,
    )

    sealed_hashes = evidence["sealed_artifact_sha256"]
    mapping = {
        "REPORT.md": SEALED / "REPORT.md",
        "figures/recovery_by_rho.png": SEALED / "figures" / "recovery_by_rho.png",
        "figures/regret_by_rho.png": SEALED / "figures" / "regret_by_rho.png",
        "manifest.json": SEALED / "manifest.json",
        "processed/analysis.json": SEALED / "analysis.json",
    }
    for relative, path in mapping.items():
        observed = sha256_file(path)
        expected = sealed_hashes[relative]
        check(observed == expected, f"seal:{relative}", observed[:16], failures)

    invariants = audit_v1_invariants(MATRIX, ROOT)
    check(invariants["ok"], "claim_invariants", str(invariants.get("failures") or "ok"), failures)

    recomputed_primary = None
    cpu_hours = None
    if args.full:
        cmd = [
            sys.executable,
            "-m",
            "mycelial_graph",
            "experiment",
            "--config",
            "experiments/v1/config.confirmatory.yaml",
            "--output",
            str(output),
            "--workers",
            str(args.workers),
        ]
        print("Re-executing frozen confirmatory experiment...")
        subprocess.check_call(cmd, cwd=ROOT)
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "mycelial_graph",
                "analyze",
                "--config",
                "experiments/v1/config.confirmatory.yaml",
                "--output",
                str(output),
            ],
            cwd=ROOT,
        )
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "mycelial_graph",
                "report",
                "--config",
                "experiments/v1/config.confirmatory.yaml",
                "--output",
                str(output),
            ],
            cwd=ROOT,
        )

    analysis_path = output / "processed" / "analysis.json"
    if not analysis_path.exists() and (output / "raw").exists():
        analyze_results(config, output)
    if analysis_path.exists():
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        recomputed_primary = analysis["primary_contrast"]["estimate"]
        check(
            abs(recomputed_primary - float(evidence["primary_contrast"]["estimate"])) < 1e-12,
            "recomputed_primary",
            str(recomputed_primary),
            failures,
        )
        check(analysis["result_state"]["state"] == "REFUTED", "recomputed_state", analysis["result_state"]["state"], failures)
        cpu = 0.0
        n_trials = 0
        for path in (output / "raw").rglob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))["scientific_payload"]
            for trial in payload["results"]:
                cpu += float(trial["decision_cpu_seconds"])
                n_trials += 1
        cpu_hours = cpu / 3600.0
        print(f"[MEASURED] cpu_hours={cpu_hours:.6f} n_trials={n_trials}")
    else:
        print("[SKIP] local raw confirmatory outputs not present; sealed hashes verified only.")

    wall = time.perf_counter() - started
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = [
        "# V1 confirmatory reproduction report",
        "",
        f"Wall-clock of this invocation: **{wall:.3f} seconds**",
        f"Measured CPU-hours from confirmatory raw trials: **{cpu_hours if cpu_hours is not None else 'NOT_MEASURED_THIS_INVOCATION'}**",
        f"Failures: {len(failures)}",
        f"Full re-execution requested: {bool(args.full)}",
        "",
        "Hardware assumption: ordinary x86-64 CPU, no GPU, no network.",
        "The sealed confirmatory execution used Python 3.13.3, numpy 2.2.6, scipy 1.15.3, PyYAML 6.0.2.",
        "",
    ]
    if failures:
        report.append("## Failures")
        report.extend(f"- {item}" for item in failures)
    else:
        report.append("All verification checks passed.")
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wall_clock_seconds={wall:.3f}")
    print(f"wrote {REPORT_PATH}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
