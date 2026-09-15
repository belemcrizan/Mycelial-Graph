"""Post-confirmatory diagnostics required to interpret Paper A.

These analyses are labelled POST_CONFIRMATORY_DIAGNOSTIC. They do not alter the
frozen V1 estimand, hypotheses, sample size, seeds, or result state. They exist
so that the manuscript can report variance instability, censoring, effective-policy
comparability, and dynamic-range limitations without promoting any of them into
confirmatory evidence.

Equalization triage classification is a submission-safety judgement, not a freeze
gate. Tolerances below were fixed before inspecting confirmatory traces and must
not be retuned against the confirmatory outcome.
"""

from __future__ import annotations

import gzip
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

from ..analysis.bootstrap import paired_relative_effect
from ..environment.graph import LayeredDAG

# Pre-declared triage tolerances. Do not edit after seeing confirmatory numbers.
PATH_COUNT = 27  # 3 internal layers x 3 alternatives, complete layered DAG
MAX_PATH_ENTROPY = math.log(PATH_COUNT)
EQ_ENTROPY_FRACTION = 0.20  # |H1-H0| / log(|paths|)
EQ_OPT_RATE_GAP = 0.15
EQ_EXPLORATION_GAP = 0.05
EQ_SCORE_STD_RATIO = 2.0
EQ_C_LOW_FRACTION = 0.20
EQ_C_HIGH_FRACTION = 0.70

WARMUP_STEPS = 200
PRIMARY_RHO = 0.50
SAFETY_RHO = 0.0
DIAGNOSTIC_RHOS = (0.0, 0.25, 0.50, 0.75, 1.0)
COMPARED_METHODS = ("edge_only", "hierarchical")


def _shannon(counts: Counter[Any] | dict[Any, int]) -> float:
    total = float(sum(counts.values()))
    if total <= 0:
        return 0.0
    entropy = 0.0
    for count in counts.values():
        if count <= 0:
            continue
        p = count / total
        entropy -= p * math.log(p)
    return float(entropy)


def _quantiles(values: np.ndarray, probs: tuple[float, ...]) -> dict[str, float]:
    if len(values) == 0:
        return {f"q{int(p * 100):02d}": float("nan") for p in probs}
    qs = np.quantile(values, probs)
    return {f"q{int(p * 100):02d}": float(q) for p, q in zip(probs, qs)}


def _skewness(values: np.ndarray) -> float:
    if len(values) < 3:
        return float("nan")
    centered = values - np.mean(values)
    denom = float(np.std(values, ddof=1) ** 3)
    if denom == 0:
        return 0.0
    return float(np.mean(centered**3) / denom)


def read_raw_trials(
    output_directory: Path,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    trials: list[dict[str, Any]] = []
    scenarios: dict[str, dict[str, Any]] = {}
    raw_root = output_directory / "raw"
    if not raw_root.exists():
        raise FileNotFoundError(f"No raw trials under {raw_root}")
    for path in sorted(raw_root.rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))["scientific_payload"]
        scenario_id = payload["scenario_id"]
        scenarios[scenario_id] = {
            "optimal_pre_path": tuple(payload["optimal_pre_path"]),
            "optimal_post_path": tuple(payload["optimal_post_path"]),
            "rho": float(payload["rho"]),
            "seed": int(payload["seed"]),
            "shock_node": payload.get("shock_node"),
            "interaction_edge": payload.get("interaction_edge"),
        }
        for trial in payload["results"]:
            row = dict(trial)
            row["_source"] = str(path)
            trials.append(row)
    return trials, scenarios


def paired_rrt(
    trials: list[dict[str, Any]],
    rho: float,
    treatment: str = "hierarchical",
    control: str = "edge_only",
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    by_scenario: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for trial in trials:
        if np.isclose(float(trial["rho"]), rho):
            by_scenario[trial["scenario_id"]][trial["method"]] = trial
    treatment_values = []
    control_values = []
    ids = []
    for scenario_id, methods in sorted(by_scenario.items()):
        if treatment in methods and control in methods:
            treatment_values.append(float(methods[treatment]["restricted_recovery_time"]))
            control_values.append(float(methods[control]["restricted_recovery_time"]))
            ids.append(scenario_id)
    return np.array(treatment_values, dtype=float), np.array(control_values, dtype=float), ids


def paired_regret(
    trials: list[dict[str, Any]],
    rho: float,
    treatment: str = "hierarchical",
    control: str = "edge_only",
) -> tuple[np.ndarray, np.ndarray]:
    by_scenario: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for trial in trials:
        if np.isclose(float(trial["rho"]), rho):
            by_scenario[trial["scenario_id"]][trial["method"]] = trial
    treatment_values = []
    control_values = []
    for _, methods in sorted(by_scenario.items()):
        if treatment in methods and control in methods:
            treatment_values.append(float(methods[treatment]["dynamic_regret"]))
            control_values.append(float(methods[control]["dynamic_regret"]))
    return np.array(treatment_values, dtype=float), np.array(control_values, dtype=float)


def variance_diagnostic(
    confirmatory_trials: list[dict[str, Any]],
    pilot_trials: list[dict[str, Any]],
    bootstrap_samples: int = 10000,
) -> dict[str, Any]:
    """Pilot vs confirmatory paired-effect distribution. Not confirmatory evidence."""
    quantiles = (0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95)
    blocks = {}
    for label, trials in (("pilot", pilot_trials), ("confirmatory", confirmatory_trials)):
        treatment, control, _ = paired_rrt(trials, PRIMARY_RHO)
        if len(treatment) == 0:
            blocks[label] = {"available": False}
            continue
        paired_diff = treatment - control
        relative_pair = np.divide(
            paired_diff,
            control,
            out=np.full_like(paired_diff, np.nan),
            where=control != 0,
        )
        contrast = paired_relative_effect(
            treatment,
            control,
            bootstrap_samples,
            0.95,
            seed=20260824 if label == "confirmatory" else 20260824,
        )
        rng = np.random.default_rng(20260915)
        n = len(paired_diff)
        boot_sd = []
        for _ in range(min(bootstrap_samples, 4000)):
            draw = paired_diff[rng.integers(0, n, size=n)]
            boot_sd.append(float(np.std(draw, ddof=1)))
        boot_sd_arr = np.array(boot_sd, dtype=float)
        abs_diff = np.abs(paired_diff)
        outlier_mask = abs_diff > (np.median(abs_diff) + 3 * np.median(np.abs(paired_diff - np.median(paired_diff))))
        trimmed = paired_diff[~outlier_mask] if np.any(~outlier_mask) else paired_diff
        blocks[label] = {
            "available": True,
            "n": int(len(treatment)),
            "status": "POST_CONFIRMATORY_DIAGNOSTIC" if label == "confirmatory" else "PILOT_EVIDENCE_NOT_CONFIRMATORY",
            "control_mean_rrt": float(np.mean(control)),
            "treatment_mean_rrt": float(np.mean(treatment)),
            "relative_effect_point": float((np.mean(treatment) - np.mean(control)) / np.mean(control)),
            "frozen_bootstrap": contrast.__dict__,
            "paired_difference": {
                "mean": float(np.mean(paired_diff)),
                "sd": float(np.std(paired_diff, ddof=1)),
                "mad": float(np.median(np.abs(paired_diff - np.median(paired_diff)))),
                "iqr": float(np.quantile(paired_diff, 0.75) - np.quantile(paired_diff, 0.25)),
                "skewness": _skewness(paired_diff),
                "min": float(np.min(paired_diff)),
                "max": float(np.max(paired_diff)),
                "quantiles": _quantiles(paired_diff, quantiles),
                "fraction_positive": float(np.mean(paired_diff > 0)),
                "fraction_negative": float(np.mean(paired_diff < 0)),
            },
            "relative_paired_difference": {
                "mean": float(np.nanmean(relative_pair)),
                "sd": float(np.nanstd(relative_pair, ddof=1)),
                "quantiles": _quantiles(relative_pair[np.isfinite(relative_pair)], quantiles),
            },
            "bootstrap_sd_of_paired_difference": {
                "mean": float(np.mean(boot_sd_arr)),
                "sd": float(np.std(boot_sd_arr, ddof=1)),
                "quantiles": _quantiles(boot_sd_arr, (0.05, 0.50, 0.95)),
            },
            "outlier_sensitivity": {
                "rule": "absolute deviation from median > 3 * MAD",
                "n_flagged": int(np.sum(outlier_mask)),
                "sd_all": float(np.std(paired_diff, ddof=1)),
                "sd_without_flagged": float(np.std(trimmed, ddof=1)),
            },
            "censoring_in_pairs": {
                "treatment_at_tau": int(np.sum(treatment >= 300)),
                "control_at_tau": int(np.sum(control >= 300)),
            },
        }
    ratio = None
    if blocks["pilot"].get("available") and blocks["confirmatory"].get("available"):
        pilot_sd = blocks["pilot"]["paired_difference"]["sd"]
        conf_sd = blocks["confirmatory"]["paired_difference"]["sd"]
        ratio = float(conf_sd / pilot_sd) if pilot_sd else None
    return {
        "status": "POST_CONFIRMATORY_DIAGNOSTIC",
        "estimand_note": "Frozen confirmatory estimand is unchanged. This block diagnoses variance estimation only.",
        "pilot": blocks["pilot"],
        "confirmatory": blocks["confirmatory"],
        "variance_ratio_confirmatory_over_pilot": ratio,
        "sample_size_lesson": (
            "A 20-pair pilot produced an unstable variance estimate relative to the "
            "confirmatory paired-difference dispersion. Future protocols should not rely "
            "on a normal approximation from a small pilot unless a bootstrap or "
            "simulation-based procedure confirms stability. This lesson is local to this "
            "environment and is not a general theorem."
            if ratio is not None
            else "Pilot or confirmatory raw trials were unavailable."
        ),
    }


def censoring_diagnostic(trials: list[dict[str, Any]], tau: int = 300) -> dict[str, Any]:
    rows = []
    for rho in DIAGNOSTIC_RHOS:
        for method in ("edge_only", "hierarchical", "node_only", "structured_sw_ucb"):
            items = [
                trial
                for trial in trials
                if np.isclose(float(trial["rho"]), rho) and trial["method"] == method
            ]
            if not items:
                continue
            censored = [trial for trial in items if trial["censored"]]
            administrative = [
                trial
                for trial in censored
                if int(trial["restricted_recovery_time"]) == tau
            ]
            non_administrative = len(censored) - len(administrative)
            rows.append(
                {
                    "rho": rho,
                    "method": method,
                    "n": len(items),
                    "n_censored": len(censored),
                    "proportion_censored": len(censored) / len(items),
                    "administrative": len(administrative),
                    "non_administrative": non_administrative,
                    "role": (
                        "CONFIRMATORY INPUT"
                        if method in COMPARED_METHODS and rho in {0.0, PRIMARY_RHO}
                        else "DIAGNOSTIC"
                    ),
                }
            )
    frozen = [
        row
        for row in rows
        if row["method"] in COMPARED_METHODS and row["rho"] in {0.0, PRIMARY_RHO}
    ]
    method_gap = None
    primary = {row["method"]: row for row in rows if np.isclose(row["rho"], PRIMARY_RHO)}
    if "hierarchical" in primary and "edge_only" in primary:
        method_gap = (
            primary["hierarchical"]["proportion_censored"]
            - primary["edge_only"]["proportion_censored"]
        )
    return {
        "status": "POST_CONFIRMATORY_DIAGNOSTIC",
        "tau": tau,
        "rule": "Administrative censoring is restriction at tau. Any other censoring is non-administrative.",
        "rows": rows,
        "frozen_contrasts": frozen,
        "primary_censoring_gap_hierarchical_minus_edge": method_gap,
        "non_administrative_total": int(sum(row["non_administrative"] for row in rows)),
        "limitation": (
            "Restricted recovery time is a thresholded, right-censored functional. "
            "It is the frozen primary outcome and is not replaced here. Sensitivity "
            "statements about tau are diagnostic only."
        ),
    }


def _trace_path(output_directory: Path, trial: dict[str, Any]) -> Path:
    relative = trial.get("trace_ref")
    if not relative:
        raise FileNotFoundError(f"Trial {trial.get('trial_id')} has no trace_ref")
    return output_directory / relative


def _warmup_policy_metrics(
    trace_path: Path,
    optimal_pre_path: tuple[int, ...],
    graph: LayeredDAG,
) -> dict[str, Any]:
    path_counts: Counter[tuple[int, ...]] = Counter()
    layer_counts: list[Counter[int]] = [Counter() for _ in range(len(graph.layers) - 1)]
    selected_scores: list[float] = []
    exploratory_steps = 0
    optimal_steps = 0
    n_steps = 0
    with gzip.open(trace_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if int(record["step"]) >= WARMUP_STEPS:
                break
            n_steps += 1
            path = tuple(record["path"])
            path_counts[path] += 1
            edge_ids = list(record["edge_ids"])
            for layer, edge_id in enumerate(edge_ids):
                layer_counts[layer][int(edge_id)] += 1
            selected_scores.extend(float(s) for s in record["selected_edge_scores"])
            if int(record["exploratory_edges"]) > 0:
                exploratory_steps += 1
            if path == optimal_pre_path:
                optimal_steps += 1
    total = sum(path_counts.values()) or 1
    max_p = max((c / total for c in path_counts.values()), default=0.0)
    hhi = sum((c / total) ** 2 for c in path_counts.values())
    scores = np.array(selected_scores, dtype=float) if selected_scores else np.array([np.nan])
    layer_entropy = [_shannon(counts) for counts in layer_counts]
    branching = [len(graph.outgoing[layer[0]]) for layer in graph.layers[:-1]]
    return {
        "n_warmup_steps": n_steps,
        "path_entropy": _shannon(path_counts),
        "path_entropy_fraction_of_max": _shannon(path_counts) / MAX_PATH_ENTROPY,
        "unique_paths": len(path_counts),
        "max_path_probability": float(max_p),
        "herfindahl": float(hhi),
        "layer_conditional_entropy": layer_entropy,
        "layer_entropy_fraction": [
            (ent / math.log(k) if k > 1 else 0.0) for ent, k in zip(layer_entropy, branching)
        ],
        "selected_score_mean": float(np.nanmean(scores)),
        "selected_score_std": float(np.nanstd(scores, ddof=1)) if len(scores) > 1 else 0.0,
        "selected_score_min": float(np.nanmin(scores)),
        "selected_score_max": float(np.nanmax(scores)),
        "exploration_step_rate": exploratory_steps / n_steps if n_steps else 0.0,
        "optimal_pre_path_rate": optimal_steps / n_steps if n_steps else 0.0,
        "effective_temperature_proxy": 1.0 - (_shannon(path_counts) / MAX_PATH_ENTROPY),
    }


def equalization_triage(
    confirmatory_dir: Path,
    trials: list[dict[str, Any]],
    scenarios: dict[str, dict[str, Any]],
    rhos: tuple[float, ...] = (SAFETY_RHO, PRIMARY_RHO, 1.0),
) -> dict[str, Any]:
    graph = LayeredDAG.complete_layered(3, 3)
    by_rho_method: dict[tuple[float, str], list[dict[str, Any]]] = defaultdict(list)
    missing_traces = 0
    for trial in trials:
        rho = float(trial["rho"])
        if trial["method"] not in COMPARED_METHODS:
            continue
        if not any(np.isclose(rho, target) for target in rhos):
            continue
        scenario = scenarios[trial["scenario_id"]]
        try:
            metrics = _warmup_policy_metrics(
                _trace_path(confirmatory_dir, trial),
                tuple(scenario["optimal_pre_path"]),
                graph,
            )
        except FileNotFoundError:
            missing_traces += 1
            continue
        metrics["seed"] = trial["seed"]
        by_rho_method[(rho, trial["method"])].append(metrics)

    summaries = []
    for rho in rhos:
        for method in COMPARED_METHODS:
            items = by_rho_method.get((rho, method)) or by_rho_method.get(
                (float(np.round(rho, 2)), method), []
            )
            # Keys may be 0.5 vs 0.50 depending on JSON.
            if not items:
                for (key_rho, key_method), value in by_rho_method.items():
                    if key_method == method and np.isclose(key_rho, rho):
                        items = value
                        break
            if not items:
                continue
            numeric_keys = [
                "path_entropy",
                "path_entropy_fraction_of_max",
                "unique_paths",
                "max_path_probability",
                "herfindahl",
                "selected_score_mean",
                "selected_score_std",
                "selected_score_min",
                "selected_score_max",
                "exploration_step_rate",
                "optimal_pre_path_rate",
                "effective_temperature_proxy",
            ]
            summary = {
                "rho": rho,
                "method": method,
                "n_trials": len(items),
                "phase": "pre-shock warm-up",
                "steps": WARMUP_STEPS,
            }
            for key in numeric_keys:
                values = np.array([item[key] for item in items], dtype=float)
                summary[key] = {
                    "mean": float(np.mean(values)),
                    "sd": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
                }
            layer_stack = np.array([item["layer_conditional_entropy"] for item in items], dtype=float)
            summary["layer_conditional_entropy_mean"] = layer_stack.mean(axis=0).tolist()
            summaries.append(summary)

    def _pick(rho: float, method: str) -> dict[str, Any] | None:
        for row in summaries:
            if row["method"] == method and np.isclose(row["rho"], rho):
                return row
        return None

    primary_edge = _pick(PRIMARY_RHO, "edge_only")
    primary_hier = _pick(PRIMARY_RHO, "hierarchical")
    classification, reasons = _classify_equalization(primary_edge, primary_hier)
    return {
        "status": "POST_CONFIRMATORY_DIAGNOSTIC",
        "principle": "Parameter parity is not policy parity.",
        "compared_methods": list(COMPARED_METHODS),
        "shared_nominal_parameters": {
            "temperature": 0.20,
            "exploration_probability": 0.08,
            "feedback_contract": "local traversed-edge rewards only",
        },
        "known_implementation_differences": [
            "edge-only uses clipped conductance and learning_rate",
            "hierarchical uses unbounded additive scores, node_learning_rate, interaction_learning_rate, shrinkage, and sum-to-zero projection",
        ],
        "trace_limitation": (
            "Stored traces contain selected-edge scores, not the full candidate-score vector. "
            "Action entropy, layer-conditional entropy, selection concentration, exploration "
            "rate, and optimal-path rate are therefore computed from realized actions. "
            "A softmax effective temperature is a proxy derived from path-entropy, not a "
            "fitted temperature."
        ),
        "missing_traces": missing_traces,
        "tolerances": {
            "path_entropy_fraction_gap": EQ_ENTROPY_FRACTION,
            "optimal_action_rate_gap": EQ_OPT_RATE_GAP,
            "exploration_rate_gap": EQ_EXPLORATION_GAP,
            "selected_score_std_ratio": EQ_SCORE_STD_RATIO,
            "eq_c_low_entropy_fraction": EQ_C_LOW_FRACTION,
            "eq_c_high_entropy_fraction": EQ_C_HIGH_FRACTION,
            "frozen_before_inspection": True,
        },
        "summaries": summaries,
        "classification": classification,
        "reasons": reasons,
        "manuscript_action": {
            "EQ-A": "disclose -> submit",
            "EQ-B": "revise claims -> disclose prominently -> submit",
            "EQ-C": "do not submit the existing interpretation unchanged",
        }[classification],
    }


def _classify_equalization(
    edge: dict[str, Any] | None,
    hier: dict[str, Any] | None,
) -> tuple[str, list[str]]:
    if edge is None or hier is None:
        return "EQ-C", ["Unable to compute warm-up policy metrics for both arms at rho=0.50."]
    reasons = []
    h_edge = edge["path_entropy_fraction_of_max"]["mean"]
    h_hier = hier["path_entropy_fraction_of_max"]["mean"]
    entropy_gap = abs(h_hier - h_edge)
    opt_gap = abs(hier["optimal_pre_path_rate"]["mean"] - edge["optimal_pre_path_rate"]["mean"])
    exp_gap = abs(hier["exploration_step_rate"]["mean"] - edge["exploration_step_rate"]["mean"])
    std_edge = edge["selected_score_std"]["mean"]
    std_hier = hier["selected_score_std"]["mean"]
    std_ratio = max(std_edge, std_hier) / min(std_edge, std_hier) if min(std_edge, std_hier) > 0 else float("inf")

    extremes = sorted([h_edge, h_hier])
    eq_c = extremes[0] <= EQ_C_LOW_FRACTION and extremes[1] >= EQ_C_HIGH_FRACTION
    material = (
        entropy_gap >= EQ_ENTROPY_FRACTION
        or opt_gap >= EQ_OPT_RATE_GAP
        or exp_gap >= EQ_EXPLORATION_GAP
        or std_ratio >= EQ_SCORE_STD_RATIO
    )
    reasons.append(
        f"warm-up path-entropy fraction edge={h_edge:.3f} hierarchical={h_hier:.3f} gap={entropy_gap:.3f}"
    )
    reasons.append(f"optimal-pre-path rate gap={opt_gap:.3f}")
    reasons.append(f"exploration-step rate gap={exp_gap:.3f}")
    reasons.append(f"selected-score std ratio={std_ratio:.3f}")
    if eq_c:
        return "EQ-C", reasons + [
            "One arm is near-deterministic and the other near-diffuse during warm-up, "
            "so the contrast is not an equalized representation comparison."
        ]
    if material:
        return "EQ-B", reasons + [
            "Realized action distributions differ enough to limit mechanistic interpretation, "
            "but both arms remain in a comparable non-degenerate exploration regime. "
            "The frozen REFUTED outcome stands as a comparison of the implemented methods, "
            "not as proof that representation was isolated."
        ]
    return "EQ-A", reasons + [
        "Warm-up realized-action differences are below the pre-declared material thresholds."
    ]


def dynamic_range_diagnostic(
    trials: list[dict[str, Any]],
    bootstrap_samples: int = 10000,
) -> dict[str, Any]:
    rows = []
    for rho in DIAGNOSTIC_RHOS:
        treatment, control, _ = paired_rrt(trials, rho)
        if len(treatment) < 2:
            continue
        rrt = paired_relative_effect(treatment, control, bootstrap_samples, 0.95, seed=20260824)
        t_reg, c_reg = paired_regret(trials, rho)
        regret = paired_relative_effect(t_reg, c_reg, bootstrap_samples, 0.95, seed=20260826)
        rows.append(
            {
                "rho": rho,
                "role": (
                    "PRIMARY"
                    if np.isclose(rho, PRIMARY_RHO)
                    else "SAFETY GATE"
                    if np.isclose(rho, 0.0)
                    else "DIAGNOSTIC"
                    if np.isclose(rho, 1.0)
                    else "EXPLORATORY"
                ),
                "rrt_relative": rrt.__dict__,
                "regret_relative": regret.__dict__,
                "hierarchical_faster_on_rrt": bool(np.mean(treatment) < np.mean(control)),
                "hierarchical_lower_regret": bool(np.mean(t_reg) < np.mean(c_reg)),
                "rrt_regret_agree_on_sign": bool(np.sign(rrt.estimate) == np.sign(regret.estimate)),
            }
        )
    detectable_sharing_advantage = any(
        row["rho"] == 1.0 and row["hierarchical_faster_on_rrt"] and row["rrt_relative"]["one_sided_upper_bound"] < 0
        for row in rows
    )
    any_point_advantage = any(row["hierarchical_faster_on_rrt"] for row in rows)
    return {
        "status": "POST_CONFIRMATORY_DIAGNOSTIC",
        "rule": "diagnostic may explain REFUTED; it may never overwrite REFUTED",
        "grid": "frozen confirmatory rho grid; no new protected population was used",
        "rows": rows,
        "rrt_regret_sign_disagreement_count": int(
            sum(not row["rrt_regret_agree_on_sign"] for row in rows)
        ),
        "any_rho_where_hierarchical_mean_rrt_is_better": any_point_advantage,
        "rho1_detectable_sharing_advantage_on_frozen_one_sided_rule": detectable_sharing_advantage,
        "interpretation": (
            "A mean RRT advantage at rho=1, if present, is a construct/dynamic-range check, "
            "not a confirmatory finding. Failure to see a clear sharing advantage even at "
            "rho=1 is compatible with implementation weakness, sharing-mechanism weakness, "
            "or insufficient environmental dynamic range; this diagnostic cannot separate "
            "those three explanations."
        ),
        "not_done": [
            "factorial variation of K_edge/K_node",
            "shared vs idiosyncratic shock magnitude factorization beyond rho",
            "noise-scale sweep",
            "structural-compression sweep",
            "equalized effective-policy-scale controls",
        ],
        "reason_not_done": (
            "Those sweeps would start a V1.5-scale programme. Paper A uses the already-frozen "
            "rho grid, including the pre-specified rho=1 diagnostic cell."
        ),
    }


def runtime_diagnostic(trials: list[dict[str, Any]]) -> dict[str, Any]:
    cpu = np.array([float(trial["decision_cpu_seconds"]) for trial in trials], dtype=float)
    cpu_hours = float(np.sum(cpu) / 3600.0)
    return {
        "status": "MEASURED",
        "n_trials": len(trials),
        "cpu_seconds_sum": float(np.sum(cpu)),
        "cpu_hours": cpu_hours,
        "cpu_seconds_mean": float(np.mean(cpu)) if len(cpu) else 0.0,
        "note": (
            "CPU-hours are the sum of per-trial decision_cpu_seconds recorded in confirmatory "
            "raw payloads. Wall-clock of the original run was not stored in manifest.json; "
            "the runbook measurement of about 11 minutes serial is a separate machine-specific "
            "observation and is not re-used here unless re-measured."
        ),
        "wall_clock_original_run": "NOT_IN_MANIFEST",
    }


def write_markdown_report(payload: dict[str, Any], path: Path) -> None:
    variance = payload["variance"]
    equalization = payload["equalization"]
    censoring = payload["censoring"]
    dynamic = payload["dynamic_range"]
    runtime = payload["runtime"]
    ratio = variance.get("variance_ratio_confirmatory_over_pilot")
    ratio_text = "unavailable"
    if ratio is not None:
        ratio_text = f"{ratio:.2f}x"
    lines = [
        "# Paper A post-confirmatory diagnostics",
        "",
        "Status of every number below: `POST_CONFIRMATORY_DIAGNOSTIC` unless marked `MEASURED`.",
        "None of these analyses overwrites the frozen V1 result `REFUTED`.",
        "",
        "## Equalization triage",
        "",
        f"Classification: **{equalization['classification']}**",
        "",
        f"Action: {equalization['manuscript_action']}",
        "",
        "Principle: parameter parity is not policy parity.",
        "",
        "Reasons:",
    ]
    for reason in equalization["reasons"]:
        lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "## Variance diagnostic",
            "",
            f"Confirmatory / pilot paired-difference SD ratio: **{ratio_text}**",
            "",
            variance["sample_size_lesson"],
            "",
            "## Censoring",
            "",
            f"Non-administrative censoring (all methods, all rho): {censoring['non_administrative_total']}",
            f"Primary hierarchical minus edge-only censoring gap: {censoring['primary_censoring_gap_hierarchical_minus_edge']}",
            "",
            censoring["limitation"],
            "",
            "## Dynamic range / regret",
            "",
            f"RRT vs regret sign disagreements on the frozen rho grid: {dynamic['rrt_regret_sign_disagreement_count']}",
            f"Any rho where hierarchical mean RRT is better: {dynamic['any_rho_where_hierarchical_mean_rrt_is_better']}",
            f"rho=1 detectable sharing advantage under the frozen one-sided rule: {dynamic['rho1_detectable_sharing_advantage_on_frozen_one_sided_rule']}",
            "",
            dynamic["interpretation"],
            "",
            "## Runtime",
            "",
            f"Measured CPU-hours from confirmatory raw trials: **{runtime['cpu_hours']:.6f}**",
            f"Wall-clock of original run: {runtime['wall_clock_original_run']}",
            "",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
