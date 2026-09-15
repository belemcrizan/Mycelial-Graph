from __future__ import annotations

import hashlib
import json
import os
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
from ..artifacts import ArtifactError, ensure_unsealed, file_hash, load_validated_trials, source_digest
from ..protocol import protocol_files, validate_confirmatory_execution_authorization
from ..science.canonical_bytes import canonicalize_text_bytes, sha256_bytes
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
    output = path.parents[2]
    checksum_path = output / "checkpoints" / path.parent.name / path.name
    if not checksum_path.exists():
        raise ArtifactError("Partial checkpoint lacks its integrity record; preserve it and use a new directory.")
    checksums = json.loads(checksum_path.read_text(encoding="utf-8"))
    from ..artifacts import safe_artifact_path
    expected_paths = {path.relative_to(output).as_posix(), *(r["trace_ref"] for r in payload["scientific_payload"]["results"])}
    if set(checksums) != expected_paths:
        raise ArtifactError("Checkpoint integrity record has an incomplete inventory.")
    for name, digest in checksums.items():
        artifact = safe_artifact_path(output, name)
        if not artifact.is_file() or file_hash(artifact) != digest:
            raise ArtifactError(f"Checkpoint artifact missing or modified: {name}")
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


def _authorize_confirmatory(config: ExperimentConfig, *, confirmatory_replay: bool) -> None:
    if config.run_kind != "confirmatory":
        return
    if confirmatory_replay:
        from ..science.reproduction import verify_historical_confirmatory_replay_authorization

        errors = verify_historical_confirmatory_replay_authorization(config)
        label = "Historical confirmatory replay is not authorized"
    else:
        errors = validate_confirmatory_execution_authorization(config)
        label = "Confirmatory execution is not authorized"
    if errors:
        joined = "\n - ".join(errors)
        raise ValueError(f"{label}:\n - {joined}")


def _refuse_sealed_confirmatory_output(config: ExperimentConfig, output: Path) -> None:
    root = config.source_path.parents[2].resolve()
    sealed = (root / "experiments" / "v1" / "artifacts" / "confirmatory").resolve()
    resolved = output.resolve()
    if resolved == sealed or sealed in resolved.parents:
        raise ArtifactError("Refusing to write into sealed confirmatory artifacts.")


def _seed_identity_bytes(seeds_path: Path) -> bytes:
    """Canonical LF bytes of a frozen seed file. Independent of working-tree EOL."""
    return canonicalize_text_bytes(seeds_path.read_bytes())


def run_experiment(
    config: ExperimentConfig,
    output_directory: str | Path,
    workers: int = 1,
    *,
    confirmatory_replay: bool = False,
) -> Path:
    require_valid_config(config)
    _authorize_confirmatory(config, confirmatory_replay=confirmatory_replay)
    output = Path(output_directory).resolve()
    _refuse_sealed_confirmatory_output(config, output)
    ensure_unsealed(output)
    if type(workers) is not int or workers < 1:
        raise ValueError("workers must be a positive integer.")
    output.mkdir(parents=True, exist_ok=True)
    lock = output / ".execution.lock"
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise ArtifactError("Output directory is already locked by an execution; inspect before recovery.") from exc
    try:
        os.close(handle)
        return _run_experiment(config, output, workers)
    finally:
        lock.unlink()


def _run_experiment(config: ExperimentConfig, output: Path, workers: int) -> Path:
    project_root = config.source_path.parents[2]
    seeds_path = (config.source_path.parent / config.seeds_file).resolve()
    seeds = load_seeds(seeds_path)
    source_hash = source_digest(project_root)
    if (output / "manifest.json").exists():
        _, provenance = load_validated_trials(config, output)
        if provenance["source_tree_sha256"] != source_hash or provenance["code_revision"] != code_commit(project_root):
            raise ArtifactError("Completed experiment belongs to another source revision; use a new output directory.")
        return output / "manifest.json"
    if list((output / "failures").glob("*.json")):
        raise ArtifactError("Previous failures are retained. Review and log a rerun; never silently retry them.")
    protocol_names = protocol_files(config.source_path.parent)
    protocol_hashes = {name: file_hash(config.source_path.parent / name) for name in protocol_names}
    execution = {
        "experiment_id": config.experiment_id, "run_kind": config.run_kind,
        "config_hash": config_hash(config), "source_tree_sha256": source_hash,
        "code_revision": code_commit(project_root),
        "seeds_file_sha256": sha256_bytes(_seed_identity_bytes(seeds_path)),
        "protocol_files": protocol_hashes,
    }
    execution_path = output / "execution.json"
    if execution_path.exists():
        if json.loads(execution_path.read_text(encoding="utf-8")) != execution:
            raise ArtifactError("Partial experiment code, protocol, or configuration changed.")
    else:
        if any(output.iterdir()):
            # The exclusive execution lock is the only file allowed on first use.
            if list(output.iterdir()) != [output / ".execution.lock"]:
                raise ArtifactError("Output is not empty and has no execution identity; use a new directory.")
        atomic_write_json(execution_path, execution)
        atomic_write_json(output / "provenance" / "config.json", config.to_dict())
        (output / "provenance" / "seeds.txt").write_bytes(_seed_identity_bytes(seeds_path))
        for name in protocol_names:
            (output / "provenance" / name).write_bytes((config.source_path.parent / name).read_bytes())
    requested_jobs = [(seed, rho) for rho in config.environment.rho_values for seed in seeds]
    expected_raw = {output / "raw" / f"rho-{rho:.2f}" / f"seed-{seed}.json" for seed, rho in requested_jobs}
    if not set((output / "raw").rglob("*.json")).issubset(expected_raw):
        raise ArtifactError("Partial experiment contains unplanned raw records.")
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
            _write_checkpoint_integrity(output, destination, payload)
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
                _write_checkpoint_integrity(output, destination, payload)

    artifact_files = sorted((output / "raw").rglob("*.json")) + sorted(
        (output / "traces").rglob("*.jsonl.gz")
    )
    artifact_files += sorted((output / "checkpoints").rglob("*.json"))
    artifact_files += sorted((output / "provenance").iterdir()) + [execution_path]
    manifest = {
        "schema_version": 2,
        "run_kind": config.run_kind,
        "source_tree_sha256": source_hash,
        "protocol_files": protocol_hashes,
        "experiment_id": config.experiment_id,
        "protocol_version": config.protocol_version,
        "config_hash": config_hash(config),
        "config_file": str(config.source_path),
        "seeds_file": str(seeds_path),
        "seeds_file_sha256": sha256_bytes(_seed_identity_bytes(seeds_path)),
        "code_revision": code_commit(project_root),
        "scientific_job_count": len(requested_jobs),
        "executed_job_count_this_invocation": len(jobs),
        "method_count": len(config.methods),
        "environment": {
            "python": sys.version,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pyyaml": yaml.__version__,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "workers": workers,
            "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "files": {path.relative_to(output).as_posix(): _file_sha256(path) for path in artifact_files},
    }
    manifest_path = output / "manifest.json"
    atomic_write_json(manifest_path, manifest)
    load_validated_trials(config, output)
    return manifest_path


def _write_checkpoint_integrity(output: Path, path: Path, payload: dict[str, Any]) -> None:
    paths = [path, *(output / r["trace_ref"] for r in payload["scientific_payload"]["results"])]
    atomic_write_json(output / "checkpoints" / path.parent.name / path.name,
                      {p.relative_to(output).as_posix(): file_hash(p) for p in paths})
