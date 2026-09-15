from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
from scipy.stats import spearmanr

from ..biology.voc import estimate_voc
from ..environment.roles import edge_role
from ..environment.scenario import ResourceScenario, generate_resource_scenario
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
    candidates = [
        edge.id
        for edge in scenario.graph.edges
        if edge_role(scenario.graph, edge.id) == "verification"
    ]
    if len(candidates) < 2:
        return None
    skip = min(candidates, key=lambda edge_id: float(scenario.token_means_pre[edge_id]))
    spend = max(candidates, key=lambda edge_id: float(scenario.token_means_pre[edge_id]))
    if skip == spend:
        return None
    return int(skip), int(spend)


def run_voc_benchmark(
    config: V2ExperimentConfig,
    seeds: tuple[int, ...],
    *,
    lambda_tokens: float | None = None,
    quality_help_margin: float = 0.01,
) -> dict[str, Any]:
    """Evaluation-only counterfactual VOC bench.

    For each (seed, regime, step) the frozen potential outcomes of skip-verify
    and spend-verify are both observed. Predictions use only pre-step means
    (no future leakage). The oracle never enters a treatment policy.
    """
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
            q_skip_hat = 0.55
            q_spend_hat = 0.62
            t_skip_hat = 8.0
            t_spend_hat = 140.0
            n_skip = n_spend = 0
            for step in range(config.horizon.total_steps):
                predicted_dq = q_spend_hat - q_skip_hat
                predicted_dt = max(t_spend_hat - t_skip_hat, 1.0)
                voc = estimate_voc(predicted_dq, predicted_dt, lam)
                allocated = voc.difference > 0.0
                # Counterfactual: same retrieval/model prefix is not needed;
                # verification edges are independently indexed.
                skip_q = float(scenario.quality_outcomes[step, skip_id])
                spend_q = float(scenario.quality_outcomes[step, spend_id])
                skip_t = float(scenario.token_outcomes[step, skip_id])
                spend_t = float(scenario.token_outcomes[step, spend_id])
                observed_dq = spend_q - skip_q
                observed_dt = spend_t - skip_t
                helps = observed_dq > quality_help_margin
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
                # Online estimates from the *chosen* arm only would be causal
                # for a policy. Calibration uses both potential outcomes as
                # labels, but updates hats from skip then spend independently
                # as if both were seen — this is evaluation-only.
                n_skip += 1
                n_spend += 1
                q_skip_hat += (skip_q - q_skip_hat) / n_skip
                q_spend_hat += (spend_q - q_spend_hat) / n_spend
                t_skip_hat += (skip_t - t_skip_hat) / n_skip
                t_spend_hat += (spend_t - t_spend_hat) / n_spend

    if not records:
        raise ValueError("VOC benchmark produced no records.")
    predicted = np.array([item.predicted_delta_q for item in records], dtype=float)
    observed = np.array([item.observed_delta_q for item in records], dtype=float)
    helps = np.array([item.additional_compute_helps for item in records], dtype=float)
    allocated = np.array([item.allocated for item in records], dtype=bool)
    p_help = 1.0 / (1.0 + np.exp(-8.0 * predicted))
    false_stop = float(np.mean((~allocated) & (helps > 0.5)))
    false_spend = float(np.mean(allocated & (helps < 0.5)))
    spearman = spearmanr(predicted, observed)
    rho = getattr(spearman, "statistic", getattr(spearman, "correlation", float("nan")))
    return {
        "protocol": "MG-EXP-V2.1-VOC",
        "n_records": len(records),
        "voc_calibration_mae": float(np.mean(np.abs(predicted - observed))),
        "mvc_calibration_mae": float(
            np.mean(
                np.abs(
                    np.array([item.voc_ratio for item in records])
                    - np.divide(
                        observed,
                        np.maximum(np.array([item.observed_delta_tokens for item in records]), 1.0),
                    )
                )
            )
        ),
        "ranking_accuracy": ranking_accuracy(predicted, observed),
        "brier": brier_score(p_help, helps),
        "ece": expected_calibration_error(p_help, helps),
        "spearman_rho": float(rho) if rho is not None else float("nan"),
        "false_stop_rate": false_stop,
        "false_spend_rate": false_spend,
        "claim_boundary": (
            "These metrics evaluate a mean-based VOC estimator on frozen "
            "synthetic potential outcomes. They are not real-agent evidence."
        ),
        "records": [asdict(item) for item in records[:200]],
    }
