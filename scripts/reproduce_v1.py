"""Run the unchanged development or pilot design through a sealed artifact."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from mycelial_graph.analysis.aggregate import analyze_results
from mycelial_graph.analysis.power import estimate_confirmatory_sample_size
from mycelial_graph.artifacts import load_validated_trials, seal_artifact, verify_seal
from mycelial_graph.reporting import generate_report
from mycelial_graph.runner.experiment import run_experiment
from mycelial_graph.types import load_config

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("development", "pilot"), default="development")
    parser.add_argument("--output", required=True)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    config = load_config(ROOT / "experiments/v1" / f"config.{args.kind}.yaml")
    if (output / "artifact_seal.json").exists():
        load_validated_trials(config, output)
        print(json.dumps({"action": "verified existing artifact", **verify_seal(output)}, indent=2))
        return
    run_experiment(config, output, args.workers)
    analyze_results(config, output)
    if args.kind == "pilot":
        estimate_confirmatory_sample_size(config, output)
    generate_report(config, output)
    seal_artifact(config, output)
    print(json.dumps({"action": "executed and sealed", "kind": args.kind, **verify_seal(output)}, indent=2))


if __name__ == "__main__":
    main()
