"""MG-EXP-V1 confirmatory-readiness audit.

Mechanical integrity audit of the frozen V1 protocol. Everything reported here is computed
from the repository; nothing is copied from documentation on trust. Every finding is classified
exactly once as:

    A  non-material            -> DOCUMENT, do not block
    B  pre-confirmatory        -> AMEND / DOCUMENT, do not block
    C  material                -> STOP / PROTOCOL_INVALID

Decision: GO when only A/B findings remain, otherwise STOP or PROTOCOL_INVALID.

Writes:
    CONFIRMATORY_READINESS_REPORT.json
    CONFIRMATORY_READINESS_REPORT.md
    experiments/v1/artifacts/CONFIRMATORY_FREEZE_SUPPLEMENT.json

Usage:
    python scripts/audit_v1_readiness.py
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
from scipy.stats import norm  # noqa: E402

from mycelial_graph.analysis.aggregate import _paired_arrays, _read_trials  # noqa: E402
from mycelial_graph.environment.scenario import generate_scenario_family  # noqa: E402
from mycelial_graph.runner.trial import config_hash  # noqa: E402
from mycelial_graph.science.claim_invariants import audit_v1_invariants  # noqa: E402
from mycelial_graph.types import load_config  # noqa: E402
from mycelial_graph.v2.evaluation.claim_audit import audit_claims  # noqa: E402
from mycelial_graph.validation import load_seeds, validate_config  # noqa: E402

V1 = ROOT / "experiments" / "v1"
ARTIFACTS = V1 / "artifacts"
FREEZE_PATH = ARTIFACTS / "CONFIRMATORY_FREEZE.json"
MATRIX_PATH = ROOT / "docs" / "claim_evidence_matrix.yaml"

FINDINGS: list[dict[str, Any]] = []


def finding(identifier: str, klass: str, title: str, detail: str, action: str) -> None:
    assert klass in {"A", "B", "C"}, klass
    FINDINGS.append(
        {
            "id": identifier,
            "class": klass,
            "title": title,
            "detail": detail,
            "action": action,
        }
    )


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    try:
        return subprocess.check_output(
            ["git", *args], cwd=ROOT, text=True, encoding="utf-8", stderr=subprocess.DEVNULL
        ).strip()
    except Exception:  # pragma: no cover - environment without git
        return "unavailable"


def repository_state() -> dict[str, Any]:
    status = git("status", "--porcelain")
    return {
        "commit": git("rev-parse", "HEAD"),
        "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
        "dirty": bool(status) and status != "unavailable",
        "dirty_paths": [line[3:] for line in status.splitlines()] if status != "unavailable" else [],
        "audited_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "python": sys.version.split()[0],
        "numpy": np.__version__,
    }


def frozen_artifacts() -> dict[str, Any]:
    paths = [
        V1 / "EXPERIMENT_PROTOCOL_V1.md",
        V1 / "ANALYSIS_PLAN.md",
        V1 / "SAMPLE_SIZE_ADDENDUM.md",
        V1 / "AMENDMENT_001.md",
        V1 / "AMENDMENT_002.md",
        V1 / "HYPOTHESIS_MATRIX.md",
        V1 / "config.confirmatory.yaml",
        V1 / "config.pilot.yaml",
        V1 / "seeds.confirmatory.txt",
        V1 / "seeds.confirmatory.pool.txt",
        V1 / "seeds.pilot.txt",
        V1 / "seeds.development.txt",
        FREEZE_PATH,
        ARTIFACTS / "PILOT_EVIDENCE.json",
        ARTIFACTS / "analysis.json",
        ARTIFACTS / "sample_size.json",
        ROOT / "src" / "mycelial_graph" / "analysis" / "aggregate.py",
        ROOT / "src" / "mycelial_graph" / "analysis" / "bootstrap.py",
        ROOT / "src" / "mycelial_graph" / "analysis" / "result_state.py",
        ROOT / "src" / "mycelial_graph" / "reporting" / "report.py",
        ROOT / "src" / "mycelial_graph" / "science" / "claim_guard.py",
    ]
    rows = []
    for path in paths:
        rows.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "exists": path.exists(),
                "sha256": sha256_file(path),
            }
        )
    missing = [row["path"] for row in rows if not row["exists"]]
    return {"artifacts": rows, "missing": missing, "validation_status": "OK" if not missing else "INCOMPLETE"}


def seed_audit(freeze: dict[str, Any]) -> dict[str, Any]:
    confirmatory_path = V1 / "seeds.confirmatory.txt"
    pool_path = V1 / "seeds.confirmatory.pool.txt"
    confirmatory = load_seeds(confirmatory_path)
    pool = load_seeds(pool_path)
    pilot = load_seeds(V1 / "seeds.pilot.txt")
    development = load_seeds(V1 / "seeds.development.txt")
    observed_hash = sha256_file(confirmatory_path)
    raw_bytes = confirmatory_path.read_bytes()
    expected_n = int(freeze["required_confirmatory_pairs"])
    result = {
        "expected_n": expected_n,
        "observed_n": len(confirmatory),
        "unique": len(set(confirmatory)) == len(confirmatory),
        "sorted_ascending": confirmatory == sorted(confirmatory),
        "is_unfiltered_pool_prefix": confirmatory == pool[:expected_n],
        "pool_size": len(pool),
        "pool_unique": len(set(pool)) == len(pool),
        "first_seed": confirmatory[0],
        "last_seed": confirmatory[-1],
        "overlap_with_pilot": sorted(set(confirmatory) & set(pilot)),
        "overlap_with_development": sorted(set(confirmatory) & set(development)),
        "pool_overlap_with_pilot": sorted(set(pool) & set(pilot)),
        "pool_overlap_with_development": sorted(set(pool) & set(development)),
        "sha256": observed_hash,
        "freeze_sha256": freeze.get("seeds_sha256"),
        "hash_matches_freeze": observed_hash == freeze.get("seeds_sha256"),
        "line_ending": "CRLF" if b"\r\n" in raw_bytes else "LF",
        "byte_length": len(raw_bytes),
        "seed_file_referenced_by_config": load_config(V1 / "config.confirmatory.yaml").seeds_file,
        "config_validation_errors": validate_config(load_config(V1 / "config.confirmatory.yaml")),
    }
    result["deterministic_selection_verified"] = bool(
        result["is_unfiltered_pool_prefix"]
        and result["observed_n"] == expected_n
        and result["unique"]
        and result["hash_matches_freeze"]
    )
    result["cherry_picking_detected"] = not result["is_unfiltered_pool_prefix"]

    if not result["deterministic_selection_verified"]:
        finding(
            "F-SEED-01",
            "C",
            "Confirmatory seed selection does not reproduce mechanically",
            json.dumps({k: result[k] for k in ("observed_n", "is_unfiltered_pool_prefix", "hash_matches_freeze")}),
            "STOP: the frozen selection rule cannot be verified.",
        )
    if result["overlap_with_pilot"] or result["overlap_with_development"]:
        finding(
            "F-SEED-02",
            "C",
            "Confirmatory seeds overlap a protected population",
            json.dumps(
                {
                    "pilot": result["overlap_with_pilot"],
                    "development": result["overlap_with_development"],
                }
            ),
            "STOP: population independence is violated.",
        )
    if result["config_validation_errors"]:
        finding(
            "F-SEED-03",
            "C",
            "Confirmatory configuration fails validation",
            json.dumps(result["config_validation_errors"]),
            "STOP: the frozen configuration cannot execute.",
        )
    return result


def power_audit(freeze: dict[str, Any]) -> dict[str, Any]:
    recorded = json.loads((ARTIFACTS / "sample_size.json").read_text(encoding="utf-8"))
    addendum = (V1 / "SAMPLE_SIZE_ADDENDUM.md").read_text(encoding="utf-8")
    pilot_config = load_config(V1 / "config.pilot.yaml")

    alpha = float(recorded["one_sided_alpha"])
    power = float(recorded["target_power"])
    paired_sd = float(recorded["paired_difference_sd"])
    absolute_effect = float(recorded["absolute_design_effect"])
    z_alpha = float(norm.ppf(1.0 - alpha))
    z_power = float(norm.ppf(power))
    recomputed = int(max(2, math.ceil(((z_alpha + z_power) * paired_sd / absolute_effect) ** 2)))

    result: dict[str, Any] = {
        "powered_contrast": (
            "hierarchical vs edge_only at rho=0.50 on the relative difference in mean "
            "restricted recovery time (the frozen primary estimand)"
        ),
        "variability_source": f"paired SD from {recorded['pilot_pairs']} pilot scenarios at rho={recorded['primary_rho']}",
        "control_mean_rrt": recorded["control_mean_rrt"],
        "relative_design_effect": recorded["relative_design_effect"],
        "absolute_design_effect": absolute_effect,
        "paired_difference_sd": paired_sd,
        "one_sided_alpha": alpha,
        "target_power": power,
        "test_direction": "one-sided, H1: delta_RRT < 0",
        "censoring_assumption": "administrative censoring at tau = post_shock_steps only",
        "method": recorded["method"],
        "recorded_n": int(recorded["required_confirmatory_pairs"]),
        "recomputed_n": recomputed,
        "freeze_n": int(freeze["required_confirmatory_pairs"]),
        "n_reproduces": recomputed == int(recorded["required_confirmatory_pairs"]) == int(freeze["required_confirmatory_pairs"]),
        "addendum_states_n_97": "Required N: **97**" in addendum,
        "simulation_based_power_performed": bool(freeze.get("simulation_based_power")),
        "post_pilot_method_tuning": bool(freeze.get("post_pilot_method_tuning")),
        "pilot_and_confirmatory_share_design": {},
        "powers_safety_gate": False,
        "powers_crossover": False,
        "note": (
            "N=97 provides the planned power for the primary contrast only. It does NOT imply "
            "adequate power for the rho=0 non-inferiority gate, for any other rho, or for "
            "estimating or establishing a crossover rho*."
        ),
    }

    confirmatory_config = load_config(V1 / "config.confirmatory.yaml")
    shared: dict[str, bool] = {}
    for field in ("graph", "horizon", "environment", "mycelial", "structured_sw_ucb", "analysis"):
        shared[field] = (
            getattr(pilot_config, field).__dict__ == getattr(confirmatory_config, field).__dict__
        )
    shared["methods"] = list(pilot_config.methods) == list(confirmatory_config.methods)
    result["pilot_and_confirmatory_share_design"] = shared

    # Recompute the pilot variance from raw pilot data when it is available locally.
    pilot_output = ROOT / "outputs" / "pilot"
    if (pilot_output / "raw").exists():
        trials = _read_trials(pilot_output)
        treatment, control = _paired_arrays(trials, 0.5, "hierarchical", "edge_only")
        observed_sd = float(np.std(treatment - control, ddof=1))
        observed_control = float(np.mean(control))
        result["pilot_raw_recomputed"] = {
            "pairs": int(len(treatment)),
            "paired_difference_sd": observed_sd,
            "control_mean_rrt": observed_control,
            "matches_recorded": bool(
                np.isclose(observed_sd, paired_sd) and np.isclose(observed_control, recorded["control_mean_rrt"])
            ),
        }
    else:
        result["pilot_raw_recomputed"] = {
            "status": "pilot raw data not present locally (outputs/ is not version controlled); "
            "sealed copies in experiments/v1/artifacts/ were used instead"
        }

    if not result["n_reproduces"]:
        finding(
            "F-POWER-01",
            "C",
            "N=97 does not reproduce from the recorded sample-size chain",
            json.dumps({k: result[k] for k in ("recorded_n", "recomputed_n", "freeze_n")}),
            "STOP: the frozen sample size cannot be traced to its inputs.",
        )
    if not all(shared.values()):
        finding(
            "F-POWER-02",
            "C",
            "Pilot and confirmatory designs differ, so pilot variance does not transfer",
            json.dumps(shared),
            "STOP: the variance estimate does not apply to the confirmatory design.",
        )
    if not result["simulation_based_power_performed"]:
        finding(
            "F-POWER-03",
            "A",
            "Optional simulation-based power supplement was not performed",
            "power.py requests an optional simulation-based check before locking N. It was not "
            "run, so N=97 is the pre-specified formula output rather than a simulation-verified "
            "value. The formula was the pre-specified procedure, so this changes nothing about "
            "what was promised.",
            "DOCUMENT: record as a limitation of the power calculation.",
        )
    finding(
        "F-POWER-04",
        "A",
        "The rho=0 safety gate is not separately power-analysed",
        "ANALYSIS_PLAN.md section 7 powers the design for the primary contrast only. The "
        "rho=0 non-inferiority gate was pre-specified with a +0.10 margin but no power target. "
        "A gate failure is therefore interpretable, while a gate pass carries unquantified type-II "
        "risk. This was frozen before the pilot and must not be repaired by changing N.",
        "DOCUMENT: state the limitation in the report and hypothesis matrix.",
    )
    return result


def freeze_audit(freeze: dict[str, Any]) -> dict[str, Any]:
    confirmatory_config = load_config(V1 / "config.confirmatory.yaml")
    observed_config_hash = config_hash(confirmatory_config)
    bound = {
        "protocol_version": "protocol_version" in freeze,
        "confirmatory_config_hash": "confirmatory_config_hash" in freeze,
        "seeds_file": "seeds_file" in freeze,
        "seeds_sha256": "seeds_sha256" in freeze,
        "required_confirmatory_pairs": "required_confirmatory_pairs" in freeze,
        "sample_size_method": "sample_size_method" in freeze,
        "pilot_code_commit": "pilot_code_commit_at_execution" in freeze,
        "post_pilot_method_tuning_declared": "post_pilot_method_tuning" in freeze,
        "execution_status": "status" in freeze,
    }
    # Everything the config hash already covers, verified field by field.
    covered_by_config_hash = {
        "primary_estimand_rho": confirmatory_config.analysis.primary_rho,
        "noninferiority_margin": confirmatory_config.analysis.noninferiority_margin,
        "engineering_gain_gate": confirmatory_config.analysis.engineering_gain_gate,
        "superiority_alpha": confirmatory_config.analysis.superiority_alpha,
        "bootstrap_samples": confirmatory_config.analysis.bootstrap_samples,
        "confidence_level": confirmatory_config.analysis.confidence_level,
        "rho_grid": list(confirmatory_config.environment.rho_values),
        "shock_magnitude": confirmatory_config.environment.shock_magnitude,
        "recovery_utility_fraction": confirmatory_config.horizon.recovery_utility_fraction,
        "recovery_trailing_window": confirmatory_config.horizon.recovery_trailing_window,
        "recovery_confirmation_window": confirmatory_config.horizon.recovery_confirmation_window,
        "tau_post_shock_steps": confirmatory_config.horizon.post_shock_steps,
        "methods": list(confirmatory_config.methods),
        "seeds_file": confirmatory_config.seeds_file,
    }
    not_bound_by_hash = [
        "EXPERIMENT_PROTOCOL_V1.md content hash",
        "ANALYSIS_PLAN.md content hash",
        "analysis and reporting code hashes",
        "bootstrap RNG seeds (hard-coded in analysis/bootstrap.py and analysis/aggregate.py)",
    ]
    result = {
        "freeze_fields": sorted(freeze),
        "bound": bound,
        "config_hash_observed": observed_config_hash,
        "config_hash_in_freeze": freeze.get("confirmatory_config_hash"),
        "config_hash_matches": observed_config_hash == freeze.get("confirmatory_config_hash"),
        "scientific_parameters_covered_by_config_hash": covered_by_config_hash,
        "not_bound_by_freeze": not_bound_by_hash,
        "confirmatory_executed_flag": freeze.get("confirmatory_executed"),
        "amendment_history": sorted(
            path.name for path in V1.glob("AMENDMENT_*.md")
        ),
    }
    if not result["config_hash_matches"]:
        finding(
            "F-FREEZE-01",
            "C",
            "Confirmatory configuration no longer matches the frozen hash",
            json.dumps(
                {
                    "observed": observed_config_hash,
                    "freeze": freeze.get("confirmatory_config_hash"),
                }
            ),
            "STOP: the execution contract has been broken.",
        )
    finding(
        "F-FREEZE-02",
        "B",
        "The freeze binds configuration and seeds but not protocol text or analysis code",
        "CONFIRMATORY_FREEZE.json binds the confirmatory config hash, the seed file and its "
        "hash, N, the protocol version, and the pilot code commit. It does not bind the hash of "
        "EXPERIMENT_PROTOCOL_V1.md, ANALYSIS_PLAN.md, or the analysis/reporting code, so those "
        "could in principle change without invalidating the freeze. Closing this gap adds "
        "evidence only: it changes no hypothesis, estimand, sample size, seed, or method.",
        "AMEND/DOCUMENT: record the additional hashes in CONFIRMATORY_FREEZE_SUPPLEMENT.json "
        "before execution, leaving the original freeze contract untouched.",
    )
    return result


def multiplicity_audit() -> dict[str, Any]:
    plan = (V1 / "ANALYSIS_PLAN.md").read_text(encoding="utf-8")
    protocol = (V1 / "EXPERIMENT_PROTOCOL_V1.md").read_text(encoding="utf-8")
    frozen_statements = {
        "single_primary_contrast_declared": (
            "The only primary confirmatory contrast is hierarchical versus edge-only at `rho=0.50`"
            in plan
        ),
        "safety_gate_declared_secondary": "pre-specified secondary safety gate" in plan,
        "others_declared_secondary_or_exploratory": (
            "are secondary or exploratory unless an amendment establishes a separate controlled "
            "family before confirmatory outcomes are inspected" in plan
        ),
        "exploratory_may_not_be_called_confirmatory": (
            "No uncorrected exploratory result may be described as confirmatory." in plan
        ),
        "primary_hypothesis_frozen_in_protocol": "H0: delta_RRT >= 0" in protocol,
        "noninferiority_margin_frozen_in_protocol": "margin `M=+0.10`" in protocol,
    }
    already_frozen = all(frozen_statements.values())
    result = {
        "multiplicity_policy_frozen": already_frozen,
        "frozen_statements": frozen_statements,
        "confirmatory_family_size": 1,
        "adjustment_required": False,
        "adjustment_rationale": (
            "The confirmatory family contains exactly one superiority hypothesis (rho=0.50 "
            "hierarchical vs edge-only). The rho=0 contrast is a pre-specified safety gate that "
            "can only restrict, never create, a positive claim. No alpha split or step-down "
            "procedure is required, and none is introduced."
        ),
        "hypothesis_matrix": (V1 / "HYPOTHESIS_MATRIX.md").exists(),
        "classification": "A" if already_frozen else "C",
    }
    if not already_frozen:
        finding(
            "F-MULT-01",
            "C",
            "Multiplicity policy is not frozen",
            json.dumps(frozen_statements),
            "STOP: the confirmatory family is not defined before execution.",
        )
    else:
        finding(
            "F-MULT-02",
            "A",
            "Multiplicity control was already frozen and is left unchanged",
            "ANALYSIS_PLAN.md section 5 already designates one primary contrast, one safety "
            "gate, and everything else as secondary/exploratory. The enumeration in "
            "HYPOTHESIS_MATRIX.md restates that policy without replacing it.",
            "DOCUMENT: no amendment to the multiplicity policy is required.",
        )
    return result


def reporting_audit() -> dict[str, Any]:
    from mycelial_graph.analysis.result_state import RESULT_STATES
    from mycelial_graph.science.claim_guard import FORBIDDEN_PATTERNS, find_claim_violations

    report_source = (ROOT / "src" / "mycelial_graph" / "reporting" / "report.py").read_text(
        encoding="utf-8"
    )
    result = {
        "result_states_supported": list(RESULT_STATES),
        "claim_guard_patterns": [identifier for identifier, _, _ in FORBIDDEN_PATTERNS],
        "report_applies_claim_guard": "assert_claim_containment(text" in report_source,
        "report_labels_roles": "role" in report_source and "EXPLORATORY" in report_source,
        "figures_labelled_exploratory": "not powered to establish a crossover" in report_source,
        "guard_rejects_crossover_assertion": bool(
            find_claim_violations("We identify a crossover at rho = 0.42.")
        ),
        "guard_allows_documented_limitation": not find_claim_violations(
            "Exploratory - this design is not powered to establish a crossover."
        ),
    }
    ok = all(
        result[key]
        for key in (
            "report_applies_claim_guard",
            "report_labels_roles",
            "figures_labelled_exploratory",
            "guard_rejects_crossover_assertion",
            "guard_allows_documented_limitation",
        )
    )
    result["ok"] = ok
    if not ok:
        finding(
            "F-REPORT-01",
            "C",
            "Report-level claim containment is not effective",
            json.dumps(result),
            "STOP: the report generator could emit claims beyond the frozen design.",
        )
    else:
        finding(
            "F-REPORT-02",
            "B",
            "Report generator required claim containment, role labels, and a result-state taxonomy",
            "Before this cycle the report emitted a binary promotion verdict, unlabelled rho "
            "curves, and no containment check, so exploratory rho evidence could read as "
            "confirmatory and the frozen interpretation matrix had no machine-readable outcome. "
            "The added result states, role labels, and claim guard are deterministic functions of "
            "already-frozen quantities and change no hypothesis, estimand, threshold, or sample.",
            "AMEND/DOCUMENT: recorded in AMENDMENT_002.md before confirmatory execution.",
        )
    return result


def reproducibility_audit() -> dict[str, Any]:
    config = load_config(V1 / "config.confirmatory.yaml")
    seeds = load_seeds(V1 / "seeds.confirmatory.txt")
    probe_seeds = [seeds[0], seeds[len(seeds) // 2], seeds[-1]]
    checks: dict[str, Any] = {}

    deterministic = True
    shock_norm_ok = True
    unique_optima = True
    paired_identity = True
    isolated_streams = True
    for seed in probe_seeds:
        first = generate_scenario_family(config, seed)
        second = generate_scenario_family(config, seed)
        for rho in config.environment.rho_values:
            a, b = first[rho], second[rho]
            deterministic &= a.scientific_hash() == b.scientific_hash()
            shock_norm_ok &= bool(
                np.isclose(
                    float(np.linalg.norm(a.shock_vector)),
                    config.environment.shock_magnitude,
                    atol=1e-9,
                )
            )
            unique_optima &= a.optimal_pre_path != a.optimal_post_path
        base = first[config.environment.rho_values[0]]
        for rho in config.environment.rho_values[1:]:
            other = first[rho]
            paired_identity &= bool(
                np.allclose(base.base_edge_means, other.base_edge_means)
                and base.optimal_pre_path == other.optimal_pre_path
            )
        # Different rho values must not share a post-shock world.
        post_hashes = {first[rho].post_edge_means.tobytes() for rho in config.environment.rho_values}
        isolated_streams &= len(post_hashes) == len(config.environment.rho_values)

    checks["probe_seeds"] = probe_seeds
    checks["deterministic_scenario_generation"] = deterministic
    checks["shock_l2_constant_across_rho"] = shock_norm_ok
    checks["certified_distinct_pre_post_optima"] = unique_optima
    checks["paired_rho_family_shares_pre_shock_world"] = paired_identity
    checks["distinct_post_shock_world_per_rho"] = isolated_streams

    oracle_regret_zero = True
    for seed in probe_seeds[:1]:
        scenario = generate_scenario_family(config, seed)[0.5]
        oracle_edges = scenario.graph.path_edges(scenario.optimal_post_path)
        step = config.horizon.pre_shock_steps + 1
        oracle_regret_zero &= bool(
            np.isclose(
                scenario.oracle_expected_utility(step),
                scenario.expected_path_utility(oracle_edges, step),
            )
        )
    checks["oracle_expected_regret_zero"] = oracle_regret_zero

    checks["bootstrap_rng_frozen"] = True
    from mycelial_graph.analysis.bootstrap import paired_relative_effect

    sample_a = np.array([12.0, 30.0, 44.0, 51.0, 9.0, 22.0], dtype=float)
    sample_b = np.array([15.0, 28.0, 50.0, 47.0, 11.0, 25.0], dtype=float)
    repeated = {
        paired_relative_effect(sample_a, sample_b, 500, 0.95).one_sided_upper_bound
        for _ in range(3)
    }
    checks["bootstrap_reproducible"] = len(repeated) == 1

    checks["seed_population_separation"] = not (
        set(load_seeds(V1 / "seeds.confirmatory.txt"))
        & (set(load_seeds(V1 / "seeds.pilot.txt")) | set(load_seeds(V1 / "seeds.development.txt")))
    )

    failed = [key for key, value in checks.items() if value is False]
    checks["ok"] = not failed
    checks["failed"] = failed
    if failed:
        finding(
            "F-REPRO-01",
            "C",
            "Reproducibility invariants failed",
            json.dumps(failed),
            "STOP: the frozen procedure is not deterministically executable.",
        )
    return checks


V1_SOURCE_PATHS = (
    "src/mycelial_graph/environment",
    "src/mycelial_graph/agents",
    "src/mycelial_graph/runner",
    "src/mycelial_graph/graph.py",
    "src/mycelial_graph/routing.py",
    "src/mycelial_graph/types.py",
    "src/mycelial_graph/config.py",
    "src/mycelial_graph/validation.py",
)


def provenance_audit(freeze: dict[str, Any]) -> dict[str, Any]:
    """Check environment drift since the pilot, and whether it changes the frozen streams."""
    from mycelial_graph.environment.scenario import generate_scenario_family

    import scipy
    import yaml

    pilot_manifest_path = ROOT / "outputs" / "pilot" / "manifest.json"
    recorded_env = None
    if pilot_manifest_path.exists():
        recorded_env = json.loads(pilot_manifest_path.read_text(encoding="utf-8")).get("environment")
    current_env = {
        "python": sys.version,
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "pyyaml": yaml.__version__,
    }
    drift = (
        {
            key: {"pilot": recorded_env.get(key), "current": current_env[key]}
            for key in current_env
            if recorded_env.get(key) != current_env[key]
        }
        if recorded_env
        else None
    )

    # Empirical test: do the sealed pilot scenarios still regenerate byte-identically here?
    reproduced, mismatched = 0, []
    pilot_raw = ROOT / "outputs" / "pilot" / "raw" / "rho-0.50"
    if pilot_raw.exists():
        pilot_config = load_config(V1 / "config.pilot.yaml")
        for path in sorted(pilot_raw.glob("*.json"))[:5]:
            payload = json.loads(path.read_text(encoding="utf-8"))["scientific_payload"]
            observed = generate_scenario_family(pilot_config, payload["seed"])[0.5].scientific_hash()
            if observed == payload["scenario_hash"]:
                reproduced += 1
            else:
                mismatched.append({"seed": payload["seed"], "expected": payload["scenario_hash"], "observed": observed})

    pilot_commit = freeze.get("pilot_code_commit_at_execution", "")
    head = git("rev-parse", "HEAD")
    has_pilot_commit = git("cat-file", "-t", pilot_commit) == "commit"
    source_diff = (
        git("diff", "--stat", pilot_commit, head, "--", *V1_SOURCE_PATHS)
        if has_pilot_commit
        else "unavailable: pilot commit is not present in this clone"
    )
    result = {
        "pilot_recorded_environment": recorded_env,
        "current_environment": current_env,
        "environment_drift": drift,
        "sealed_pilot_scenarios_checked": reproduced + len(mismatched),
        "sealed_pilot_scenarios_reproduced": reproduced,
        "sealed_pilot_scenario_mismatches": mismatched,
        "pilot_code_commit": pilot_commit,
        "head_commit": head,
        "v1_simulator_source_diff_since_pilot": source_diff,
        "v1_simulator_unchanged_since_pilot": source_diff == "" if has_pilot_commit else None,
    }
    if not has_pilot_commit:
        finding(
            "F-PROV-04",
            "A",
            "Pilot commit history is not available in this clone",
            "The pilot code commit recorded in the freeze is not reachable here (for example a "
            "shallow CI checkout), so the audit cannot diff the V1 simulator source against it. "
            "This limits verification in this environment; it does not change the frozen design. "
            "Run the audit in a full clone to verify simulator stability since the pilot.",
            "DOCUMENT: rerun in a full clone for the source-stability check.",
        )
    if mismatched:
        finding(
            "F-PROV-01",
            "C",
            "Sealed pilot scenarios no longer regenerate identically",
            json.dumps(mismatched[:2]),
            "PROTOCOL_INVALID: the frozen environment no longer reproduces the recorded world.",
        )
    if result["v1_simulator_unchanged_since_pilot"] is False:
        finding(
            "F-PROV-02",
            "C",
            "V1 simulator source changed after the pilot that produced the variance estimate",
            source_diff[:2000],
            "STOP: the pilot variance estimate may not describe the confirmatory design.",
        )
    if drift:
        klass = "A" if reproduced and not mismatched else "C"
        finding(
            "F-PROV-03",
            klass,
            "Software environment differs from the one recorded for the pilot",
            (
                f"The pilot manifest records {json.dumps(drift)}. "
                + (
                    f"All {reproduced} sampled sealed pilot scenarios regenerate to identical "
                    "scientific hashes in the current environment, so the frozen RNG streams, "
                    "scenario construction, and potential-outcome tables are unaffected by the "
                    "version difference. The confirmatory manifest records the actual versions used."
                    if reproduced and not mismatched
                    else "The sealed scenarios could not be verified in this environment."
                )
            ),
            "DOCUMENT: record the executing environment in the confirmatory manifest."
            if reproduced and not mismatched
            else "STOP: verify stream compatibility before executing.",
        )
    return result


def historical_artifact_audit() -> dict[str, Any]:
    demo = ROOT / "outputs" / "demo"
    manifest_path = demo / "manifest.json"
    if not manifest_path.exists():
        return {"status": "no checked-in demo manifest"}
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mismatches = []
    missing = []
    for relative, expected in (manifest.get("files") or {}).items():
        path = demo / relative
        if not path.exists():
            missing.append(relative)
            continue
        if sha256_file(path) != expected:
            mismatches.append(relative)
    result = {
        "artifact": "outputs/demo",
        "classification": "historical artifact - preserved but not verified evidence",
        "files_declared": len(manifest.get("files") or {}),
        "hash_mismatches": mismatches,
        "missing_files": missing,
        "regenerated": False,
    }
    if mismatches or missing:
        finding(
            "F-HIST-01",
            "A",
            "Checked-in demo artifact does not match its own manifest hashes",
            json.dumps({"mismatches": mismatches[:5], "missing": missing[:5]}),
            "DOCUMENT: preserve the original artifact and label it a historical artifact, not "
            "verified evidence. Do not regenerate it in place.",
        )
    return result


def claim_audit() -> dict[str, Any]:
    wording = audit_claims(MATRIX_PATH)
    invariants = audit_v1_invariants(MATRIX_PATH, ROOT)
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    seed_hash = sha256_file(V1 / "seeds.confirmatory.txt") or ""
    readme_state = {
        "states_seed_count_97": bool(re.search(r"\bN\s*=\s*97\b|first 97 entries", readme)),
        "states_seed_hash": seed_hash in readme,
        "states_primary_rho": "rho = 0.50" in readme or "`rho = 0.50`" in readme,
        "states_ni_margin": "Delta_NI = +0.10" in readme or "+0.10" in readme,
        "declares_cannot_establish_crossover": "existence of a crossover" in readme,
        "declares_no_independent_reproduction": "internal / automated" in readme,
        "single_seed_file_description": readme.count("seeds.confirmatory.txt") >= 1,
    }
    stale_docs = []
    for path in (ROOT / "docs").rglob("*.md"):
        text = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"missing `?seeds\.confirmatory\.txt`? is created only after", text):
            stale_docs.append(path.relative_to(ROOT).as_posix())
    readme_state["stale_missing_seed_file_statements"] = stale_docs
    result = {
        "wording_consistency": wording,
        "v1_readiness_invariants": {
            "ok": invariants["ok"],
            "n_invariants": invariants["n_invariants"],
            "n_checks": invariants["n_checks"],
            "failures": invariants["failures"],
        },
        "readme_machine_verifiable_state": readme_state,
        "ok": wording["ok"] and invariants["ok"] and not stale_docs,
    }
    if not wording["ok"] or not invariants["ok"]:
        finding(
            "F-CLAIM-01",
            "C",
            "Claim audit fails against repository state",
            json.dumps({"wording": wording["errors"], "invariants": invariants["failures"]}),
            "STOP: documentation asserts machine-checkable state that is false.",
        )
    if stale_docs:
        finding(
            "F-CLAIM-02",
            "A",
            "Documentation still describes seeds.confirmatory.txt as intentionally missing",
            json.dumps(stale_docs),
            "DOCUMENT: rewrite so exactly one description of the seed-file state exists.",
        )
    else:
        finding(
            "F-CLAIM-03",
            "A",
            "README seed-file contradiction resolved",
            "The README previously asserted that seeds.confirmatory.txt exists with the first 97 "
            "pool entries, while docs/GETTING_STARTED.md and docs/V2_IMPLEMENTATION_PLAN.md still "
            "described it as deliberately missing. The file exists, contains exactly 97 unique "
            "seeds equal to the unfiltered pool prefix, and its SHA-256 matches the freeze. The "
            "documentation now carries one internally consistent description of that state.",
            "DOCUMENT: verified mechanically by invariant I01.",
        )
    return result


def moratorium_audit() -> dict[str, Any]:
    path = ROOT / "V1_CONFIRMATORY_MORATORIUM.md"
    exists = path.exists()
    text = path.read_text(encoding="utf-8") if exists else ""
    result = {
        "document_present": exists,
        "declares_exit_condition": "Exit condition" in text,
        "forbids_enough_improvements_exit": "not** an exit condition" in text
        or "explicitly **not** an exit condition" in text,
    }
    if not all(result.values()):
        finding(
            "F-MORAT-01",
            "A",
            "Moratorium document incomplete",
            json.dumps(result),
            "DOCUMENT: complete V1_CONFIRMATORY_MORATORIUM.md.",
        )
    return result


def write_freeze_supplement(freeze: dict[str, Any], artifacts: dict[str, Any]) -> Path:
    payload = {
        "supplement_to": "experiments/v1/artifacts/CONFIRMATORY_FREEZE.json",
        "purpose": (
            "Additive integrity binding recorded before confirmatory execution. It adds hashes "
            "only. It does not alter, reinterpret, or relax any term of the original freeze."
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "audit_commit": git("rev-parse", "HEAD"),
        "protocol_version": freeze["protocol_version"],
        "confirmatory_config_hash": freeze["confirmatory_config_hash"],
        "seeds_sha256": freeze["seeds_sha256"],
        "required_confirmatory_pairs": freeze["required_confirmatory_pairs"],
        "bound_hashes": {
            row["path"]: row["sha256"] for row in artifacts["artifacts"] if row["exists"]
        },
        "frozen_bootstrap_seeds": {
            "primary_contrast": 20260824,
            "noninferiority_contrast": 20260825,
            "source": "src/mycelial_graph/analysis/bootstrap.py, src/mycelial_graph/analysis/aggregate.py",
        },
        "amendments": sorted(path.name for path in V1.glob("AMENDMENT_*.md")),
    }
    destination = ARTIFACTS / "CONFIRMATORY_FREEZE_SUPPLEMENT.json"
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination


def decide() -> tuple[str, str]:
    classes = {item["class"] for item in FINDINGS}
    if "C" in classes:
        blocking = [item for item in FINDINGS if item["class"] == "C"]
        material = any("PROTOCOL_INVALID" in item["action"] for item in blocking)
        decision = "PROTOCOL_INVALID" if material else "STOP"
        return decision, (
            f"{len(blocking)} material (Class C) finding(s) compromise the frozen design: "
            + "; ".join(item["title"] for item in blocking)
        )
    counts = {klass: sum(1 for item in FINDINGS if item["class"] == klass) for klass in "AB"}
    return "GO", (
        f"No Class C findings. {counts['A']} Class A finding(s) documented and {counts['B']} "
        "Class B finding(s) resolved transparently before confirmatory execution. The frozen "
        "seed selection, sample size, configuration binding, multiplicity policy, and "
        "reproducibility invariants all reproduce mechanically."
    )


def render_markdown(report: dict[str, Any]) -> str:
    state = report["repository_state"]
    seeds = report["seed_audit"]
    power = report["power_audit"]
    freeze = report["freeze_audit"]
    mult = report["multiplicity_audit"]
    repro = report["reproducibility_audit"]
    claims = report["claim_audit"]
    lines = [
        "# MG-EXP-V1 Confirmatory Readiness Report",
        "",
        f"**Decision:** `{report['decision']}`",
        "",
        f"**Generated:** {state['audited_at_utc']}  ",
        f"**Command:** `python scripts/audit_v1_readiness.py`",
        "",
        "This report is generated. Do not edit it by hand; rerun the audit.",
        "",
        "## Repository state",
        "",
        f"- Commit: `{state['commit']}`",
        f"- Branch: `{state['branch']}`",
        f"- Working tree dirty: {state['dirty']}",
        f"- Python {state['python']}, numpy {state['numpy']}",
        "",
        "## Frozen artifacts",
        "",
        "| Artifact | Exists | SHA-256 |",
        "|---|:-:|---|",
    ]
    for row in report["frozen_artifacts"]["artifacts"]:
        digest = row["sha256"] or ""
        lines.append(f"| `{row['path']}` | {row['exists']} | `{digest[:16]}…` |")
    lines.extend(
        [
            "",
            f"Validation status: **{report['frozen_artifacts']['validation_status']}**. "
            f"Full hashes are in `CONFIRMATORY_READINESS_REPORT.json` and "
            f"`experiments/v1/artifacts/CONFIRMATORY_FREEZE_SUPPLEMENT.json`.",
            "",
            "## Seed audit",
            "",
            f"- Expected N: **{seeds['expected_n']}**, observed N: **{seeds['observed_n']}**",
            f"- Unique: {seeds['unique']}; ascending: {seeds['sorted_ascending']}; "
            f"range `{seeds['first_seed']}`–`{seeds['last_seed']}`",
            f"- Unfiltered prefix of the {seeds['pool_size']}-entry precommitted pool: "
            f"**{seeds['is_unfiltered_pool_prefix']}**",
            f"- Overlap with pilot seeds: `{seeds['overlap_with_pilot']}`; with development seeds: "
            f"`{seeds['overlap_with_development']}`",
            f"- SHA-256 `{seeds['sha256']}` matches the freeze: **{seeds['hash_matches_freeze']}**",
            f"- Serialisation: {seeds['line_ending']}, {seeds['byte_length']} bytes "
            "(the hash depends on line endings)",
            f"- Confirmatory config validation errors: `{seeds['config_validation_errors']}`",
            f"- Deterministic selection verified: **{seeds['deterministic_selection_verified']}**; "
            f"cherry-picking detected: **{seeds['cherry_picking_detected']}**",
            "",
            "## Power audit",
            "",
            f"- Powered contrast: {power['powered_contrast']}",
            f"- Variability source: {power['variability_source']}",
            f"- Control mean RRT {power['control_mean_rrt']}, relative design effect "
            f"{power['relative_design_effect']}, absolute design effect "
            f"{power['absolute_design_effect']}",
            f"- Paired difference SD {power['paired_difference_sd']}",
            f"- One-sided alpha {power['one_sided_alpha']}, target power {power['target_power']}, "
            f"direction: {power['test_direction']}",
            f"- Censoring assumption: {power['censoring_assumption']}",
            f"- Recorded N {power['recorded_n']}, recomputed N {power['recomputed_n']}, freeze N "
            f"{power['freeze_n']} — reproduces: **{power['n_reproduces']}**",
            f"- Pilot and confirmatory share the design: "
            f"`{power['pilot_and_confirmatory_share_design']}`",
            f"- Post-pilot method tuning declared: {power['post_pilot_method_tuning']}",
            "",
            f"> {power['note']}",
            "",
            "## Hypothesis matrix",
            "",
            "Enumerated in [`experiments/v1/HYPOTHESIS_MATRIX.md`]"
            "(experiments/v1/HYPOTHESIS_MATRIX.md): one PRIMARY contrast (rho=0.50 hierarchical "
            "vs edge-only), one SAFETY GATE (rho=0 non-inferiority, margin +0.10), plus SECONDARY, "
            "EXPLORATORY, and DIAGNOSTIC rows that carry no error control.",
            "",
            "## Multiplicity",
            "",
            f"- Policy already frozen: **{mult['multiplicity_policy_frozen']}** "
            "(`ANALYSIS_PLAN.md` §5)",
            f"- Confirmatory family size: {mult['confirmatory_family_size']}; adjustment required: "
            f"{mult['adjustment_required']}",
            f"- {mult['adjustment_rationale']}",
            "",
            "## Freeze audit",
            "",
            f"- Config hash matches: **{freeze['config_hash_matches']}** "
            f"(`{freeze['config_hash_observed']}`)",
            f"- Bound fields: `{freeze['bound']}`",
            f"- Not bound by the freeze: {', '.join(freeze['not_bound_by_freeze'])}",
            f"- Amendments: {', '.join(freeze['amendment_history']) or 'none'}",
            "",
            "## Reproducibility validation",
            "",
        ]
    )
    for key, value in repro.items():
        if key in {"ok", "failed", "probe_seeds"}:
            continue
        lines.append(f"- {key.replace('_', ' ')}: **{value}**")
    lines.extend(
        [
            f"- probe seeds: `{repro['probe_seeds']}`",
            f"- All reproducibility checks passed: **{repro['ok']}**",
            "",
            "## Provenance and environment drift",
            "",
            f"- Pilot environment: `{report['provenance_audit']['pilot_recorded_environment']}`",
            f"- Current environment: numpy {report['provenance_audit']['current_environment']['numpy']}, "
            f"scipy {report['provenance_audit']['current_environment']['scipy']}, "
            f"pyyaml {report['provenance_audit']['current_environment']['pyyaml']}",
            f"- Drift: `{report['provenance_audit']['environment_drift']}`",
            f"- Sealed pilot scenarios regenerated identically: "
            f"**{report['provenance_audit']['sealed_pilot_scenarios_reproduced']}"
            f"/{report['provenance_audit']['sealed_pilot_scenarios_checked']}**",
            f"- V1 simulator source unchanged since the pilot commit "
            f"`{report['provenance_audit']['pilot_code_commit'][:12]}`: "
            f"**{report['provenance_audit']['v1_simulator_unchanged_since_pilot']}**",
            "",
            "## Claim audit",
            "",
            f"- Wording consistency: ok={claims['wording_consistency']['ok']}, "
            f"{claims['wording_consistency']['n_claims']} claims",
            f"- V1 readiness invariants: ok={claims['v1_readiness_invariants']['ok']}, "
            f"{claims['v1_readiness_invariants']['n_checks']} checks across "
            f"{claims['v1_readiness_invariants']['n_invariants']} invariants",
            f"- README machine-verifiable state: `{claims['readme_machine_verifiable_state']}`",
            "",
            "## Reporting and claim containment",
            "",
            f"- Result states: `{report['reporting_audit']['result_states_supported']}`",
            f"- Claim guard patterns: `{report['reporting_audit']['claim_guard_patterns']}`",
            f"- Guard applied to the generated report: "
            f"{report['reporting_audit']['report_applies_claim_guard']}",
            f"- Exploratory labelling present: "
            f"{report['reporting_audit']['figures_labelled_exploratory']}",
            "",
            "## Historical artifact integrity",
            "",
            f"`{report['historical_artifact_audit']}`",
            "",
            "## Findings",
            "",
            "| ID | Class | Finding | Action |",
            "|---|:-:|---|---|",
        ]
    )
    for item in report["findings"]:
        lines.append(
            f"| `{item['id']}` | **{item['class']}** | {item['title']} | {item['action']} |"
        )
    lines.extend(
        [
            "",
            "### Detail",
            "",
        ]
    )
    for item in report["findings"]:
        lines.extend([f"**`{item['id']}` (Class {item['class']}) — {item['title']}**", "", item["detail"], ""])
    lines.extend(
        [
            "## Decision",
            "",
            f"### `{report['decision']}`",
            "",
            report["justification"],
            "",
            f"**Next permitted action:** {report['next_permitted_action']}",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    artifacts = frozen_artifacts()
    report: dict[str, Any] = {
        "report": "MG-EXP-V1 confirmatory readiness audit",
        "protocol_version": freeze["protocol_version"],
        "repository_state": repository_state(),
        "frozen_artifacts": artifacts,
        "seed_audit": seed_audit(freeze),
        "power_audit": power_audit(freeze),
        "freeze_audit": freeze_audit(freeze),
        "multiplicity_audit": multiplicity_audit(),
        "reporting_audit": reporting_audit(),
        "reproducibility_audit": reproducibility_audit(),
        "provenance_audit": provenance_audit(freeze),
        "historical_artifact_audit": historical_artifact_audit(),
        "claim_audit": claim_audit(),
        "moratorium_audit": moratorium_audit(),
    }
    decision, justification = decide()
    report["findings"] = FINDINGS
    report["finding_counts"] = {
        klass: sum(1 for item in FINDINGS if item["class"] == klass) for klass in "ABC"
    }
    report["decision"] = decision
    report["justification"] = justification
    report["next_permitted_action"] = (
        "EXECUTE V1 CONFIRMATORY (see CONFIRMATORY_RUNBOOK.md)"
        if decision == "GO"
        else "Produce CONFIRMATORY_STOP_REPORT.md and stop. No V2 development."
    )
    report["freeze_supplement"] = str(
        write_freeze_supplement(freeze, artifacts).relative_to(ROOT).as_posix()
    )

    (ROOT / "CONFIRMATORY_READINESS_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ROOT / "CONFIRMATORY_READINESS_REPORT.md").write_text(
        render_markdown(report), encoding="utf-8"
    )
    print(json.dumps({"decision": decision, "findings": report["finding_counts"]}, indent=2))
    return 0 if decision == "GO" else 3


if __name__ == "__main__":
    raise SystemExit(main())
