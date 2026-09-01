from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

ALLOWED = {
    "NOT_SUPPORTED",
    "DEVELOPMENT_ONLY",
    "SYNTHETIC_ONLY",
    "PILOT_ONLY",
    "CONFIRMATORY_LOCKED",
    "UNKNOWN",
}


def load_claim_matrix(path: str | Path) -> list[dict[str, Any]]:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or "claims" not in raw:
        raise ValueError("Claim matrix must contain a 'claims' list.")
    return list(raw["claims"])


def audit_claims(path: str | Path) -> dict[str, Any]:
    claims = load_claim_matrix(path)
    errors: list[str] = []
    for row in claims:
        status = str(row.get("allowed_wording_status", ""))
        if status not in ALLOWED:
            errors.append(f"{row.get('id')}: invalid status {status!r}")
        if row.get("real_evidence") in {True, "yes"} and status == "NOT_SUPPORTED":
            errors.append(f"{row.get('id')}: real_evidence contradicts NOT_SUPPORTED")
        wording = str(row.get("allowed_wording", "")).lower()
        if "makes agents" in wording and "%" in wording and status != "CONFIRMATORY_LOCKED":
            errors.append(f"{row.get('id')}: over-general efficiency wording")
    return {
        "ok": not errors,
        "n_claims": len(claims),
        "errors": errors,
        "claim_boundary": "Passing this audit means the matrix is internally consistent, not that claims are empirically true.",
    }
