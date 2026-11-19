from __future__ import annotations

import gzip
import hashlib
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
from ..environment.roles import edge_role
from ..ledger import TokenUsage, TotalResourceLedger
from ..metrics import sustained_quality_recovery
from ..policies import create_resource_agent
from ..resources import BudgetReservation
from ..seeding import create_rng
from ..types import V2ExperimentConfig


def v2_config_hash(config: V2ExperimentConfig) -> str:
    encoded = json.dumps(config.to_dict(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class V2DecisionRecord:
    step: int
    task_id: str
    path: tuple[int, ...]
    edge_ids: tuple[int, ...]
    candidate_paths_available: int
    router_candidates: int
    edge_scores: tuple[float, ...]
    component_health: tuple[float, ...]
    estimated_utility: float
    estimated_tokens: float
    estimated_cost: float
    uncertainty: float
    decision_mode: str
    fallback_reason: str | None
    objective_mode: str
    anastomosis_gate: float
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
    budget_remaining: float
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
    post_realized_quality: float
    post_regret: float
    post_tokens: int
    post_router_tokens: int
    post_cost: float
    post_latency: float
    success_rate: float
    route_switches: int
    exploratory_steps: int
    fallback_steps: int
    prune_count: int
    resource_transfers: float
    budget_reservation: dict[str, Any]
    ledger: dict[str, Any]
    pre_shock_steps: int
    post_shock_steps: int
    decision_cpu_seconds: float
    trace_ref: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_trace(path: Path, records: list[V2DecisionRecord]) -> None:
    """Write deterministic mtime=0 gzipped JSONL trace with atomic fsync + replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    os.close(handle)
    try:
        with open(temporary, "wb") as raw_file:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw_file, mtime=0) as gz:
                for record in records:
                    line = (json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                    gz.write(line)
            raw_file.flush()
            os.fsync(raw_file.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def _minimal_token_path(scenario: ResourceScenario, step: int) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Deterministic minimum-token fallback path when hard trial budget is nearly exhausted."""
    t_means = scenario.token_means(step)
    node = scenario.graph.source
    path = [node]
    edges: list[int] = []
    while node != scenario.graph.sink:
        cands = scenario.graph.outgoing[node]
        best = min(cands, key=lambda eid: float(t_means[eid]))
        edges.append(best)
        node = scenario.graph.edges[best].target
        path.append(node)
    return tuple(path), tuple(edges)


def _agent_rng_namespace(regime: str, method_name: str) -> str:
    # Controlled V2 mechanism ablations share a common random stream so differences reflect
    # mechanism toggles rather than Monte Carlo seed divergence.
    if method_name.startswith("v2_"):
        return f"agent:{regime}:v2_mycelial_family"
    return f"agent:{regime}:{method_name}"


def run_v2_method(
    scenario: ResourceScenario,
    method_name: str,
    config: V2ExperimentConfig,
    output_directory: Path,
    project_root: Path,
) -> V2TrialResult:
    rng = create_rng(scenario.seed, _agent_rng_namespace(scenario.regime, method_name))
    agent = create_resource_agent(method_name, config, scenario.graph, rng)
    records: list[V2DecisionRecord] = []
    ledger = TotalResourceLedger()
    wallet = BudgetReservation(cap=float(config.resources.global_budget_tokens))
    expected_series: list[float] = []
    oracle_series: list[float] = []
    switches = 0
    exploratory_steps = 0
    fallback_steps = 0
    last_path: tuple[int, ...] | None = None
    cpu_started = time.process_time()

    total_steps = config.horizon.total_steps
    for step in range(total_steps):
        steps_left = max(total_steps - step, 1)
        is_post = step >= config.horizon.pre_shock_steps
        regime_cap = float(scenario.budget_cap(step))
        # Effective remaining envelope combines wallet remaining capacity and regime scarcity cap.
        if is_post and regime_cap < float(config.resources.global_budget_tokens):
            post_left = max(config.horizon.post_shock_steps - (step - config.horizon.pre_shock_steps), 1)
            effective_step_cap = min(
                wallet.sustainable_step_allowance(steps_left),
                regime_cap / float(max(config.horizon.post_shock_steps, 1)),
            )
            effective_cap_signal = effective_step_cap * float(post_left)
        else:
            effective_step_cap = wallet.sustainable_step_allowance(steps_left)
            effective_cap_signal = min(wallet.remaining, regime_cap)

        step_cpu_start = time.process_time()
        decision = agent.choose(scenario.graph, step, max(effective_step_cap, 1.0))
        step_policy_ms = (time.process_time() - step_cpu_start) * 1000.0

        chosen_path = decision.path
        chosen_edges = decision.edge_ids
        fallback_reason = decision.fallback_reason
        decision_mode = decision.decision_mode

        # Hard budget reservation guard: if wallet cannot cover estimated step tokens and a cheaper
        # path exists, downgrade before execution so hard budgets are respected.
        router_tokens = decision.router_candidates * config.resources.router_tokens_per_candidate
        state_overhead = config.resources.state_overhead_tokens
        planned_est = max(decision.estimated_tokens, 1.0) + router_tokens + state_overhead
        if wallet.remaining < planned_est and wallet.remaining > 0.0:
            min_path, min_edges = _minimal_token_path(scenario, step)
            if min_edges != chosen_edges:
                chosen_path = min_path
                chosen_edges = min_edges
                fallback_reason = fallback_reason or "hard_wallet_reservation_downgrade"
                decision_mode = "budget_downgrade"

        observations = scenario.observations(chosen_edges, step)
        path_usage = TokenUsage()
        latency = 0.0
        monetary = 0.0
        qualities = []
        successes = []
        model_calls = 0
        tool_calls = 0
        retriever_calls = 0
        validator_calls = 0
        for obs in observations:
            path_usage = path_usage.merged(obs.token_usage)
            latency += obs.latency_ms
            monetary += obs.monetary_cost
            qualities.append(obs.quality)
            successes.append(obs.success)
            role = edge_role(scenario.graph, obs.edge_id)
            if role == "model":
                model_calls += 1
            elif role == "tool":
                tool_calls += 1
            elif role == "retrieval":
                retriever_calls += 1
            elif role == "verification":
                validator_calls += 1

        step_total_tokens = path_usage.path_tokens + router_tokens + state_overhead
        reserve_amt = min(float(step_total_tokens), max(wallet.remaining, 0.0))
        if reserve_amt > 0.0 and wallet.can_afford(reserve_amt):
            wallet.reserve(reserve_amt)
            wallet.commit(reserve_amt, float(step_total_tokens))
        else:
            wallet.spent += float(step_total_tokens)
            wallet.overruns += 1

        realized_q = float(np.mean(qualities)) if qualities else 0.0
        success = all(successes) if successes else False
        expected = scenario.expected_path_quality(chosen_edges, step)
        oracle = scenario.oracle_quality(step)
        expected_series.append(expected)
        oracle_series.append(oracle)
        if last_path is not None and chosen_path != last_path:
            switches += 1
        last_path = chosen_path
        if decision.exploratory_edges > 0:
            exploratory_steps += 1
        is_fb = fallback_reason is not None
        if is_fb:
            fallback_steps += 1

        ledger.record_step(
            path_usage,
            router_tokens,
            state_overhead,
            latency,
            monetary,
            expected,
            success,
            model_calls=model_calls,
            tool_calls=tool_calls,
            retriever_calls=retriever_calls,
            validator_calls=validator_calls,
            fallback_count=1 if is_fb else 0,
            policy_cpu_ms=step_policy_ms,
            realized_quality=realized_q,
            is_post_shock=is_post,
        )
        full_step_usage = path_usage.merged(
            TokenUsage(router_tokens=router_tokens, state_overhead_tokens=state_overhead)
        )
        records.append(
            V2DecisionRecord(
                step=step,
                task_id=f"{scenario.scenario_id}:step-{step:04d}",
                path=chosen_path,
                edge_ids=chosen_edges,
                candidate_paths_available=decision.candidate_paths_available or len(scenario.graph.all_paths()),
                router_candidates=decision.router_candidates,
                edge_scores=decision.edge_scores,
                component_health=decision.component_health,
                estimated_utility=decision.estimated_utility,
                estimated_tokens=decision.estimated_tokens,
                estimated_cost=decision.estimated_cost,
                uncertainty=decision.uncertainty,
                decision_mode=decision_mode,
                fallback_reason=fallback_reason,
                objective_mode=decision.objective_mode,
                anastomosis_gate=decision.anastomosis_gate,
                expected_quality=expected,
                realized_quality=realized_q,
                oracle_quality=oracle,
                success=success,
                total_tokens=full_step_usage.total_tokens,
                path_tokens=full_step_usage.path_tokens,
                router_tokens=router_tokens,
                monetary_cost=monetary,
                latency_ms=latency,
                mvc=decision.mvc,
                prune_count=decision.prune_count,
                transfer_l1=decision.transfer_l1,
                budget_remaining=max(0.0, wallet.remaining),
                token_usage=full_step_usage.to_dict(),
            )
        )
        upd_start = time.process_time()
        agent.update(scenario.graph, decision, observations, step, max(effective_step_cap, 1.0))
        ledger.policy_cpu_ms += (time.process_time() - upd_start) * 1000.0
        _ = effective_cap_signal

    elapsed = time.process_time() - cpu_started
    recovery, restricted, recovered = sustained_quality_recovery(
        expected_series, oracle_series, config.horizon
    )
    post = records[config.horizon.pre_shock_steps :]
    post_regret = float(sum(max(0.0, row.oracle_quality - row.expected_quality) for row in post))
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
        post_realized_quality=float(np.mean([row.realized_quality for row in post])),
        post_regret=post_regret,
        post_tokens=int(sum(row.total_tokens for row in post)),
        post_router_tokens=int(sum(row.router_tokens for row in post)),
        post_cost=float(sum(row.monetary_cost for row in post)),
        post_latency=float(sum(row.latency_ms for row in post)),
        success_rate=float(np.mean([row.success for row in post])),
        route_switches=switches,
        exploratory_steps=exploratory_steps,
        fallback_steps=fallback_steps,
        prune_count=max((row.prune_count for row in records), default=0),
        resource_transfers=float(sum(row.transfer_l1 for row in records)),
        budget_reservation=wallet.to_dict(),
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
