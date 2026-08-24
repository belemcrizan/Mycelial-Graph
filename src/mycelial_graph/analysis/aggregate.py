from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from ..runner.checkpoint import atomic_write_json
from ..types import ExperimentConfig
from .bootstrap import paired_relative_effect


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
            **primary.__dict__,
        },
        "noninferiority_contrast": (
            {
                "rho": 0.0,
                "margin": config.analysis.noninferiority_margin,
                **noninferiority.__dict__,
            }
            if noninferiority
            else None
        ),
        "decision_gate": gate,
        "group_metrics": _group_metrics(trials),
    }
    path = output / "processed" / "analysis.json"
    atomic_write_json(path, analysis)
    return path
