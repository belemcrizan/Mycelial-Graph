"""Experiment runner with censoring-aware V0 metrics."""

from __future__ import annotations

import hashlib
import json
import math
import random
import statistics
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .graph import HardPolicy, LayeredGraph
from .routing import Router, build_routers
from .trial import FrozenTrial, aggregate_path, oracle_path


def _router_seed(trial_seed: int, router_name: str) -> int:
    payload = f"{trial_seed}|{router_name}|routing".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


@dataclass(frozen=True)
class StepRecord:
    step: int
    edge_ids: tuple[str, ...]
    node_ids: tuple[str, ...]
    choice_modes: tuple[str, ...]
    quality: float
    latency_ms: float
    cost_usd: float
    success: bool
    realized_utility: float
    expected_utility: float
    oracle_expected_utility: float
    oracle_edge_ids: tuple[str, ...]
    feedback_samples: int
    structural_reexploration_samples: int
    decision_ms: float
    primitive_operations: int


@dataclass(frozen=True)
class RunSummary:
    method: str
    seed: int
    trial_digest: str
    recovered: bool
    sample_recovery_cost: int | None
    recovery_task: int | None
    cpst_usd: float
    success_rate: float
    postshock_success_rate: float
    mean_utility: float
    postshock_mean_utility: float
    structural_reexploration_rate: float
    mean_decision_ms: float
    p95_decision_ms: float
    mean_primitive_operations: float


@dataclass(frozen=True)
class RunResult:
    summary: RunSummary
    records: tuple[StepRecord, ...]


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile * len(ordered)) - 1))
    return ordered[index]


def run_router(
    trial: FrozenTrial,
    router: Router,
    policy: HardPolicy,
) -> RunResult:
    rng = random.Random(_router_seed(trial.seed, router.name))
    config = trial.config
    exp = config["experiment"]
    records: list[StepRecord] = []

    oracle_cache: dict[bool, tuple[tuple[str, ...], Any]] = {}
    for step in range(trial.steps):
        postshock = step >= trial.shock_step
        if postshock not in oracle_cache:
            oracle_cache[postshock] = oracle_path(trial, step, policy)
        best_path, best_metrics = oracle_cache[postshock]

        started = time.perf_counter_ns()
        decision = router.select(step, rng)
        decision_ms = (time.perf_counter_ns() - started) / 1_000_000.0
        observations = trial.observations_for(step, decision.edge_ids)
        realized = aggregate_path(observations, config, expected=False)
        expected = aggregate_path(trial.expected_for(step, decision.edge_ids), config, expected=True)
        router.observe(step, decision, observations)

        shock_component = config["shock"]["component"]
        reexploration = sum(
            1
            for observation in observations
            if observation.scored
            and observation.component_id != shock_component
            and observation.edge_id not in best_path
        )
        records.append(
            StepRecord(
                step=step,
                edge_ids=decision.edge_ids,
                node_ids=trial.graph.node_path(decision.edge_ids),
                choice_modes=tuple(choice.mode for choice in decision.choices),
                quality=realized.quality,
                latency_ms=realized.latency_ms,
                cost_usd=realized.cost_usd,
                success=realized.success,
                realized_utility=realized.utility,
                expected_utility=expected.utility,
                oracle_expected_utility=best_metrics.utility,
                oracle_edge_ids=best_path,
                feedback_samples=sum(1 for observation in observations if observation.scored),
                structural_reexploration_samples=reexploration if postshock else 0,
                decision_ms=decision_ms,
                primitive_operations=decision.primitive_operations,
            )
        )

    recovery_window = int(exp["recovery_window"])
    tolerance = float(exp["recovery_tolerance"])
    recovery_task: int | None = None
    post_records = records[trial.shock_step :]
    for end in range(recovery_window, len(post_records) + 1):
        window = post_records[end - recovery_window : end]
        mean_selected = statistics.fmean(item.expected_utility for item in window)
        mean_oracle = statistics.fmean(item.oracle_expected_utility for item in window)
        if mean_selected >= mean_oracle - tolerance:
            recovery_task = window[-1].step
            break
    recovered = recovery_task is not None
    src = None
    if recovery_task is not None:
        src = sum(
            record.feedback_samples
            for record in records[trial.shock_step : recovery_task + 1]
        )

    successes = sum(record.success for record in records)
    post = records[trial.shock_step :]
    post_successes = sum(record.success for record in post)
    total_cost = sum(record.cost_usd for record in records)
    post_feedback = sum(record.feedback_samples for record in post)
    summary = RunSummary(
        method=router.name,
        seed=trial.seed,
        trial_digest=trial.digest,
        recovered=recovered,
        sample_recovery_cost=src,
        recovery_task=recovery_task,
        cpst_usd=total_cost / successes if successes else float("inf"),
        success_rate=successes / len(records),
        postshock_success_rate=post_successes / len(post),
        mean_utility=statistics.fmean(record.realized_utility for record in records),
        postshock_mean_utility=statistics.fmean(record.realized_utility for record in post),
        structural_reexploration_rate=(
            sum(record.structural_reexploration_samples for record in post) / post_feedback
            if post_feedback
            else 0.0
        ),
        mean_decision_ms=statistics.fmean(record.decision_ms for record in records),
        p95_decision_ms=_percentile([record.decision_ms for record in records], 0.95),
        mean_primitive_operations=statistics.fmean(record.primitive_operations for record in records),
    )
    return RunResult(summary, tuple(records))


def _mean_ci(values: Iterable[float]) -> dict[str, float | int | None]:
    finite = [float(value) for value in values if math.isfinite(float(value))]
    if not finite:
        return {"n": 0, "mean": None, "ci95_low": None, "ci95_high": None}
    mean = statistics.fmean(finite)
    if len(finite) == 1:
        margin = 0.0
    else:
        margin = 1.96 * statistics.stdev(finite) / math.sqrt(len(finite))
    return {
        "n": len(finite),
        "mean": mean,
        "ci95_low": mean - margin,
        "ci95_high": mean + margin,
    }


def aggregate_summaries(summaries: Iterable[RunSummary]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[RunSummary]] = {}
    for summary in summaries:
        grouped.setdefault(summary.method, []).append(summary)
    result: dict[str, dict[str, Any]] = {}
    for method, rows in sorted(grouped.items()):
        recovered_src = [
            float(row.sample_recovery_cost)
            for row in rows
            if row.sample_recovery_cost is not None
        ]
        result[method] = {
            "runs": len(rows),
            "recovered_runs": sum(row.recovered for row in rows),
            "censored_runs": sum(not row.recovered for row in rows),
            "recovery_probability": sum(row.recovered for row in rows) / len(rows),
            "sample_recovery_cost_recovered_only": _mean_ci(recovered_src),
            "cpst_usd": _mean_ci(row.cpst_usd for row in rows),
            "success_rate": _mean_ci(row.success_rate for row in rows),
            "postshock_success_rate": _mean_ci(row.postshock_success_rate for row in rows),
            "mean_utility": _mean_ci(row.mean_utility for row in rows),
            "postshock_mean_utility": _mean_ci(row.postshock_mean_utility for row in rows),
            "structural_reexploration_rate": _mean_ci(
                row.structural_reexploration_rate for row in rows
            ),
            "mean_decision_ms": _mean_ci(row.mean_decision_ms for row in rows),
            "p95_decision_ms": _mean_ci(row.p95_decision_ms for row in rows),
            "mean_primitive_operations": _mean_ci(
                row.mean_primitive_operations for row in rows
            ),
        }
    return result


def run_experiment(
    config: dict[str, Any],
    output_dir: str | Path,
    *,
    seeds: Iterable[int] | None = None,
    save_trials: bool = True,
) -> dict[str, Any]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    graph = LayeredGraph.from_config(config["graph"])
    policy = HardPolicy.from_config(config["policy"])
    chosen_seeds = tuple(int(seed) for seed in (seeds or config["experiment"]["seeds"]))
    run_results: list[RunResult] = []
    trials: list[dict[str, Any]] = []
    certification: dict[str, Any] | None = None

    for seed in chosen_seeds:
        trial = FrozenTrial.generate(graph, config, seed)
        if certification is None:
            certification = trial.certification
        if save_trials:
            trial.save(output / "trials" / f"trial_seed_{seed}.json.gz")
        trials.append({"seed": seed, "digest": trial.digest, "certification": trial.certification})
        for router in build_routers(graph, policy, config):
            run_results.append(run_router(trial, router, policy))

    summaries = [result.summary for result in run_results]
    result_payload: dict[str, Any] = {
        "schema": "mycelial-graph-results-v0",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "project": config["project"],
        "scope": {
            "claim": "software demonstrator; no empirical superiority claim",
            "hypotheses_validated": [],
            "graph_paths": graph.path_count,
            "nodes": len(graph.components),
            "edges": len(graph.edges),
            "steps_per_run": int(config["experiment"]["steps"]),
            "shock_step": int(config["experiment"]["shock_step"]),
            "development_seeds": list(config["experiment"]["development_seeds"]),
            "seeds": list(chosen_seeds),
            "trial_certification": certification,
        },
        "trial_manifest": trials,
        "aggregate": aggregate_summaries(summaries),
        "runs": [asdict(summary) for summary in summaries],
        "trace_samples": [
            {
                "method": result.summary.method,
                "seed": result.summary.seed,
                "records": [
                    asdict(record)
                    for record in result.records
                    if record.step in {0, int(config["experiment"]["shock_step"]) - 1, int(config["experiment"]["shock_step"]), int(config["experiment"]["steps"]) - 1}
                ],
            }
            for result in run_results
            if result.summary.seed == chosen_seeds[0]
        ],
    }
    with (output / "results.json").open("w", encoding="utf-8") as stream:
        json.dump(result_payload, stream, indent=2, sort_keys=True, allow_nan=False)
    return result_payload
