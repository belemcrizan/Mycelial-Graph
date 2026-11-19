from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .types import load_config
from .validation import load_seeds, require_valid_config, validate_config


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

    audit = sub.add_parser("validate-artifacts", help="Verify a complete V1 population and all manifest hashes.")
    audit.add_argument("--config", required=True)
    audit.add_argument("--output", required=True)
    seal = sub.add_parser("seal-artifact", help="Seal raw data, statistics, report, figures, and provenance.")
    seal.add_argument("--config", required=True)
    seal.add_argument("--output", required=True)
    verify = sub.add_parser("verify-seal", help="Read-only verification of every sealed artifact byte.")
    verify.add_argument("--output", required=True)

    demo = sub.add_parser("demo", help="Run the non-confirmatory demonstrator end to end.")
    demo.add_argument("--output", default="outputs/v1-development")
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

    voc = sub.add_parser("voc-bench", help="Counterfactual VOC calibration on frozen V2 scenarios.")
    voc.add_argument("--config", required=True)

    budget = sub.add_parser("budget-curve", help="Quality versus budget curve for one method.")
    budget.add_argument("--config", required=True)
    budget.add_argument("--method", default="v2_mycelial")
    budget.add_argument("--output", default="outputs/v2_1-budget")

    waste = sub.add_parser("waste-audit", help="Decompose ledger totals into waste proxies.")
    waste.add_argument("--output", required=True)

    v2_viz = sub.add_parser("v2-viz", help="Render optional SVG topology and trace dashboard from V2 output.")
    v2_viz.add_argument("--config", required=True)
    v2_viz.add_argument("--output", required=True)
    v2_viz.add_argument("--method", default="v2_mycelial")

    sub.add_parser("real-smoke", help="Run local executable coding fixtures (not SWE-bench).")
    sub.add_parser("shadow-run", help="Shadow-mode recommendations on local coding fixtures.")

    claim = sub.add_parser("claim-audit", help="Audit the machine-readable claim matrix.")
    claim.add_argument("--matrix", default="docs/claim_evidence_matrix.yaml")

    collect = sub.add_parser("collect", help="Conservative trace collector (dry-run by default).")
    collect.add_argument("--dry-run", action=argparse.BooleanOptionalAction, default=True)
    collect.add_argument("--max-cost", type=float, default=0.0)
    collect.add_argument("--max-requests", type=int, default=1)
    collect.add_argument("--max-duration", type=float, default=1.0)
    collect.add_argument("--authorize-spend", action="store_true", default=False)

    ope = sub.add_parser("ope-check", help="IPS diagnostics on a JSONL logged-bandit file.")
    ope.add_argument("--input", required=True)

    freeze_run = sub.add_parser("bind-run", help="Bind hashes for a completed run without unlocking confirmatory.")
    freeze_run.add_argument("--config", required=True)
    freeze_run.add_argument("--output", required=True)
    freeze_run.add_argument("--destination", required=True)

    pooling_toy = sub.add_parser("pooling-toy", help="Run the isolated MG-EXP-POOLING-001 toy model.")
    pooling_toy.add_argument("--seed", type=int, default=0)

    sub.add_parser("evidence-audit", help="Print the next-stage audit document path.")
    return parser


def _default_demo_config() -> Path:
    return Path(__file__).resolve().parents[2] / "experiments" / "v1" / "config.development.yaml"


def _default_v2_demo_config() -> Path:
    return Path(__file__).resolve().parents[2] / "experiments" / "v2" / "config.development.yaml"


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "verify-seal":
            from .artifacts import verify_seal
            print(json.dumps(verify_seal(Path(args.output).resolve()), indent=2))
            return 0
        if args.command == "validate":
            import yaml

            try:
                config = load_config(args.config)
            except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
                print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
                return 2
            errors = validate_config(config)
            if errors:
                print(json.dumps({"valid": False, "errors": errors}, indent=2))
                return 2
            print(json.dumps({"valid": True, "config": str(config.source_path)}, indent=2))
            return 0

        if args.command == "v2-validate":
            import yaml

            from .v2.config import load_v2_config
            from .v2.validation import validate_v2_config

            try:
                v2_cfg = load_v2_config(args.config)
            except (OSError, ValueError, TypeError, KeyError, yaml.YAMLError) as exc:
                print(json.dumps({"valid": False, "errors": [str(exc)]}, indent=2))
                return 2
            errors = validate_v2_config(v2_cfg)
            if errors:
                print(json.dumps({"valid": False, "errors": errors}, indent=2))
                return 2
            print(json.dumps({"valid": True, "config": str(v2_cfg.source_path)}, indent=2))
            return 0

        if args.command == "v2-demo":
            from .v2.analysis import analyze_v2_results
            from .v2.config import load_v2_config
            from .v2.reporting import generate_v2_report
            from .v2.runner import run_v2_experiment
            from .v2.validation import require_valid_v2_config

            v2_cfg = load_v2_config(_default_v2_demo_config())
            require_valid_v2_config(v2_cfg)
            manifest = run_v2_experiment(v2_cfg, args.output, args.workers)
            analysis = analyze_v2_results(v2_cfg, args.output)
            report = generate_v2_report(v2_cfg, args.output)
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

            v2_cfg = load_v2_config(args.config)
            require_valid_v2_config(v2_cfg)
            print(run_v2_experiment(v2_cfg, args.output, args.workers))
            return 0

        if args.command == "v2-analyze":
            from .v2.analysis import analyze_v2_results
            from .v2.config import load_v2_config
            from .v2.validation import require_valid_v2_config

            v2_cfg = load_v2_config(args.config)
            require_valid_v2_config(v2_cfg)
            print(analyze_v2_results(v2_cfg, args.output))
            return 0

        if args.command == "v2-report":
            from .v2.config import load_v2_config
            from .v2.reporting import generate_v2_report
            from .v2.validation import require_valid_v2_config

            v2_cfg = load_v2_config(args.config)
            require_valid_v2_config(v2_cfg)
            print(generate_v2_report(v2_cfg, args.output))
            return 0

        if args.command == "v2-ablate":
            from .v2.analysis import analyze_v2_results
            from .v2.config import load_v2_config
            from .v2.validation import require_valid_v2_config

            v2_cfg = load_v2_config(args.config)
            require_valid_v2_config(v2_cfg)
            path = analyze_v2_results(v2_cfg, args.output)
            analysis_obj = json.loads(Path(path).read_text(encoding="utf-8"))
            ablations = [
                row
                for row in analysis_obj["group_metrics"]
                if row["method"].startswith("v2_")
                and row["regime"] == analysis_obj["primary_regime"]
            ]
            print(json.dumps({"primary_regime": analysis_obj["primary_regime"], "v2_methods": ablations}, indent=2))
            return 0

        if args.command == "v2-pareto":
            analysis_path = Path(args.output) / "processed" / "analysis.json"
            analysis_obj = json.loads(analysis_path.read_text(encoding="utf-8"))
            print(json.dumps(analysis_obj["pareto_nondominated_methods"], indent=2))
            return 0

        if args.command == "v2-resource-audit":
            from .v2.audit import audit_resource_traces

            result = audit_resource_traces(args.output)
            print(json.dumps(result, indent=2))
            return 0 if result["ok"] else 3

        if args.command == "voc-bench":
            from .v2.config import load_v2_config
            from .v2.evaluation import run_voc_benchmark
            from .v2.validation import require_valid_v2_config

            v2_cfg = load_v2_config(args.config)
            require_valid_v2_config(v2_cfg)
            seeds_path = v2_cfg.source_path.parent / v2_cfg.seeds_file
            seeds = tuple(load_seeds(seeds_path))
            print(json.dumps(run_voc_benchmark(v2_cfg, seeds), indent=2, default=str))
            return 0

        if args.command == "budget-curve":
            from .v2.config import load_v2_config
            from .v2.evaluation import budget_response_curve
            from .v2.validation import require_valid_v2_config

            v2_cfg = load_v2_config(args.config)
            require_valid_v2_config(v2_cfg)
            seeds_path = v2_cfg.source_path.parent / v2_cfg.seeds_file
            seeds = tuple(load_seeds(seeds_path))
            Path(args.output).mkdir(parents=True, exist_ok=True)
            result = budget_response_curve(
                v2_cfg,
                args.method,
                seeds,
                output_directory=Path(args.output),
                project_root=Path(__file__).resolve().parents[2],
            )
            out = Path(args.output) / "budget_curve.json"
            out.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(out)
            return 0

        if args.command == "v2-viz":
            import gzip

            from .environment.graph import LayeredDAG
            from .v2.config import load_v2_config
            from .v2.graph_model import ComputationalGraph
            from .v2.viz import render_topology_svg, render_trace_dashboard

            v2_cfg = load_v2_config(args.config)
            output_dir = Path(args.output)
            dag = LayeredDAG.complete_layered(
                v2_cfg.graph.internal_layers, v2_cfg.graph.alternatives_per_layer
            )
            comp_graph = ComputationalGraph.from_layered_dag(dag)
            fig_dir = output_dir / "figures"
            fig_dir.mkdir(parents=True, exist_ok=True)

            traces = sorted((output_dir / "traces").rglob(f"*-{args.method}.jsonl.gz"))
            if not traces:
                traces = sorted((output_dir / "traces").rglob("*.jsonl.gz"))
            active_edges: list[int] = []
            records: list[dict[str, object]] = []
            if traces:
                with gzip.open(traces[0], "rt", encoding="utf-8") as handle:
                    records = [json.loads(line) for line in handle if line.strip()]
                if records:
                    raw_edges = records[-1].get("edge_ids", [])
                    if isinstance(raw_edges, list):
                        active_edges = [int(eid) for eid in raw_edges]
            svg_path = fig_dir / "v2_topology.svg"
            svg_path.write_text(
                render_topology_svg(comp_graph, active_edges=active_edges),
                encoding="utf-8",
                newline="\n",
            )
            created = [str(svg_path)]
            if records:
                dash_path = render_trace_dashboard(
                    records,
                    fig_dir / "v2_trace_dashboard.png",
                    shock_step=v2_cfg.horizon.pre_shock_steps,
                    budget_cap=v2_cfg.resources.global_budget_tokens,
                )
                created.append(str(dash_path))
            print(json.dumps({"figures": created}, indent=2))
            return 0

        if args.command == "waste-audit":
            from .v2.evaluation.waste import decompose_waste, waste_identity_ok

            mismatches = []
            rows = []
            for path in sorted((Path(args.output) / "raw").rglob("*.json")):
                payload = json.loads(path.read_text(encoding="utf-8"))["scientific_payload"]
                for trial in payload["results"]:
                    breakdown = decompose_waste(
                        trial["ledger"],
                        success=trial["success_rate"] >= 0.5,
                        retrieval_used=True,
                    )
                    if not waste_identity_ok(breakdown, trial["ledger"]["total_tokens"]):
                        mismatches.append(trial["trial_id"])
                    rows.append(breakdown.to_dict())
            print(json.dumps({"ok": not mismatches, "mismatches": mismatches, "n": len(rows)}, indent=2))
            return 0 if not mismatches else 3

        if args.command == "real-smoke":
            from .v2.real import run_real_smoke

            print(json.dumps(run_real_smoke(), indent=2))
            return 0

        if args.command == "shadow-run":
            from .v2.real import default_smoke_tasks, run_real_task

            rows = [run_real_task(task, "always_high_compute", shadow=True).__dict__ for task in default_smoke_tasks()]
            print(json.dumps({"mode": "shadow", "results": rows}, indent=2))
            return 0

        if args.command == "claim-audit":
            from .science.claim_invariants import audit_v1_invariants
            from .science.scientific_state import audit_scientific_state
            from .v2.evaluation.claim_audit import audit_claims

            root = Path(__file__).resolve().parents[2]
            wording = audit_claims(args.matrix)
            invariants = audit_v1_invariants(args.matrix, root)
            scientific_state = audit_scientific_state(root)
            result = {
                "ok": wording["ok"] and invariants["ok"] and scientific_state["ok"],
                "wording_consistency": wording,
                "v1_readiness_invariants": invariants,
                "scientific_state": scientific_state,
            }
            print(json.dumps(result, indent=2))
            return 0 if result["ok"] else 3

        if args.command == "collect":
            from .external.collector import CollectorLimits, collect_workload

            result = collect_workload(
                [{"prompt_id": "dry-run-fixture", "task_type": "healthcheck"}],
                [{"provider": "none", "model": "none", "estimated_cost": 0.0, "endpoint": "dry-run"}],
                CollectorLimits(
                    dry_run=True if args.dry_run else False,
                    max_cost=args.max_cost,
                    max_requests=args.max_requests,
                    max_duration_seconds=args.max_duration,
                    authorize_spend=args.authorize_spend,
                ),
            )
            print(json.dumps(result, indent=2))
            return 0

        if args.command == "ope-check":
            from .external.ope import ips_estimate

            rows = [json.loads(line) for line in Path(args.input).read_text(encoding="utf-8").splitlines() if line.strip()]
            print(json.dumps(ips_estimate(rows).to_dict(), indent=2))
            return 0

        if args.command == "bind-run":
            from .science.freeze import bind_run_contract, write_contract

            payload = bind_run_contract(args.config, args.output, Path(__file__).resolve().parents[2])
            print(write_contract(args.destination, payload))
            return 0

        if args.command == "pooling-toy":
            from dataclasses import asdict

            from .pooling.toy_model import rho_grid

            print(json.dumps([asdict(row) for row in rho_grid(args.seed)], indent=2))
            return 0

        if args.command == "evidence-audit":
            path = Path(__file__).resolve().parents[2] / "docs" / "NEXT_STAGE_AUDIT.md"
            print(str(path))
            return 0 if path.exists() else 2

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
        elif args.command == "validate-artifacts":
            from .artifacts import load_validated_trials
            _, provenance = load_validated_trials(config, Path(args.output))
            print(json.dumps({"valid": True, **provenance}, indent=2))
            return 0
        elif args.command == "seal-artifact":
            from .artifacts import seal_artifact
            path = seal_artifact(config, Path(args.output).resolve())
        else:
            raise RuntimeError(f"Unhandled command: {args.command}")
        print(path)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
