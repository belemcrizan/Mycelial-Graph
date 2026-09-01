from __future__ import annotations

import unittest
from pathlib import Path

from mycelial_graph.cli import main
from mycelial_graph.v2.biology.voc import estimate_voc, voc_difference, voc_ratio
from mycelial_graph.v2.config import load_v2_config
from mycelial_graph.v2.environment import generate_resource_scenario
from mycelial_graph.v2.environment.roles import edge_role
from mycelial_graph.v2.evaluation.claim_audit import audit_claims
from mycelial_graph.v2.evaluation.counterfactual import run_voc_benchmark
from mycelial_graph.v2.evaluation.waste import decompose_waste, waste_identity_ok
from mycelial_graph.v2.policies.factory import UNIMPLEMENTED_ALPHA_ALIASES, create_resource_agent
from mycelial_graph.v2.policies.oracle import allocation_regret
from mycelial_graph.v2.resources import BudgetReservation, ReservationError
from mycelial_graph.v2.real import run_real_smoke
from mycelial_graph.v2.seeding import create_rng


ROOT = Path(__file__).resolve().parents[1]
V2_DEV = ROOT / "experiments" / "v2" / "config.development.yaml"
V21_DEV = ROOT / "experiments" / "v2_1" / "config.development.yaml"


class VOCTests(unittest.TestCase):
    def test_difference_and_ratio_disagree_near_zero_resource(self) -> None:
        tiny = estimate_voc(0.02, 1e-9, 0.35)
        self.assertFalse(tiny.ratio_stable)
        self.assertAlmostEqual(voc_difference(0.10, 100.0, 0.001), 0.0, places=6)
        self.assertGreater(voc_ratio(0.10, 100.0), 0.0)


class ReservationTests(unittest.TestCase):
    def test_hard_budget_cannot_be_silently_exceeded(self) -> None:
        wallet = BudgetReservation(cap=10.0)
        wallet.reserve(6.0)
        wallet.commit(6.0, 5.0)
        with self.assertRaises(ReservationError):
            wallet.reserve(6.0)


class IsoModelTests(unittest.TestCase):
    def test_iso_model_collapses_model_class_latents(self) -> None:
        config = load_v2_config(V21_DEV)
        self.assertTrue(config.environment.iso_model)
        scenario = generate_resource_scenario(config, 9101, "STATIC")
        model_tokens = [
            int(scenario.token_means_pre[edge.id])
            for edge in scenario.graph.edges
            if edge_role(scenario.graph, edge.id) == "model"
        ]
        self.assertGreater(len(model_tokens), 1)
        self.assertEqual(len(set(model_tokens)), 1)

    def test_alpha_config_is_not_iso_model(self) -> None:
        config = load_v2_config(V2_DEV)
        self.assertFalse(config.environment.iso_model)


class OracleTests(unittest.TestCase):
    def test_oracle_regret_is_non_negative_on_expected_quality(self) -> None:
        config = load_v2_config(V21_DEV)
        scenario = generate_resource_scenario(config, 9101, "STATIC")
        path = scenario.graph.all_paths()[0]
        edges = scenario.graph.path_edges(path)
        self.assertGreaterEqual(allocation_regret(scenario, 0, edges), -1e-9)


class StrongBaselineTests(unittest.TestCase):
    def test_factory_builds_strong_baselines(self) -> None:
        config = load_v2_config(V21_DEV)
        scenario = generate_resource_scenario(config, 9101, "STATIC")
        rng = create_rng(9101, "agent:STATIC:thompson_sampling")
        agent = create_resource_agent("thompson_sampling", config, scenario.graph, rng)
        decision = agent.choose(scenario.graph, 0, float(scenario.budget_pre))
        self.assertTrue(decision.edge_ids)

    def test_unimplemented_alpha_aliases_are_explicit(self) -> None:
        self.assertIn("v2_no_branching", UNIMPLEMENTED_ALPHA_ALIASES)


class WasteTests(unittest.TestCase):
    def test_waste_identity_matches_ledger(self) -> None:
        ledger = {
            "input_tokens": 10,
            "output_tokens": 4,
            "reasoning_tokens": 2,
            "retrieval_tokens": 6,
            "verification_tokens": 3,
            "tool_tokens": 0,
            "summarization_tokens": 1,
            "router_tokens": 5,
            "state_overhead_tokens": 1,
            "total_tokens": 32,
        }
        breakdown = decompose_waste(ledger, success=True, retrieval_used=True)
        self.assertTrue(waste_identity_ok(breakdown, 32))


class VOCBenchTests(unittest.TestCase):
    def test_voc_bench_runs_on_v21_config(self) -> None:
        config = load_v2_config(V21_DEV)
        payload = run_voc_benchmark(config, (9101,))
        self.assertGreater(payload["n_records"], 0)
        self.assertIn("false_stop_rate", payload)


class RealSmokeTests(unittest.TestCase):
    def test_executable_grader_distinguishes_fix_from_bug(self) -> None:
        payload = run_real_smoke(("always_high_compute", "always_low_compute"))
        by_policy: dict[str, list[bool]] = {}
        for row in payload["results"]:
            by_policy.setdefault(row["policy"], []).append(row["passed"])
        self.assertTrue(all(by_policy["always_high_compute"]))
        self.assertFalse(any(by_policy["always_low_compute"]))


class ClaimAuditTests(unittest.TestCase):
    def test_claim_matrix_is_internally_consistent(self) -> None:
        result = audit_claims(ROOT / "docs" / "claim_evidence_matrix.yaml")
        self.assertTrue(result["ok"], result)


class CLIV21Tests(unittest.TestCase):
    def test_claim_audit_cli(self) -> None:
        self.assertEqual(main(["claim-audit", "--matrix", str(ROOT / "docs" / "claim_evidence_matrix.yaml")]), 0)

    def test_real_smoke_cli(self) -> None:
        self.assertEqual(main(["real-smoke"]), 0)

    def test_v2_alpha_config_still_validates(self) -> None:
        self.assertEqual(main(["v2-validate", "--config", str(V2_DEV)]), 0)


if __name__ == "__main__":
    unittest.main()
