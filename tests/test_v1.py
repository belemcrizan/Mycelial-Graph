from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

from mycelial_graph.analysis.metrics import sustained_recovery_time
from mycelial_graph.environment import generate_scenario_family
from mycelial_graph.runner.checkpoint import canonical_scientific_payload
from mycelial_graph.runner.experiment import _scenario_job, run_experiment
from mycelial_graph.types import DecisionRecord, load_config
from mycelial_graph.validation import validate_config, validate_result_payload


ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_CONFIG = ROOT / "experiments" / "v1" / "config.development.yaml"


class ScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(DEVELOPMENT_CONFIG)

    def test_development_config_is_valid(self) -> None:
        self.assertEqual(validate_config(self.config), [])

    def test_rho_family_is_deterministic_and_magnitude_is_constant(self) -> None:
        left = generate_scenario_family(self.config, 1103)
        right = generate_scenario_family(self.config, 1103)
        self.assertEqual(set(left), set(self.config.environment.rho_values))
        first_base = None
        for rho in self.config.environment.rho_values:
            self.assertEqual(left[rho].scientific_hash(), right[rho].scientific_hash())
            self.assertAlmostEqual(
                float(np.linalg.norm(left[rho].post_edge_means - left[rho].base_edge_means)),
                self.config.environment.shock_magnitude,
                places=10,
            )
            if first_base is None:
                first_base = left[rho].base_edge_means
            np.testing.assert_array_equal(first_base, left[rho].base_edge_means)

    def test_method_runs_are_deterministic_excluding_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as left_dir, tempfile.TemporaryDirectory() as right_dir:
            left = _scenario_job(self.config, 1103, 0.5, left_dir, str(ROOT))
            right = _scenario_job(self.config, 1103, 0.5, right_dir, str(ROOT))
            validate_result_payload(left, self.config)
            validate_result_payload(right, self.config)
            self.assertEqual(
                canonical_scientific_payload(left),
                canonical_scientific_payload(right),
            )


class MetricTests(unittest.TestCase):
    def test_censored_recovery_uses_horizon(self) -> None:
        config = load_config(DEVELOPMENT_CONFIG)
        records = [
            DecisionRecord(
                step=step,
                path=(0, 1),
                edge_ids=(0,),
                expected_utility=0.1,
                realized_utility=0.1,
                oracle_expected_utility=1.0,
                exploratory_edges=0,
                selected_edge_scores=(0.5,),
            )
            for step in range(config.horizon.total_steps)
        ]
        recovery, restricted, recovered = sustained_recovery_time(records, config.horizon)
        self.assertIsNone(recovery)
        self.assertEqual(restricted, config.horizon.post_shock_steps)
        self.assertFalse(recovered)


class CheckpointTests(unittest.TestCase):
    def test_completed_checkpoint_is_idempotent(self) -> None:
        config = load_config(DEVELOPMENT_CONFIG)
        one_rho = replace(
            config,
            environment=replace(config.environment, rho_values=(0.5,)),
            methods=("edge_only", "hierarchical"),
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            first_manifest = run_experiment(one_rho, output, workers=1)
            first_raw = next((output / "raw").rglob("*.json"))
            first_payload = json.loads(first_raw.read_text(encoding="utf-8"))
            second_manifest = run_experiment(one_rho, output, workers=1)
            second_payload = json.loads(first_raw.read_text(encoding="utf-8"))
            self.assertEqual(
                canonical_scientific_payload(first_payload),
                canonical_scientific_payload(second_payload),
            )
            manifest = json.loads(second_manifest.read_text(encoding="utf-8"))
            self.assertEqual(manifest["executed_job_count_this_invocation"], 0)
            self.assertTrue(first_manifest.exists())

    def test_serial_and_parallel_payloads_match(self) -> None:
        config = load_config(DEVELOPMENT_CONFIG)
        small = replace(
            config,
            environment=replace(config.environment, rho_values=(0.5,)),
            methods=("edge_only", "hierarchical"),
        )
        with tempfile.TemporaryDirectory() as serial_dir, tempfile.TemporaryDirectory() as parallel_dir:
            run_experiment(small, serial_dir, workers=1)
            run_experiment(small, parallel_dir, workers=2)
            serial_files = sorted((Path(serial_dir) / "raw").rglob("*.json"))
            parallel_files = sorted((Path(parallel_dir) / "raw").rglob("*.json"))
            self.assertEqual([path.name for path in serial_files], [path.name for path in parallel_files])
            for serial_path, parallel_path in zip(serial_files, parallel_files):
                serial_payload = json.loads(serial_path.read_text(encoding="utf-8"))
                parallel_payload = json.loads(parallel_path.read_text(encoding="utf-8"))
                self.assertEqual(
                    canonical_scientific_payload(serial_payload),
                    canonical_scientific_payload(parallel_payload),
                )


if __name__ == "__main__":
    unittest.main()
