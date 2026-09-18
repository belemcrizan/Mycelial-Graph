"""Additive scientific-invariant regression tests (Master Prompt Part II §15, Kernel §P8).

These tests hard-code the immutable canonical state (INV-01/INV-02) and assert that the newly
added staged artifacts remain honestly frozen/unauthorized (INV-06). They read files directly and
avoid importing package internals so they cannot mask a state regression behind an import.

Nothing here mutates any artifact. If any assertion fails, a sealed fact or a staged-vs-executed
boundary has drifted and CI must stop.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read_text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _read_json(rel: str) -> dict:
    return json.loads(_read_text(rel))


class SealedResultIsImmutable(unittest.TestCase):
    """INV-01/INV-02: REFUTED and its numbers are historical and immutable."""

    def test_state_json_canonical_fields(self) -> None:
        state = _read_json("research/state.json")
        self.assertTrue(state["confirmatory"]["executed"])
        self.assertEqual(state["confirmatory"]["status"], "REFUTED")
        self.assertEqual(state["confirmatory"]["n"], 97)
        self.assertEqual(state["equalization_triage"]["status"], "EQ-B")
        self.assertFalse(state["paper_a"]["submitted"])
        self.assertTrue(state["moratorium"]["active"])

    def test_sealed_confirmatory_numbers(self) -> None:
        analysis = _read_json(
            "experiments/v1/artifacts/confirmatory/analysis.json"
        )
        self.assertEqual(analysis["result_state"]["state"], "REFUTED")
        primary = analysis["primary_contrast"]
        # +42.1% slower at rho=0.50; interval strictly above zero.
        self.assertAlmostEqual(round(primary["estimate"], 3), 0.421, places=3)
        self.assertGreater(primary["confidence_low"], 0.0)
        self.assertAlmostEqual(round(primary["confidence_low"], 3), 0.119, places=3)
        self.assertAlmostEqual(round(primary["confidence_high"], 3), 0.791, places=3)
        self.assertEqual(analysis["frozen_contrast_integrity"]["primary_pairs"], 97)
        # rho=0 non-inferiority gate did NOT pass.
        self.assertFalse(analysis["decision_gate"]["noninferiority_at_rho_0"])
        self.assertFalse(analysis["decision_gate"]["statistical_superiority"])


class StagedArtifactsRemainUnauthorized(unittest.TestCase):
    """INV-06: prepared work must never look executed/authorized."""

    def test_equalized_config_is_frozen_and_unauthorized(self) -> None:
        cfg = _read_text("experiments/v1_5/config.equalized.yaml")
        self.assertIn("status: frozen", cfg)
        self.assertIn("authorized: false", cfg)

    def test_external_ope_prereg_is_frozen_unauthorized(self) -> None:
        doc = _read_text("external/protocols/EXTERNAL_OPE_PREREG.md")
        self.assertIn("authorized: false", doc)

    def test_moratorium_amendment_is_a_proposal(self) -> None:
        doc = _read_text("experiments/PROTOCOL_AMENDMENT_002_PROPOSAL.md")
        self.assertIn("Status:", doc)
        self.assertIn("PROPOSAL", doc)

    def test_proposed_claims_are_not_in_the_enforced_matrix(self) -> None:
        # The proposed additions live in a separate file, keeping the CI-enforced
        # canonical matrix unchanged (§P9 conservative choice).
        canonical = _read_text("docs/claim_evidence_matrix.yaml")
        self.assertNotIn("proposed_claims", canonical)
        additions = _read_text("docs/claim_evidence_matrix.additions.yaml")
        self.assertIn("proposed_claims", additions)


if __name__ == "__main__":
    unittest.main()
