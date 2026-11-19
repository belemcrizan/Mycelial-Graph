from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from scipy.stats import spearmanr

from ..biology.voc import TOKEN_SCALE, estimate_token_voc
from ..environment.roles import edge_role
from ..environment.scenario import FAILURE_QUALITY_MULTIPLIER, ResourceScenario, generate_resource_scenario
from ..types import V2ExperimentConfig
from .calibration import brier_score, expected_calibration_error, ranking_accuracy


@dataclass(frozen=True)
class VOCRecord:
    seed: int
    regime: str
    step: int
    predicted_delta_q: float
    observed_delta_q: float
    predicted_delta_tokens: float
    observed_delta_tokens: float
    voc_difference: float
    voc_ratio: float
    allocated: bool
    additional_compute_helps: bool


def _verify_pair(scenario: ResourceScenario) -> tuple[int, int] | None:
    # Compare skip vs spend verification transitions outgoing from the same model node.
    for _, outgoing in scenario.graph.outgoing.items():
        if len(outgoing) >= 2 and edge_role(scenario.graph, outgoing[0]) == "verification":
            skip = min(outgoing, key=lambda edge_id: float(scenario.token_means_pre[edge_id]))
            spend = max(outgoing, key=lambda edge_id: float(scenario.token_means_pre[edge_id]))
            if skip != spend:
                return int(skip), int(spend)
    return None


def _realized_edge_quality(scenario: ResourceScenario, step: int, edge_id: int) -> float:
    q = float(scenario.quality_outcomes[step, edge_id])
    fail_p = float(scenario.fail_prob(step)[edge_id])
    if float(scenario.fail_uniforms[step, edge_id]) < fail_p:
        q *= FAILURE_QUALITY_MULTIPLIER
    return q


def run_voc_benchmark(
    config: V2ExperimentConfig,
    seeds: tuple[int, ...],
    *,
    lambda_tokens: float | None = None,
    quality_help_margin: float = 0.01,
) -> dict[str, Any]:
    """Evaluation-only counterfactual VOC benchmark using normalized per-1k token costs."""
    lam = config.utility.lambda_tokens if lambda_tokens is None else lambda_tokens
    records: list[VOCRecord] = []
    regimes = config.environment.regimes
    for seed in seeds:
        for regime in regimes:
            scenario = generate_resource_scenario(config, seed, regime)
            pair = _verify_pair(scenario)
            if pair is None:
                continue
            skip_id, spend_id = pair
            q_skip_hat = 0.64
            q_spend_hat = 0.73
            t_skip_hat = 8.0
            t_spend_hat = 140.0
            n_skip = n_spend = 0
            for step in range(config.horizon.total_steps):
                predicted_dq = q_spend_hat - q_skip_hat
                predicted_dt = max(t_spend_hat - t_skip_hat, 1.0)
                voc = estimate_token_voc(predicted_dq, predicted_dt, lam)
                allocated = voc.difference > 0.0

                skip_q = _realized_edge_quality(scenario, step, skip_id)
                spend_q = _realized_edge_quality(scenario, step, spend_id)
                skip_t = float(scenario.token_outcomes[step, skip_id])
                spend_t = float(scenario.token_outcomes[step, spend_id])
                observed_dq = spend_q - skip_q
                observed_dt = spend_t - skip_t
                helps = (observed_dq - lam * (max(observed_dt, 0.0) / TOKEN_SCALE)) > quality_help_margin
                records.append(
                    VOCRecord(
                        seed=seed,
                        regime=regime,
                        step=step,
                        predicted_delta_q=predicted_dq,
                        observed_delta_q=observed_dq,
                        predicted_delta_tokens=predicted_dt,
                        observed_delta_tokens=observed_dt,
                        voc_difference=voc.difference,
                        voc_ratio=voc.ratio,
                        allocated=allocated,
                        additional_compute_helps=helps,
                    )
                )
                n_skip += 1
                n_spend += 1
                alpha_s = max(0.20, 1.0 / n_skip)
                alpha_v = max(0.20, 1.0 / n_spend)
                q_skip_hat += alpha_s * (skip_q - q_skip_hat)
                q_spend_hat += alpha_v * (spend_q - q_spend_hat)
                t_skip_hat += alpha_s * (skip_t - t_skip_hat)
                t_spend_hat += alpha_v * (spend_t - t_spend_hat)

    if not records:
        raise ValueError("VOC benchmark produced no records.")
    predicted = np.array([item.predicted_delta_q for item in records], dtype=float)
    observed = np.array([item.observed_delta_q for item in records], dtype=float)
    helps_arr = np.array([item.additional_compute_helps for item in records], dtype=float)
    allocated_arr = np.array([item.allocated for item in records], dtype=bool)
    voc_diffs = np.array([item.voc_difference for item in records], dtype=float)
    p_help = 1.0 / (1.0 + np.exp(-12.0 * voc_diffs))
    false_stop = float(np.mean((~allocated_arr) & (helps_arr > 0.5)))
    false_spend = float(np.mean(allocated_arr & (helps_arr < 0.5)))
    spearman = spearmanr(predicted, observed)
    rho = getattr(spearman, "statistic", getattr(spearman, "correlation", float("nan")))
    obs_norm_dt = np.maximum(np.array([item.observed_delta_tokens for item in records]) / TOKEN_SCALE, 1e-3)
    return {
        "protocol": "MG-EXP-V2.1-VOC",
        "n_records": len(records),
        "voc_calibration_mae": float(np.mean(np.abs(predicted - observed))),
        "mvc_calibration_mae": float(
            np.mean(np.abs(np.array([item.voc_ratio for item in records]) - np.divide(observed, obs_norm_dt)))
        ),
        "ranking_accuracy": ranking_accuracy(predicted, observed),
        "brier": brier_score(p_help, helps_arr),
        "ece": expected_calibration_error(p_help, helps_arr),
        "spearman_rho": float(rho) if rho is not None else float("nan"),
        "allocation_rate": float(np.mean(allocated_arr)),
        "false_stop_rate": false_stop,
        "false_spend_rate": false_spend,
        "claim_boundary": (
            "These metrics evaluate a mean-based VOC estimator on frozen "
            "synthetic potential outcomes. They are not real-agent evidence."
        ),
        "records": [asdict(item) for item in records[:200]],
    }
