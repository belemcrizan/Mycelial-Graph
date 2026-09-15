from __future__ import annotations

from dataclasses import replace
from typing import Any

from ..environment import generate_resource_scenario
from ..runner.trial import run_v2_method
from ..types import V2ExperimentConfig


DEFAULT_BUDGETS = (5_000, 10_000, 20_000, 40_000, 80_000)


def quality_at_budget(
    config: V2ExperimentConfig,
    method: str,
    budget: int,
    seed: int,
    regime: str,
    output_directory,
    project_root,
) -> dict[str, float]:
    resources = replace(config.resources, global_budget_tokens=budget, scarce_budget_tokens=min(budget, config.resources.scarce_budget_tokens))
    local = replace(config, resources=resources)
    scenario = generate_resource_scenario(local, seed, regime)
    result = run_v2_method(scenario, method, local, output_directory, project_root)
    return {
        "budget": float(budget),
        "quality": float(result.post_quality),
        "tokens": float(result.ledger["total_tokens"]),
        "cost": float(result.post_cost),
        "success": float(result.success_rate),
    }


def budget_response_curve(
    config: V2ExperimentConfig,
    method: str,
    seeds: tuple[int, ...],
    budgets: tuple[int, ...] = DEFAULT_BUDGETS,
    output_directory=None,
    project_root=None,
) -> dict[str, Any]:
    from pathlib import Path
    import tempfile

    regime = config.environment.primary_regime
    points: list[dict[str, float]] = []
    owned = output_directory is None
    tmp = None
    if owned:
        tmp = tempfile.TemporaryDirectory()
        output_directory = Path(tmp.name)
        project_root = Path(__file__).resolve().parents[4]
    try:
        for budget in budgets:
            qualities = []
            tokens = []
            for seed in seeds:
                row = quality_at_budget(
                    config,
                    method,
                    budget,
                    seed,
                    regime,
                    output_directory,
                    project_root,
                )
                qualities.append(row["quality"])
                tokens.append(row["tokens"])
            points.append(
                {
                    "budget": float(budget),
                    "quality_mean": float(sum(qualities) / len(qualities)),
                    "tokens_mean": float(sum(tokens) / len(tokens)),
                }
            )
    finally:
        if tmp is not None:
            tmp.cleanup()
    return {
        "method": method,
        "regime": regime,
        "points": points,
        "B_70": _min_budget_for_quality(points, 0.70),
        "B_80": _min_budget_for_quality(points, 0.80),
        "B_90": _min_budget_for_quality(points, 0.90),
        "claim_boundary": "Budget curves are development diagnostics unless a frozen V2.1 confirmatory protocol says otherwise.",
    }


def _min_budget_for_quality(points: list[dict[str, float]], target: float) -> float | None:
    eligible = [row["budget"] for row in points if row["quality_mean"] >= target]
    return float(min(eligible)) if eligible else None
