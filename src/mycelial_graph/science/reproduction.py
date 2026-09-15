"""Post-execution verification of the historical MG-EXP-V1 confirmatory result.

This is not a pre-execution authorization gate. A passing historical reproduction
does not unlock a new confirmatory execution.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .canonical_bytes import (
        CONFIRMATORY_METHOD_TRIALS,
        CONFIRMATORY_N,
        CONFIRMATORY_SCIENTIFIC_JOBS,
        FROZEN_CONFIG_HASH,
        FROZEN_SEED_SHA256,
        HISTORICAL_BINARY_SEAL_ARTIFACTS,
        HISTORICAL_CRLF_SEAL_SHA256,
        HISTORICAL_TEXT_SEAL_ARTIFACTS,
        PRIMARY_ESTIMATE,
        PROTOCOL_VERSION,
        RESULT_STATE,
        SealCheck,
        SealIdentity,
        human_seal_line,
        verify_frozen_seed_identity,
        verify_historical_text_seal,
    verify_raw_bytes_seal,
)

HISTORICAL_FREEZE_RELATIVE = "experiments/v1/artifacts/CONFIRMATORY_FREEZE.json"
HISTORICAL_FREEZE_SUPPLEMENT_RELATIVE = "experiments/v1/artifacts/CONFIRMATORY_FREEZE_SUPPLEMENT.json"
HISTORICAL_EVIDENCE_RELATIVE = "experiments/v1/artifacts/confirmatory/CONFIRMATORY_EVIDENCE.json"
REPRODUCTION_SUPPLEMENT_RELATIVE = (
    "experiments/v1/artifacts/confirmatory/CONFIRMATORY_REPRODUCTION_SUPPLEMENT.json"
)
SEALED_DIR_RELATIVE = "experiments/v1/artifacts/confirmatory"

SEALED_PATH_FOR_EVIDENCE_KEY = {
    "REPORT.md": "REPORT.md",
    "manifest.json": "manifest.json",
    "processed/analysis.json": "analysis.json",
    "figures/recovery_by_rho.png": "figures/recovery_by_rho.png",
    "figures/regret_by_rho.png": "figures/regret_by_rho.png",
}

REQUIRED_SUPPLEMENT_FIELDS = (
    "schema_version",
    "document_type",
    "protocol_version",
    "supplement_to",
    "reason",
    "affected_artifacts",
    "scientific_content_changed",
    "result_state",
    "primary_estimate",
    "required_confirmatory_pairs",
    "seeds_sha256",
    "confirmatory_config_hash",
    "original_evidence_immutable",
    "repairs_provenance_interpretation_only",
)


@dataclass
class HistoricalVerification:
    errors: list[str] = field(default_factory=list)
    seal_checks: list[SealCheck] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and all(check.ok for check in self.seal_checks)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_historical_confirmatory_freeze(root: Path) -> list[str]:
    """Recognize the historical freeze schema. Do not require schema_version=1."""
    errors: list[str] = []
    freeze_path = root / HISTORICAL_FREEZE_RELATIVE
    if not freeze_path.is_file():
        return [f"Historical freeze missing: {HISTORICAL_FREEZE_RELATIVE}"]
    freeze = _load_json(freeze_path)
    if freeze.get("schema_version") == 1 or freeze.get("status") == "frozen":
        errors.append(
            "Historical freeze was rewritten into the modern execution schema. "
            "The original pre-execution record must remain unmodified."
        )
    if freeze.get("protocol_version") != PROTOCOL_VERSION:
        errors.append(
            f"Historical freeze protocol_version is {freeze.get('protocol_version')!r}, "
            f"expected {PROTOCOL_VERSION}."
        )
    if freeze.get("required_confirmatory_pairs") != CONFIRMATORY_N:
        errors.append(
            f"Historical freeze N is {freeze.get('required_confirmatory_pairs')!r}, "
            f"expected {CONFIRMATORY_N}."
        )
    if freeze.get("confirmatory_config_hash") != FROZEN_CONFIG_HASH:
        errors.append("Historical freeze confirmatory_config_hash does not match the frozen config.")
    if freeze.get("seeds_sha256") != FROZEN_SEED_SHA256:
        errors.append("Historical freeze seeds_sha256 does not match the frozen seed identity.")
    if freeze.get("status") != "SAMPLE_SIZE_RECORDED_SEEDS_SELECTED_CONFIRMATORY_NOT_EXECUTED":
        errors.append(
            "Historical freeze status is not the recorded pre-execution status. "
            "Do not mutate it to 'frozen'."
        )
    if freeze.get("confirmatory_executed") is not False:
        errors.append(
            "Historical freeze confirmatory_executed must remain false; execution is "
            "recorded in CONFIRMATORY_EVIDENCE.json, not by rewriting the freeze."
        )
    supplement_path = root / HISTORICAL_FREEZE_SUPPLEMENT_RELATIVE
    if not supplement_path.is_file():
        errors.append(f"Freeze supplement missing: {HISTORICAL_FREEZE_SUPPLEMENT_RELATIVE}")
        return errors
    supplement = _load_json(supplement_path)
    if supplement.get("supplement_to") != HISTORICAL_FREEZE_RELATIVE:
        errors.append("Freeze supplement does not point at the historical freeze.")
    if supplement.get("protocol_version") != PROTOCOL_VERSION:
        errors.append("Freeze supplement protocol_version mismatch.")
    if supplement.get("required_confirmatory_pairs") != CONFIRMATORY_N:
        errors.append("Freeze supplement N mismatch.")
    if supplement.get("seeds_sha256") != FROZEN_SEED_SHA256:
        errors.append("Freeze supplement seeds_sha256 mismatch.")
    if supplement.get("confirmatory_config_hash") != FROZEN_CONFIG_HASH:
        errors.append("Freeze supplement confirmatory_config_hash mismatch.")
    if supplement.get("audit_commit") != "5f314d2dfb15f508dfd4e630e8c0e49031e60c6a":
        errors.append("Freeze supplement audit_commit is not the recorded pre-execution commit.")
    purpose = str(supplement.get("purpose") or "")
    if "does not alter, reinterpret, or relax" not in purpose.lower() and "adds hashes only" not in purpose.lower():
        errors.append("Freeze supplement purpose no longer states that it is additive-only.")
    return errors


def verify_reproduction_supplement(root: Path) -> list[str]:
    path = root / REPRODUCTION_SUPPLEMENT_RELATIVE
    if not path.is_file():
        return [f"Reproduction supplement missing: {REPRODUCTION_SUPPLEMENT_RELATIVE}"]
    try:
        payload = _load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"Reproduction supplement is malformed: {exc}"]
    if not isinstance(payload, dict):
        return ["Reproduction supplement must be a JSON object."]
    errors: list[str] = []
    missing = [name for name in REQUIRED_SUPPLEMENT_FIELDS if name not in payload]
    if missing:
        errors.append(f"Reproduction supplement missing fields: {missing}")
        return errors
    if payload.get("document_type") != "CONFIRMATORY_REPRODUCTION_SUPPLEMENT":
        errors.append("Reproduction supplement document_type is invalid.")
    if payload.get("schema_version") != 1:
        errors.append("Reproduction supplement schema_version must be 1.")
    if payload.get("protocol_version") != PROTOCOL_VERSION:
        errors.append("Reproduction supplement protocol_version mismatch.")
    if payload.get("supplement_to") != HISTORICAL_EVIDENCE_RELATIVE:
        errors.append("Reproduction supplement must reference the immutable historical evidence.")
    if payload.get("scientific_content_changed") is not False:
        errors.append("Reproduction supplement must record scientific_content_changed=false.")
    if payload.get("result_state") != RESULT_STATE:
        errors.append("Reproduction supplement must not change result_state from REFUTED.")
    if abs(float(payload.get("primary_estimate")) - PRIMARY_ESTIMATE) > 1e-12:
        errors.append("Reproduction supplement primary_estimate does not match the historical value.")
    if payload.get("required_confirmatory_pairs") != CONFIRMATORY_N:
        errors.append("Reproduction supplement N mismatch.")
    if payload.get("seeds_sha256") != FROZEN_SEED_SHA256:
        errors.append("Reproduction supplement must preserve the frozen seed hash.")
    if payload.get("confirmatory_config_hash") != FROZEN_CONFIG_HASH:
        errors.append("Reproduction supplement must preserve the frozen config hash.")
    if payload.get("original_evidence_immutable") is not True:
        errors.append("Reproduction supplement must state that original evidence remains immutable.")
    if payload.get("repairs_provenance_interpretation_only") is not True:
        errors.append("Reproduction supplement must state that it repairs provenance interpretation only.")
    artifacts = payload.get("affected_artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != 3:
        errors.append("Reproduction supplement must list the three historical text artifacts.")
        return errors
    seen: set[str] = set()
    for row in artifacts:
        if not isinstance(row, dict):
            errors.append("Reproduction supplement artifact rows must be objects.")
            continue
        name = row.get("artifact")
        seen.add(str(name))
        expected = HISTORICAL_CRLF_SEAL_SHA256.get(str(name))
        if expected is None:
            errors.append(f"Unknown supplement artifact: {name!r}")
            continue
        if row.get("historical_crlf_sha256") != expected:
            errors.append(f"Supplement historical_crlf_sha256 for {name} does not match the sealed hash.")
        if row.get("exact_historical_crlf_reconstruction") is not True:
            errors.append(f"Supplement must record successful CRLF reconstruction for {name}.")
    missing_artifacts = HISTORICAL_TEXT_SEAL_ARTIFACTS - seen
    if missing_artifacts:
        errors.append(f"Reproduction supplement missing artifacts: {sorted(missing_artifacts)}")
    return errors


def verify_sealed_artifacts(root: Path, evidence: dict[str, Any]) -> list[SealCheck]:
    sealed = root / SEALED_DIR_RELATIVE
    hashes = evidence.get("sealed_artifact_sha256") or {}
    checks: list[SealCheck] = []
    for relative, filename in SEALED_PATH_FOR_EVIDENCE_KEY.items():
        path = sealed / filename
        expected = hashes.get(relative)
        if expected is None:
            checks.append(
                SealCheck(
                    artifact=relative,
                    identity=SealIdentity.MISMATCH,
                    expected_sha256="",
                    repository_raw_sha256="",
                    canonical_text_sha256=None,
                    reconstructed_crlf_sha256=None,
                    message=f"{relative}: missing from sealed_artifact_sha256",
                )
            )
            continue
        if not path.is_file():
            checks.append(
                SealCheck(
                    artifact=relative,
                    identity=SealIdentity.MISMATCH,
                    expected_sha256=expected,
                    repository_raw_sha256="",
                    canonical_text_sha256=None,
                    reconstructed_crlf_sha256=None,
                    message=f"{relative}: missing file {path}",
                )
            )
            continue
        if relative in HISTORICAL_TEXT_SEAL_ARTIFACTS:
            checks.append(verify_historical_text_seal(path, expected, relative))
        elif relative in HISTORICAL_BINARY_SEAL_ARTIFACTS:
            checks.append(verify_raw_bytes_seal(path, expected, relative))
        else:
            checks.append(verify_raw_bytes_seal(path, expected, relative))
    return checks


def verify_historical_confirmatory_evidence(root: Path) -> HistoricalVerification:
    """Does the repository faithfully reproduce and audit the historical result?"""
    result = HistoricalVerification()
    root = Path(root).resolve()
    result.errors.extend(verify_historical_confirmatory_freeze(root))
    result.errors.extend(verify_reproduction_supplement(root))

    evidence_path = root / HISTORICAL_EVIDENCE_RELATIVE
    if not evidence_path.is_file():
        result.errors.append(f"Historical evidence missing: {HISTORICAL_EVIDENCE_RELATIVE}")
        return result
    evidence = _load_json(evidence_path)
    if evidence.get("protocol_version") != PROTOCOL_VERSION:
        result.errors.append("Historical evidence protocol_version mismatch.")
    state = (evidence.get("result_state") or {}).get("state")
    if state != RESULT_STATE:
        result.errors.append(f"Historical result_state is {state!r}, expected {RESULT_STATE}.")
    estimate = (evidence.get("primary_contrast") or {}).get("estimate")
    try:
        if abs(float(estimate) - PRIMARY_ESTIMATE) > 1e-12:
            result.errors.append(
                f"Historical primary estimate is {estimate!r}, expected {PRIMARY_ESTIMATE}."
            )
    except (TypeError, ValueError):
        result.errors.append(f"Historical primary estimate is not numeric: {estimate!r}")
    if evidence.get("config_hash") != FROZEN_CONFIG_HASH:
        result.errors.append("Historical evidence config_hash mismatch.")
    if evidence.get("seeds_file_sha256") != FROZEN_SEED_SHA256:
        result.errors.append("Historical evidence seeds_file_sha256 mismatch.")
    if int(evidence.get("scientific_job_count", -1)) != CONFIRMATORY_SCIENTIFIC_JOBS:
        result.errors.append(
            f"scientific_job_count is {evidence.get('scientific_job_count')!r}, "
            f"expected {CONFIRMATORY_SCIENTIFIC_JOBS} (N × rho values)."
        )
    pairs = (evidence.get("frozen_contrast_integrity") or {}).get("primary_pairs")
    if pairs != CONFIRMATORY_N:
        result.errors.append(f"primary_pairs is {pairs!r}, expected {CONFIRMATORY_N}.")
    if "independent" in str(evidence.get("reproduction_status", "")).lower() and "no independent" not in str(
        evidence.get("reproduction_status", "")
    ).lower():
        result.errors.append("Historical evidence must not claim independent reproduction.")

    seed_path = root / "experiments" / "v1" / "seeds.confirmatory.txt"
    if not seed_path.is_file():
        result.errors.append("Confirmatory seed file is missing.")
    else:
        seed_check = verify_frozen_seed_identity(seed_path, FROZEN_SEED_SHA256)
        if not seed_check.ok:
            result.errors.append(seed_check.message)
        elif seed_check.identity is SealIdentity.HISTORICAL_EOL_EQUIVALENT:
            result.notes.append(seed_check.message)

    from ..runner.trial import config_hash
    from ..types import load_config

    config = load_config(root / "experiments" / "v1" / "config.confirmatory.yaml")
    observed_config = config_hash(config)
    if observed_config != FROZEN_CONFIG_HASH:
        result.errors.append(
            f"Frozen config hash mismatch: {observed_config}, expected {FROZEN_CONFIG_HASH}."
        )

    result.seal_checks = verify_sealed_artifacts(root, evidence)
    for check in result.seal_checks:
        if check.identity is SealIdentity.HISTORICAL_EOL_EQUIVALENT:
            result.notes.append(human_seal_line(check))
    return result


def verify_historical_confirmatory_replay_authorization(config: Any) -> list[str]:
    """Allow --full replay of the already-executed frozen experiment.

    This is not a new confirmatory unlock. It still binds N, seeds, and config
    to the historical freeze and requires sealed REFUTED evidence to exist.
    """
    root = config.source_path.parents[2]
    verification = verify_historical_confirmatory_evidence(root)
    errors = list(verification.errors)
    errors.extend(check.message for check in verification.seal_checks if not check.ok)
    if getattr(config, "run_kind", None) != "confirmatory":
        errors.append("Historical confirmatory replay requires run_kind=confirmatory.")
    if getattr(config, "protocol_version", None) != PROTOCOL_VERSION:
        errors.append("Historical confirmatory replay requires protocol MG-EXP-V1.")
    return errors


def method_trial_count(*, n_pairs: int, n_rho: int, n_methods: int) -> int:
    return n_pairs * n_rho * n_methods


def scientific_job_count(*, n_pairs: int, n_rho: int) -> int:
    return n_pairs * n_rho


# Silence unused-import concern for documented constants re-exported here.
__all__ = [
    "CONFIRMATORY_METHOD_TRIALS",
    "CONFIRMATORY_N",
    "CONFIRMATORY_SCIENTIFIC_JOBS",
    "HistoricalVerification",
    "method_trial_count",
    "scientific_job_count",
    "verify_historical_confirmatory_evidence",
    "verify_historical_confirmatory_freeze",
    "verify_historical_confirmatory_replay_authorization",
    "verify_reproduction_supplement",
]
