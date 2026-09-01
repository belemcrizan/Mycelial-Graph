from __future__ import annotations

import hashlib
import json
import platform
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import scipy
import yaml

from ...runner.checkpoint import atomic_write_json
from ...validation import load_seeds
from ..environment import generate_resource_scenario
from ..types import V2ExperimentConfig
from ..validation import require_valid_v2_config
from ...runner.trial import code_commit
from .trial import run_paired_v2_scenario, v2_config_hash


def canonical_v2_payload(payload: dict[str, Any]) -> dict[str, Any]:
    scientific = json.loads(json.dumps(payload["scientific_payload"]))
    for result in scientific.get("results", []):
        result.pop("decision_cpu_seconds", None)
        result.pop("trace_ref", None)
    return scientific


def _scenario_job(
    config: V2ExperimentConfig,
    seed: int,
    regime: str,
    output_directory: str,
    project_root: str,
) -> dict[str, Any]:
    output = Path(output_directory)
    scenario = generate_resource_scenario(config, seed, regime)
    results = run_paired_v2_scenario(scenario, config, output, Path(project_root))
    return {
        "scientific_payload": {
            "scenario_hash": scenario.scientific_hash(),
            "scenario_id": scenario.scenario_id,
            "regime": regime,
            "seed": seed,
            "difficulty": scenario.difficulty,
            "optimal_pre_path": scenario.optimal_pre_path,
            "optimal_post_path": scenario.optimal_post_path,
            "budget_pre": scenario.budget_pre,
            "budget_post": scenario.budget_post,
            "results": [result.to_dict() for result in results],
        },
        "provenance": {
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "python": sys.version,
            "platform": platform.platform(),
        },
    }


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checkpoint_matches(
    path: Path,
    config: V2ExperimentConfig,
    seed: int,
    regime: str,
    project_root: Path,
) -> bool:
    if not path.exists():
        return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    scientific = payload["scientific_payload"]
    expected = code_commit(project_root)
    hashes = {result["config_hash"] for result in scientific["results"]}
    revisions = {result["code_commit"] for result in scientific["results"]}
    if (
        scientific["seed"] == seed
        and scientific["regime"] == regime
        and hashes == {v2_config_hash(config)}
        and revisions == {expected}
    ):
        return True
    raise RuntimeError(
        f"V2 checkpoint exists but does not match current code/config: {path}. "
        "Use a new output directory."
    )


def run_v2_experiment(
    config: V2ExperimentConfig,
    output_directory: str | Path,
    workers: int = 1,
) -> Path:
    require_valid_v2_config(config)
    output = Path(output_directory).resolve()
    output.mkdir(parents=True, exist_ok=True)
    project_root = config.source_path.parents[2]
    seeds_path = (config.source_path.parent / config.seeds_file).resolve()
    seeds = load_seeds(seeds_path)
    requested = [(seed, regime) for regime in config.environment.regimes for seed in seeds]
    jobs = []
    for seed, regime in requested:
        destination = output / "raw" / regime / f"seed-{seed}.json"
        if not _checkpoint_matches(destination, config, seed, regime, project_root):
            jobs.append((seed, regime))

    if workers <= 1:
        for seed, regime in jobs:
            payload = _scenario_job(config, seed, regime, str(output), str(project_root))
            destination = output / "raw" / regime / f"seed-{seed}.json"
            atomic_write_json(destination, payload)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(_scenario_job, config, seed, regime, str(output), str(project_root)): (
                    seed,
                    regime,
                )
                for seed, regime in jobs
            }
            for future in as_completed(futures):
                seed, regime = futures[future]
                payload = future.result()
                destination = output / "raw" / regime / f"seed-{seed}.json"
                atomic_write_json(destination, payload)

    artifact_files = sorted((output / "raw").rglob("*.json")) + sorted(
        (output / "traces").rglob("*.jsonl.gz")
    )
    manifest = {
        "experiment_id": config.experiment_id,
        "protocol_version": config.protocol_version,
        "config_hash": v2_config_hash(config),
        "config_file": str(config.source_path),
        "seeds_file": str(seeds_path),
        "seeds_file_sha256": _file_sha256(seeds_path),
        "code_revision": code_commit(project_root),
        "scientific_job_count": len(requested),
        "executed_job_count_this_invocation": len(jobs),
        "method_count": len(config.methods),
        "environment": {
            "python": sys.version,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pyyaml": yaml.__version__,
        },
        "files": {str(path.relative_to(output)): _file_sha256(path) for path in artifact_files},
    }
    manifest_path = output / "manifest.json"
    atomic_write_json(manifest_path, manifest)
    return manifest_path
