"""Regression tests for V1 confirmatory reproduction integrity.

These tests encode the forensic EOL/seal/freeze findings. They must not rewrite
the historical REFUTED result, frozen N, seeds, or config hash.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mycelial_graph.protocol import (
    validate_confirmatory_execution_authorization,
    validate_confirmatory_freeze,
)
from mycelial_graph.runner.experiment import run_experiment
from mycelial_graph.science.canonical_bytes import (
    CONFIRMATORY_METHOD_TRIALS,
    CONFIRMATORY_N,
    CONFIRMATORY_SCIENTIFIC_JOBS,
    FROZEN_CONFIG_HASH,
    FROZEN_SEED_GIT_BLOB_LF_SHA256,
    FROZEN_SEED_SHA256,
    HISTORICAL_CRLF_SEAL_SHA256,
    PRIMARY_ESTIMATE,
    SealIdentity,
    canonicalize_text_bytes,
    contains_non_lf_newlines,
    historical_text_identity_matches,
    lf_to_crlf,
    normalize_newlines,
    sha256_canonical_text,
    sha256_lf_text,
    sha256_raw,
    verify_frozen_seed_identity,
    verify_historical_text_seal,
    verify_raw_bytes_seal,
)
from mycelial_graph.science.reproduction import (
    HISTORICAL_FREEZE_RELATIVE,
    HISTORICAL_FREEZE_SUPPLEMENT_RELATIVE,
    REPRODUCTION_SUPPLEMENT_RELATIVE,
    method_trial_count,
    scientific_job_count,
    verify_historical_confirmatory_evidence,
    verify_historical_confirmatory_freeze,
    verify_reproduction_supplement,
)
from mycelial_graph.types import load_config
from mycelial_graph.validation import load_seeds, validate_config, validate_config_semantics

V1 = ROOT / "experiments" / "v1"
SEALED = V1 / "artifacts" / "confirmatory"


class EOLHashingTests(unittest.TestCase):
    def test_lf_text_canonical_hash(self) -> None:
        lf = b"alpha\nbeta\n"
        self.assertEqual(sha256_canonical_text(lf), hashlib.sha256(lf).hexdigest())

    def test_crlf_equivalent_canonical_hash(self) -> None:
        crlf = b"alpha\r\nbeta\r\n"
        self.assertEqual(sha256_canonical_text(crlf), sha256_canonical_text(b"alpha\nbeta\n"))

    def test_lf_and_crlf_canonical_hashes_are_equal(self) -> None:
        lf = b"seed=700000\nseed=700001\n"
        crlf = b"seed=700000\r\nseed=700001\r\n"
        self.assertEqual(sha256_lf_text(lf), sha256_lf_text(crlf))
        self.assertEqual(normalize_newlines(crlf), lf)

    def test_lf_and_crlf_raw_hashes_differ(self) -> None:
        lf = b"seed=700000\nseed=700001\n"
        crlf = b"seed=700000\r\nseed=700001\r\n"
        self.assertNotEqual(sha256_raw(lf), sha256_raw(crlf))

    def test_historical_report_crlf_reconstruction(self) -> None:
        reconstructed = lf_to_crlf((SEALED / "REPORT.md").read_bytes())
        self.assertEqual(sha256_raw(reconstructed), HISTORICAL_CRLF_SEAL_SHA256["REPORT.md"])

    def test_historical_manifest_crlf_reconstruction(self) -> None:
        reconstructed = lf_to_crlf((SEALED / "manifest.json").read_bytes())
        self.assertEqual(sha256_raw(reconstructed), HISTORICAL_CRLF_SEAL_SHA256["manifest.json"])

    def test_historical_analysis_crlf_reconstruction(self) -> None:
        reconstructed = lf_to_crlf((SEALED / "analysis.json").read_bytes())
        self.assertEqual(sha256_raw(reconstructed), HISTORICAL_CRLF_SEAL_SHA256["processed/analysis.json"])

    def test_arbitrary_textual_content_changes_still_fail(self) -> None:
        original = canonicalize_text_bytes((SEALED / "REPORT.md").read_bytes())
        mutated = original.replace(b"REFUTED", b"ACCEPTED", 1)
        self.assertNotEqual(original, mutated)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "REPORT.md"
            path.write_bytes(mutated)
            check = verify_historical_text_seal(
                path, HISTORICAL_CRLF_SEAL_SHA256["REPORT.md"], "REPORT.md"
            )
            self.assertIs(check.identity, SealIdentity.MISMATCH)
            self.assertFalse(check.ok)

    def test_binary_content_is_never_eol_normalized(self) -> None:
        png = SEALED / "figures" / "recovery_by_rho.png"
        raw = png.read_bytes()
        self.assertTrue(raw.startswith(b"\x89PNG"))
        expected = hashlib.sha256(raw).hexdigest()
        check = verify_raw_bytes_seal(png, expected, "figures/recovery_by_rho.png")
        self.assertIs(check.identity, SealIdentity.EXACT)
        injected = raw.replace(b"\n", b"\r\n", 1) if b"\n" in raw else raw + b"\r\n"
        self.assertNotEqual(sha256_raw(injected), expected)
        self.assertNotEqual(sha256_canonical_text(injected), expected)


class FrozenSeedTests(unittest.TestCase):
    def test_confirmatory_seed_canonical_hash_matches_frozen_hash(self) -> None:
        path = V1 / "seeds.confirmatory.txt"
        check = verify_frozen_seed_identity(path, FROZEN_SEED_SHA256)
        self.assertTrue(check.ok, check.message)
        self.assertEqual(len(load_seeds(path)), CONFIRMATORY_N)
        lf = canonicalize_text_bytes(path.read_bytes())
        self.assertEqual(sha256_canonical_text(lf), FROZEN_SEED_GIT_BLOB_LF_SHA256)
        self.assertEqual(sha256_raw(lf_to_crlf(lf)), FROZEN_SEED_SHA256)

    def test_crlf_seed_materialization_is_canonicalized_to_frozen_hash(self) -> None:
        lf = canonicalize_text_bytes((V1 / "seeds.confirmatory.txt").read_bytes())
        crlf = lf_to_crlf(lf)
        self.assertNotEqual(sha256_raw(lf), sha256_raw(crlf))
        self.assertEqual(sha256_raw(crlf), FROZEN_SEED_SHA256)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "seeds.confirmatory.txt"
            path.write_bytes(crlf)
            check = verify_frozen_seed_identity(path, FROZEN_SEED_SHA256)
            self.assertTrue(check.ok, check.message)
            self.assertEqual(load_seeds(path), load_seeds(V1 / "seeds.confirmatory.txt"))
            path.write_bytes(lf)
            check = verify_frozen_seed_identity(path, FROZEN_SEED_SHA256)
            self.assertTrue(check.ok, check.message)

    def test_seed_content_mutation_fails(self) -> None:
        seeds = load_seeds(V1 / "seeds.confirmatory.txt")
        mutated = [seed + 1 if i == 0 else seed for i, seed in enumerate(seeds)]
        payload = "".join(f"{seed}\n" for seed in mutated).encode("ascii")
        self.assertFalse(historical_text_identity_matches(payload, FROZEN_SEED_SHA256))

    def test_seed_ordering_mutation_fails(self) -> None:
        seeds = load_seeds(V1 / "seeds.confirmatory.txt")
        reordered = [seeds[1], seeds[0], *seeds[2:]]
        payload = "".join(f"{seed}\n" for seed in reordered).encode("ascii")
        self.assertFalse(historical_text_identity_matches(payload, FROZEN_SEED_SHA256))
        self.assertEqual(sorted(reordered), sorted(seeds))


class FreezeContractTests(unittest.TestCase):
    def test_historical_freeze_is_recognized_as_historical_schema(self) -> None:
        freeze = json.loads((V1 / "artifacts" / "CONFIRMATORY_FREEZE.json").read_text(encoding="utf-8"))
        self.assertNotEqual(freeze.get("schema_version"), 1)
        self.assertNotEqual(freeze.get("status"), "frozen")
        self.assertEqual(freeze["protocol_version"], "MG-EXP-V1")
        self.assertEqual(freeze["required_confirmatory_pairs"], 97)
        self.assertEqual(freeze["status"], "SAMPLE_SIZE_RECORDED_SEEDS_SELECTED_CONFIRMATORY_NOT_EXECUTED")
        self.assertEqual(freeze["confirmatory_config_hash"], FROZEN_CONFIG_HASH)
        self.assertEqual(freeze["seeds_sha256"], FROZEN_SEED_SHA256)

    def test_freeze_supplement_is_recognized_separately(self) -> None:
        supplement = json.loads((V1 / "artifacts" / "CONFIRMATORY_FREEZE_SUPPLEMENT.json").read_text(encoding="utf-8"))
        self.assertEqual(supplement["supplement_to"], HISTORICAL_FREEZE_RELATIVE)
        self.assertEqual(supplement["audit_commit"], "5f314d2dfb15f508dfd4e630e8c0e49031e60c6a")
        self.assertNotEqual(supplement["supplement_to"], HISTORICAL_FREEZE_SUPPLEMENT_RELATIVE)

    def test_historical_reproduction_does_not_require_modern_freeze_schema(self) -> None:
        result = verify_historical_confirmatory_evidence(ROOT)
        self.assertTrue(result.ok, result.errors)
        freeze_path = V1 / "CONFIRMATORY_FREEZE.json"
        self.assertFalse(freeze_path.exists())

    def test_copying_historical_freeze_does_not_authorize_execution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for path in V1.iterdir():
                if path.is_file():
                    shutil.copy(path, target / path.name)
            shutil.copy(V1 / "artifacts" / "CONFIRMATORY_FREEZE.json", target / "CONFIRMATORY_FREEZE.json")
            config = load_config(target / "config.confirmatory.yaml")
            errors = validate_confirmatory_execution_authorization(config)
            self.assertTrue(errors)
            self.assertTrue(any("schema_version=1" in error and "status=frozen" in error for error in errors))

    def test_new_confirmatory_execution_requires_authorization_gate(self) -> None:
        config = load_config(V1 / "config.confirmatory.yaml")
        self.assertEqual(validate_config(config), [])
        self.assertEqual(validate_config_semantics(config), [])
        errors = validate_confirmatory_execution_authorization(config)
        self.assertTrue(errors)
        self.assertTrue(any("CONFIRMATORY_FREEZE" in error for error in errors))
        self.assertEqual(validate_confirmatory_freeze(config), errors)

    def test_execution_cannot_bypass_freeze_validation(self) -> None:
        config = load_config(V1 / "config.confirmatory.yaml")
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError) as ctx:
                run_experiment(config, directory)
            message = str(ctx.exception)
            self.assertIn("not authorized", message.lower())
            self.assertIn("CONFIRMATORY_FREEZE", message)
            self.assertFalse((Path(directory) / "manifest.json").exists())

    def test_validate_config_passing_is_not_execution_authorization(self) -> None:
        config = load_config(V1 / "config.confirmatory.yaml")
        self.assertEqual(validate_config(config), [])
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                run_experiment(config, Path(directory) / "out")


class ReproductionIntegrityTests(unittest.TestCase):
    def test_refuted_is_a_valid_scientific_result_state(self) -> None:
        evidence = json.loads((SEALED / "CONFIRMATORY_EVIDENCE.json").read_text(encoding="utf-8"))
        self.assertEqual(evidence["result_state"]["state"], "REFUTED")
        result = verify_historical_confirmatory_evidence(ROOT)
        self.assertTrue(result.ok, result.errors)

    def test_primary_estimate_matches_historical_value(self) -> None:
        evidence = json.loads((SEALED / "CONFIRMATORY_EVIDENCE.json").read_text(encoding="utf-8"))
        self.assertAlmostEqual(float(evidence["primary_contrast"]["estimate"]), PRIMARY_ESTIMATE, places=12)

    def test_historical_eol_equivalent_seals_are_reported_explicitly(self) -> None:
        result = verify_historical_confirmatory_evidence(ROOT)
        text_checks = [row for row in result.seal_checks if row.artifact in HISTORICAL_CRLF_SEAL_SHA256]
        self.assertEqual(len(text_checks), 3)
        for row in text_checks:
            self.assertIn(row.identity, {SealIdentity.EXACT, SealIdentity.HISTORICAL_EOL_EQUIVALENT})
            if row.identity is SealIdentity.HISTORICAL_EOL_EQUIVALENT:
                self.assertIn("historical CRLF seal verified from canonical LF content", row.message)

    def test_genuine_seal_mutation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_bytes(b'{"tampered": true}\n')
            check = verify_historical_text_seal(
                path, HISTORICAL_CRLF_SEAL_SHA256["manifest.json"], "manifest.json"
            )
            self.assertIs(check.identity, SealIdentity.MISMATCH)

    def test_png_raw_hashes_match_exactly(self) -> None:
        result = verify_historical_confirmatory_evidence(ROOT)
        pngs = [row for row in result.seal_checks if row.artifact.startswith("figures/")]
        self.assertEqual(len(pngs), 2)
        for row in pngs:
            self.assertIs(row.identity, SealIdentity.EXACT, row.message)

    def test_missing_required_evidence_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            errors = verify_historical_confirmatory_freeze(Path(directory))
            self.assertTrue(errors)
            self.assertTrue(any("missing" in error.lower() for error in errors))

    def test_malformed_supplement_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / REPRODUCTION_SUPPLEMENT_RELATIVE
            path.parent.mkdir(parents=True)
            path.write_text("{not json", encoding="utf-8")
            errors = verify_reproduction_supplement(root)
            self.assertTrue(errors)
            self.assertTrue(any("malformed" in error.lower() for error in errors))
            path.write_text("{}\n", encoding="utf-8")
            errors = verify_reproduction_supplement(root)
            self.assertTrue(errors)
            self.assertTrue(any("missing fields" in error for error in errors))

    def test_failed_validation_never_prints_ok(self) -> None:
        import reproduce_confirmatory as rc

        failures: list[str] = []
        buf = io.StringIO()
        errors = ["Confirmatory freeze invalid: missing committed CONFIRMATORY_FREEZE.json"]
        with contextlib.redirect_stdout(buf):
            rc.check(not errors, "validate", rc.format_validation_detail(errors), failures)
        text = buf.getvalue()
        self.assertIn("[FAIL] validate:", text)
        self.assertNotIn("[FAIL] validate: ok", text)
        self.assertIn("missing committed CONFIRMATORY_FREEZE.json", text)
        self.assertIn("missing committed CONFIRMATORY_FREEZE.json", failures[0])

    def test_actual_validation_error_text_appears(self) -> None:
        import reproduce_confirmatory as rc

        self.assertEqual(rc.format_validation_detail([]), "ok")
        self.assertEqual(rc.format_validation_detail(["alpha", "beta"]), "alpha; beta")
        self.assertNotEqual(rc.format_validation_detail(["broken"]), "ok")

    def test_method_trial_counting_semantics(self) -> None:
        self.assertEqual(scientific_job_count(n_pairs=97, n_rho=5), 485)
        self.assertEqual(method_trial_count(n_pairs=97, n_rho=5, n_methods=4), 1940)
        self.assertEqual(CONFIRMATORY_SCIENTIFIC_JOBS, 485)
        self.assertEqual(CONFIRMATORY_METHOD_TRIALS, 1940)
        self.assertNotEqual(CONFIRMATORY_SCIENTIFIC_JOBS, CONFIRMATORY_METHOD_TRIALS)

    def test_eol_compatibility_is_not_defined_for_arbitrary_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "notes.md"
            path.write_bytes(b"hello\n")
            with self.assertRaises(ValueError):
                verify_historical_text_seal(path, "abc", "notes.md")


class CrossPlatformNewlineTests(unittest.TestCase):
    def test_lf_checkout_simulation(self) -> None:
        payload = b"700000\n700001\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "seeds.txt"
            path.write_bytes(payload)
            self.assertFalse(contains_non_lf_newlines(path.read_bytes()))
            self.assertEqual(path.read_bytes(), payload)

    def test_crlf_input_materialization_simulation(self) -> None:
        payload = b"700000\r\n700001\r\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "seeds.txt"
            path.write_bytes(payload)
            self.assertTrue(contains_non_lf_newlines(path.read_bytes()))
            self.assertEqual(canonicalize_text_bytes(path.read_bytes()), b"700000\n700001\n")

    def test_behavior_is_independent_of_os_linesep(self) -> None:
        original = os.linesep
        try:
            for fake in ("\n", "\r\n"):
                os.linesep = fake
                self.assertEqual(lf_to_crlf(b"a\nb\n"), b"a\r\nb\r\n")
                self.assertEqual(canonicalize_text_bytes(b"a\r\nb\r\n"), b"a\nb\n")
        finally:
            os.linesep = original

    def test_no_test_depends_on_platform_newline_defaults(self) -> None:
        self.assertEqual(canonicalize_text_bytes(b"x\r\ny"), canonicalize_text_bytes(b"x\ny"))
        self.assertNotEqual(os.linesep, None)

    def test_repository_git_blobs_of_frozen_text_are_lf(self) -> None:
        import subprocess

        committed = [
            "experiments/v1/seeds.confirmatory.txt",
            "experiments/v1/seeds.confirmatory.pool.txt",
            "experiments/v1/config.confirmatory.yaml",
            "experiments/v1/artifacts/confirmatory/REPORT.md",
            "experiments/v1/artifacts/confirmatory/manifest.json",
            "experiments/v1/artifacts/confirmatory/analysis.json",
            "experiments/v1/artifacts/confirmatory/CONFIRMATORY_EVIDENCE.json",
            "experiments/v1/artifacts/CONFIRMATORY_FREEZE.json",
        ]
        for rel in committed:
            blob = subprocess.check_output(["git", "cat-file", "-p", f"HEAD:{rel}"], cwd=ROOT)
            self.assertFalse(contains_non_lf_newlines(blob), rel)


class DiagnosticsImportTests(unittest.TestCase):
    def test_reproduce_module_uses_error_preserving_validate_detail(self) -> None:
        import inspect
        import reproduce_confirmatory as rc

        source = inspect.getsource(rc.main)
        self.assertIn("format_validation_detail", source)
        self.assertNotIn('check(validate_config(config) == [], "validate", "ok", failures)', source)


if __name__ == "__main__":
    unittest.main()
