"""Deterministic scientific-state and document-consistency audit.

This is not a natural-language theorem prover. It checks:

* ``research/state.json`` against the filesystem and the submission receipt;
* moratorium/submission coupling;
* explicit stale phrases that previously contradicted confirmatory state;
* declared CPU metrics against ``research/runtime.json``;
* presence of required claim-boundary markers.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

STALE_NOT_EXECUTED = "Confirmatory execution has not been run."
STALE_MISSING_SEEDS = "deliberately points to a missing seeds.confirmatory.txt"
STALE_NO_RESULT = "No V1 confirmatory result is available."

STALE_CURRENT_STATE_PHRASES: tuple[tuple[str, str], ...] = (
    ("stale_not_executed", STALE_NOT_EXECUTED.lower()),
    ("stale_missing_seeds_as_current", STALE_MISSING_SEEDS.lower()),
    ("stale_no_result", STALE_NO_RESULT.lower()),
)

FORBIDDEN_HIERARCHY_ONLY_ASSERTIONS: tuple[str, ...] = (
    "hierarchical representation caused the loss",
    "hierarchical representation caused the failure",
    "hierarchical pooling is generally worse",
    "hierarchical methods generally fail",
)

REQUIRED_UNSUPPORTED_ATTRIBUTION = (
    "Attribution of the V1 performance difference to hierarchical representation alone"
)

REQUIRED_EQ_B_HONEST_STATUS = (
    "Post-confirmatory equalization triage identified a material mismatch in effective policy scale"
)

MORATORIUM_EXIT_MARKER = (
    "Paper A has been submitted and submission state/receipt has been recorded."
)

README_STATE_KEYS = (
    "confirmatory.executed",
    "confirmatory.status",
    "confirmatory.n",
    "equalization_triage.status",
    "paper_a.submitted",
    "moratorium.active",
)

CPU_HOUR_TOKEN = re.compile(r"(0\.11[12]|0\.122|0\.12)\b")
CPU_SECONDS_TOKEN = re.compile(r"(402(?:\.0)?)\b")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _check(results: list[dict[str, Any]], name: str, ok: bool, detail: Any) -> None:
    results.append({"check": name, "ok": bool(ok), "detail": detail})


def _readme_state_block(text: str) -> dict[str, str]:
    match = re.search(
        r"<!--\s*canonical-scientific-state\b(.*?)-->",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return {}
    parsed: dict[str, str] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def find_stale_confirmatory_phrases(text: str) -> list[dict[str, str]]:
    """Return current-state contradictions that previously survived in README prose."""
    lowered = text.lower()
    hits: list[dict[str, str]] = []
    for identifier, needle in STALE_CURRENT_STATE_PHRASES:
        if needle in lowered:
            hits.append({"id": identifier, "phrase": needle})
    return hits


def find_hierarchy_only_assertions(text: str) -> list[str]:
    hits: list[str] = []
    for segment in re.split(r"[.!?;\n]+", text):
        lowered = segment.lower()
        if any(
            cue in lowered
            for cue in (
                "not ",
                "n't",
                "no ",
                "never",
                "cannot",
                "unsupported",
                "does not",
                "do not",
                "must not",
                "without",
            )
        ):
            continue
        for phrase in FORBIDDEN_HIERARCHY_ONLY_ASSERTIONS:
            if phrase in lowered:
                hits.append(phrase)
    return hits


def _declared_runtime_values(text: str) -> dict[str, list[str]]:
    hours: list[str] = []
    for match in CPU_HOUR_TOKEN.finditer(text):
        window = text[match.start() : match.end() + 64]
        if re.search(r"CPU[- ]h", window, flags=re.IGNORECASE):
            hours.append(match.group(1))
    seconds: list[str] = []
    for match in CPU_SECONDS_TOKEN.finditer(text):
        window = text[match.start() : match.end() + 32]
        if re.search(r"CPU[- ]s", window, flags=re.IGNORECASE):
            seconds.append(match.group(1))
    return {"cpu_hours": hours, "cpu_seconds": seconds}


def audit_scientific_state(
    project_root: str | Path,
    *,
    readme_text: str | None = None,
    paper_text: str | None = None,
    moratorium_text: str | None = None,
) -> dict[str, Any]:
    root = Path(project_root).resolve()
    results: list[dict[str, Any]] = []
    state_path = root / "research" / "state.json"
    runtime_path = root / "research" / "runtime.json"
    receipt_path = root / "paper" / "SUBMISSION_RECEIPT.json"

    _check(results, "state_file_exists", state_path.is_file(), str(state_path))
    _check(results, "runtime_file_exists", runtime_path.is_file(), str(runtime_path))
    _check(results, "receipt_file_exists", receipt_path.is_file(), str(receipt_path))
    if not (state_path.is_file() and runtime_path.is_file() and receipt_path.is_file()):
        failures = [row for row in results if not row["ok"]]
        return {"ok": False, "checks": results, "failures": failures}

    state = load_json(state_path)
    runtime = load_json(runtime_path)
    receipt = load_json(receipt_path)
    confirmatory = state.get("confirmatory") or {}
    paper_a = state.get("paper_a") or {}
    eq = state.get("equalization_triage") or {}
    moratorium = state.get("moratorium") or {}

    seed_path = root / str(confirmatory.get("seed_file", "experiments/v1/seeds.confirmatory.txt"))
    freeze_path = root / str(confirmatory.get("freeze_path", "experiments/v1/artifacts/CONFIRMATORY_FREEZE.json"))
    sealed_dir = root / str(confirmatory.get("sealed_dir", "experiments/v1/artifacts/confirmatory"))
    evidence_path = sealed_dir / "CONFIRMATORY_EVIDENCE.json"
    manuscript = root / str(paper_a.get("manuscript", "paper/tmlr/paper.tex"))
    eq_path = root / str(eq.get("artifact", "experiments/v1/artifacts/diagnostics/equalization.json"))
    measured_runtime_path = root / "experiments" / "v1" / "artifacts" / "diagnostics" / "runtime.json"

    _check(results, "confirmatory.seed_file_exists", seed_path.is_file() == bool(confirmatory.get("seed_file_exists")), str(seed_path))
    _check(results, "confirmatory.freeze_exists", freeze_path.is_file() == bool(confirmatory.get("freeze_exists")), str(freeze_path))
    sealed_ok = evidence_path.is_file() and (sealed_dir / "REPORT.md").is_file() and (sealed_dir / "analysis.json").is_file()
    _check(results, "confirmatory.sealed_artifacts_exist", sealed_ok == bool(confirmatory.get("sealed_artifacts_exist")), str(sealed_dir))
    _check(results, "paper_a.exists", manuscript.is_file() == bool(paper_a.get("exists")), str(manuscript))

    if seed_path.is_file():
        seeds = [line for line in seed_path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.strip().startswith("#")]
        _check(results, "confirmatory.n", len(seeds) == int(confirmatory.get("n", -1)), {"expected": confirmatory.get("n"), "observed": len(seeds)})

    if evidence_path.is_file():
        evidence = load_json(evidence_path)
        _check(
            results,
            "confirmatory.status",
            evidence.get("result_state", {}).get("state") == confirmatory.get("status"),
            {"state": confirmatory.get("status"), "evidence": evidence.get("result_state", {}).get("state")},
        )
        _check(results, "confirmatory.executed", bool(confirmatory.get("executed")) is True, confirmatory.get("executed"))
        _check(
            results,
            "confirmatory.n_trials_schema",
            int(confirmatory.get("n_trials", 0)) == 1940,
            confirmatory.get("n_trials"),
        )
        _check(
            results,
            "confirmatory.scientific_job_count",
            evidence.get("scientific_job_count") == confirmatory.get("scientific_job_count"),
            evidence.get("scientific_job_count"),
        )

    if eq_path.is_file():
        equalization = load_json(eq_path)
        _check(
            results,
            "equalization_triage.status",
            equalization.get("classification") == eq.get("status"),
            {"state": eq.get("status"), "artifact": equalization.get("classification")},
        )
        _check(results, "equalization_does_not_overwrite_refuted", eq.get("alters_confirmatory_status") is False, eq.get("alters_confirmatory_status"))

    submitted_state = bool(paper_a.get("submitted"))
    submitted_receipt = bool(receipt.get("submitted"))
    _check(results, "paper_a.submitted_matches_receipt", submitted_state == submitted_receipt, {"state": submitted_state, "receipt": submitted_receipt})
    if submitted_receipt:
        _check(results, "paper_a.submission_id_present", bool(receipt.get("submission_id")), receipt.get("submission_id"))
    else:
        _check(results, "paper_a.submission_id_absent", receipt.get("submission_id") in (None, ""), receipt.get("submission_id"))

    moratorium_active = bool(moratorium.get("active"))
    if not submitted_state:
        _check(
            results,
            "moratorium.active_while_unsubmitted",
            moratorium_active is True,
            "paper_a.submitted == false → moratorium.active MUST be true",
        )
    _check(
        results,
        "moratorium.exit_condition",
        moratorium.get("exit_condition") == MORATORIUM_EXIT_MARKER,
        moratorium.get("exit_condition"),
    )

    sealed = runtime.get("sealed_confirmatory") or {}
    if measured_runtime_path.is_file():
        measured = load_json(measured_runtime_path)
        _check(
            results,
            "runtime.decision_cpu_seconds_matches_measurement",
            abs(float(sealed["decision_cpu_seconds"]) - float(measured["cpu_seconds_sum"])) < 1e-9,
            {"canonical": sealed.get("decision_cpu_seconds"), "measured": measured.get("cpu_seconds_sum")},
        )
        _check(
            results,
            "runtime.decision_cpu_hours_matches_measurement",
            abs(float(sealed["decision_cpu_hours"]) - float(measured["cpu_hours"])) < 1e-12,
            {"canonical": sealed.get("decision_cpu_hours"), "measured": measured.get("cpu_hours")},
        )
    expected_hours = round(float(sealed["decision_cpu_seconds"]) / 3600.0, 3)
    _check(
        results,
        "runtime.decision_cpu_hours_rounded_3dp",
        abs(float(sealed["decision_cpu_hours_rounded_3dp"]) - expected_hours) < 1e-12,
        {"declared": sealed.get("decision_cpu_hours_rounded_3dp"), "computed": expected_hours},
    )
    _check(
        results,
        "runtime.rejects_stale_402s_as_decision_cpu",
        abs(float(sealed["decision_cpu_seconds"]) - 402.0) > 1.0,
        sealed.get("decision_cpu_seconds"),
    )

    readme = readme_text if readme_text is not None else (root / "README.md").read_text(encoding="utf-8")
    paper = paper_text if paper_text is not None else manuscript.read_text(encoding="utf-8") if manuscript.is_file() else ""
    moratorium_md = (
        moratorium_text
        if moratorium_text is not None
        else (root / "V1_CONFIRMATORY_MORATORIUM.md").read_text(encoding="utf-8")
    )
    matrix = (root / "docs" / "claim_evidence_matrix.yaml").read_text(encoding="utf-8")
    claims_md = (root / "research" / "CLAIMS.md").read_text(encoding="utf-8") if (root / "research" / "CLAIMS.md").is_file() else ""

    stale = find_stale_confirmatory_phrases(readme)
    _check(results, "readme.no_stale_confirmatory_phrases", not stale, stale)
    _check(results, "readme.contains_refuted", "REFUTED" in readme, None)
    _check(results, "readme.contains_eq_b_honest_status", REQUIRED_EQ_B_HONEST_STATUS in readme, None)
    _check(results, "readme.contains_unsupported_hierarchy_only", REQUIRED_UNSUPPORTED_ATTRIBUTION in readme, None)
    _check(results, "readme.no_hierarchy_only_assertion", not find_hierarchy_only_assertions(readme), find_hierarchy_only_assertions(readme))
    _check(results, "paper.no_hierarchy_only_assertion", not find_hierarchy_only_assertions(paper), find_hierarchy_only_assertions(paper))
    _check(results, "matrix.contains_unsupported_hierarchy_only", REQUIRED_UNSUPPORTED_ATTRIBUTION in matrix, None)
    _check(results, "claims_md.contains_unsupported_hierarchy_only", REQUIRED_UNSUPPORTED_ATTRIBUTION in claims_md, None)

    readme_block = _readme_state_block(readme)
    for key in README_STATE_KEYS:
        _check(results, f"readme.state_marker:{key}", key in readme_block, readme_block)
    if readme_block:
        _check(results, "readme.marker.confirmatory.executed", readme_block.get("confirmatory.executed") == str(confirmatory.get("executed")).lower(), readme_block.get("confirmatory.executed"))
        _check(results, "readme.marker.confirmatory.status", readme_block.get("confirmatory.status") == str(confirmatory.get("status")), readme_block.get("confirmatory.status"))
        _check(results, "readme.marker.confirmatory.n", readme_block.get("confirmatory.n") == str(confirmatory.get("n")), readme_block.get("confirmatory.n"))
        _check(results, "readme.marker.equalization", readme_block.get("equalization_triage.status") == str(eq.get("status")), readme_block.get("equalization_triage.status"))
        _check(results, "readme.marker.paper_a.submitted", readme_block.get("paper_a.submitted") == str(submitted_state).lower(), readme_block.get("paper_a.submitted"))
        _check(results, "readme.marker.moratorium.active", readme_block.get("moratorium.active") == str(moratorium_active).lower(), readme_block.get("moratorium.active"))

    if submitted_state is False:
        _check(results, "readme.states_not_yet_submitted", "not yet submitted" in readme.lower(), None)
        positive_submission = False
        lowered = readme.lower()
        for match in re.finditer(r"paper a has been submitted", lowered):
            prefix = lowered[max(0, match.start() - 12) : match.start()]
            if "until" in prefix or "when" in prefix or "unless" in prefix:
                continue
            positive_submission = True
        _check(results, "readme.does_not_claim_submitted", not positive_submission, None)

    rounded = f"{float(sealed['decision_cpu_hours_rounded_3dp']):.3f}"
    for label, text in (("readme", readme), ("paper", paper)):
        declared = _declared_runtime_values(text)
        bad_hours = [value for value in declared["cpu_hours"] if value != rounded and value not in {"0.12"}]
        # 0.12 without the third digit is too coarse; require 0.122 in documents that mention CPU-h.
        coarse = [value for value in declared["cpu_hours"] if value == "0.12"]
        _check(results, f"{label}.runtime_cpu_hours", not bad_hours and not coarse, {"found": declared["cpu_hours"], "required": rounded})
        _check(results, f"{label}.runtime_no_stale_402s", not declared["cpu_seconds"], declared["cpu_seconds"])

    _check(results, "moratorium.md.exit_condition", MORATORIUM_EXIT_MARKER in moratorium_md, None)
    _check(
        results,
        "moratorium.md.not_exited_by_result_alone",
        "A completed result alone does NOT unlock the broader program" in moratorium_md
        or "completed confirmatory result alone does not unlock" in moratorium_md.lower(),
        None,
    )
    _check(results, "readme.commands_active_heading", "Active V1 / Paper A commands" in readme, None)
    _check(results, "readme.commands_frozen_heading", "Frozen under submission moratorium" in readme, None)
    _check(
        results,
        "readme.v0_wording_not_causal",
        "needed to determine why a method wins" not in readme.lower(),
        None,
    )
    _check(
        results,
        "readme.headline_names_frozen_mechanism",
        "fixed hierarchical routing update" in readme.lower() and "frozen v1 configuration" in readme.lower(),
        None,
    )

    failures = [row for row in results if not row["ok"]]
    return {
        "ok": not failures,
        "n_checks": len(results),
        "checks": results,
        "failures": failures,
        "state": {
            "confirmatory.executed": confirmatory.get("executed"),
            "confirmatory.status": confirmatory.get("status"),
            "confirmatory.n": confirmatory.get("n"),
            "equalization_triage.status": eq.get("status"),
            "paper_a.submitted": submitted_state,
            "moratorium.active": moratorium_active,
        },
        "claim_boundary": (
            "Passing this audit means repository documents match canonical scientific state. "
            "It does not mean any scientific claim is empirically true."
        ),
    }
