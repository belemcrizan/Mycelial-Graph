"""Append a verified artifact identity to a hash-linked experiment ledger."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from mycelial_graph.artifacts import file_hash, verify_seal

ROOT = Path(__file__).resolve().parents[1]


def entry_hash(entry: dict) -> str:
    return hashlib.sha256(json.dumps(entry, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def record(output: Path, ledger: Path) -> None:
    verify_seal(output)
    manifest = json.loads((output / "manifest.json").read_text())
    analysis = json.loads((output / "processed/analysis.json").read_text())
    data = {
        "experiment_id": manifest["experiment_id"], "run_kind": manifest["run_kind"],
        "purpose": "V1 recovery evaluation" if manifest["run_kind"] != "pilot" else "Independent pilot variance and sample-size planning",
        "hypothesis": "Hierarchical vs edge-only recovery at rho=0.50 with rho=0 negative-transfer gate",
        "protocol": manifest["protocol_version"], "code_revision": manifest["code_revision"],
        "config_hash": manifest["config_hash"], "seed_hash": manifest["seeds_file_sha256"],
        "artifact": output.resolve().relative_to(ROOT).as_posix(),
        "artifact_seal_sha256": file_hash(output / "artifact_seal.json"),
        "result": analysis["decision_state"],
        "claim_impact": "No confirmatory claim" if manifest["run_kind"] != "confirmatory" else analysis["decision_state"],
    }
    ledger.parent.mkdir(parents=True, exist_ok=True)
    lock = ledger.with_suffix(".lock")
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.close(descriptor)
        previous = "0" * 64
        records = [json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
        for record in records:
            payload = {key: value for key, value in record.items() if key != "entry_sha256"}
            if payload["previous_sha256"] != previous or record["entry_sha256"] != entry_hash(payload):
                raise ValueError("Existing experiment ledger was modified.")
            previous = record["entry_sha256"]
        if any(record["artifact_seal_sha256"] == data["artifact_seal_sha256"] for record in records):
            return
        data["previous_sha256"] = previous
        data["entry_sha256"] = entry_hash(data)
        with ledger.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(data, sort_keys=True) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        lock.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ledger", default=str(ROOT / "research/experiment_ledger.jsonl"))
    args = parser.parse_args()
    record(Path(args.output), Path(args.ledger))
