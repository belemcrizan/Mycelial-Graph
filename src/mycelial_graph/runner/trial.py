from __future__ import annotations

import gzip
import hashlib
import json
import os
import subprocess
import tempfile
import time
from functools import lru_cache
from pathlib import Path

import numpy as np

from ..agents.factory import create_agent
from ..analysis.metrics import post_shock_dynamic_regret, sustained_recovery_time
from ..environment.scenario import Scenario
from ..types import DecisionRecord, ExperimentConfig, TrialResult
from .seeding import create_rng


def config_hash(config: ExperimentConfig) -> str:
    encoded = json.dumps(config.to_dict(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def code_commit(project_root: Path) -> str:
    try:
        top_level = Path(
            subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=project_root,
                text=True,
                encoding="utf-8",
                stderr=subprocess.DEVNULL,
            ).strip()
        ).resolve()
        if top_level != project_root.resolve():
            return f"tree:{source_tree_hash(project_root)}"
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            text=True,
            encoding="utf-8",
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return f"tree:{source_tree_hash(project_root)}"


@lru_cache(maxsize=8)
def source_tree_hash(project_root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((project_root / "src").rglob("*.py")):
        digest.update(str(path.relative_to(project_root)).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _write_trace(path: Path, records: list[DecisionRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    os.close(handle)
    try:
        with gzip.open(temporary, "wt", encoding="utf-8") as stream:
            for record in records:
                stream.write(json.dumps(record.__dict__, sort_keys=True) + "\n")
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def run_method(
    scenario: Scenario,
    method_name: str,
    config: ExperimentConfig,
    output_directory: Path,
    project_root: Path,
) -> TrialResult:
    rng = create_rng(scenario.seed, f"agent:{scenario.rho:.8f}:{method_name}")
    agent = create_agent(method_name, config, scenario.graph, rng)
    records: list[DecisionRecord] = []
    cpu_started = time.process_time()
    for step in range(config.horizon.total_steps):
        decision = agent.choose(scenario.graph, step)
        rewards = scenario.realized_edge_rewards(decision.edge_ids, step)
        expected = scenario.expected_path_utility(decision.edge_ids, step)
        realized = float(np.mean(rewards))
        oracle = scenario.oracle_expected_utility(step)
        records.append(
            DecisionRecord(
                step=step,
                path=decision.path,
                edge_ids=decision.edge_ids,
                expected_utility=expected,
                realized_utility=realized,
                oracle_expected_utility=oracle,
                exploratory_edges=decision.exploratory_edges,
                selected_edge_scores=decision.edge_scores,
            )
        )
        agent.update(scenario.graph, decision, rewards, step)
    elapsed = time.process_time() - cpu_started
    recovery, restricted, recovered = sustained_recovery_time(records, config.horizon)
    regret = post_shock_dynamic_regret(records, config.horizon)
    tail = records[-config.horizon.recovery_trailing_window :]
    final_expected = float(np.mean([record.expected_utility for record in tail]))
    trace_relative = Path("traces") / f"{scenario.scenario_id}-{method_name}.jsonl.gz"
    _write_trace(output_directory / trace_relative, records)
    trial_id = f"{scenario.scenario_id}-{method_name}"
    return TrialResult(
        trial_id=trial_id,
        scenario_id=scenario.scenario_id,
        protocol_version=config.protocol_version,
        config_hash=config_hash(config),
        code_commit=code_commit(project_root),
        rho=scenario.rho,
        seed=scenario.seed,
        method=method_name,
        method_status="completed",
        recovery_time=recovery,
        restricted_recovery_time=restricted,
        recovered=recovered,
        censored=not recovered,
        dynamic_regret=regret,
        final_expected_utility=final_expected,
        pre_shock_steps=config.horizon.pre_shock_steps,
        post_shock_steps=config.horizon.post_shock_steps,
        decision_cpu_seconds=elapsed,
        trace_ref=trace_relative.as_posix(),
    )


def run_paired_scenario(
    scenario: Scenario,
    config: ExperimentConfig,
    output_directory: Path,
    project_root: Path,
) -> list[TrialResult]:
    results = [
        run_method(scenario, method, config, output_directory, project_root)
        for method in config.methods
    ]
    scenario_ids = {result.scenario_id for result in results}
    config_hashes = {result.config_hash for result in results}
    if scenario_ids != {scenario.scenario_id} or len(config_hashes) != 1:
        raise RuntimeError("Paired-result integrity validation failed.")
    return results
