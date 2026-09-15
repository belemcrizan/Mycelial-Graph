"""Integrity tests for the frozen MG-EXP-V1 confirmatory contract.

These tests fail if the frozen seed population, sample size, configuration binding, result-state
mapping, or claim containment is altered. They are deliberately strict: they exist so that a
future change cannot quietly move the goalposts of the confirmatory experiment.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from mycelial_graph.analysis.result_state import RESULT_STATES, classify_result_state
from mycelial_graph.runner.trial import config_hash
from mycelial_graph.science.claim_guard import (
    ClaimContainmentError,
    assert_claim_containment,
    find_claim_violations,
)
from mycelial_graph.science.claim_invariants import audit_v1_invariants
from mycelial_graph.types import load_config
from mycelial_graph.validation import load_seeds, validate_config

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "experiments" / "v1"
FREEZE = json.loads((V1 / "artifacts" / "CONFIRMATORY_FREEZE.json").read_text(encoding="utf-8"))
MATRIX = ROOT / "docs" / "claim_evidence_matrix.yaml"

CLEAN_INTEGRITY = {
    "non_administrative_censoring": 0,
    "method_failures_in_frozen_contrasts": 0,
    "primary_pairs": 97,
}


def _contrast(estimate: float, low: float, high: float, upper: float) -> dict[str, float]:
    return {
        "estimate": estimate,
        "confidence_low": low,
        "confidence_high": high,
        "one_sided_upper_bound": upper,
    }


class FrozenSeedPopulationTests(unittest.TestCase):
    def test_confirmatory_seeds_are_the_unfiltered_pool_prefix(self) -> None:
        seeds = load_seeds(V1 / "seeds.confirmatory.txt")
        pool = load_seeds(V1 / "seeds.confirmatory.pool.txt")
        expected = int(FREEZE["required_confirmatory_pairs"])
        self.assertEqual(len(seeds), expected)
        self.assertEqual(seeds, pool[:expected])
        self.assertEqual(len(set(seeds)), len(seeds))

    def test_confirmatory_seed_hash_matches_the_freeze(self) -> None:
        from mycelial_graph.science.canonical_bytes import verify_frozen_seed_identity

        check = verify_frozen_seed_identity(V1 / "seeds.confirmatory.txt", FREEZE["seeds_sha256"])
        self.assertTrue(check.ok, check.message)

    def test_confirmatory_seeds_are_disjoint_from_protected_populations(self) -> None:
        seeds = set(load_seeds(V1 / "seeds.confirmatory.txt"))
        self.assertFalse(seeds & set(load_seeds(V1 / "seeds.pilot.txt")))
        self.assertFalse(seeds & set(load_seeds(V1 / "seeds.development.txt")))

    def test_confirmatory_config_matches_the_frozen_hash_and_validates(self) -> None:
        config = load_config(V1 / "config.confirmatory.yaml")
        self.assertEqual(config_hash(config), FREEZE["confirmatory_config_hash"])
        self.assertEqual(validate_config(config), [])

    def test_frozen_scientific_parameters_are_unchanged(self) -> None:
        analysis = load_config(V1 / "config.confirmatory.yaml").analysis
        self.assertEqual(analysis.primary_rho, 0.5)
        self.assertEqual(analysis.noninferiority_margin, 0.10)
        self.assertEqual(analysis.engineering_gain_gate, 0.20)
        self.assertEqual(analysis.superiority_alpha, 0.05)
        self.assertEqual(analysis.bootstrap_samples, 10000)
        self.assertEqual(analysis.confidence_level, 0.95)

    def test_readiness_invariants_hold(self) -> None:
        result = audit_v1_invariants(MATRIX, ROOT)
        self.assertTrue(result["ok"], result["failures"])


class ResultStateTests(unittest.TestCase):
    def test_all_five_states_are_reachable(self) -> None:
        self.assertEqual(len(RESULT_STATES), 5)

    def test_supported_requires_all_three_frozen_requirements(self) -> None:
        state = classify_result_state(
            _contrast(-0.30, -0.45, -0.12, -0.15),
            {**_contrast(-0.05, -0.20, 0.06, 0.05), "margin": 0.10},
            CLEAN_INTEGRITY,
            0.20,
            0.10,
            97,
        )
        self.assertEqual(state["state"], "SUPPORTED")
        self.assertEqual(state["safety_gate_state"], "NON_INFERIOR")

    def test_safety_gate_failure_downgrades_to_conditional(self) -> None:
        state = classify_result_state(
            _contrast(-0.30, -0.45, -0.12, -0.15),
            {**_contrast(0.14, -0.02, 0.30, 0.26), "margin": 0.10},
            CLEAN_INTEGRITY,
            0.20,
            0.10,
            97,
        )
        self.assertEqual(state["state"], "CONDITIONAL")
        self.assertEqual(state["safety_gate_state"], "NEGATIVE_TRANSFER_NOT_EXCLUDED")

    def test_small_but_significant_effect_is_conditional_not_supported(self) -> None:
        state = classify_result_state(
            _contrast(-0.08, -0.15, -0.02, -0.03),
            {**_contrast(-0.05, -0.20, 0.06, 0.05), "margin": 0.10},
            CLEAN_INTEGRITY,
            0.20,
            0.10,
            97,
        )
        self.assertEqual(state["state"], "CONDITIONAL")

    def test_excluded_relevant_benefit_is_refuted(self) -> None:
        state = classify_result_state(
            _contrast(0.05, -0.05, 0.16, 0.14),
            {**_contrast(0.02, -0.08, 0.11, 0.09), "margin": 0.10},
            CLEAN_INTEGRITY,
            0.20,
            0.10,
            97,
        )
        self.assertEqual(state["state"], "REFUTED")

    def test_wide_interval_is_inconclusive(self) -> None:
        state = classify_result_state(
            _contrast(-0.10, -0.36, 0.30, 0.22),
            {**_contrast(-0.08, -0.34, 0.23, 0.18), "margin": 0.10},
            CLEAN_INTEGRITY,
            0.20,
            0.10,
            97,
        )
        self.assertEqual(state["state"], "INCONCLUSIVE")

    def test_missing_pairs_are_protocol_invalid(self) -> None:
        state = classify_result_state(
            _contrast(-0.30, -0.45, -0.12, -0.15),
            {**_contrast(-0.05, -0.20, 0.06, 0.05), "margin": 0.10},
            {**CLEAN_INTEGRITY, "primary_pairs": 60},
            0.20,
            0.10,
            97,
        )
        self.assertEqual(state["state"], "PROTOCOL_INVALID")

    def test_non_administrative_censoring_is_protocol_invalid(self) -> None:
        state = classify_result_state(
            _contrast(-0.30, -0.45, -0.12, -0.15),
            {**_contrast(-0.05, -0.20, 0.06, 0.05), "margin": 0.10},
            {**CLEAN_INTEGRITY, "non_administrative_censoring": 1},
            0.20,
            0.10,
            97,
        )
        self.assertEqual(state["state"], "PROTOCOL_INVALID")


class ClaimContainmentTests(unittest.TestCase):
    def test_crossover_assertions_are_rejected(self) -> None:
        for text in (
            "We identify a crossover in the shared-shock fraction.",
            "The crossover occurs at rho = 0.42.",
            "rho* = 0.37 according to the confirmatory run.",
            "This confirms a phase transition in rho.",
        ):
            with self.subTest(text=text):
                self.assertTrue(find_claim_violations(text), text)

    def test_overreaching_claims_are_rejected(self) -> None:
        for text in (
            "Hierarchical pooling is universally superior.",
            "Hierarchical pooling wins for all rho values.",
            "The router is production-ready.",
            "This establishes real-world superiority.",
            "The shock causally explains the recovery gap.",
            "This theorem bounds the regret of hierarchical pooling.",
            "The result was independently reproduced by our second script.",
        ):
            with self.subTest(text=text):
                self.assertTrue(find_claim_violations(text), text)

    def test_documented_limitations_remain_sayable(self) -> None:
        text = "\n".join(
            [
                "Exploratory across rho - this design is not powered to establish a crossover.",
                "No rho* may be read off these curves.",
                "This is not a production-readiness claim and it does not generalise to real providers.",
                "The execution DAG is not a causal DAG, so no causal claim is made.",
                "Reproduction here is internal and automated, never independent.",
                "At rho=0.50 the estimated relative difference was -22.5%.",
            ]
        )
        self.assertEqual(find_claim_violations(text), [])
        assert_claim_containment(text, "test")

    def test_assert_raises_on_violation(self) -> None:
        with self.assertRaises(ClaimContainmentError):
            assert_claim_containment("We establish the crossover rho* = 0.5.", "test")

    def test_sealed_confirmatory_report_stays_inside_the_claim_boundary(self) -> None:
        report = V1 / "artifacts" / "confirmatory" / "REPORT.md"
        if not report.exists():
            self.skipTest("no sealed confirmatory report yet")
        assert_claim_containment(report.read_text(encoding="utf-8"), str(report))


class SealedConfirmatoryEvidenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = V1 / "artifacts" / "confirmatory" / "CONFIRMATORY_EVIDENCE.json"
        if not self.path.exists():
            self.skipTest("no sealed confirmatory evidence yet")
        self.evidence = json.loads(self.path.read_text(encoding="utf-8"))

    def test_executed_under_the_frozen_contract(self) -> None:
        self.assertEqual(self.evidence["config_hash"], FREEZE["confirmatory_config_hash"])
        self.assertEqual(self.evidence["seeds_file_sha256"], FREEZE["seeds_sha256"])
        self.assertEqual(self.evidence["protocol_version"], FREEZE["protocol_version"])

    def test_full_frozen_sample_was_executed(self) -> None:
        self.assertEqual(self.evidence["frozen_contrast_integrity"]["primary_pairs"], 97)
        self.assertEqual(self.evidence["frozen_contrast_integrity"]["non_administrative_censoring"], 0)

    def test_result_state_is_terminal(self) -> None:
        self.assertIn(self.evidence["result_state"]["state"], RESULT_STATES)

    def test_reproduction_is_not_labelled_independent(self) -> None:
        self.assertIn("internal", self.evidence["reproduction_status"])


if __name__ == "__main__":
    unittest.main()
