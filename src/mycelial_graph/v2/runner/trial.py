from __future__ import annotations

import gzip
import json
import os
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np

from ...runner.trial import code_commit
from ..environment import ResourceScenario
from ..ledger import TokenUsage, TotalResourceLedger
from ..metrics import sustained_quality_recovery
from ..policies import create_resource_agent
from ..seeding import create_rng
from ..types import V2ExperimentConfig


def v2_config_hash(config: V2ExperimentConfig) -> str:
    encoded = json.dumps(config.to_dict(), sort_keys=True, separators=(",", ":")).encode()
    import hashlib

    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class V2DecisionRecord:
    step: int
    path: tuple[int, ...]
    edge_ids: tuple[int, ...]
    expected_quality: float
    realized_quality: float
    oracle_quality: float
    success: bool
    total_tokens: int
    path_tokens: int
    router_tokens: int
    monetary_cost: float
    latency_ms: float
    mvc: float
    prune_count: int
    transfer_l1: float
    token_usage: dict[str, Any]


@dataclass(frozen=True)
class V2TrialResult:
    trial_id: str
    scenario_id: str
    protocol_version: str
    config_hash: str
    code_commit: str
    regime: str
    seed: int
    difficulty: str
    method: str
    method_status: str
    recovery_time: int | None
    restricted_recovery_time: int
    recovered: bool
    censored: bool
    post_quality: float
    post_tokens: int
    post_cost: float
    post_latency: float
    success_rate: float
    route_switches: int
    prune_count: int
    resource_transfers: float
    ledger: dict[str, Any]
    pre_shock_steps: int
    post_shock_steps: int
    decision_cpu_seconds: float
    trace_ref: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_trace(path: Path, records: list[V2DecisionRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(handle)
    try:
        with gzip.open(temporary, "wt", encoding="utf-8") as stream:
            for record in records:
                stream.write(json.dumps(asdict(record), sort_keys=True) + "\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def run_v2_method(
    scenario: ResourceScenario,
    method_name: str,
    config: V2ExperimentConfig,
    output_directory: Path,
    project_root: Path,
) -> V2TrialResult:
    rng = create_rng(scenario.seed, f"agent:{scenario.regime}:{method_name}")
    agent = create_resource_agent(method_name, config, scenario.graph, rng)
    records: list[V2DecisionRecord] = []
    ledger = TotalResourceLedger()
    expected_series: list[float] = []
    oracle_series: list[float] = []
    switches = 0
    last_path: tuple[int, ...] | None = None
    cpu_started = time.process_time()
    for step in range(config.horizon.total_steps):
        cap = float(scenario.budget_cap(step))
        decision = agent.choose(scenario.graph, step, cap)
        observations = scenario.observations(decision.edge_ids, step)
        path_usage = TokenUsage()
        latency = 0.0
        monetary = 0.0
        qualities = []
        successes = []
        for obs in observations:
            path_usage = path_usage.merged(obs.token_usage)
            latency += obs.latency_ms
            monetary += obs.monetary_cost
            qualities.append(obs.quality)
            successes.append(obs.success)
        router_tokens = decision.router_candidates * config.resources.router_tokens_per_candidate
        state_overhead = config.resources.state_overhead_tokens
        realized_q = float(np.mean(qualities)) if qualities else 0.0
        success = all(successes) if successes else False
        expected = scenario.expected_path_quality(decision.edge_ids, step)
        oracle = scenario.oracle_quality(step)
        expected_series.append(expected)
        oracle_series.append(oracle)
        if last_path is not None and decision.path != last_path:
            switches += 1
        last_path = decision.path
        ledger.record_step(
            path_usage,
            router_tokens,
            state_overhead,
            latency,
            monetary,
            expected,
            success,
            model_calls=1,
            tool_calls=1,
        )
        usage_dict = path_usage.merged(TokenUsage(router_tokens=router_tokens)).to_dict()
        usage_dict["state_overhead_tokens"] = state_overhead
        records.append(
            V2DecisionRecord(
                step=step,
                path=decision.path,
                edge_ids=decision.edge_ids,
                expected_quality=expected,
                realized_quality=realized_q,
                oracle_quality=oracle,
                success=success,
                total_tokens=path_usage.path_tokens + router_tokens + state_overhead,
                path_tokens=path_usage.path_tokens,
                router_tokens=router_tokens,
                monetary_cost=monetary,
                latency_ms=latency,
                mvc=decision.mvc,
                prune_count=decision.prune_count,
                transfer_l1=decision.transfer_l1,
                token_usage=usage_dict,
            )
        )
        agent.update(scenario.graph, decision, observations, step, cap)
    elapsed = time.process_time() - cpu_started
    recovery, restricted, recovered = sustained_quality_recovery(
        expected_series, oracle_series, config.horizon
    )
    post = records[config.horizon.pre_shock_steps :]
    trace_relative = Path("traces") / f"{scenario.scenario_id}-{method_name}.jsonl.gz"
    _write_trace(output_directory / trace_relative, records)
    return V2TrialResult(
        trial_id=f"{scenario.scenario_id}-{method_name}",
        scenario_id=scenario.scenario_id,
        protocol_version=config.protocol_version,
        config_hash=v2_config_hash(config),
        code_commit=code_commit(project_root),
        regime=scenario.regime,
        seed=scenario.seed,
        difficulty=scenario.difficulty,
        method=method_name,
        method_status="completed",
        recovery_time=recovery,
        restricted_recovery_time=restricted,
        recovered=recovered,
        censored=not recovered,
        post_quality=float(np.mean([row.expected_quality for row in post])),
        post_tokens=int(sum(row.total_tokens for row in post)),
        post_cost=float(sum(row.monetary_cost for row in post)),
        post_latency=float(sum(row.latency_ms for row in post)),
        success_rate=float(np.mean([row.success for row in post])),
        route_switches=switches,
        prune_count=max((row.prune_count for row in records), default=0),
        resource_transfers=float(sum(row.transfer_l1 for row in records)),
        ledger=ledger.to_dict(),
        pre_shock_steps=config.horizon.pre_shock_steps,
        post_shock_steps=config.horizon.post_shock_steps,
        decision_cpu_seconds=elapsed,
        trace_ref=trace_relative.as_posix(),
    )


def run_paired_v2_scenario(
    scenario: ResourceScenario,
    config: V2ExperimentConfig,
    output_directory: Path,
    project_root: Path,
) -> list[V2TrialResult]:
    results = [
        run_v2_method(scenario, method, config, output_directory, project_root)
        for method in config.methods
    ]
    if {result.scenario_id for result in results} != {scenario.scenario_id}:
        raise RuntimeError("Paired V2 integrity validation failed.")
    return results
