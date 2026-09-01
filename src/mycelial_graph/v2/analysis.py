from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from ..runner.checkpoint import atomic_write_json
from .metrics import MethodPoint, nondominated, paired_absolute_effect
from .types import V2ExperimentConfig


def _read_trials(output_directory: Path) -> list[dict[str, Any]]:
    trials: list[dict[str, Any]] = []
    for path in sorted((output_directory / "raw").rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))["scientific_payload"]
        trials.extend(payload["results"])
    if not trials:
        raise ValueError(f"No V2 raw trials under {output_directory / 'raw'}")
    return trials


def _group(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for trial in trials:
        groups[(trial["regime"], trial["method"])].append(trial)
    rows = []
    for (regime, method), items in sorted(groups.items()):
        quality = np.array([item["post_quality"] for item in items], dtype=float)
        tokens = np.array([item["post_tokens"] for item in items], dtype=float)
        cost = np.array([item["post_cost"] for item in items], dtype=float)
        latency = np.array([item["post_latency"] for item in items], dtype=float)
        success = np.array([item["success_rate"] for item in items], dtype=float)
        rrt = np.array([item["restricted_recovery_time"] for item in items], dtype=float)
        recovered = np.array([item["recovered"] for item in items], dtype=float)
        ledger_tokens = np.array([item["ledger"]["total_tokens"] for item in items], dtype=float)
        router = np.array([item["ledger"]["router_tokens"] for item in items], dtype=float)
        rows.append(
            {
                "regime": regime,
                "method": method,
                "trials": len(items),
                "quality_mean": float(np.mean(quality)),
                "tokens_mean": float(np.mean(tokens)),
                "ledger_tokens_mean": float(np.mean(ledger_tokens)),
                "router_tokens_mean": float(np.mean(router)),
                "cost_mean": float(np.mean(cost)),
                "latency_mean": float(np.mean(latency)),
                "success_mean": float(np.mean(success)),
                "rrt_mean": float(np.mean(rrt)),
                "recovery_probability": float(np.mean(recovered)),
                "switches_mean": float(np.mean([item["route_switches"] for item in items])),
            }
        )
    return rows


def _paired(
    trials: list[dict[str, Any]], regime: str, field: str, treatment: str, control: str
) -> tuple[np.ndarray, np.ndarray]:
    by_scenario: dict[str, dict[str, float]] = defaultdict(dict)
    for trial in trials:
        if trial["regime"] == regime:
            by_scenario[trial["scenario_id"]][trial["method"]] = float(trial[field])
    pairs = [values for values in by_scenario.values() if treatment in values and control in values]
    if len(pairs) < 2:
        raise ValueError(f"Not enough paired V2 results for regime={regime}.")
    return (
        np.array([pair[treatment] for pair in pairs], dtype=float),
        np.array([pair[control] for pair in pairs], dtype=float),
    )


def _label(quality_ni: bool, token_reduction: bool | None, interval_crosses: bool) -> str:
    if quality_ni and token_reduction:
        return "PASS"
    if quality_ni and token_reduction is False:
        return "CONDITIONAL"
    if interval_crosses:
        return "INCONCLUSIVE"
    if not quality_ni:
        return "REFUTED"
    return "CONDITIONAL"


def analyze_v2_results(config: V2ExperimentConfig, output_directory: str | Path) -> Path:
    output = Path(output_directory).resolve()
    trials = _read_trials(output)
    regime = config.environment.primary_regime
    q_t, q_c = _paired(trials, regime, "post_quality", "v2_mycelial", "always_high_compute")
    t_t, t_c = _paired(trials, regime, "post_tokens", "v2_mycelial", "always_high_compute")
    quality = paired_absolute_effect(
        q_t, q_c, config.analysis.bootstrap_samples, config.analysis.confidence_level
    )
    tokens = paired_absolute_effect(
        t_t,
        t_c,
        config.analysis.bootstrap_samples,
        config.analysis.confidence_level,
        seed=20260832,
    )
    eps = config.analysis.quality_noninferiority_margin
    quality_ni = quality.one_sided_lower_bound > -eps
    token_reduction = tokens.one_sided_upper_bound < 0.0
    interval_crosses = quality.confidence_low <= -eps <= quality.confidence_high
    label = _label(quality_ni, token_reduction, interval_crosses)
    group_metrics = _group(trials)
    points = [
        MethodPoint(row["method"], row["quality_mean"], row["tokens_mean"], row["cost_mean"], row["latency_mean"])
        for row in group_metrics
        if row["regime"] == regime
    ]
    frontier = [point.method for point in nondominated(points)]
    analysis = {
        "run_kind": config.run_kind,
        "status": (
            "confirmatory"
            if config.run_kind == "confirmatory"
            else "development-only; no confirmatory claim"
        ),
        "decision_label": label if config.run_kind == "confirmatory" else f"non-confirmatory:{label}",
        "primary_regime": regime,
        "quality_noninferiority": {
            "margin": eps,
            "treatment": "v2_mycelial",
            "control": "always_high_compute",
            "passed": quality_ni,
            **quality.__dict__,
        },
        "token_reduction": {
            "treatment": "v2_mycelial",
            "control": "always_high_compute",
            "passed": token_reduction,
            **tokens.__dict__,
        },
        "pareto_nondominated_methods": frontier,
        "group_metrics": group_metrics,
        "claim_boundary": (
            "Do not describe this run as evidence that mycelial routing is optimal. "
            "Quality is tested for non-inferiority first; token totals include router overhead."
        ),
    }
    path = output / "processed" / "analysis.json"
    atomic_write_json(path, analysis)
    return path
