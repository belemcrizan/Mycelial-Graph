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

    v2_validate = sub.add_parser("v2-validate", help="Validate a frozen V2 YAML configuration.")
    v2_validate.add_argument("--config", required=True)

    v2_experiment = sub.add_parser("v2-experiment", help="Run paired V2 resource scenarios.")
    v2_experiment.add_argument("--config", required=True)
    v2_experiment.add_argument("--output", required=True)
    v2_experiment.add_argument("--workers", type=int, default=1)

    v2_analyze = sub.add_parser("v2-analyze", help="Run V2 quality non-inferiority and Pareto analysis.")
    v2_analyze.add_argument("--config", required=True)
    v2_analyze.add_argument("--output", required=True)

    v2_report = sub.add_parser("v2-report", help="Generate the V2 Markdown report and figures.")
    v2_report.add_argument("--config", required=True)
    v2_report.add_argument("--output", required=True)

    v2_demo = sub.add_parser("v2-demo", help="Run the V2.0-alpha development demonstrator.")
    v2_demo.add_argument("--output", default="outputs/v2-demo")
    v2_demo.add_argument("--workers", type=int, default=1)

    v2_ablate = sub.add_parser("v2-ablate", help="Analyze biological-mechanism ablations from V2 output.")
    v2_ablate.add_argument("--config", required=True)
    v2_ablate.add_argument("--output", required=True)

    v2_pareto = sub.add_parser("v2-pareto", help="Print the quality-resource Pareto set from analyzed output.")
    v2_pareto.add_argument("--output", required=True)

    v2_audit = sub.add_parser("v2-resource-audit", help="Check traces against ledger totals.")
    v2_audit.add_argument("--output", required=True)
    return parser


def _default_demo_config() -> Path:
    return Path(__file__).resolve().parents[2] / "experiments" / "v1" / "config.development.yaml"


def _default_v2_demo_config() -> Path:
    return Path(__file__).resolve().parents[2] / "experiments" / "v2" / "config.development.yaml"


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

        if args.command == "v2-validate":
            from .v2.config import load_v2_config
            from .v2.validation import validate_v2_config

            config = load_v2_config(args.config)
            errors = validate_v2_config(config)
            if errors:
                print(json.dumps({"valid": False, "errors": errors}, indent=2))
                return 2
            print(json.dumps({"valid": True, "config": str(config.source_path)}, indent=2))
            return 0

        if args.command == "v2-demo":
            from .v2.analysis import analyze_v2_results
            from .v2.config import load_v2_config
            from .v2.reporting import generate_v2_report
            from .v2.runner import run_v2_experiment
            from .v2.validation import require_valid_v2_config

            config = load_v2_config(_default_v2_demo_config())
            require_valid_v2_config(config)
            manifest = run_v2_experiment(config, args.output, args.workers)
            analysis = analyze_v2_results(config, args.output)
            report = generate_v2_report(config, args.output)
            print("Mycelial Graph V2.0-alpha development demonstrator completed.")
            print(f"Manifest: {manifest}")
            print(f"Analysis: {analysis}")
            print(f"Report:   {report}")
            print("Scientific status: development-only; no confirmatory claim.")
            return 0

        if args.command == "v2-experiment":
            from .v2.config import load_v2_config
            from .v2.runner import run_v2_experiment
            from .v2.validation import require_valid_v2_config

            config = load_v2_config(args.config)
            require_valid_v2_config(config)
            print(run_v2_experiment(config, args.output, args.workers))
            return 0

        if args.command == "v2-analyze":
            from .v2.analysis import analyze_v2_results
            from .v2.config import load_v2_config
            from .v2.validation import require_valid_v2_config

            config = load_v2_config(args.config)
            require_valid_v2_config(config)
            print(analyze_v2_results(config, args.output))
            return 0

        if args.command == "v2-report":
            from .v2.config import load_v2_config
            from .v2.reporting import generate_v2_report
            from .v2.validation import require_valid_v2_config

            config = load_v2_config(args.config)
            require_valid_v2_config(config)
            print(generate_v2_report(config, args.output))
            return 0

        if args.command == "v2-ablate":
            from .v2.analysis import analyze_v2_results
            from .v2.config import load_v2_config
            from .v2.validation import require_valid_v2_config

            config = load_v2_config(args.config)
            require_valid_v2_config(config)
            path = analyze_v2_results(config, args.output)
            analysis = json.loads(Path(path).read_text(encoding="utf-8"))
            ablations = [
                row
                for row in analysis["group_metrics"]
                if row["method"].startswith("v2_")
                and row["regime"] == analysis["primary_regime"]
            ]
            print(json.dumps({"primary_regime": analysis["primary_regime"], "v2_methods": ablations}, indent=2))
            return 0

        if args.command == "v2-pareto":
            analysis_path = Path(args.output) / "processed" / "analysis.json"
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
            print(json.dumps(analysis["pareto_nondominated_methods"], indent=2))
            return 0

        if args.command == "v2-resource-audit":
            from .v2.audit import audit_resource_traces

            result = audit_resource_traces(args.output)
            print(json.dumps(result, indent=2))
            return 0 if result["ok"] else 3

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
