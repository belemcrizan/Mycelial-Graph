from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from mycelial_graph.external.adapters import (
    adapt_arena_preference_row,
    adapt_incident_row,
    deduplicate_by_id,
    detect_overlapping_incidents,
)
from mycelial_graph.external.collector import CollectorLimits, CollectorSafetyError, collect_workload
from mycelial_graph.external.hashing import sha256_json
from mycelial_graph.external.licenses import require_transform_allowed
from mycelial_graph.external.ope import ips_estimate
from mycelial_graph.external.schemas import SchemaError, validate_logged_bandit


class LicenseTests(unittest.TestCase):
    def test_unknown_source_is_refused(self) -> None:
        with self.assertRaises(PermissionError):
            require_transform_allowed("not-a-source", for_redistribution=False)

    def test_gated_source_cannot_be_marked_for_redistribution(self) -> None:
        with self.assertRaises(PermissionError):
            require_transform_allowed("lmsys-chat-1m", for_redistribution=True)


class AdapterTests(unittest.TestCase):
    def test_arena_adapter_is_deterministic_and_hashes_stable(self) -> None:
        raw = {
            "id": "q1",
            "model_a": "a",
            "model_b": "b",
            "winner_model_a": 1,
            "winner_model_b": 0,
            "winner_tie": 0,
            "tstamp": 1_700_000_000,
        }
        left = adapt_arena_preference_row(
            raw, source_id="synthetic-fixture", source_version="test-v1"
        )
        right = adapt_arena_preference_row(
            raw, source_id="synthetic-fixture", source_version="test-v1"
        )
        self.assertTrue(left["ok"])
        self.assertEqual(left["record"]["record_sha256"], right["record"]["record_sha256"])
        self.assertEqual(left["record"]["winner"], "model_a")
        self.assertEqual(
            left["record"]["record_sha256"],
            sha256_json({k: v for k, v in left["record"].items() if k != "record_sha256"}),
        )

    def test_malformed_arena_row_is_not_silently_dropped(self) -> None:
        result = adapt_arena_preference_row(
            {"id": "q2"},
            source_id="synthetic-fixture",
            source_version="test-v1",
        )
        self.assertFalse(result["ok"])
        self.assertIsNone(result["record"])
        self.assertTrue(result["errors"])

    def test_duplicate_and_overlap_incidents(self) -> None:
        rows = [
            {
                "incident_id": "i1",
                "provider": "example",
                "service": "api",
                "incident_start_utc": "2026-01-01T00:00:00Z",
                "incident_end_utc": "2026-01-01T02:00:00Z",
                "status": "degraded",
                "source": "fixture",
                "retrieved_at_utc": "2026-01-02T00:00:00Z",
                "source_version": "1",
            },
            {
                "incident_id": "i2",
                "provider": "example",
                "service": "api",
                "incident_start_utc": "2026-01-01T01:00:00Z",
                "incident_end_utc": "2026-01-01T03:00:00Z",
                "status": "degraded",
                "source": "fixture",
                "retrieved_at_utc": "2026-01-02T00:00:00Z",
                "source_version": "1",
            },
        ]
        adapted = [adapt_incident_row(row)["record"] for row in rows]
        unique, duplicates = deduplicate_by_id(adapted + [adapted[0]], "incident_id")
        self.assertEqual(duplicates, ["i1"])
        self.assertEqual(len(unique), 2)
        overlaps = detect_overlapping_incidents(adapted)
        self.assertEqual(overlaps, [("i1", "i2")])

    def test_incident_without_timezone_fails(self) -> None:
        result = adapt_incident_row(
            {
                "incident_id": "i3",
                "provider": "example",
                "service": "api",
                "incident_start": "2026-01-01T00:00:00",
                "status": "degraded",
                "retrieved_at_utc": "2026-01-02T00:00:00Z",
            }
        )
        self.assertFalse(result["ok"])

    def test_partial_incident_missing_id_fails(self) -> None:
        result = adapt_incident_row({"provider": "example", "service": "api", "incident_start_utc": "2026-01-01T00:00:00Z", "status": "x"})
        self.assertFalse(result["ok"])


class OPETests(unittest.TestCase):
    def test_missing_propensity_is_error(self) -> None:
        with self.assertRaises(SchemaError):
            validate_logged_bandit({"timestamp_utc": "Z", "context_id": "c", "action": "a", "reward": 1.0, "policy_version": "p"})

    def test_near_zero_support_is_reported(self) -> None:
        records = [
            {
                "timestamp_utc": "2026-01-01T00:00:00Z",
                "context_id": "c",
                "action": "a",
                "reward": 1.0,
                "propensity": 0.0,
                "policy_version": "log-1",
            }
        ]
        report = ips_estimate(records, target_propensity={"a": 1.0})
        self.assertIsNone(report.estimate)
        self.assertGreaterEqual(report.support_violations, 1)
        self.assertGreaterEqual(report.near_zero_propensity, 1)


class CollectorTests(unittest.TestCase):
    def test_dry_run_default_does_not_require_spend(self) -> None:
        result = collect_workload(
            [{"prompt_id": "p1", "task_type": "toy"}],
            [{"provider": "local", "model": "fixture", "estimated_cost": 1.0, "endpoint": "none"}],
            CollectorLimits(dry_run=True, max_cost=0.0, max_requests=1, max_duration_seconds=5.0),
        )
        self.assertEqual(result["n_records"], 1)
        self.assertTrue(result["records"][0]["dry_run"])
        self.assertEqual(result["records"][0]["error_type"], "dry_run_no_network")

    def test_live_without_authorization_is_refused(self) -> None:
        with self.assertRaises(CollectorSafetyError):
            collect_workload([], [], CollectorLimits(dry_run=False, max_cost=1.0, authorize_spend=False))

    def test_cost_and_request_caps(self) -> None:
        result = collect_workload(
            [{"prompt_id": "p1"}, {"prompt_id": "p2"}],
            [{"provider": "local", "model": "fixture", "estimated_cost": 0.5}],
            CollectorLimits(dry_run=True, max_cost=0.0, max_requests=1, max_duration_seconds=5.0),
        )
        self.assertEqual(result["n_records"], 1)
        self.assertIn("max_requests", result["skipped"])


class CostVersionTests(unittest.TestCase):
    def test_model_and_cost_fields_are_retained_when_present(self) -> None:
        raw = {
            "id": "q3",
            "model_a": "gpt-4-1106-preview",
            "model_b": "gpt-4-0613",
            "winner": "model_b",
            "timestamp_utc": "2024-03-07T00:00:00Z",
            "pricing_source": "historical-not-current",
            "retrieved_at": "2026-09-14T00:00:00Z",
        }
        adapted = adapt_arena_preference_row(raw, source_id="synthetic-fixture", source_version="v")
        self.assertTrue(adapted["ok"])
        self.assertEqual(adapted["record"]["model_a"], "gpt-4-1106-preview")
        self.assertEqual(adapted["record"]["temporal_status"], "TIMESTAMPED")


class LedgerRoundtrip(unittest.TestCase):
    def test_append_only_file(self) -> None:
        from mycelial_graph.science.ledger import append_entry, read_ledger

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            entry = {
                "experiment_id": "MG-EXP-TOY",
                "protocol": "MG-EXP-POOLING-001",
                "commit": "deadbeef",
                "config": "none",
                "seeds": "none",
                "dataset": "synthetic-toy",
                "status": "development",
                "start": "2026-09-14T00:00:00Z",
                "finish": "2026-09-14T00:00:01Z",
                "result_classification": "not_evidence_for_v1",
                "artifact_location": str(path),
                "invalidations": [],
                "amendments": [],
                "notes": "unit test",
            }
            append_entry(path, entry)
            rows = read_ledger(path)
            self.assertEqual(len(rows), 1)
            append_entry(path, {**entry, "status": "sealed"})
            with self.assertRaises(ValueError):
                append_entry(path, {**entry, "status": "sealed"})


if __name__ == "__main__":
    unittest.main()
