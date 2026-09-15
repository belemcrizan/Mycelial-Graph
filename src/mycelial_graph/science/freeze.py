"""Bind hashes for a completed run without promoting confirmatory status."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from ..runner.trial import code_commit, config_hash
from ..types import load_config


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def bind_run_contract(
    config_path: str | Path,
    output_directory: str | Path,
    project_root: str | Path,
) -> dict[str, Any]:
    config = load_config(config_path)
    output = Path(output_directory).resolve()
    root = Path(project_root).resolve()
    seeds = (config.source_path.parent / config.seeds_file).resolve()
    manifest = output / "manifest.json"
    analysis = output / "processed" / "analysis.json"
    sample_size = output / "processed" / "sample_size.json"
    payload = {
        "protocol_version": config.protocol_version,
        "experiment_id": config.experiment_id,
        "run_kind": config.run_kind,
        "code_commit": code_commit(root),
        "config_hash": config_hash(config),
        "config_path": str(config.source_path),
        "seeds_file": str(seeds),
        "seeds_sha256": _sha256_file(seeds) if seeds.exists() else None,
        "manifest_sha256": _sha256_file(manifest) if manifest.exists() else None,
        "analysis_sha256": _sha256_file(analysis) if analysis.exists() else None,
        "sample_size_sha256": _sha256_file(sample_size) if sample_size.exists() else None,
        "confirmatory_unlocked": False,
        "scientific_status": (
            "PILOT_EVIDENCE_NOT_CONFIRMATORY"
            if config.run_kind == "pilot"
            else f"RUN_KIND_{config.run_kind.upper()}_NOT_PROMOTED"
        ),
    }
    return payload


def write_contract(destination: str | Path, payload: dict[str, Any]) -> Path:
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
