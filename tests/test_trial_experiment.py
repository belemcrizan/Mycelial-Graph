from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from mycelial_graph.config import load_config
from mycelial_graph.experiment import run_experiment
from mycelial_graph.graph import LayeredGraph
from mycelial_graph.report import write_report
from mycelial_graph.trial import FrozenTrial


ROOT = Path(__file__).resolve().parents[1]


class TrialAndExperimentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(ROOT / "configs" / "v0_demo.yaml").copy()
        self.graph = LayeredGraph.from_config(self.config["graph"])

    def test_trial_generation_is_reproducible(self) -> None:
        first = FrozenTrial.generate(self.graph, self.config, 101)
        second = FrozenTrial.generate(self.graph, self.config, 101)
        other = FrozenTrial.generate(self.graph, self.config, 102)
        self.assertEqual(first.digest, second.digest)
        self.assertNotEqual(first.digest, other.digest)

    def test_trial_certifies_a_real_optimum_change(self) -> None:
        trial = FrozenTrial.generate(self.graph, self.config, 101)
        certification = trial.certification
        self.assertIn("model_balanced", certification["pre_oracle_nodes"])
        self.assertNotIn("model_balanced", certification["post_oracle_nodes"])
        self.assertIn("model_economy", certification["post_oracle_nodes"])
        minimum = self.config["experiment"]["minimum_oracle_margin"]
        self.assertGreaterEqual(certification["pre_oracle_margin"], minimum)
        self.assertGreaterEqual(certification["post_oracle_margin"], minimum)
        self.assertGreater(certification["shared_edge_fraction"], 0.0)

    def test_pre_shock_outcome_does_not_depend_on_future_shock(self) -> None:
        changed = load_config(ROOT / "configs" / "v0_demo.yaml").copy()
        changed["shock"]["quality_multiplier"] = 0.25
        first = FrozenTrial.generate(self.graph, self.config, 101)
        second = FrozenTrial.generate(self.graph, changed, 101)
        edge_id = "retriever_hybrid__model_balanced"
        self.assertEqual(first.observation(99, edge_id), second.observation(99, edge_id))
        self.assertNotEqual(first.observation(100, edge_id), second.observation(100, edge_id))

    def test_experiment_writes_machine_and_human_results(self) -> None:
        small = load_config(ROOT / "configs" / "v0_demo.yaml").copy()
        small["experiment"]["steps"] = 35
        small["experiment"]["shock_step"] = 15
        small["experiment"]["recovery_window"] = 3
        with tempfile.TemporaryDirectory() as directory:
            results = run_experiment(small, directory, seeds=[101], save_trials=True)
            report = write_report(results, Path(directory) / "REPORT.md")
            self.assertTrue((Path(directory) / "results.json").exists())
            self.assertTrue((Path(directory) / "trials" / "trial_seed_101.json.gz").exists())
            self.assertTrue(report.exists())
            payload = json.loads((Path(directory) / "results.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "mycelial-graph-results-v0")
            self.assertIn("mycelial_v0", payload["aggregate"])
            self.assertIn("no H1, H2, or H3", report.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
