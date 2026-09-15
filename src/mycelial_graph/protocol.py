"""Seed isolation and a verifiable, committed V1 confirmatory freeze."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .artifacts import config_digest, file_hash, source_digest, safe_artifact_path
from .types import ExperimentConfig, load_config


PROTOCOL_FILES = ("EXPERIMENT_PROTOCOL_V1.md", "ANALYSIS_PLAN.md", "experiment.schema.json")


def protocol_files(directory: Path) -> tuple[str, ...]:
    return (*PROTOCOL_FILES, *(p.name for p in sorted(directory.glob("PROTOCOL_AMENDMENT_*.md"))))


def validate_phase_seeds(config: ExperimentConfig) -> list[str]:
    from .validation import load_seeds

    errors = []
    directory = config.source_path.parent
    populations = {}
    for kind in ("development", "pilot", "confirmatory.pool"):
        path = directory / f"seeds.{kind}.txt"
        if path.exists():
            try:
                populations[kind] = set(load_seeds(path))
            except ValueError as exc:
                errors.append(str(exc))
    kinds = list(populations)
    if config.run_kind in {"pilot", "confirmatory"} and len(populations.get("pilot", ())) != 20:
        errors.append("MG-EXP-V1 requires the complete 20-seed independent pilot.")
    if config.run_kind == "confirmatory" and len(populations.get("confirmatory.pool", ())) != 500:
        errors.append("MG-EXP-V1 requires its original 500-seed pool; extension requires an amendment.")
    for i, left in enumerate(kinds):
        for right in kinds[i + 1:]:
            if populations[left] & populations[right]:
                errors.append(f"Seed overlap between {left} and {right}.")
    requested = directory / config.seeds_file
    if requested.exists():
        try:
            seeds = set(load_seeds(requested))
            allowed_kind = "confirmatory.pool" if config.run_kind == "confirmatory" else config.run_kind
            for kind, population in populations.items():
                if kind != allowed_kind and seeds & population:
                    errors.append(f"Requested {config.run_kind} seeds overlap {kind}.")
            if config.run_kind == "pilot" and seeds != populations.get("pilot"):
                errors.append("Pilot must use the complete precommitted pilot population.")
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def validate_confirmatory_freeze(config: ExperimentConfig) -> list[str]:
    """An arbitrary seed file must not unlock confirmatory inference.

    The review record is a commit before outcomes, not an interactive approval.
    See experiments/v1/FREEZE_CONTRACT.md for the complete contract.
    """
    from .validation import load_seeds

    directory = config.source_path.parent
    root = config.source_path.parents[2]
    freeze_path = directory / "CONFIRMATORY_FREEZE.json"
    if not freeze_path.is_file():
        return ["Confirmatory execution locked: missing committed CONFIRMATORY_FREEZE.json and reviewed sample-size evidence."]
    try:
        freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
        if freeze.get("schema_version") != 1 or freeze.get("status") != "frozen":
            raise ValueError("Freeze record must have schema_version=1 and status=frozen.")
        n = freeze["required_confirmatory_pairs"]
        if type(n) is not int or not 2 <= n <= 500:
            raise ValueError("Required N must be an integer from 2 to 500; otherwise an amendment is required.")
        seeds = load_seeds(directory / config.seeds_file)
        pool = load_seeds(directory / "seeds.confirmatory.pool.txt")
        if len(seeds) != n or seeds != pool[:n]:
            raise ValueError("Confirmatory seeds must be exactly the first N entries of the frozen pool.")
        if freeze["config_hash"] != config_digest(config) or freeze["source_tree_sha256"] != source_digest(root):
            raise ValueError("Code or confirmatory configuration changed after freeze.")
        required = [*protocol_files(directory), "SAMPLE_SIZE_ADDENDUM.md", "seeds.confirmatory.pool.txt", config.seeds_file]
        for name in required:
            if freeze["files"].get(name) != file_hash(directory / name):
                raise ValueError(f"Frozen file mismatch: {name}")
        addendum = (directory / "SAMPLE_SIZE_ADDENDUM.md").read_text(encoding="utf-8")
        if "PENDING PILOT" in addendum or "TBD" in addendum:
            raise ValueError("Sample-size addendum is still incomplete.")
        # All freeze inputs must already be versioned with unchanged bytes.
        for path in [freeze_path, config.source_path, *(directory / name for name in required), *sorted((root / "src").rglob("*.py"))]:
            relative = path.resolve().relative_to(root.resolve()).as_posix()
            committed = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root, stderr=subprocess.DEVNULL)
            if committed != path.read_bytes():
                raise ValueError(f"Freeze input is not committed: {relative}")
        from .artifacts import verify_seal, load_validated_trials
        pilot_output = safe_artifact_path(root, freeze["pilot_artifact_path"])
        verify_seal(pilot_output)
        if file_hash(pilot_output / "artifact_seal.json") != freeze["pilot_artifact_seal_sha256"]:
            raise ValueError("Pilot artifact seal mismatch.")
        pilot_config = load_config(directory / "config.pilot.yaml")
        _, pilot_provenance = load_validated_trials(pilot_config, pilot_output)
        if pilot_provenance["source_tree_sha256"] != freeze["source_tree_sha256"]:
            raise ValueError("Source differs from the independent pilot; document an amendment.")
        scientific_sections = ("graph", "horizon", "environment", "mycelial", "structured_sw_ucb", "analysis", "methods")
        if any(getattr(config, key) != getattr(pilot_config, key) for key in scientific_sections):
            raise ValueError("Pilot and confirmatory scientific configurations differ.")
        power_path = pilot_output / "processed" / "sample_size.json"
        power = json.loads(power_path.read_text(encoding="utf-8"))
        if (power.get("status") != "planning_estimate" or power.get("target_power") != 0.8
                or power.get("provenance") != pilot_provenance
                or power.get("required_confirmatory_pairs", 501) > n):
            raise ValueError("No eligible pilot sample-size estimate supporting the chosen N.")
        review = safe_artifact_path(root, freeze["power_review_path"])
        if file_hash(review) != freeze["power_review_sha256"]:
            raise ValueError("Power review hash mismatch.")
        for path in (review, pilot_output / "artifact_seal.json"):
            relative = path.relative_to(root).as_posix()
            committed = subprocess.check_output(["git", "show", f"HEAD:{relative}"], cwd=root, stderr=subprocess.DEVNULL)
            if committed != path.read_bytes():
                raise ValueError(f"Review or pilot seal not committed: {relative}")
    except (KeyError, TypeError, ValueError, OSError, subprocess.CalledProcessError) as exc:
        return [f"Confirmatory freeze invalid: {exc}"]
    return []
