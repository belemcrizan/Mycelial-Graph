"""Canonical one-command verification of the frozen V1 confirmatory result.

Usage (from the repository root):

    python reproduce_confirmatory.py          # sealed-evidence verification
    python reproduce_confirmatory.py --full   # full re-execution of 1940 method-level trials

Counting semantics (frozen MG-EXP-V1 confirmatory design):

    97 paired scenarios (N)
  ×  5 rho values
  = 485 scientific jobs (one job per seed×rho; ``scientific_job_count``)
  ×  4 methods (edge_only, node_only, hierarchical, structured_sw_ucb)
  = 1940 method-level trials

Default mode is not complete end-to-end reproduction. It verifies freeze bindings,
historical EOL-equivalent text seals, and PNG raw hashes. It recomputes the frozen
primary contrast only when local raw trials already exist. ``--full`` recreates the
experiment from frozen inputs into a fresh directory and does not overwrite sealed
artifacts.

A passing verification does not reclassify REFUTED as ACCEPTED and does not unlock
a new confirmatory execution.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from mycelial_graph.analysis.aggregate import analyze_results  # noqa: E402
from mycelial_graph.reporting.report import generate_report  # noqa: E402
from mycelial_graph.runner.experiment import run_experiment  # noqa: E402
from mycelial_graph.runner.trial import config_hash  # noqa: E402
from mycelial_graph.science.canonical_bytes import (  # noqa: E402
    CONFIRMATORY_METHOD_TRIALS,
    CONFIRMATORY_N,
    CONFIRMATORY_SCIENTIFIC_JOBS,
    FROZEN_CONFIG_HASH,
    FROZEN_SEED_SHA256,
    ONE_SIDED_UPPER_BOUND,
    PRIMARY_ESTIMATE,
    SealIdentity,
    human_seal_line,
    verify_frozen_seed_identity,
)
from mycelial_graph.science.claim_invariants import audit_v1_invariants  # noqa: E402
from mycelial_graph.science.reproduction import (  # noqa: E402
    verify_historical_confirmatory_evidence,
)
from mycelial_graph.science.scientific_state import audit_scientific_state  # noqa: E402
from mycelial_graph.types import load_config  # noqa: E402
from mycelial_graph.validation import load_seeds, validate_config  # noqa: E402

SEALED = ROOT / "experiments" / "v1" / "artifacts" / "confirmatory"
EVIDENCE = SEALED / "CONFIRMATORY_EVIDENCE.json"
FREEZE = ROOT / "experiments" / "v1" / "artifacts" / "CONFIRMATORY_FREEZE.json"
MATRIX = ROOT / "docs" / "claim_evidence_matrix.yaml"
RUNTIME_PATH = ROOT / "research" / "runtime.json"
REPORT_PATH = ROOT / "experiments" / "v1" / "artifacts" / "diagnostics" / "REPRODUCTION_REPORT.md"


def check(ok: bool, name: str, detail: str, failures: list[str]) -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}: {detail}")
    if not ok:
        failures.append(f"{name}: {detail}")


def format_validation_detail(errors: list[str]) -> str:
    """Human-readable validation detail. Never report a failure as ``ok``."""
    return "ok" if not errors else "; ".join(errors)


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


def _write_report(
    *,
    mode: str,
    wall: float,
    process_cpu: float,
    cpu_hours: float | None,
    n_trials: int | None,
    failures: list[str],
    full_requested: bool,
    raw_present: bool,
    analysis_recomputed: bool,
    seal_checks: list,
    scientific_ok: bool,
) -> None:
    png = [c for c in seal_checks if c.artifact.startswith("figures/")]
    text = [c for c in seal_checks if not c.artifact.startswith("figures/")]
    png_status = "EXACT" if png and all(c.identity is SealIdentity.EXACT for c in png) else "FAIL"
    text_lines = []
    for check_row in text:
        text_lines.append(f"{check_row.artifact}: {check_row.identity.value}")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if full_requested:
        reproduction_level = "full_reexecution" if not failures else "full_reexecution_failed"
    elif analysis_recomputed:
        reproduction_level = "analysis_recomputed_from_local_raw"
    elif raw_present:
        reproduction_level = "raw_present_but_analysis_not_recomputed"
    else:
        reproduction_level = "sealed_artifact_verification_only"
    report = [
        "# V1 confirmatory reproduction report",
        "",
        f"Mode: **{mode}**",
        f"Reproduction level achieved: **{reproduction_level}**",
        f"Wall-clock of this invocation: **{wall:.3f} seconds**",
        f"Process CPU of this invocation: **{process_cpu:.3f} seconds**",
        f"Measured decision CPU-hours from confirmatory raw trials: **{cpu_hours if cpu_hours is not None else 'NOT_MEASURED_THIS_INVOCATION'}**",
        f"n_trials: **{n_trials if n_trials is not None else 'NOT_COUNTED'}**",
        f"Failures: {len(failures)}",
        f"Full re-execution requested: {bool(full_requested)}",
        "",
        "## Scientific result verification",
        "",
        f"Scientific result: **{'VERIFIED' if scientific_ok else 'FAILED'}**",
        f"Historical result state: **REFUTED**",
        f"Primary estimate: **{PRIMARY_ESTIMATE}**",
        "",
        "A verified REFUTED result is a valid scientific outcome. Verification is not acceptance.",
        "",
        "## Frozen inputs",
        "",
        f"N: **{CONFIRMATORY_N}**",
        "Seeds: frozen SHA-256 is the CRLF-sealed identity; Git blob is LF; values identical",
        "Config: parsed semantic ``config_hash`` against the freeze",
        "",
        f"scientific_job_count = N × rho = {CONFIRMATORY_N} × 5 = **{CONFIRMATORY_SCIENTIFIC_JOBS}**",
        f"method-level trials = jobs × methods = {CONFIRMATORY_SCIENTIFIC_JOBS} × 4 = **{CONFIRMATORY_METHOD_TRIALS}**",
        "",
        "## Artifact integrity",
        "",
        f"PNG artifacts: **{png_status}**",
        *[f"- {line}" for line in text_lines],
        "",
        "Scientific-content mutation detected: **NO**" if not failures else "Scientific-content mutation or integrity failure: **YES**",
        "",
        "## Reproduction depth",
        "",
        f"Raw confirmatory trials available locally: **{'YES' if raw_present else 'NO'}**",
        f"Analysis recomputed from raw trials: **{'YES' if analysis_recomputed else 'NO'}**",
        f"Full re-execution performed: **{'YES' if full_requested and not failures else 'NO'}**",
        "",
        "Sealed-hash verification is not a full independent reproduction.",
        "Reproduction status remains: internal / automated; no independent external reproduction.",
        "",
        "## Provenance",
        "",
        "- Historical evidence: `experiments/v1/artifacts/confirmatory/CONFIRMATORY_EVIDENCE.json` (immutable).",
        "- Historical freeze: `experiments/v1/artifacts/CONFIRMATORY_FREEZE.json` (pre-execution schema; not `schema_version=1`).",
        "- Freeze supplement: `experiments/v1/artifacts/CONFIRMATORY_FREEZE_SUPPLEMENT.json` (additive).",
        "- Reproduction supplement: `experiments/v1/artifacts/confirmatory/CONFIRMATORY_REPRODUCTION_SUPPLEMENT.json`.",
        "- Code revision at execution/seal: `5f314d2dfb15f508dfd4e630e8c0e49031e60c6a`.",
        "- Historical text seals captured CRLF bytes; the repository stores LF. Byte representation changed; scientific textual content did not.",
        "",
        "Default `python reproduce_confirmatory.py` is verification of sealed evidence.",
        "`python reproduce_confirmatory.py --full` is canonical full re-execution from frozen inputs.",
        "Hardware assumption: ordinary x86-64 CPU, no GPU, no network.",
        "The sealed confirmatory execution used Python 3.13.3, numpy 2.2.6, scipy 1.15.3, PyYAML 6.0.2.",
        f"This invocation: Python {sys.version.split()[0]}, {platform.platform()}.",
        "",
    ]
    if failures:
        report.append("## Failures")
        report.extend(f"- {item}" for item in failures)
        report.append("")
        if full_requested:
            report.append("STOP SUBMISSION: full replay did not reproduce the sealed result.")
    else:
        report.append("All verification checks passed at the reproduction level stated above.")
        report.append("The V1 confirmatory result remains **REFUTED**.")
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")


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
        help=(
            "Re-execute the frozen confirmatory experiment from frozen inputs "
            f"({CONFIRMATORY_METHOD_TRIALS} method-level trials = "
            f"{CONFIRMATORY_SCIENTIFIC_JOBS} scientific jobs × 4 methods)."
        ),
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
    seed_check = verify_frozen_seed_identity(
        ROOT / "experiments" / "v1" / "seeds.confirmatory.txt", freeze["seeds_sha256"]
    )
    pilot = set(load_seeds(ROOT / "experiments" / "v1" / "seeds.pilot.txt"))
    development = set(load_seeds(ROOT / "experiments" / "v1" / "seeds.development.txt"))

    check(len(seeds) == CONFIRMATORY_N, "N", f"{len(seeds)}", failures)
    check(seed_check.ok and freeze["seeds_sha256"] == FROZEN_SEED_SHA256, "seeds_sha256", seed_check.message, failures)
    observed_config = config_hash(config)
    check(
        observed_config == freeze["confirmatory_config_hash"] == FROZEN_CONFIG_HASH,
        "config_hash",
        observed_config,
        failures,
    )
    validation_errors = validate_config(config)
    check(not validation_errors, "validate", format_validation_detail(validation_errors), failures)
    check(not (set(seeds) & pilot), "no_pilot_overlap", str(sorted(set(seeds) & pilot)), failures)
    check(not (set(seeds) & development), "no_development_overlap", str(sorted(set(seeds) & development)), failures)
    check(evidence["result_state"]["state"] == "REFUTED", "result_state", evidence["result_state"]["state"], failures)
    check(
        abs(float(evidence["primary_contrast"]["estimate"]) - PRIMARY_ESTIMATE) < 1e-12,
        "primary_estimate",
        str(evidence["primary_contrast"]["estimate"]),
        failures,
    )
    check(
        abs(float(evidence["primary_contrast"]["one_sided_upper_bound"]) - ONE_SIDED_UPPER_BOUND) < 1e-12,
        "one_sided_upper_bound",
        str(evidence["primary_contrast"]["one_sided_upper_bound"]),
        failures,
    )
    check(evidence["decision_gate"]["noninferiority_at_rho_0"] is False, "safety_gate", "failed", failures)
    check(
        int(evidence["scientific_job_count"]) == CONFIRMATORY_SCIENTIFIC_JOBS,
        "paired_scenarios",
        str(evidence["scientific_job_count"]),
        failures,
    )
    check(int(evidence["frozen_contrast_integrity"]["primary_pairs"]) == CONFIRMATORY_N, "primary_pairs", "97", failures)

    historical = verify_historical_confirmatory_evidence(ROOT)
    for error in historical.errors:
        check(False, "historical_evidence", error, failures)
    hash_match = True
    for seal_check in historical.seal_checks:
        ok = seal_check.ok
        hash_match = hash_match and ok
        if seal_check.identity is SealIdentity.HISTORICAL_EOL_EQUIVALENT:
            print(human_seal_line(seal_check))
            if not ok:
                failures.append(seal_check.message)
        else:
            check(ok, f"seal:{seal_check.artifact}", seal_check.message.split(": ", 1)[-1], failures)

    invariants = audit_v1_invariants(MATRIX, ROOT)
    check(invariants["ok"], "claim_invariants", str(invariants.get("failures") or "ok"), failures)
    state = audit_scientific_state(ROOT)
    check(state["ok"], "scientific_state", str(state.get("failures") or "ok"), failures)

    recomputed_primary = None
    cpu_hours = None
    n_trials = None
    decision_cpu_seconds = None
    result_match = True
    analysis_recomputed = False
    if args.full:
        print("Re-executing frozen confirmatory experiment...")
        print(f"[MODE] full reproduction into {output}")
        print(
            f"[COUNT] {CONFIRMATORY_N} pairs × 5 rho = {CONFIRMATORY_SCIENTIFIC_JOBS} jobs; "
            f"× 4 methods = {CONFIRMATORY_METHOD_TRIALS} method-level trials"
        )
        try:
            run_experiment(config, output, args.workers, confirmatory_replay=True)
            analyze_results(config, output)
            generate_report(config, output)
        except Exception as exc:
            check(False, "full_reexecution", f"{type(exc).__name__}: {exc}", failures)
            print("STOP SUBMISSION: full replay did not complete.")
            _write_report(
                mode=mode,
                wall=time.perf_counter() - started,
                process_cpu=time.process_time() - cpu_started,
                cpu_hours=None,
                n_trials=None,
                failures=failures,
                full_requested=True,
                raw_present=False,
                analysis_recomputed=False,
                seal_checks=historical.seal_checks,
                scientific_ok=False,
            )
            print(f"wrote {REPORT_PATH}")
            return 1

    analysis_path = output / "processed" / "analysis.json"
    raw_present = (output / "raw").exists()
    if not analysis_path.exists() and raw_present:
        analyze_results(config, output)
    if analysis_path.exists():
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        analysis_recomputed = True
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
        if raw_present:
            decision_cpu_seconds, n_trials = _sum_decision_cpu(output / "raw")
            check(n_trials == CONFIRMATORY_METHOD_TRIALS, "n_trials", str(n_trials), failures)
            cpu_hours = decision_cpu_seconds / 3600.0
            print(f"[MEASURED] decision_cpu_hours={cpu_hours:.6f} n_trials={n_trials}")
    else:
        print("[SKIP] local raw confirmatory outputs not present; sealed hashes verified only.")
        print("[MODE] verification only; this is not full reproduction.")
        print("[LEVEL] sealed_artifact_verification_only")

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

    scientific_ok = not any(
        item.startswith(prefix)
        for item in failures
        for prefix in ("N:", "seeds_sha256:", "config_hash:", "result_state:", "primary_estimate:", "claim_invariants:")
    )
    _write_report(
        mode=mode,
        wall=wall,
        process_cpu=process_cpu,
        cpu_hours=cpu_hours,
        n_trials=n_trials,
        failures=failures,
        full_requested=bool(args.full),
        raw_present=raw_present,
        analysis_recomputed=analysis_recomputed,
        seal_checks=historical.seal_checks,
        scientific_ok=scientific_ok and not failures,
    )
    print(f"wall_clock_seconds={wall:.3f}")
    print(f"wrote {REPORT_PATH}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
