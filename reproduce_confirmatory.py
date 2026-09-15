"""Canonical one-command reproduction / verification of the frozen V1 confirmatory result.

Usage (from the repository root):

    python reproduce_confirmatory.py          # verification / reanalysis
    python reproduce_confirmatory.py --full   # full re-execution of 1940 trials

Default mode is not complete end-to-end reproduction. It verifies freeze bindings and
sealed hashes, and recomputes the frozen primary contrast only when local raw trials
already exist. ``--full`` recreates the experiment from frozen inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mycelial_graph.analysis.aggregate import analyze_results  # noqa: E402
from mycelial_graph.runner.trial import config_hash  # noqa: E402
from mycelial_graph.science.claim_invariants import audit_v1_invariants  # noqa: E402
from mycelial_graph.science.scientific_state import audit_scientific_state  # noqa: E402
from mycelial_graph.types import load_config  # noqa: E402
from mycelial_graph.validation import load_seeds, validate_config  # noqa: E402

SEALED = ROOT / "experiments" / "v1" / "artifacts" / "confirmatory"
EVIDENCE = SEALED / "CONFIRMATORY_EVIDENCE.json"
FREEZE = ROOT / "experiments" / "v1" / "artifacts" / "CONFIRMATORY_FREEZE.json"
MATRIX = ROOT / "docs" / "claim_evidence_matrix.yaml"
RUNTIME_PATH = ROOT / "research" / "runtime.json"
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


def _sum_decision_cpu(raw_dir: Path) -> tuple[float, int]:
    cpu = 0.0
    n_trials = 0
    for path in raw_dir.rglob("*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))["scientific_payload"]
        for trial in payload["results"]:
            cpu += float(trial["decision_cpu_seconds"])
            n_trials += 1
    return cpu, n_trials


def _write_full_runtime(
    *,
    decision_cpu_seconds: float | None,
    n_trials: int | None,
    wall_clock_seconds: float,
    workers: int,
    result_match: bool,
    hash_match: bool,
    process_cpu_seconds: float,
) -> None:
    payload = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
    payload["full_reproduction"] = {
        "status": "MEASURED",
        "decision_cpu_seconds": decision_cpu_seconds,
        "decision_cpu_hours": None if decision_cpu_seconds is None else decision_cpu_seconds / 3600.0,
        "process_cpu_seconds": process_cpu_seconds,
        "process_cpu_hours": process_cpu_seconds / 3600.0,
        "wall_clock_seconds": wall_clock_seconds,
        "n_trials": n_trials,
        "workers": workers,
        "python_version": sys.version.split()[0],
        "os": platform.platform(),
        "cpu_model": platform.processor() or platform.machine(),
        "peak_memory_bytes": None,
        "result_match": result_match,
        "hash_match": hash_match,
        "command": "python reproduce_confirmatory.py --full",
        "measurement_environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "processor": platform.processor() or platform.machine(),
            "workers": workers,
        },
    }
    try:
        import resource  # type: ignore

        payload["full_reproduction"]["peak_memory_bytes"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    except Exception:
        payload["full_reproduction"]["peak_memory_bytes"] = None
    RUNTIME_PATH.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory. Default: outputs/confirmatory for verification, "
        "outputs/confirmatory-full for --full (never overwrite sealed-run checkpoints).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Re-execute the frozen confirmatory experiment from frozen inputs.",
    )
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    if args.output is None:
        args.output = "outputs/confirmatory-full" if args.full else "outputs/confirmatory"
    started = time.perf_counter()
    cpu_started = time.process_time()
    failures: list[str] = []
    output = (ROOT / args.output).resolve()
    mode = "full_reproduction" if args.full else "verification_or_reanalysis"

    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    config = load_config(ROOT / "experiments" / "v1" / "config.confirmatory.yaml")
    seeds = load_seeds(ROOT / "experiments" / "v1" / "seeds.confirmatory.txt")
    seed_hash = sha256_file(ROOT / "experiments" / "v1" / "seeds.confirmatory.txt")
    pilot = set(load_seeds(ROOT / "experiments" / "v1" / "seeds.pilot.txt"))
    development = set(load_seeds(ROOT / "experiments" / "v1" / "seeds.development.txt"))

    check(len(seeds) == 97, "N", f"{len(seeds)}", failures)
    check(seed_hash == freeze["seeds_sha256"], "seeds_sha256", seed_hash, failures)
    check(config_hash(config) == freeze["confirmatory_config_hash"], "config_hash", config_hash(config), failures)
    check(validate_config(config) == [], "validate", "ok", failures)
    check(not (set(seeds) & pilot), "no_pilot_overlap", str(sorted(set(seeds) & pilot)), failures)
    check(not (set(seeds) & development), "no_development_overlap", str(sorted(set(seeds) & development)), failures)
    check(evidence["result_state"]["state"] == "REFUTED", "result_state", evidence["result_state"]["state"], failures)
    check(
        abs(float(evidence["primary_contrast"]["estimate"]) - 0.42112797022616655) < 1e-12,
        "primary_estimate",
        str(evidence["primary_contrast"]["estimate"]),
        failures,
    )
    check(
        abs(float(evidence["primary_contrast"]["one_sided_upper_bound"]) - 0.7213788509020655) < 1e-12,
        "one_sided_upper_bound",
        str(evidence["primary_contrast"]["one_sided_upper_bound"]),
        failures,
    )
    check(evidence["decision_gate"]["noninferiority_at_rho_0"] is False, "safety_gate", "failed", failures)
    check(int(evidence["scientific_job_count"]) == 485, "paired_scenarios", str(evidence["scientific_job_count"]), failures)
    check(int(evidence["frozen_contrast_integrity"]["primary_pairs"]) == 97, "primary_pairs", "97", failures)

    sealed_hashes = evidence["sealed_artifact_sha256"]
    mapping = {
        "REPORT.md": SEALED / "REPORT.md",
        "figures/recovery_by_rho.png": SEALED / "figures" / "recovery_by_rho.png",
        "figures/regret_by_rho.png": SEALED / "figures" / "regret_by_rho.png",
        "manifest.json": SEALED / "manifest.json",
        "processed/analysis.json": SEALED / "analysis.json",
    }
    hash_match = True
    for relative, path in mapping.items():
        observed = sha256_file(path)
        expected = sealed_hashes[relative]
        ok = observed == expected
        hash_match = hash_match and ok
        check(ok, f"seal:{relative}", observed[:16], failures)

    invariants = audit_v1_invariants(MATRIX, ROOT)
    check(invariants["ok"], "claim_invariants", str(invariants.get("failures") or "ok"), failures)
    state = audit_scientific_state(ROOT)
    check(state["ok"], "scientific_state", str(state.get("failures") or "ok"), failures)

    recomputed_primary = None
    cpu_hours = None
    n_trials = None
    decision_cpu_seconds = None
    result_match = True
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
        print(f"[MODE] full reproduction into {output}")
        try:
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
        except subprocess.CalledProcessError as exc:
            check(False, "full_reexecution", f"command failed with {exc.returncode}", failures)
            print("STOP SUBMISSION: full replay did not complete.")
            REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
            REPORT_PATH.write_text(
                "# V1 confirmatory reproduction report\n\n"
                "STOP SUBMISSION: full re-execution command failed.\n"
                f"{exc}\n",
                encoding="utf-8",
            )
            return 1

    analysis_path = output / "processed" / "analysis.json"
    if not analysis_path.exists() and (output / "raw").exists():
        analyze_results(config, output)
    if analysis_path.exists():
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        recomputed_primary = analysis["primary_contrast"]["estimate"]
        primary_ok = abs(recomputed_primary - float(evidence["primary_contrast"]["estimate"])) < 1e-12
        result_match = result_match and primary_ok
        check(primary_ok, "recomputed_primary", str(recomputed_primary), failures)
        state_ok = analysis["result_state"]["state"] == "REFUTED"
        result_match = result_match and state_ok
        check(state_ok, "recomputed_state", analysis["result_state"]["state"], failures)
        interval_ok = abs(
            float(analysis["primary_contrast"]["confidence_low"])
            - float(evidence["primary_contrast"]["confidence_low"])
        ) < 1e-12
        check(interval_ok, "recomputed_interval_low", str(analysis["primary_contrast"]["confidence_low"]), failures)
        result_match = result_match and interval_ok
        if (output / "raw").exists():
            decision_cpu_seconds, n_trials = _sum_decision_cpu(output / "raw")
            check(n_trials == 1940, "n_trials", str(n_trials), failures)
            cpu_hours = decision_cpu_seconds / 3600.0
            print(f"[MEASURED] decision_cpu_hours={cpu_hours:.6f} n_trials={n_trials}")
    else:
        print("[SKIP] local raw confirmatory outputs not present; sealed hashes verified only.")
        print("[MODE] verification only; this is not full reproduction.")

    wall = time.perf_counter() - started
    process_cpu = time.process_time() - cpu_started
    if args.full:
        _write_full_runtime(
            decision_cpu_seconds=decision_cpu_seconds,
            n_trials=n_trials,
            wall_clock_seconds=wall,
            workers=args.workers,
            result_match=result_match and not failures,
            hash_match=hash_match,
            process_cpu_seconds=process_cpu,
        )

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = [
        "# V1 confirmatory reproduction report",
        "",
        f"Mode: **{mode}**",
        f"Wall-clock of this invocation: **{wall:.3f} seconds**",
        f"Process CPU of this invocation: **{process_cpu:.3f} seconds**",
        f"Measured decision CPU-hours from confirmatory raw trials: **{cpu_hours if cpu_hours is not None else 'NOT_MEASURED_THIS_INVOCATION'}**",
        f"n_trials: **{n_trials if n_trials is not None else 'NOT_COUNTED'}**",
        f"Failures: {len(failures)}",
        f"Full re-execution requested: {bool(args.full)}",
        "",
        "Default `python reproduce_confirmatory.py` is verification/reanalysis.",
        "`python reproduce_confirmatory.py --full` is canonical full reproduction.",
        "Hardware assumption: ordinary x86-64 CPU, no GPU, no network.",
        "The sealed confirmatory execution used Python 3.13.3, numpy 2.2.6, scipy 1.15.3, PyYAML 6.0.2.",
        f"This invocation: Python {sys.version.split()[0]}, {platform.platform()}.",
        "",
    ]
    if failures:
        report.append("## Failures")
        report.extend(f"- {item}" for item in failures)
        report.append("")
        if args.full:
            report.append("STOP SUBMISSION: full replay did not reproduce the sealed result.")
    else:
        report.append("All verification checks passed.")
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"wall_clock_seconds={wall:.3f}")
    print(f"wrote {REPORT_PATH}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
