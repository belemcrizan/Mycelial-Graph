"""Regression tests for scientific-state assertions and the three stale README contradictions."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from mycelial_graph.science.canonical_bytes import normalize_newlines, sha256_lf_text, sha256_raw
from mycelial_graph.science.scientific_state import (
    STALE_MISSING_SEEDS,
    STALE_NO_RESULT,
    STALE_NOT_EXECUTED,
    audit_scientific_state,
    find_stale_confirmatory_phrases,
)

ROOT = Path(__file__).resolve().parents[1]


class StalePhraseRegressionTests(unittest.TestCase):
    def test_the_three_surviving_contradictions_are_detected_in_stale_prose(self) -> None:
        stale = "\n".join(
            [
                STALE_NOT_EXECUTED,
                f"The lock {STALE_MISSING_SEEDS} so validation fails.",
                STALE_NO_RESULT,
            ]
        )
        hits = {item["id"] for item in find_stale_confirmatory_phrases(stale)}
        self.assertEqual(
            hits,
            {"stale_not_executed", "stale_missing_seeds_as_current", "stale_no_result"},
        )

    def test_current_readme_does_not_contain_the_three_contradictions(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(find_stale_confirmatory_phrases(readme), [])

    def test_audit_fails_on_stale_readme_injected_over_current_repo(self) -> None:
        stale_readme = "\n".join(
            [
                "# Mycelial Graph",
                STALE_NOT_EXECUTED,
                STALE_MISSING_SEEDS,
                STALE_NO_RESULT,
                "Paper A has been submitted.",
            ]
        )
        result = audit_scientific_state(ROOT, readme_text=stale_readme)
        self.assertFalse(result["ok"])
        failed = {row["check"] for row in result["failures"]}
        self.assertIn("readme.no_stale_confirmatory_phrases", failed)
        self.assertIn("readme.does_not_claim_submitted", failed)

    def test_each_contradiction_fails_in_isolation(self) -> None:
        current = (ROOT / "README.md").read_text(encoding="utf-8")
        for phrase, identifier in (
            (STALE_NOT_EXECUTED, "stale_not_executed"),
            (STALE_MISSING_SEEDS, "stale_missing_seeds_as_current"),
            (STALE_NO_RESULT, "stale_no_result"),
        ):
            with self.subTest(identifier=identifier):
                poisoned = current + "\n\n" + phrase + "\n"
                hits = find_stale_confirmatory_phrases(poisoned)
                self.assertEqual([item["id"] for item in hits], [identifier])
                result = audit_scientific_state(ROOT, readme_text=poisoned)
                self.assertFalse(result["ok"])


class CanonicalStateTests(unittest.TestCase):
    def test_repository_scientific_state_passes(self) -> None:
        result = audit_scientific_state(ROOT)
        self.assertTrue(result["ok"], result["failures"])
        self.assertEqual(result["state"]["confirmatory.executed"], True)
        self.assertEqual(result["state"]["confirmatory.status"], "REFUTED")
        self.assertEqual(result["state"]["confirmatory.n"], 97)
        self.assertEqual(result["state"]["equalization_triage.status"], "EQ-B")
        self.assertEqual(result["state"]["paper_a.submitted"], False)
        self.assertEqual(result["state"]["moratorium.active"], True)

    def test_readme_cannot_disable_moratorium_without_receipt(self) -> None:
        state_path = ROOT / "research" / "state.json"
        original = state_path.read_text(encoding="utf-8")
        try:
            payload = json.loads(original)
            payload["moratorium"]["active"] = False
            state_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            result = audit_scientific_state(ROOT)
            self.assertFalse(result["ok"])
            failed = {row["check"] for row in result["failures"]}
            self.assertIn("moratorium.active_while_unsubmitted", failed)
        finally:
            state_path.write_text(original, encoding="utf-8")

    def test_runtime_divergence_fails(self) -> None:
        runtime_path = ROOT / "research" / "runtime.json"
        original = runtime_path.read_text(encoding="utf-8")
        try:
            payload = json.loads(original)
            payload["sealed_confirmatory"]["decision_cpu_hours_rounded_3dp"] = 0.112
            runtime_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            result = audit_scientific_state(ROOT)
            self.assertFalse(result["ok"])
            failed = {row["check"] for row in result["failures"]}
            self.assertIn("runtime.decision_cpu_hours_rounded_3dp", failed)
        finally:
            runtime_path.write_text(original, encoding="utf-8")

    def test_paper_runtime_402_fails(self) -> None:
        paper = (ROOT / "paper" / "tmlr" / "paper.tex").read_text(encoding="utf-8")
        result = audit_scientific_state(ROOT, paper_text=paper + "\n402.0 CPU-s\n")
        self.assertFalse(result["ok"])
        failed = {row["check"] for row in result["failures"]}
        self.assertIn("paper.runtime_no_stale_402s", failed)


class CRLFCanonicalizationTests(unittest.TestCase):
    def test_lf_and_crlf_text_share_a_canonical_hash_but_not_a_raw_hash(self) -> None:
        lf = b"seed=700000\nseed=700001\n"
        crlf = b"seed=700000\r\nseed=700001\r\n"
        self.assertNotEqual(sha256_raw(lf), sha256_raw(crlf))
        self.assertEqual(sha256_lf_text(lf), sha256_lf_text(crlf))
        self.assertEqual(normalize_newlines(crlf), lf)

    def test_frozen_seed_identity_is_canonical_lf(self) -> None:
        from mycelial_graph.science.canonical_bytes import lf_to_crlf, verify_frozen_seed_identity

        path = ROOT / "experiments" / "v1" / "seeds.confirmatory.txt"
        freeze = json.loads((ROOT / "experiments" / "v1" / "artifacts" / "CONFIRMATORY_FREEZE.json").read_text(encoding="utf-8"))
        stored = path.read_bytes()
        check = verify_frozen_seed_identity(path, freeze["seeds_sha256"])
        self.assertTrue(check.ok, check.message)
        canonical = normalize_newlines(stored)
        self.assertEqual(sha256_raw(lf_to_crlf(canonical)), freeze["seeds_sha256"])
        crlf = stored.replace(b"\n", b"\r\n") if b"\r\n" not in stored else stored
        if stored != crlf:
            self.assertNotEqual(sha256_raw(stored), sha256_raw(crlf) if b"\r\n" not in stored else sha256_raw(canonical))
            self.assertEqual(sha256_lf_text(crlf), sha256_lf_text(stored))


if __name__ == "__main__":
    unittest.main()
