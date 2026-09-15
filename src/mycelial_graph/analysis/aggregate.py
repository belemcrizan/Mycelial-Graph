from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from ..runner.checkpoint import atomic_write_json
from ..types import ExperimentConfig
from .bootstrap import paired_relative_effect
from .result_state import classify_result_state


def _read_trials(output_directory: Path) -> list[dict[str, Any]]:
    trials: list[dict[str, Any]] = []
    for path in sorted((output_directory / "raw").rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))["scientific_payload"]
        trials.extend(payload["results"])
    if not trials:
        raise ValueError(f"No raw trial results found under {output_directory / 'raw'}")
    return trials


def _group_metrics(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[float, str], list[dict[str, Any]]] = defaultdict(list)
    for trial in trials:
        groups[(float(trial["rho"]), trial["method"])].append(trial)
    rows = []
    for (rho, method), items in sorted(groups.items()):
        rrt = np.array([item["restricted_recovery_time"] for item in items], dtype=float)
        regret = np.array([item["dynamic_regret"] for item in items], dtype=float)
        utility = np.array([item["final_expected_utility"] for item in items], dtype=float)
        recovered = np.array([item["recovered"] for item in items], dtype=float)
        cpu = np.array([item["decision_cpu_seconds"] for item in items], dtype=float)
        rows.append(
            {
                "rho": rho,
                "method": method,
                "trials": len(items),
                "restricted_recovery_time_mean": float(np.mean(rrt)),
                "restricted_recovery_time_std": float(np.std(rrt, ddof=1)) if len(rrt) > 1 else 0.0,
                "rmst_estimate": float(np.mean(rrt)),
                "recovery_probability": float(np.mean(recovered)),
                "dynamic_regret_mean": float(np.mean(regret)),
                "final_expected_utility_mean": float(np.mean(utility)),
                "decision_cpu_seconds_mean": float(np.mean(cpu)),
                "decision_cpu_seconds_p95": float(np.quantile(cpu, 0.95)),
            }
        )
    return rows


def _row_role(row: dict[str, Any], config: ExperimentConfig) -> str:
    """Role label from `HYPOTHESIS_MATRIX.md`, so no row can be read as confirmatory."""
    rho = float(row["rho"])
    primary_rho = float(config.analysis.primary_rho)
    frozen_pair = row["method"] in {"hierarchical", "edge_only"}
    if frozen_pair and (np.isclose(rho, primary_rho) or np.isclose(rho, 0.0)):
        return "CONFIRMATORY INPUT"
    if np.isclose(rho, primary_rho) or np.isclose(rho, 0.0):
        return "SECONDARY"
    if np.isclose(rho, 1.0):
        return "DIAGNOSTIC"
    return "EXPLORATORY"


def _paired_arrays(
    trials: list[dict[str, Any]], rho: float, treatment: str, control: str
) -> tuple[np.ndarray, np.ndarray]:
    by_scenario: dict[str, dict[str, float]] = defaultdict(dict)
    for trial in trials:
        if np.isclose(float(trial["rho"]), rho):
            by_scenario[trial["scenario_id"]][trial["method"]] = float(
                trial["restricted_recovery_time"]
            )
    pairs = [values for values in by_scenario.values() if treatment in values and control in values]
    if len(pairs) < 2:
        raise ValueError(f"Not enough paired results for rho={rho}.")
    return (
        np.array([pair[treatment] for pair in pairs], dtype=float),
        np.array([pair[control] for pair in pairs], dtype=float),
    )


def _frozen_sample_size(config: ExperimentConfig) -> int | None:
    """Frozen pair count for a confirmatory run, or None when no lock applies."""
    if config.run_kind != "confirmatory":
        return None
    from ..validation import load_seeds

    return len(load_seeds((config.source_path.parent / config.seeds_file).resolve()))


def _frozen_contrast_integrity(
    trials: list[dict[str, Any]],
    config: ExperimentConfig,
    primary_pairs: int,
) -> dict[str, Any]:
    """Count integrity violations that suspend automated primary interpretation.

    Censoring is administrative when an unrecovered trial is restricted at the post-shock
    horizon. Anything else, and any method-level failure inside the frozen rho=0.50 primary
    contrast or the rho=0 safety gate, is an integrity violation under `ANALYSIS_PLAN.md` §6.
    """
    frozen_rho = {0.0, float(config.analysis.primary_rho)}
    frozen_methods = {"hierarchical", "edge_only"}
    non_administrative = 0
    failures_in_frozen = 0
    for trial in trials:
        if trial["censored"] and int(trial["restricted_recovery_time"]) != config.horizon.post_shock_steps:
            non_administrative += 1
        in_frozen_contrast = trial["method"] in frozen_methods and any(
            np.isclose(float(trial["rho"]), rho) for rho in frozen_rho
        )
        if in_frozen_contrast and trial.get("method_status", "completed") != "completed":
            failures_in_frozen += 1
    return {
        "non_administrative_censoring": non_administrative,
        "method_failures_in_frozen_contrasts": failures_in_frozen,
        "primary_pairs": primary_pairs,
        "censoring_is_administrative_only": non_administrative == 0,
    }


def analyze_results(config: ExperimentConfig, output_directory: str | Path) -> Path:
    output = Path(output_directory).resolve()
    trials = _read_trials(output)
    primary_treatment, primary_control = _paired_arrays(
        trials,
        config.analysis.primary_rho,
        "hierarchical",
        "edge_only",
    )
    primary = paired_relative_effect(
        primary_treatment,
        primary_control,
        config.analysis.bootstrap_samples,
        config.analysis.confidence_level,
    )
    noninferiority = None
    if 0.0 in config.environment.rho_values:
        treatment, control = _paired_arrays(trials, 0.0, "hierarchical", "edge_only")
        noninferiority = paired_relative_effect(
            treatment,
            control,
            config.analysis.bootstrap_samples,
            config.analysis.confidence_level,
            seed=20260825,
            null_margin=config.analysis.noninferiority_margin,
        )
    gate = {
        "statistical_superiority": primary.one_sided_upper_bound < 0.0,
        "engineering_gain": primary.estimate <= -config.analysis.engineering_gain_gate,
        "noninferiority_at_rho_0": (
            noninferiority.one_sided_upper_bound < config.analysis.noninferiority_margin
            if noninferiority
            else None
        ),
    }
    gate["promote_to_v1"] = bool(
        gate["statistical_superiority"]
        and gate["engineering_gain"]
        and gate["noninferiority_at_rho_0"] is True
    )
    gate["automated_requirements"] = "protocol section 8.2 requirements 1-3"
    gate["operational_cost_budget_requirement"] = (
        "protocol section 8.2 requirement 4 is not automated: no cost budget is frozen, "
        "so product promotion additionally requires a separate operational-cost decision"
    )
    primary_dict = {**primary.__dict__}
    noninferiority_dict = {**noninferiority.__dict__} if noninferiority else None
    integrity = _frozen_contrast_integrity(trials, config, len(primary_treatment))
    result_state = classify_result_state(
        primary_dict,
        noninferiority_dict,
        integrity,
        config.analysis.engineering_gain_gate,
        config.analysis.noninferiority_margin,
        _frozen_sample_size(config),
    )
    analysis = {
        "run_kind": config.run_kind,
        "status": (
            "confirmatory"
            if config.run_kind == "confirmatory"
            else "development-only; no confirmatory claim"
        ),
        "estimand": "relative difference in mean restricted recovery time",
        "primary_contrast": {
            "rho": config.analysis.primary_rho,
            "treatment": "hierarchical",
            "control": "edge_only",
            "role": "PRIMARY",
            **primary_dict,
        },
        "noninferiority_contrast": (
            {
                "rho": 0.0,
                "margin": config.analysis.noninferiority_margin,
                "role": "SAFETY GATE",
                **noninferiority_dict,
            }
            if noninferiority_dict
            else None
        ),
        "decision_gate": gate,
        "frozen_contrast_integrity": integrity,
        "result_state": result_state,
        "group_metrics": [
            {**row, "role": _row_role(row, config)} for row in _group_metrics(trials)
        ],
        "claim_boundary": (
            "Only the rho=0.50 hierarchical-versus-edge-only contrast and the rho=0 "
            "non-inferiority gate are confirmatory. Every other row is secondary, exploratory, "
            "or diagnostic and cannot support an inferential claim. See "
            "experiments/v1/HYPOTHESIS_MATRIX.md."
        ),
    }
    path = output / "processed" / "analysis.json"
    atomic_write_json(path, analysis)
    return path
