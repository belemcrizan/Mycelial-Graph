"""Paper A submission-safety tests.

These tests do not re-execute the confirmatory experiment. They lock claim-map
presence, seed reservations, equalization-class logic, and the sealed REFUTED
state so that a later edit cannot quietly drop the negative result.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from mycelial_graph.science.paper_a_diagnostics import _classify_equalization

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "experiments" / "v1"


def _arm(entropy_frac: float, opt: float, explore: float, std: float) -> dict:
    return {
        "path_entropy_fraction_of_max": {"mean": entropy_frac},
        "optimal_pre_path_rate": {"mean": opt},
        "exploration_step_rate": {"mean": explore},
        "selected_score_std": {"mean": std},
    }


class EqualizationClassificationTests(unittest.TestCase):
    def test_eq_a_when_gaps_are_small(self) -> None:
        label, _ = _classify_equalization(
            _arm(0.60, 0.20, 0.22, 0.50),
            _arm(0.62, 0.18, 0.23, 0.55),
        )
        self.assertEqual(label, "EQ-A")

    def test_eq_b_on_material_but_non_extreme_gap(self) -> None:
        label, _ = _classify_equalization(
            _arm(0.63, 0.14, 0.22, 0.51),
            _arm(0.97, 0.04, 0.22, 0.04),
        )
        self.assertEqual(label, "EQ-B")

    def test_eq_c_when_one_arm_is_collapsed_and_the_other_is_diffuse(self) -> None:
        label, _ = _classify_equalization(
            _arm(0.10, 0.80, 0.02, 1.0),
            _arm(0.90, 0.04, 0.40, 0.02),
        )
        self.assertEqual(label, "EQ-C")


class PaperAArtifactTests(unittest.TestCase):
    def test_claim_map_covers_required_sections(self) -> None:
        text = (ROOT / "paper" / "CLAIM_MAP.yaml").read_text(encoding="utf-8")
        for needle in (
            "Abstract",
            "Confirmatory Results",
            "Safety Gate",
            "Equalization Triage",
            "Post-Confirmatory Diagnostics",
            "Threats to Validity",
            "Reproducibility",
            "Conclusion",
            "REFUTED",
            "EQ-B",
            "1.72",
            "UNSUPPORTED",
            "hierarchical representation alone",
        ):
            self.assertIn(needle, text)

    def test_manuscript_exists_and_stays_inside_the_refutation(self) -> None:
        tex = (ROOT / "paper" / "tmlr" / "paper.tex").read_text(encoding="utf-8")
        self.assertIn("REFUTED", tex)
        self.assertIn("EQ-B", tex)
        self.assertNotIn("rho^* =", tex.replace(" ", ""))
        self.assertNotIn("independently reproduced", tex.lower())
        self.assertNotIn("belemcrizan", tex.lower())
        self.assertNotIn("Crizan", tex)

    def test_variance_ratio_is_not_hard_coded_as_4_54(self) -> None:
        variance = json.loads((V1 / "artifacts" / "diagnostics" / "variance.json").read_text(encoding="utf-8"))
        ratio = variance["variance_ratio_confirmatory_over_pilot"]
        self.assertGreater(ratio, 1.0)
        self.assertLess(abs(ratio - 1.7202583266956992), 1e-9)
        report = (V1 / "artifacts" / "diagnostics" / "REPORT.md").read_text(encoding="utf-8")
        self.assertNotIn("4.54", report)

    def test_equalization_triage_is_eq_b(self) -> None:
        payload = json.loads((V1 / "artifacts" / "diagnostics" / "equalization.json").read_text(encoding="utf-8"))
        self.assertEqual(payload["classification"], "EQ-B")

    def test_cpu_hours_are_measured(self) -> None:
        runtime = json.loads((V1 / "artifacts" / "diagnostics" / "runtime.json").read_text(encoding="utf-8"))
        canonical = json.loads((ROOT / "research" / "runtime.json").read_text(encoding="utf-8"))
        self.assertAlmostEqual(runtime["cpu_hours"], 0.12155381944444445, places=9)
        self.assertAlmostEqual(
            canonical["sealed_confirmatory"]["decision_cpu_hours"],
            runtime["cpu_hours"],
            places=12,
        )
        self.assertEqual(canonical["sealed_confirmatory"]["decision_cpu_hours_rounded_3dp"], 0.122)

    def test_sealed_result_remains_refuted(self) -> None:
        evidence = json.loads(
            (V1 / "artifacts" / "confirmatory" / "CONFIRMATORY_EVIDENCE.json").read_text(encoding="utf-8")
        )
        self.assertEqual(evidence["result_state"]["state"], "REFUTED")

    def test_reserved_seeds_are_disjoint_from_v1_populations(self) -> None:
        reserved = (V1 / "SEEDS_RESERVED.md").read_text(encoding="utf-8")
        self.assertIn("800000", reserved)
        self.assertIn("840000", reserved)
        used = set()
        for name in ("seeds.development.txt", "seeds.pilot.txt", "seeds.confirmatory.pool.txt"):
            used.update(
                int(line)
                for line in (V1 / name).read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        reserved_ranges = [
            range(800000, 800100),
            range(810000, 810100),
            range(820000, 820100),
            range(830000, 830100),
            range(840000, 840500),
        ]
        for block in reserved_ranges:
            self.assertFalse(used & set(block))

    def test_canonical_reproduce_entry_point_exists(self) -> None:
        self.assertTrue((ROOT / "reproduce_confirmatory.py").exists())


if __name__ == "__main__":
    unittest.main()
