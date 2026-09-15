from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

import numpy as np

from mycelial_graph.analysis.aggregate import _paired_arrays, analyze_results
from mycelial_graph.analysis.bootstrap import BootstrapResult, paired_relative_effect
from mycelial_graph.analysis.power import estimate_confirmatory_sample_size
from mycelial_graph.artifacts import ArtifactError, file_hash, load_validated_trials, seal_artifact, verify_seal
from mycelial_graph.environment import generate_scenario_family
from mycelial_graph.reporting import generate_report
from mycelial_graph.runner.experiment import run_experiment
from mycelial_graph.types import load_config
from mycelial_graph.validation import validate_config

ROOT = Path(__file__).resolve().parents[1]
BASE = load_config(ROOT / "experiments/v1/config.development.yaml")


class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory()
        cls.reference = Path(cls.temp.name) / "reference"
        cls.config = replace(BASE, environment=replace(BASE.environment, rho_values=(0.0, 0.5)))
        run_experiment(cls.config, cls.reference, workers=1)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "artifact"
        shutil.copytree(self.reference, self.output)

    def alter_raw(self, edit) -> None:
        path = next((self.output / "raw").rglob("*.json"))
        payload = json.loads(path.read_text())
        edit(payload["scientific_payload"])
        path.write_text(json.dumps(payload))
        # An internally consistent checksum is not sufficient: semantics matter.
        manifest = json.loads((self.output / "manifest.json").read_text())
        manifest["files"][path.relative_to(self.output).as_posix()] = file_hash(path)
        (self.output / "manifest.json").write_text(json.dumps(manifest))

    def test_complete_four_method_population_passes(self) -> None:
        trials, provenance = load_validated_trials(self.config, self.output)
        self.assertEqual(len(trials), 40)
        self.assertEqual(provenance["scenario_count"], 10)
        self.assertEqual(provenance["provenance_level"], "snapshotted")

    def test_missing_pair_is_rejected_before_statistics(self) -> None:
        next((self.output / "raw").rglob("*.json")).unlink()
        with self.assertRaisesRegex(ArtifactError, "population"):
            analyze_results(self.config, self.output)
        self.assertFalse((self.output / "processed/analysis.json").exists())

    def test_extra_raw_record_is_rejected(self) -> None:
        path = next((self.output / "raw").rglob("*.json"))
        shutil.copy(path, path.parent / "seed-999999.json")
        with self.assertRaises(ArtifactError):
            load_validated_trials(self.config, self.output)

    def test_modified_trace_cannot_be_rehashed_by_resume(self) -> None:
        trace = next((self.output / "traces").glob("*.gz"))
        trace.write_bytes(b"corrupted")
        before = (self.output / "manifest.json").read_bytes()
        with self.assertRaisesRegex(ArtifactError, "modified"):
            run_experiment(self.config, self.output)
        self.assertEqual((self.output / "manifest.json").read_bytes(), before)

    def test_duplicate_method_rejected_even_with_updated_hash(self) -> None:
        self.alter_raw(lambda p: p["results"].append(p["results"][0]))
        with self.assertRaisesRegex(ValueError, "exactly"):
            load_validated_trials(self.config, self.output)

    def test_foreign_config_in_pair_rejected(self) -> None:
        self.alter_raw(lambda p: p["results"][0].update(config_hash="0" * 64))
        with self.assertRaisesRegex(ValueError, "config_hash"):
            load_validated_trials(self.config, self.output)

    def test_mixed_code_revision_rejected(self) -> None:
        self.alter_raw(lambda p: p["results"][0].update(code_commit="unrelated"))
        with self.assertRaisesRegex(ArtifactError, "revisions"):
            load_validated_trials(self.config, self.output)

    def test_nonadministrative_status_suspends_inference(self) -> None:
        self.alter_raw(lambda p: p["results"][0].update(method_status="timeout"))
        with self.assertRaisesRegex(ArtifactError, "suspends"):
            analyze_results(self.config, self.output)

    def test_invalid_recovery_and_nonfinite_utility_rejected(self) -> None:
        self.alter_raw(lambda p: p["results"][0].update(final_expected_utility=float("nan")))
        with self.assertRaisesRegex(ValueError, "finite"):
            load_validated_trials(self.config, self.output)

    def test_development_cannot_be_relabelled_pilot(self) -> None:
        pilot = load_config(ROOT / "experiments/v1/config.pilot.yaml")
        with self.assertRaisesRegex(ArtifactError, "experiment_id"):
            estimate_confirmatory_sample_size(pilot, self.output)

    def test_passing_descriptive_gates_never_promotes_development(self) -> None:
        result = BootstrapResult(-0.3, -0.4, -0.2, -0.2, 0.001, 1000)
        with patch("mycelial_graph.analysis.aggregate.paired_relative_effect", return_value=result):
            path = analyze_results(self.config, self.output)
        analysis = json.loads(path.read_text())
        self.assertTrue(analysis["decision_gate"]["scientific_criteria_met"])
        self.assertFalse(analysis["decision_gate"]["promote_to_v1"])
        self.assertEqual(analysis["decision_state"], "inconclusive")

    def test_report_rejects_foreign_analysis(self) -> None:
        path = analyze_results(self.config, self.output)
        analysis = json.loads(path.read_text())
        analysis["provenance"]["input_manifest_sha256"] = "0" * 64
        path.write_text(json.dumps(analysis))
        with self.assertRaisesRegex(ArtifactError, "does not belong"):
            generate_report(self.config, self.output)

    def test_seal_verifies_and_blocks_reanalysis(self) -> None:
        analyze_results(self.config, self.output)
        generate_report(self.config, self.output)
        seal_artifact(self.config, self.output)
        self.assertTrue(verify_seal(self.output)["valid"])
        with self.assertRaisesRegex(ArtifactError, "sealed"):
            analyze_results(self.config, self.output)
        (self.output / "REPORT.md").write_text("changed")
        with self.assertRaisesRegex(ArtifactError, "changed"):
            verify_seal(self.output)

    def test_parallel_matches_every_trace_byte(self) -> None:
        other = Path(self.directory.name) / "parallel"
        run_experiment(self.config, other, workers=2)
        for trace in (self.output / "traces").glob("*.gz"):
            self.assertEqual(file_hash(trace), file_hash(other / "traces" / trace.name))

    def test_failure_retained_and_not_silently_rerun(self) -> None:
        other = Path(self.directory.name) / "failed"
        with patch("mycelial_graph.runner.trial.create_agent", side_effect=RuntimeError("injected failure")):
            with self.assertRaisesRegex(RuntimeError, "injected"):
                run_experiment(self.config, other)
        failure = json.loads(next((other / "failures").glob("*.json")).read_text())
        self.assertEqual(failure["method"], "edge_only")
        self.assertEqual(failure["exception_type"], "RuntimeError")
        self.assertFalse((other / "manifest.json").exists())
        with self.assertRaisesRegex(ArtifactError, "failures are retained"):
            run_experiment(self.config, other)


class ProtocolTests(unittest.TestCase):
    def test_module_command_propagates_failure_exit_status(self) -> None:
        result = subprocess.run([sys.executable, "-m", "mycelial_graph", "verify-seal", "--output", "missing-artifact"], cwd=ROOT, capture_output=True)
        self.assertNotEqual(result.returncode, 0)

    def test_seed_file_alone_does_not_unlock_confirmatory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for path in (ROOT / "experiments/v1").iterdir():
                if path.is_file():
                    shutil.copy(path, target / path.name)
            pool = (target / "seeds.confirmatory.pool.txt").read_text().splitlines()
            seeds = [line for line in pool if line and not line.startswith("#")][:2]
            (target / "seeds.confirmatory.txt").write_text("\n".join(seeds))
            errors = validate_config(load_config(target / "config.confirmatory.yaml"))
            self.assertTrue(any("CONFIRMATORY_FREEZE" in error for error in errors))

    def test_nonfinite_and_invalid_numeric_configs_fail(self) -> None:
        cases = [
            replace(BASE, environment=replace(BASE.environment, reward_noise_std=float("nan"))),
            replace(BASE, mycelial=replace(BASE.mycelial, learning_rate=float("inf"))),
            replace(BASE, horizon=replace(BASE.horizon, recovery_trailing_window=0)),
            replace(BASE, analysis=replace(BASE.analysis, bootstrap_samples=1.5)),
            replace(BASE, environment=replace(BASE.environment, rho_values=(0.5, 0.501))),
        ]
        for config in cases:
            with self.subTest(config=config):
                self.assertTrue(validate_config(config))

    def test_scenario_buffers_and_topology_are_immutable(self) -> None:
        scenario = generate_scenario_family(BASE, 1103)[0.5]
        for name in ("base_edge_means", "post_edge_means", "potential_rewards", "shock_vector"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                getattr(scenario, name).setflags(write=True)
        with self.assertRaises(TypeError):
            scenario.graph.outgoing[scenario.graph.source] = ()

    def test_pairing_never_discards_missing_control(self) -> None:
        rows = [{"scenario_id": "a", "rho": 0.5, "method": "hierarchical", "restricted_recovery_time": 10}]
        with self.assertRaisesRegex(ValueError, "Incomplete pair"):
            _paired_arrays(rows, 0.5, "hierarchical", "edge_only")

    def test_bootstrap_known_constant_relative_effect(self) -> None:
        control = np.array([10.0, 20.0, 40.0, 80.0])
        result = paired_relative_effect(control * 0.8, control, 1000, 0.95)
        self.assertAlmostEqual(result.estimate, -0.2)
        self.assertAlmostEqual(result.one_sided_upper_bound, -0.2)
        self.assertAlmostEqual(result.confidence_low, -0.2)
        with self.assertRaises(ValueError):
            paired_relative_effect(control, np.zeros(4), 1000, 0.95)

    def test_zero_pilot_variance_produces_no_sample_size(self) -> None:
        config = load_config(ROOT / "experiments/v1/config.pilot.yaml")
        rows = [{"scenario_id": str(seed), "rho": 0.5, "method": method, "restricted_recovery_time": 10}
                for seed in range(20) for method in ("edge_only", "hierarchical")]
        with tempfile.TemporaryDirectory() as directory, patch(
            "mycelial_graph.analysis.power.load_validated_trials", return_value=(rows, {"fixture": "synthetic"})
        ):
            result = json.loads(estimate_confirmatory_sample_size(config, directory).read_text())
        self.assertEqual(result["status"], "unestimable")
        self.assertIsNone(result["required_confirmatory_pairs"])
        self.assertFalse(result["confirmatory_ready"])


if __name__ == "__main__":
    unittest.main()
