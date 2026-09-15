"""Machine-verifiable V1 confirmatory-readiness invariants.

A deterministic auditor cannot detect arbitrary natural-language contradictions. It can,
however, refuse to let documentation assert machine-checkable state that is false. Each
invariant declared under ``v1_readiness_invariants`` in the claim matrix is checked against
the actual repository: file existence, seed counts, hashes, seed-population disjointness,
frozen-config binding, and required literal records.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_seeds(path: Path) -> list[int]:
    return [
        int(line.strip())
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]


def _config_hash(path: Path) -> str:
    from ..runner.trial import config_hash
    from ..types import load_config

    return config_hash(load_config(path))


def _check(results: list[dict[str, Any]], name: str, ok: bool, detail: Any) -> bool:
    results.append({"check": name, "ok": bool(ok), "detail": detail})
    return bool(ok)


def _verify_invariant(
    invariant: dict[str, Any],
    root: Path,
    results: list[dict[str, Any]],
) -> None:
    identifier = invariant.get("id", "?")
    claim = invariant.get("claim", "?")
    prefix = f"{identifier}:{claim}"
    requires = invariant.get("requires") or {}

    if "allowed_by_v1_confirmatory" in invariant:
        _check(
            results,
            f"{prefix}:allowed_by_v1_confirmatory",
            invariant["allowed_by_v1_confirmatory"] is False,
            "V1 confirmatory evidence must not be allowed to support this claim.",
        )
        return

    freeze_path = root / requires["freeze"] if "freeze" in requires else None
    freeze = json.loads(freeze_path.read_text(encoding="utf-8")) if freeze_path else {}

    if "file" in requires:
        target = root / requires["file"]
        exists = target.exists()
        _check(results, f"{prefix}:file_exists", exists == requires.get("file_exists", True), str(target))
        if not exists:
            return
        if "sha256" in requires:
            observed = _sha256_file(target)
            _check(
                results,
                f"{prefix}:sha256",
                observed == requires["sha256"],
                {"expected": requires["sha256"], "observed": observed},
            )
            if requires.get("hash_matches_freeze") and freeze:
                _check(
                    results,
                    f"{prefix}:hash_matches_freeze",
                    observed == freeze.get(requires.get("freeze_hash_field", "seeds_sha256")),
                    {"freeze": freeze.get(requires.get("freeze_hash_field", "seeds_sha256"))},
                )
        if "count" in requires:
            seeds = _read_seeds(target)
            _check(
                results,
                f"{prefix}:count",
                len(seeds) == requires["count"],
                {"expected": requires["count"], "observed": len(seeds)},
            )
            _check(results, f"{prefix}:unique", len(set(seeds)) == len(seeds), len(set(seeds)))
            if freeze and "freeze_count_field" in requires:
                _check(
                    results,
                    f"{prefix}:count_matches_freeze",
                    freeze.get(requires["freeze_count_field"]) == len(seeds),
                    {"freeze": freeze.get(requires["freeze_count_field"])},
                )
        if "prefix_of" in requires:
            seeds = _read_seeds(target)
            pool = _read_seeds(root / requires["prefix_of"])
            _check(
                results,
                f"{prefix}:is_unfiltered_pool_prefix",
                seeds == pool[: len(seeds)],
                {"pool_size": len(pool), "selected": len(seeds)},
            )
        for other in requires.get("disjoint_from", []):
            seeds = set(_read_seeds(target))
            overlap = sorted(seeds & set(_read_seeds(root / other)))
            _check(results, f"{prefix}:disjoint_from:{other}", not overlap, {"overlap": overlap})
        for needle in requires.get("contains", []):
            _check(
                results,
                f"{prefix}:contains:{needle[:48]}",
                needle in target.read_text(encoding="utf-8"),
                None,
            )
        for field, expected in (requires.get("json_fields") or {}).items():
            payload = json.loads(target.read_text(encoding="utf-8"))
            _check(
                results,
                f"{prefix}:json:{field}",
                payload.get(field) == expected,
                {"expected": expected, "observed": payload.get(field)},
            )

    if "config" in requires:
        config_path = root / requires["config"]
        observed = _config_hash(config_path)
        if "config_hash" in requires:
            _check(
                results,
                f"{prefix}:config_hash",
                observed == requires["config_hash"],
                {"expected": requires["config_hash"], "observed": observed},
            )
        if requires.get("hash_matches_freeze") and freeze:
            field = requires.get("freeze_hash_field", "confirmatory_config_hash")
            _check(
                results,
                f"{prefix}:config_hash_matches_freeze",
                observed == freeze.get(field),
                {"freeze": freeze.get(field)},
            )


def audit_v1_invariants(matrix_path: str | Path, project_root: str | Path) -> dict[str, Any]:
    """Verify every declared V1 readiness invariant against the repository state."""
    root = Path(project_root).resolve()
    raw = yaml.safe_load(Path(matrix_path).read_text(encoding="utf-8"))
    invariants = list((raw or {}).get("v1_readiness_invariants") or [])
    results: list[dict[str, Any]] = []
    for invariant in invariants:
        _verify_invariant(invariant, root, results)
    failures = [row for row in results if not row["ok"]]
    return {
        "ok": not failures,
        "n_invariants": len(invariants),
        "n_checks": len(results),
        "checks": results,
        "failures": failures,
        "claim_boundary": (
            "These invariants verify machine-checkable repository state only. "
            "They do not verify that any scientific claim is empirically true."
        ),
    }
