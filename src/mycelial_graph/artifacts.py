"""Fail-closed validation of V1 evidence, independent of filename claims."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Any

from .types import ExperimentConfig


class ArtifactError(ValueError):
    """Evidence is incomplete, inconsistent, or has changed."""


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def config_digest(config: ExperimentConfig) -> str:
    encoded = json.dumps(config.to_dict(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def source_digest(root: Path) -> str:
    digest = hashlib.sha256()
    paths = sorted((root / "src").rglob("*.py"))
    if not paths:
        raise ArtifactError(f"No source files under {root / 'src'}")
    for path in paths:
        digest.update(path.relative_to(root).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def safe_artifact_path(root: Path, name: str) -> Path:
    relative = PurePosixPath(name)
    if not name or relative.is_absolute() or ".." in relative.parts or "\\" in name:
        raise ArtifactError(f"Unsafe artifact path: {name!r}")
    path = root.joinpath(*relative.parts)
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ArtifactError(f"Artifact escapes its directory: {name!r}")
    return path


def ensure_unsealed(output: Path) -> None:
    if (output / "artifact_seal.json").exists():
        raise ArtifactError("Artifact is sealed. Preserve it and use a new directory for re-analysis.")


def load_validated_trials(config: ExperimentConfig, output: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Verify bytes, the complete planned population, pairing, and provenance.

    Historical manifests remain readable when they meet these checks. Missing
    source/protocol snapshots in those artifacts are reported, never invented.
    """
    from .validation import load_seeds, require_valid_config, validate_result_payload

    require_valid_config(config)
    output = output.resolve()
    manifest_path = output / "manifest.json"
    if not manifest_path.is_file():
        raise ArtifactError("A completed experiment manifest is required before analysis.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for key, expected in {
        "experiment_id": config.experiment_id,
        "protocol_version": config.protocol_version,
        "config_hash": config_digest(config),
        "method_count": len(config.methods),
    }.items():
        if manifest.get(key) != expected:
            raise ArtifactError(f"Manifest {key} does not match the requested configuration.")
    if "run_kind" in manifest and manifest["run_kind"] != config.run_kind:
        raise ArtifactError("Manifest run_kind mismatch.")
    seed_path = config.source_path.parent / config.seeds_file
    if manifest.get("seeds_file_sha256") != file_hash(seed_path):
        raise ArtifactError("Seed file differs from the completed experiment.")
    seeds = load_seeds(seed_path)
    expected_raw = {
        f"raw/rho-{rho:.2f}/seed-{seed}.json": (seed, rho)
        for rho in config.environment.rho_values for seed in seeds
    }
    if manifest.get("scientific_job_count") != len(expected_raw):
        raise ArtifactError("Manifest does not contain the planned scenario count.")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise ArtifactError("Manifest must enumerate artifact hashes.")
    if manifest.get("schema_version") != 2:
        normalized = {name.replace("\\", "/"): digest for name, digest in files.items()}
        if len(normalized) != len(files):
            raise ArtifactError("Legacy manifest paths collide after normalization.")
        files = normalized
    actual_raw = {path.relative_to(output).as_posix() for path in (output / "raw").rglob("*.json")}
    listed_raw = {name for name in files if name.startswith("raw/")}
    if actual_raw != set(expected_raw) or listed_raw != set(expected_raw):
        raise ArtifactError("Raw population is incomplete, duplicated, or contains unplanned scenarios.")
    for name, expected_hash in files.items():
        path = safe_artifact_path(output, name)
        if not path.is_file() or file_hash(path) != expected_hash:
            raise ArtifactError(f"Missing or modified artifact: {name}")
    actual_traces = {path.relative_to(output).as_posix() for path in (output / "traces").rglob("*.jsonl.gz")}
    if actual_traces != {name for name in files if name.startswith("traces/")}:
        raise ArtifactError("Trace inventory does not match the manifest.")
    if list((output / "failures").glob("*.json")):
        raise ArtifactError("Recorded execution failures require review; automated inference is suspended.")
    trials: list[dict[str, Any]] = []
    seen_scenarios: set[str] = set()
    seen_traces: set[str] = set()
    for name, (seed, rho) in sorted(expected_raw.items()):
        payload = json.loads((output / name).read_text(encoding="utf-8"))
        validate_result_payload(payload, config)
        scientific = payload["scientific_payload"]
        expected_id = f"{config.experiment_id}-rho{rho:.2f}-seed{seed}"
        if (scientific["seed"], scientific["rho"], scientific["scenario_id"]) != (seed, rho, expected_id):
            raise ArtifactError(f"Scenario identity mismatch: {name}")
        if expected_id in seen_scenarios:
            raise ArtifactError(f"Duplicate scenario: {expected_id}")
        seen_scenarios.add(expected_id)
        for trial in scientific["results"]:
            if trial["code_commit"] != manifest.get("code_revision"):
                raise ArtifactError("Paired records mix code revisions.")
            trace = trial["trace_ref"]
            if trace in seen_traces or trace not in files or not trace.startswith("traces/"):
                raise ArtifactError("Each method must reference a distinct manifested trace.")
            seen_traces.add(trace)
            if trial["method_status"] != "completed":
                raise ArtifactError("Non-administrative failure/censoring suspends automated inference.")
        trials.extend(scientific["results"])
    if seen_traces != actual_traces:
        raise ArtifactError("Unreferenced traces in completed experiment.")
    provenance = {
        "experiment_id": config.experiment_id,
        "run_kind": config.run_kind,
        "config_hash": config_digest(config),
        "input_manifest_sha256": file_hash(manifest_path),
        "scenario_count": len(expected_raw),
        "trial_count": len(trials),
        "code_revision": manifest.get("code_revision"),
        "source_tree_sha256": manifest.get("source_tree_sha256"),
        "provenance_level": "snapshotted" if manifest.get("schema_version") == 2 else "legacy; no source/protocol snapshot",
    }
    if manifest.get("schema_version") == 2:
        snapshots = {"config": "provenance/config.json", "seeds": "provenance/seeds.txt"}
        snapshots.update({name: f"provenance/{name}" for name in manifest.get("protocol_files", {})})
        if not manifest.get("source_tree_sha256") or not manifest.get("protocol_files"):
            raise ArtifactError("Version 2 manifests require source and protocol hashes.")
        if any(name not in files for name in snapshots.values()):
            raise ArtifactError("Required provenance snapshot missing from manifest.")
        if json.loads((output / snapshots["config"]).read_text(encoding="utf-8")) != json.loads(json.dumps(config.to_dict())):
            raise ArtifactError("Frozen configuration snapshot mismatch.")
        if file_hash(output / snapshots["seeds"]) != manifest["seeds_file_sha256"]:
            raise ArtifactError("Frozen seed snapshot mismatch.")
        for name, digest in manifest["protocol_files"].items():
            if files.get(f"provenance/{name}") != digest:
                raise ArtifactError("Frozen protocol snapshot mismatch.")
    return trials, provenance


def verify_seal(output: Path) -> dict[str, Any]:
    seal = json.loads((output / "artifact_seal.json").read_text(encoding="utf-8"))
    actual = {p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file() and p.name != "artifact_seal.json"}
    if actual != set(seal["files"]):
        raise ArtifactError("Sealed artifact inventory changed.")
    for name, digest in seal["files"].items():
        if file_hash(safe_artifact_path(output, name)) != digest:
            raise ArtifactError(f"Sealed artifact changed: {name}")
    return {"valid": True, "files": len(actual), "seal_sha256": file_hash(output / "artifact_seal.json")}


def seal_artifact(config: ExperimentConfig, output: Path) -> Path:
    from .runner.checkpoint import atomic_write_json

    ensure_unsealed(output)
    _, provenance = load_validated_trials(config, output)
    for required in ("processed/analysis.json", "REPORT.md"):
        if not (output / required).is_file():
            raise ArtifactError(f"Cannot seal without {required}.")
    analysis = json.loads((output / "processed/analysis.json").read_text(encoding="utf-8"))
    if analysis.get("provenance") != provenance:
        raise ArtifactError("Cannot seal stale analysis.")
    destination = output / "artifact_seal.json"
    files = {p.relative_to(output).as_posix(): file_hash(p) for p in sorted(output.rglob("*")) if p.is_file()}
    atomic_write_json(destination, {"schema_version": 1, "provenance": provenance, "files": files})
    return destination
