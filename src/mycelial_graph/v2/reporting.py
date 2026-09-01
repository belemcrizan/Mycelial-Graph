from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .types import V2ExperimentConfig


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def _figures(analysis: dict, output: Path) -> list[Path]:
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in analysis["group_metrics"]:
        grouped[row["method"]].append(row)
    paths = []

    plt.figure(figsize=(7.4, 4.6))
    for method, rows in sorted(grouped.items()):
        primary = [row for row in rows if row["regime"] == analysis["primary_regime"]]
        if not primary:
            continue
        row = primary[0]
        plt.scatter(row["tokens_mean"], row["quality_mean"], s=48, label=method)
        plt.annotate(method, (row["tokens_mean"], row["quality_mean"]), fontsize=7)
    plt.xlabel("Post-shock tokens (ledger, including router)")
    plt.ylabel("Post-shock expected quality")
    plt.grid(alpha=0.25)
    plt.legend(frameon=False, fontsize=7)
    plt.tight_layout()
    path = figures / "quality_token_frontier.png"
    plt.savefig(path, dpi=180)
    plt.close()
    paths.append(path)

    plt.figure(figsize=(7.4, 4.6))
    for method, rows in sorted(grouped.items()):
        primary = [row for row in rows if row["regime"] == analysis["primary_regime"]]
        if not primary:
            continue
        row = primary[0]
        plt.scatter(row["cost_mean"], row["quality_mean"], s=48, label=method)
        plt.annotate(method, (row["cost_mean"], row["quality_mean"]), fontsize=7)
    plt.xlabel("Post-shock monetary cost (simulated)")
    plt.ylabel("Post-shock expected quality")
    plt.grid(alpha=0.25)
    plt.legend(frameon=False, fontsize=7)
    plt.tight_layout()
    path = figures / "quality_cost_frontier.png"
    plt.savefig(path, dpi=180)
    plt.close()
    paths.append(path)
    return paths


def generate_v2_report(config: V2ExperimentConfig, output_directory: str | Path) -> Path:
    output = Path(output_directory).resolve()
    analysis = json.loads((output / "processed" / "analysis.json").read_text(encoding="utf-8"))
    figures = _figures(analysis, output)
    q = analysis["quality_noninferiority"]
    t = analysis["token_reduction"]
    warning = (
        "This is a confirmatory execution governed by MG-EXP-V2."
        if config.run_kind == "confirmatory"
        else "This is a development/pilot execution. It must not be presented as confirmatory evidence."
    )
    lines = [
        "# Mycelial Graph V2 - Experiment Report",
        "",
        f"**Protocol:** `{config.protocol_version}`  ",
        f"**Experiment:** `{config.experiment_id}`  ",
        f"**Run kind:** `{config.run_kind}`",
        "",
        f"> {warning}",
        "",
        "## Decision label",
        "",
        f"**{analysis['decision_label']}**",
        "",
        analysis["claim_boundary"],
        "",
        "## Quality non-inferiority (primary)",
        "",
        f"Regime `{analysis['primary_regime']}`: ΔQ (v2_mycelial − always_high_compute) = "
        f"**{_fmt(q['estimate'])}** (CI {_fmt(q['confidence_low'])} to {_fmt(q['confidence_high'])}; "
        f"one-sided lower bound {_fmt(q['one_sided_lower_bound'])}). Margin ε={q['margin']}. "
        f"Passed: **{q['passed']}**.",
        "",
        "## Conditional token reduction",
        "",
        f"ΔTokens = **{_fmt(t['estimate'])}** (one-sided upper bound {_fmt(t['one_sided_upper_bound'])}). "
        f"Passed: **{t['passed']}**. Totals include router and state-overhead tokens.",
        "",
        f"Pareto-nondominated methods at the primary regime: {', '.join(analysis['pareto_nondominated_methods']) or 'none'}.",
        "",
        "## Group metrics",
        "",
        "| Regime | Method | N | Quality | Tokens | Router tokens | Cost | Latency | Success | RRT |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in analysis["group_metrics"]:
        lines.append(
            f"| {row['regime']} | {row['method']} | {row['trials']} | {_fmt(row['quality_mean'])} | "
            f"{row['tokens_mean']:.0f} | {row['router_tokens_mean']:.0f} | {_fmt(row['cost_mean'])} | "
            f"{row['latency_mean']:.0f} | {row['success_mean'] * 100:.1f}% | {_fmt(row['rrt_mean'])} |"
        )
    lines.extend(
        [
            "",
            "## Figures",
            "",
            *[f"![{path.stem}](figures/{path.name})" for path in figures],
            "",
            "## Interpretation boundary",
            "",
            "- Token savings without quality non-inferiority is not a V2 success.",
            "- Always-low-compute can look efficient on tokens while failing quality; that is a control, not a target.",
            "- Physarum is not a fungus; mechanisms here are fungal-inspired candidate operators.",
            "- Development numbers cannot promote the method.",
            "",
        ]
    )
    report_path = output / "REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
