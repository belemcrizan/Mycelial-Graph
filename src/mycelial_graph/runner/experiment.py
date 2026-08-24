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

from ..environment.scenario import generate_scenario
from ..types import ExperimentConfig
from ..validation import load_seeds, require_valid_config, validate_result_payload
from .checkpoint import atomic_write_json
from .trial import code_commit, config_hash, run_paired_scenario


def _scenario_job(
    config: ExperimentConfig,
    seed: int,
    rho: float,
    output_directory: str,
    project_root: str,
) -> dict[str, Any]:
    output = Path(output_directory)
    scenario = generate_scenario(config, seed, rho)
    results = run_paired_scenario(scenario, config, output, Path(project_root))
    scientific_payload = {
        "scenario_hash": scenario.scientific_hash(),
        "scenario_id": scenario.scenario_id,
        "rho": rho,
        "seed": seed,
        "shock_l2_norm": float(np.linalg.norm(scenario.shock_vector)),
        "shock_node": scenario.shock_node,
        "interaction_edge": scenario.interaction_edge,
        "optimal_pre_path": scenario.optimal_pre_path,
        "optimal_post_path": scenario.optimal_post_path,
        "results": [result.to_dict() for result in results],
    }
    return {
        "scientific_payload": scientific_payload,
        "provenance": {
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
            "python": sys.version,
            "platform": platform.platform(),
        },
    }


def _completed_checkpoint_matches(
    path: Path,
    config: ExperimentConfig,
    seed: int,
    rho: float,
    project_root: Path,
) -> bool:
    if not path.exists():
        return False
    payload = json.loads(path.read_text(encoding="utf-8"))
    validate_result_payload(payload, config)
    scientific = payload["scientific_payload"]
    revisions = {result["code_commit"] for result in scientific["results"]}
    hashes = {result["config_hash"] for result in scientific["results"]}
    expected_revision = code_commit(project_root)
    if (
        scientific["seed"] == seed
        and np.isclose(scientific["rho"], rho)
        and revisions == {expected_revision}
        and hashes == {config_hash(config)}
    ):
        return True
    raise RuntimeError(
        f"Checkpoint exists but does not match current code/config: {path}. "
        "Use a new output directory; do not overwrite scientific data."
    )


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_experiment(
    config: ExperimentConfig,
    output_directory: str | Path,
    workers: int = 1,
) -> Path:
    require_valid_config(config)
    output = Path(output_directory).resolve()
    output.mkdir(parents=True, exist_ok=True)
    project_root = config.source_path.parents[2]
    seeds_path = (config.source_path.parent / config.seeds_file).resolve()
    seeds = load_seeds(seeds_path)
    requested_jobs = [(seed, rho) for rho in config.environment.rho_values for seed in seeds]
    jobs = []
    for seed, rho in requested_jobs:
        destination = output / "raw" / f"rho-{rho:.2f}" / f"seed-{seed}.json"
        if not _completed_checkpoint_matches(destination, config, seed, rho, project_root):
            jobs.append((seed, rho))

    if workers <= 1:
        for seed, rho in jobs:
            payload = _scenario_job(config, seed, rho, str(output), str(project_root))
            validate_result_payload(payload, config)
            destination = output / "raw" / f"rho-{rho:.2f}" / f"seed-{seed}.json"
            atomic_write_json(destination, payload)
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    _scenario_job,
                    config,
                    seed,
                    rho,
                    str(output),
                    str(project_root),
                ): (seed, rho)
                for seed, rho in jobs
            }
            for future in as_completed(futures):
                seed, rho = futures[future]
                payload = future.result()
                validate_result_payload(payload, config)
                destination = output / "raw" / f"rho-{rho:.2f}" / f"seed-{seed}.json"
                atomic_write_json(destination, payload)

    artifact_files = sorted((output / "raw").rglob("*.json")) + sorted(
        (output / "traces").rglob("*.jsonl.gz")
    )
    manifest = {
        "experiment_id": config.experiment_id,
        "protocol_version": config.protocol_version,
        "config_hash": config_hash(config),
        "config_file": str(config.source_path),
        "seeds_file": str(seeds_path),
        "seeds_file_sha256": _file_sha256(seeds_path),
        "code_revision": code_commit(project_root),
        "scientific_job_count": len(requested_jobs),
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
