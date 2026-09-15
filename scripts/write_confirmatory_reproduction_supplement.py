"""Write the append-only V1 confirmatory reproduction supplement.

The historical CONFIRMATORY_EVIDENCE.json is never modified. This script records
the CRLF/LF forensic reconstruction against the current repository bytes.

Usage (from repository root):

    python scripts/write_confirmatory_reproduction_supplement.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mycelial_graph.science.canonical_bytes import (  # noqa: E402
    FROZEN_CONFIG_HASH,
    FROZEN_SEED_SHA256,
    HISTORICAL_CRLF_SEAL_SHA256,
    PRIMARY_ESTIMATE,
    PROTOCOL_VERSION,
    RESULT_STATE,
    canonicalize_text_bytes,
    lf_to_crlf,
    sha256_bytes,
    sha256_canonical_text,
    sha256_raw,
    sha256_raw_file,
    verify_historical_text_seal,
    verify_raw_bytes_seal,
)

SEALED = ROOT / "experiments" / "v1" / "artifacts" / "confirmatory"
DESTINATION = SEALED / "CONFIRMATORY_REPRODUCTION_SUPPLEMENT.json"
PATHS = {
    "REPORT.md": SEALED / "REPORT.md",
    "manifest.json": SEALED / "manifest.json",
    "processed/analysis.json": SEALED / "analysis.json",
}


def main() -> int:
    if DESTINATION.exists():
        print(f"ERROR: {DESTINATION.relative_to(ROOT)} already exists; refusing to overwrite.", file=sys.stderr)
        return 2
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    created = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    affected = []
    for artifact, path in PATHS.items():
        raw = path.read_bytes()
        canonical = canonicalize_text_bytes(raw)
        reconstructed = lf_to_crlf(canonical)
        expected = HISTORICAL_CRLF_SEAL_SHA256[artifact]
        check = verify_historical_text_seal(path, expected, artifact)
        affected.append(
            {
                "artifact": artifact,
                "historical_crlf_sha256": expected,
                "repository_lf_sha256": sha256_raw(raw),
                "canonical_text_sha256": sha256_canonical_text(raw),
                "reconstructed_crlf_sha256": sha256_bytes(reconstructed),
                "normalization_method": "CRLF_or_CR -> LF; historical reconstruction canonical LF -> CRLF",
                "exact_historical_crlf_reconstruction": sha256_bytes(reconstructed) == expected,
                "seal_identity": check.identity.value,
            }
        )
        if not check.ok or sha256_bytes(reconstructed) != expected:
            print(f"ERROR: reconstruction failed for {artifact}: {check.message}", file=sys.stderr)
            return 2
    png_ok = True
    png_rows = []
    evidence = json.loads((SEALED / "CONFIRMATORY_EVIDENCE.json").read_text(encoding="utf-8"))
    for name in ("figures/recovery_by_rho.png", "figures/regret_by_rho.png"):
        path = SEALED / name
        expected = evidence["sealed_artifact_sha256"][name]
        check = verify_raw_bytes_seal(path, expected, name)
        png_rows.append(
            {
                "artifact": name,
                "sha256": sha256_raw_file(path),
                "identity": check.identity.value,
            }
        )
        png_ok = png_ok and check.ok
    payload = {
        "schema_version": 1,
        "document_type": "CONFIRMATORY_REPRODUCTION_SUPPLEMENT",
        "protocol_version": PROTOCOL_VERSION,
        "supplement_to": "experiments/v1/artifacts/confirmatory/CONFIRMATORY_EVIDENCE.json",
        "historical_freeze": "experiments/v1/artifacts/CONFIRMATORY_FREEZE.json",
        "historical_freeze_supplement": "experiments/v1/artifacts/CONFIRMATORY_FREEZE_SUPPLEMENT.json",
        "historical_execution_commit": "5f314d2dfb15f508dfd4e630e8c0e49031e60c6a",
        "reason": (
            "Record the CRLF/LF byte-representation discrepancy for historically sealed "
            "text artifacts and make cross-platform reproduction auditable. The historical "
            "hashes were valid for the CRLF byte representation that was sealed. The "
            "repository stores LF. Byte representation changed; scientific textual content did not."
        ),
        "classification": (
            "reproducibility/provenance correction with no change to scientific result or claim boundary"
        ),
        "affected_artifacts": affected,
        "png_artifacts": png_rows,
        "png_artifacts_exact_byte_match": png_ok,
        "scientific_content_changed": False,
        "result_state": RESULT_STATE,
        "primary_estimate": PRIMARY_ESTIMATE,
        "required_confirmatory_pairs": 97,
        "seeds_sha256": FROZEN_SEED_SHA256,
        "confirmatory_config_hash": FROZEN_CONFIG_HASH,
        "created_at_utc": created,
        "audit_base_revision": commit,
        "original_evidence_immutable": True,
        "repairs_provenance_interpretation_only": True,
        "statements": [
            "The original CONFIRMATORY_EVIDENCE.json remains immutable.",
            "This supplement repairs provenance/reproduction interpretation only.",
            "The historical hashes were valid for the CRLF byte representation that was sealed.",
            "Byte representation changed; scientific textual content did not.",
            "The V1 confirmatory result remains REFUTED.",
            "Frozen N, seeds, and confirmatory config hash are unchanged.",
        ],
    }
    DESTINATION.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(DESTINATION.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
