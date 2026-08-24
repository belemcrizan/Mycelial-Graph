from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .types import load_config
from .validation import require_valid_config, validate_config


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mycelial-graph",
        description="Reproducible experiments for adaptive AI execution graphs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate a frozen YAML configuration.")
    validate.add_argument("--config", required=True)

    experiment = sub.add_parser("experiment", help="Run paired immutable scenarios.")
    experiment.add_argument("--config", required=True)
    experiment.add_argument("--output", required=True)
    experiment.add_argument("--workers", type=int, default=1)

    analyze = sub.add_parser("analyze", help="Run the frozen paired analysis.")
    analyze.add_argument("--config", required=True)
    analyze.add_argument("--output", required=True)

    report = sub.add_parser("report", help="Generate Markdown and static figures.")
    report.add_argument("--config", required=True)
    report.add_argument("--output", required=True)

    power = sub.add_parser("sample-size", help="Estimate confirmatory N from pilot pairs.")
    power.add_argument("--config", required=True)
    power.add_argument("--output", required=True)
    power.add_argument("--power", type=float, default=0.80)

    demo = sub.add_parser("demo", help="Run the non-confirmatory demonstrator end to end.")
    demo.add_argument("--output", default="outputs/demo")
    demo.add_argument("--workers", type=int, default=1)
    return parser


def _default_demo_config() -> Path:
    return Path(__file__).resolve().parents[2] / "experiments" / "v1" / "config.development.yaml"


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "validate":
            config = load_config(args.config)
            errors = validate_config(config)
            if errors:
                print(json.dumps({"valid": False, "errors": errors}, indent=2))
                return 2
            print(json.dumps({"valid": True, "config": str(config.source_path)}, indent=2))
            return 0

        if args.command == "demo":
            from .analysis import analyze_results
            from .reporting import generate_report
            from .runner import run_experiment

            config_path = _default_demo_config()
            config = load_config(config_path)
            require_valid_config(config)
            manifest = run_experiment(config, args.output, args.workers)
            analysis = analyze_results(config, args.output)
            report = generate_report(config, args.output)
            print("Mycelial Graph V1 development demonstrator completed.")
            print(f"Manifest: {manifest}")
            print(f"Analysis: {analysis}")
            print(f"Report:   {report}")
            print("Scientific status: development-only; no confirmatory claim.")
            return 0

        config = load_config(args.config)
        require_valid_config(config)
        if args.command == "experiment":
            from .runner import run_experiment

            path = run_experiment(config, args.output, args.workers)
        elif args.command == "analyze":
            from .analysis import analyze_results

            path = analyze_results(config, args.output)
        elif args.command == "report":
            from .reporting import generate_report

            path = generate_report(config, args.output)
        elif args.command == "sample-size":
            from .analysis.power import estimate_confirmatory_sample_size

            path = estimate_confirmatory_sample_size(config, args.output, args.power)
        else:
            raise RuntimeError(f"Unhandled command: {args.command}")
        print(path)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
