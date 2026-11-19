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


def _cohens_dz(diff: np.ndarray) -> float:
    if len(diff) < 2:
        return 0.0
    sd = float(np.std(diff, ddof=1))
    return float(np.mean(diff) / sd) if sd > 1e-12 else 0.0


def _holm_bonferroni(p_values: list[float]) -> list[float]:
    """Step-down Holm-Bonferroni family-wise error adjustment."""
    m = len(p_values)
    if m == 0:
        return []
    order = np.argsort(p_values)
    adjusted = [0.0] * m
    running_max = 0.0
    for rank, idx in enumerate(order):
        val = min(1.0, float(p_values[idx]) * (m - rank))
        running_max = max(running_max, val)
        adjusted[int(idx)] = running_max
    return adjusted


def _group(trials: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for trial in trials:
        groups[(trial["regime"], trial["method"])].append(trial)
    rows = []
    for (regime, method), items in sorted(groups.items()):
        quality = np.array([item["post_quality"] for item in items], dtype=float)
        realized_q = np.array(
            [item.get("post_realized_quality", item["post_quality"]) for item in items], dtype=float
        )
        regret = np.array([item.get("post_regret", 0.0) for item in items], dtype=float)
        tokens = np.array([item["post_tokens"] for item in items], dtype=float)
        post_router = np.array(
            [item.get("post_router_tokens", item["ledger"]["router_tokens"]) for item in items],
            dtype=float,
        )
        cost = np.array([item["post_cost"] for item in items], dtype=float)
        latency = np.array([item["post_latency"] for item in items], dtype=float)
        success = np.array([item["success_rate"] for item in items], dtype=float)
        rrt = np.array([item["restricted_recovery_time"] for item in items], dtype=float)
        recovered = np.array([item["recovered"] for item in items], dtype=float)
        ledger_tokens = np.array([item["ledger"]["total_tokens"] for item in items], dtype=float)
        router_full = np.array([item["ledger"]["router_tokens"] for item in items], dtype=float)
        cpu_ms = np.array([item.get("decision_cpu_seconds", 0.0) * 1000.0 for item in items], dtype=float)

        post_steps = max(int(items[0].get("post_shock_steps", 1)), 1)
        succ_tasks = float(np.sum(success * post_steps))
        tpst = float(np.sum(tokens) / succ_tasks) if succ_tasks > 0 else None
        cpst = float(np.sum(cost) / succ_tasks) if succ_tasks > 0 else None

        rows.append(
            {
                "regime": regime,
                "method": method,
                "trials": len(items),
                "quality_mean": float(np.mean(quality)),
                "quality_sd": float(np.std(quality, ddof=1)) if len(quality) > 1 else 0.0,
                "realized_quality_mean": float(np.mean(realized_q)),
                "regret_mean": float(np.mean(regret)),
                "tokens_mean": float(np.mean(tokens)),
                "tokens_sd": float(np.std(tokens, ddof=1)) if len(tokens) > 1 else 0.0,
                "post_router_tokens_mean": float(np.mean(post_router)),
                "ledger_tokens_mean": float(np.mean(ledger_tokens)),
                "router_tokens_mean": float(np.mean(router_full)),
                "cost_mean": float(np.mean(cost)),
                "latency_mean": float(np.mean(latency)),
                "success_mean": float(np.mean(success)),
                "tokens_per_successful_task": tpst,
                "cost_per_successful_task": cpst,
                "rrt_mean": float(np.mean(rrt)),
                "recovery_probability": float(np.mean(recovered)),
                "switches_mean": float(np.mean([item["route_switches"] for item in items])),
                "exploratory_steps_mean": float(
                    np.mean([item.get("exploratory_steps", 0) for item in items])
                ),
                "policy_cpu_ms_mean": float(np.mean(cpu_ms)),
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


def _classify_v2_outcome(
    *,
    quality_lower_bound: float,
    quality_upper_bound: float,
    margin: float,
    stat_token_reduction: bool,
    practical_token_reduction: bool,
) -> str:
    """Consistent 4-state decision rule without overlapping 90%/95% contradictions."""
    if quality_upper_bound <= -margin:
        return "REFUTED"
    if quality_lower_bound <= -margin:
        return "INCONCLUSIVE"
    # Quality non-inferiority established (one_sided_lower_bound > -margin):
    if stat_token_reduction and practical_token_reduction:
        return "PASS"
    if stat_token_reduction:
        return "CONDITIONAL"
    return "CONDITIONAL"


def analyze_v2_results(config: V2ExperimentConfig, output_directory: str | Path) -> Path:
    output = Path(output_directory).resolve()
    trials = _read_trials(output)
    regime = config.environment.primary_regime
    q_t, q_c = _paired(trials, regime, "post_quality", "v2_mycelial", "always_high_compute")
    t_t, t_c = _paired(trials, regime, "post_tokens", "v2_mycelial", "always_high_compute")
    c_t, c_c = _paired(trials, regime, "post_cost", "v2_mycelial", "always_high_compute")

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
    cost_eff = paired_absolute_effect(
        c_t,
        c_c,
        config.analysis.bootstrap_samples,
        config.analysis.confidence_level,
        seed=20260833,
    )

    eps = config.analysis.quality_noninferiority_margin
    quality_ni = bool(quality.one_sided_lower_bound > -eps)
    mean_control_tokens = max(float(np.mean(t_c)), 1.0)
    relative_token_delta = float((np.mean(t_t) - np.mean(t_c)) / mean_control_tokens)
    required_rel_gate = max(float(config.analysis.engineering_token_gate), float(config.analysis.mmrr))
    stat_token_reduction = bool(tokens.one_sided_upper_bound < 0.0)
    practical_token_reduction = bool(relative_token_delta <= -required_rel_gate)
    token_gate_passed = bool(stat_token_reduction and practical_token_reduction)

    label = _classify_v2_outcome(
        quality_lower_bound=quality.one_sided_lower_bound,
        quality_upper_bound=quality.one_sided_upper_bound,
        margin=eps,
        stat_token_reduction=stat_token_reduction,
        practical_token_reduction=practical_token_reduction,
    )

    # Secondary baseline comparisons with Holm-Bonferroni adjustment at primary regime.
    methods_present = sorted({t["method"] for t in trials if t["regime"] == regime} - {"v2_mycelial"})
    secondary_contrasts: list[dict[str, Any]] = []
    raw_pvals: list[float] = []
    rng_boot = np.random.default_rng(20260840)
    for comp in methods_present:
        qt, qc = _paired(trials, regime, "post_quality", "v2_mycelial", comp)
        tt, tc = _paired(trials, regime, "post_tokens", "v2_mycelial", comp)
        q_diff = qt - qc
        t_diff = tt - tc
        # Bootstrap two-sided p-value on net utility surrogate (Q - lambda_t * dT / 1000)
        net_diff = q_diff - config.utility.lambda_tokens * (t_diff / 1000.0)
        idx = rng_boot.integers(0, len(net_diff), size=(config.analysis.bootstrap_samples, len(net_diff)))
        boot_means = np.mean(net_diff[idx], axis=1)
        p_pos = float(np.mean(boot_means <= 0.0))
        p_neg = float(np.mean(boot_means >= 0.0))
        p_two = min(1.0, 2.0 * min(p_pos, p_neg))
        raw_pvals.append(p_two)
        secondary_contrasts.append(
            {
                "comparator": comp,
                "delta_quality_mean": float(np.mean(q_diff)),
                "delta_quality_dz": _cohens_dz(q_diff),
                "delta_tokens_mean": float(np.mean(t_diff)),
                "delta_tokens_relative": float(np.mean(t_diff) / max(float(np.mean(tc)), 1.0)),
                "net_utility_diff_mean": float(np.mean(net_diff)),
                "net_utility_cohens_dz": _cohens_dz(net_diff),
                "raw_p_value": p_two,
            }
        )
    adj_pvals = _holm_bonferroni(raw_pvals)
    for row, p_adj in zip(secondary_contrasts, adj_pvals):
        row["holm_adjusted_p_value"] = p_adj

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
            else f"{config.run_kind}-only; no confirmatory claim"
        ),
        "decision_label": label if config.run_kind == "confirmatory" else f"non-confirmatory:{label}",
        "primary_regime": regime,
        "quality_noninferiority": {
            "margin": eps,
            "treatment": "v2_mycelial",
            "control": "always_high_compute",
            "passed": quality_ni,
            "cohens_dz": _cohens_dz(q_t - q_c),
            **quality.__dict__,
        },
        "token_reduction": {
            "treatment": "v2_mycelial",
            "control": "always_high_compute",
            "statistical_reduction": stat_token_reduction,
            "practical_reduction": practical_token_reduction,
            "relative_reduction": relative_token_delta,
            "required_relative_gate": -required_rel_gate,
            "passed": token_gate_passed,
            "cohens_dz": _cohens_dz(t_t - t_c),
            **tokens.__dict__,
        },
        "cost_reduction": {
            "treatment": "v2_mycelial",
            "control": "always_high_compute",
            "relative_reduction": float((np.mean(c_t) - np.mean(c_c)) / max(float(np.mean(c_c)), 1e-9)),
            **cost_eff.__dict__,
        },
        "secondary_baseline_contrasts": secondary_contrasts,
        "pareto_nondominated_methods": frontier,
        "group_metrics": group_metrics,
        "claim_boundary": (
            "Do not describe this run as evidence that mycelial routing is universally optimal. "
            "Quality is tested for non-inferiority first; token totals include router and state overhead."
        ),
    }
    path = output / "processed" / "analysis.json"
    atomic_write_json(path, analysis)
    return path
