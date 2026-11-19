"""Execute the non-confirmatory MG-EXP-V2.2 pilot, ablation, and scaling benchmark suite.

Strictly respects confirmatory locks: ``seeds.confirmatory.txt`` is never created or executed.
Transient raw traces are written under ``outputs/v2_2_*`` (gitignored) while deterministic
aggregate metrics are summarized to ``experiments/v2_2/PILOT_SUMMARY.json``.
"""

from __future__ import annotations

import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np

from mycelial_graph.validation import load_seeds
from mycelial_graph.v2.analysis import analyze_v2_results
from mycelial_graph.v2.audit import audit_resource_traces
from mycelial_graph.v2.config import load_v2_config
from mycelial_graph.v2.evaluation import budget_response_curve, run_voc_benchmark
from mycelial_graph.v2.evaluation.waste import decompose_waste, waste_identity_ok
from mycelial_graph.v2.reporting import generate_v2_report
from mycelial_graph.v2.runner import run_v2_experiment
from mycelial_graph.v2.validation import require_valid_v2_config, validate_v2_config

ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / "experiments" / "v2_2"
OUT_ROOT = ROOT / "outputs"


def _paired_ablation_contrasts(raw_dir: Path, regimes: tuple[str, ...], ablations: tuple[str, ...]) -> dict[str, Any]:
    by_regime_method: dict[tuple[str, str], dict[int, dict[str, float]]] = {}
    for raw_path in sorted(raw_dir.rglob("*.json")):
        payload = json.loads(raw_path.read_text(encoding="utf-8"))["scientific_payload"]
        regime = payload["regime"]
        seed = int(payload["seed"])
        for row in payload["results"]:
            m = row["method"]
            by_regime_method.setdefault((regime, m), {})[seed] = {
                "post_quality": float(row["post_quality"]),
                "post_tokens": float(row["post_tokens"]),
                "post_cost": float(row["post_cost"]),
                "rrt": float(row["restricted_recovery_time"]),
                "success_rate": float(row["success_rate"]),
                "router_tokens": float(row["post_router_tokens"]),
                "cpst": float(row["ledger"].get("cost_per_successful_task", 0.0)),
                "tpst": float(row["ledger"].get("tokens_per_successful_task", 0.0)),
            }

    contrasts: dict[str, dict[str, Any]] = {}
    for regime in regimes:
        base_map = by_regime_method.get((regime, "v2_mycelial"), {})
        seeds = sorted(base_map)
        if not seeds:
            continue
        contrasts[regime] = {}
        for abl in ablations:
            abl_map = by_regime_method.get((regime, abl), {})
            if set(abl_map) != set(seeds):
                continue
            dq = np.array([base_map[s]["post_quality"] - abl_map[s]["post_quality"] for s in seeds])
            dtok = np.array([base_map[s]["post_tokens"] - abl_map[s]["post_tokens"] for s in seeds])
            dcost = np.array([base_map[s]["post_cost"] - abl_map[s]["post_cost"] for s in seeds])
            drrt = np.array([base_map[s]["rrt"] - abl_map[s]["rrt"] for s in seeds])
            drouter = np.array([base_map[s]["router_tokens"] - abl_map[s]["router_tokens"] for s in seeds])
            contrasts[regime][abl] = {
                "n": len(seeds),
                "delta_quality_full_minus_ablated": round(float(np.mean(dq)), 6),
                "delta_tokens_full_minus_ablated": round(float(np.mean(dtok)), 2),
                "delta_cost_full_minus_ablated": round(float(np.mean(dcost)), 5),
                "delta_rrt_full_minus_ablated": round(float(np.mean(drrt)), 3),
                "delta_router_tokens_full_minus_ablated": round(float(np.mean(drouter)), 2),
                "full_mean_quality": round(float(np.mean([base_map[s]["post_quality"] for s in seeds])), 5),
                "ablated_mean_quality": round(float(np.mean([abl_map[s]["post_quality"] for s in seeds])), 5),
                "full_mean_rrt": round(float(np.mean([base_map[s]["rrt"] for s in seeds])), 3),
                "ablated_mean_rrt": round(float(np.mean([abl_map[s]["rrt"] for s in seeds])), 3),
            }
    return contrasts


def _audit_waste_all(raw_dir: Path) -> bool:
    for raw_path in sorted(raw_dir.rglob("*.json")):
        payload = json.loads(raw_path.read_text(encoding="utf-8"))["scientific_payload"]
        for row in payload["results"]:
            bd = decompose_waste(row["ledger"], success=row["success_rate"] >= 0.5, retrieval_used=True)
            if not waste_identity_ok(bd, row["ledger"]["total_tokens"]):
                return False
    return True


def main() -> int:
    started = time.perf_counter()

    # 1. Verify confirmatory remains strictly locked.
    conf_cfg = load_v2_config(EXP_DIR / "config.confirmatory.yaml")
    conf_errors = validate_v2_config(conf_cfg)
    if not any("Seeds file does not exist" in err for err in conf_errors):
        raise RuntimeError(f"Confirmatory lock invariant violated: {conf_errors}")

    # 2. Run Main Pilot Benchmark (N=24, 8 regimes, 12 methods).
    pilot_cfg = load_v2_config(EXP_DIR / "config.pilot.yaml")
    require_valid_v2_config(pilot_cfg)
    pilot_out = OUT_ROOT / "v2_2_pilot"
    run_v2_experiment(pilot_cfg, pilot_out, workers=1)
    pilot_analysis_path = analyze_v2_results(pilot_cfg, pilot_out)
    generate_v2_report(pilot_cfg, pilot_out)
    pilot_trace_audit = audit_resource_traces(pilot_out)
    pilot_waste_ok = _audit_waste_all(pilot_out / "raw")
    if not pilot_trace_audit["ok"] or not pilot_waste_ok:
        raise RuntimeError("Pilot resource or waste audit failed.")
    pilot_analysis = json.loads(Path(pilot_analysis_path).read_text(encoding="utf-8"))

    # 3. Run Biological Mechanism Ablation Suite (N=24, 6 regimes, 11 methods).
    abl_cfg = load_v2_config(EXP_DIR / "config.ablation.yaml")
    require_valid_v2_config(abl_cfg)
    abl_out = OUT_ROOT / "v2_2_ablation"
    run_v2_experiment(abl_cfg, abl_out, workers=1)
    analyze_v2_results(abl_cfg, abl_out)
    abl_trace_audit = audit_resource_traces(abl_out)
    if not abl_trace_audit["ok"]:
        raise RuntimeError("Ablation resource audit failed.")
    ablation_names = tuple(m for m in abl_cfg.methods if m.startswith("v2_no_"))
    ablation_contrasts = _paired_ablation_contrasts(
        abl_out / "raw",
        abl_cfg.environment.regimes,
        ablation_names,
    )

    # 4. Run Graph Scaling & Noise Sensitivity on Disjoint Development Seeds (N=10).
    dev_cfg = load_v2_config(EXP_DIR / "config.development.yaml")
    require_valid_v2_config(dev_cfg)
    dev_seeds = load_seeds(EXP_DIR / dev_cfg.seeds_file)
    scaling_rows: list[dict[str, Any]] = []
    for layers, alts in ((2, 3), (3, 3), (4, 3), (4, 4)):
        sc_cfg = replace(
            dev_cfg,
            graph=replace(dev_cfg.graph, internal_layers=layers, alternatives_per_layer=alts),
            environment=replace(dev_cfg.environment, regimes=("PRICE_SHOCK", "OUTAGE")),
            methods=("always_high_compute", "v1_edge_only", "structured_sw_ucb", "v2_mycelial"),
        )
        sc_out = OUT_ROOT / f"v2_2_scale_{layers}x{alts}"
        run_v2_experiment(sc_cfg, sc_out, workers=4)
        sc_an_path = analyze_v2_results(sc_cfg, sc_out)
        sc_an = json.loads(Path(sc_an_path).read_text(encoding="utf-8"))
        for row in sc_an["group_metrics"]:
            if row["regime"] == "PRICE_SHOCK":
                scaling_rows.append(
                    {
                        "graph": f"{layers}x{alts}",
                        "method": row["method"],
                        "mean_post_quality": round(float(row["quality_mean"]), 5),
                        "mean_post_tokens": round(float(row["tokens_mean"]), 1),
                        "mean_post_cost": round(float(row["cost_mean"]), 4),
                        "mean_rrt": round(float(row["rrt_mean"]), 2),
                        "mean_cpu_ms": round(float(row.get("policy_cpu_ms_mean", 0.0)), 3),
                    }
                )

    noise_rows: list[dict[str, Any]] = []
    for q_noise in (0.02, 0.08, 0.16):
        ns_cfg = replace(
            dev_cfg,
            environment=replace(
                dev_cfg.environment,
                regimes=("PRICE_SHOCK",),
                quality_noise_std=q_noise,
            ),
            methods=("always_high_compute", "v1_edge_only", "structured_sw_ucb", "v2_mycelial"),
        )
        ns_out = OUT_ROOT / f"v2_2_noise_{int(q_noise * 100):02d}"
        run_v2_experiment(ns_cfg, ns_out, workers=4)
        ns_an = json.loads(Path(analyze_v2_results(ns_cfg, ns_out)).read_text(encoding="utf-8"))
        for row in ns_an["group_metrics"]:
            noise_rows.append(
                {
                    "quality_noise_std": q_noise,
                    "method": row["method"],
                    "mean_post_quality": round(float(row["quality_mean"]), 5),
                    "mean_post_tokens": round(float(row["tokens_mean"]), 1),
                    "mean_rrt": round(float(row["rrt_mean"]), 2),
                }
            )

    budget_curve = budget_response_curve(
        dev_cfg,
        "v2_mycelial",
        tuple(dev_seeds[:5]),
        budgets=(5_000, 10_000, 20_000, 40_000, 80_000),
        output_directory=OUT_ROOT / "v2_2_budget_curve",
        project_root=ROOT,
    )
    voc_full = run_voc_benchmark(dev_cfg, tuple(dev_seeds[:5]))
    voc_summary = {k: v for k, v in voc_full.items() if k != "records"}

    elapsed_sec = round(time.perf_counter() - started, 2)
    summary = {
        "protocol_version": "MG-EXP-V2.2",
        "scientific_status": "pilot_and_development_only_non_confirmatory",
        "confirmatory_locked": True,
        "elapsed_wall_seconds": elapsed_sec,
        "pilot_trace_audit_ok": pilot_trace_audit["ok"],
        "pilot_waste_identity_ok": pilot_waste_ok,
        "ablation_trace_audit_ok": abl_trace_audit["ok"],
        "pilot_primary_regime": pilot_analysis["primary_regime"],
        "pilot_decision_label": pilot_analysis["decision_label"],
        "pilot_quality_noninferiority": pilot_analysis["quality_noninferiority"],
        "pilot_token_reduction": pilot_analysis["token_reduction"],
        "pilot_cost_reduction": pilot_analysis["cost_reduction"],
        "pilot_pareto_nondominated": pilot_analysis["pareto_nondominated_methods"],
        "pilot_secondary_contrasts": pilot_analysis.get("secondary_baseline_contrasts", []),
        "pilot_group_metrics": pilot_analysis["group_metrics"],
        "ablation_paired_contrasts": ablation_contrasts,
        "graph_scaling_price_shock": scaling_rows,
        "noise_sensitivity_price_shock": noise_rows,
        "budget_response_curve": budget_curve,
        "voc_calibration": voc_summary,
    }
    out_summary = EXP_DIR / "PILOT_SUMMARY.json"
    out_summary.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {out_summary} in {elapsed_sec:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
