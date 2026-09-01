from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from mycelial_graph.cli import main
from mycelial_graph.types import load_config
from mycelial_graph.v2.audit import audit_resource_traces
from mycelial_graph.v2.biology import assert_budget_conserved, translocate, update_prune_evidence
from mycelial_graph.v2.config import load_v2_config
from mycelial_graph.v2.environment import generate_resource_scenario
from mycelial_graph.v2.ledger import TokenUsage, TotalResourceLedger
from mycelial_graph.v2.metrics import MethodPoint, dominates, nondominated
from mycelial_graph.v2.runner.experiment import _scenario_job, canonical_v2_payload, run_v2_experiment
from mycelial_graph.v2.seeding import derive_seed
from mycelial_graph.v2.validation import validate_v2_config
from mycelial_graph.validation import validate_config


ROOT = Path(__file__).resolve().parents[1]
V1_DEV = ROOT / "experiments" / "v1" / "config.development.yaml"
V2_DEV = ROOT / "experiments" / "v2" / "config.development.yaml"


class V1RegressionTests(unittest.TestCase):
    def test_v1_development_config_still_valid(self) -> None:
        self.assertEqual(validate_config(load_config(V1_DEV)), [])

    def test_v1_rng_namespace_is_unchanged(self) -> None:
        from mycelial_graph.runner.seeding import derive_seed as v1_seed

        self.assertNotEqual(v1_seed(1103, "agent:0.50000000:edge_only"), derive_seed(1103, "agent:0.50000000:edge_only"))


class LedgerTests(unittest.TestCase):
    def test_cached_tokens_are_not_double_counted(self) -> None:
        usage = TokenUsage(input_tokens=10, output_tokens=5, cached_tokens=4, router_tokens=3)
        self.assertEqual(usage.total_tokens, 18)

    def test_ledger_matches_recorded_categories(self) -> None:
        ledger = TotalResourceLedger()
        usage = TokenUsage(input_tokens=10, output_tokens=8, reasoning_tokens=4, retrieval_tokens=6)
        ledger.record_step(usage, router_tokens=4, state_overhead=1, latency_ms=10.0, monetary_cost=0.2, quality=0.7, success=True, model_calls=1, tool_calls=0)
        self.assertEqual(ledger.total_tokens, 10 + 8 + 4 + 6 + 4 + 1)


class BiologyTests(unittest.TestCase):
    def test_translocation_conserves_budget(self) -> None:
        from mycelial_graph.v2.config import load_v2_config

        config = load_v2_config(V2_DEV)
        budget = np.array([10.0, 20.0, 30.0, 40.0])
        weights = np.array([0.1, 0.5, 0.2, 0.2])
        moved = translocate(budget, weights, 100.0, config.controller, True)
        assert_budget_conserved(moved, 100.0)

    def test_pruning_requires_persistence(self) -> None:
        from mycelial_graph.v2.config import load_v2_config

        config = load_v2_config(V2_DEV)
        evidence = np.zeros(2, dtype=int)
        observations = np.array([10, 10])
        scores = np.array([0.9, 0.1])
        pruned = np.zeros(2, dtype=bool)
        for _ in range(config.controller.prune_persistence - 1):
            evidence, pruned = update_prune_evidence(evidence, observations, scores, config.controller, True)
            self.assertFalse(bool(pruned[0]))
        evidence, pruned = update_prune_evidence(evidence, observations, scores, config.controller, True)
        self.assertTrue(bool(pruned[0]))
        self.assertFalse(bool(pruned[1]))


class ScenarioTests(unittest.TestCase):
    def test_v2_scenarios_are_deterministic(self) -> None:
        config = load_v2_config(V2_DEV)
        left = generate_resource_scenario(config, 7103, "PRICE_SHOCK")
        right = generate_resource_scenario(config, 7103, "PRICE_SHOCK")
        self.assertEqual(left.scientific_hash(), right.scientific_hash())
        self.assertNotEqual(left.difficulty, "")

    def test_methods_do_not_receive_difficulty_in_agent_namespace(self) -> None:
        config = load_v2_config(V2_DEV)
        scenario = generate_resource_scenario(config, 7103, "STATIC")
        self.assertIn(scenario.difficulty, {"easy", "medium", "hard"})


class ParetoTests(unittest.TestCase):
    def test_high_quality_high_cost_does_not_dominate_cheap_if_worse_on_tokens(self) -> None:
        high = MethodPoint("high", 0.9, 1000, 10, 100)
        low = MethodPoint("low", 0.5, 100, 1, 20)
        self.assertFalse(dominates(low, high))
        self.assertFalse(dominates(high, low))
        self.assertEqual({point.method for point in nondominated([high, low])}, {"high", "low"})


class ExperimentTests(unittest.TestCase):
    def test_paired_payloads_are_deterministic(self) -> None:
        config = load_v2_config(V2_DEV)
        small = replace(
            config,
            environment=replace(config.environment, regimes=("STATIC",)),
            methods=("always_high_compute", "v2_mycelial", "always_low_compute"),
        )
        with tempfile.TemporaryDirectory() as left_dir, tempfile.TemporaryDirectory() as right_dir:
            left = _scenario_job(small, 7103, "STATIC", left_dir, str(ROOT))
            right = _scenario_job(small, 7103, "STATIC", right_dir, str(ROOT))
            self.assertEqual(canonical_v2_payload(left), canonical_v2_payload(right))

    def test_ledger_matches_traces_and_budget_cap_is_recorded(self) -> None:
        config = load_v2_config(V2_DEV)
        small = replace(
            config,
            environment=replace(config.environment, regimes=("PRICE_SHOCK",)),
            methods=("always_high_compute", "v2_mycelial"),
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            run_v2_experiment(small, output, workers=1)
            audit = audit_resource_traces(output)
            self.assertTrue(audit["ok"], audit)
            payload = json.loads(next((output / "raw").rglob("*.json")).read_text(encoding="utf-8"))
            self.assertEqual(payload["scientific_payload"]["budget_pre"], config.resources.global_budget_tokens)

    def test_confirmatory_config_stays_locked(self) -> None:
        config = load_v2_config(ROOT / "experiments" / "v2" / "config.confirmatory.yaml")
        errors = validate_v2_config(config)
        self.assertTrue(any("Seeds file does not exist" in item for item in errors))

    def test_v2_validate_cli_accepts_development(self) -> None:
        self.assertEqual(main(["v2-validate", "--config", str(V2_DEV)]), 0)


if __name__ == "__main__":
    unittest.main()
