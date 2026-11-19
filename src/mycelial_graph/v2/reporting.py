from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .types import V2ExperimentConfig


def _fmt(value: float | None, digits: int = 3) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def _figures(analysis: dict, output: Path) -> list[Path]:
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in analysis["group_metrics"]:
        grouped[row["method"]].append(row)
    paths = []

    plt.figure(figsize=(7.6, 4.6))
    for method, rows in sorted(grouped.items()):
        primary = [row for row in rows if row["regime"] == analysis["primary_regime"]]
        if not primary:
            continue
        row = primary[0]
        plt.scatter(row["tokens_mean"], row["quality_mean"], s=52, label=method)
        plt.annotate(method, (row["tokens_mean"], row["quality_mean"]), fontsize=7)
    plt.xlabel("Post-shock total tokens (including router + state overhead)")
    plt.ylabel("Post-shock failure-adjusted expected quality")
    plt.title(f"Quality vs Token Frontier — Regime: {analysis['primary_regime']}", fontsize=9)
    plt.grid(alpha=0.25)
    plt.legend(frameon=False, fontsize=7)
    plt.tight_layout()
    path = figures / "quality_token_frontier.png"
    plt.savefig(path, dpi=180)
    plt.close()
    paths.append(path)

    plt.figure(figsize=(7.6, 4.6))
    for method, rows in sorted(grouped.items()):
        primary = [row for row in rows if row["regime"] == analysis["primary_regime"]]
        if not primary:
            continue
        row = primary[0]
        plt.scatter(row["cost_mean"], row["quality_mean"], s=52, label=method)
        plt.annotate(method, (row["cost_mean"], row["quality_mean"]), fontsize=7)
    plt.xlabel("Post-shock monetary cost (simulated)")
    plt.ylabel("Post-shock failure-adjusted expected quality")
    plt.title(f"Quality vs Monetary Cost Frontier — Regime: {analysis['primary_regime']}", fontsize=9)
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
        f"This is a confirmatory execution governed by {config.protocol_version}."
        if config.run_kind == "confirmatory"
        else f"This is a {config.run_kind} execution. It must not be presented as confirmatory evidence."
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
        f"Regime `{analysis['primary_regime']}`: ΔQ (`v2_mycelial` − `always_high_compute`) = "
        f"**{_fmt(q['estimate'])}** (CI {_fmt(q['confidence_low'])} to {_fmt(q['confidence_high'])}; "
        f"one-sided lower bound {_fmt(q['one_sided_lower_bound'])}; Cohen's dz={_fmt(q.get('cohens_dz', 0.0))}). "
        f"Margin ε={q['margin']}. Passed: **{q['passed']}**.",
        "",
        "## Conditional token reduction",
        "",
        f"ΔTokens = **{_fmt(t['estimate'], 1)}** ({t.get('relative_reduction', 0.0) * 100:.1f}%; "
        f"one-sided upper bound {_fmt(t['one_sided_upper_bound'], 1)}; required practical gate "
        f"{t.get('required_relative_gate', -0.10) * 100:.1f}%). "
        f"Passed: **{t['passed']}**. Totals include router and state-overhead tokens.",
        "",
        f"Pareto-nondominated methods at `{analysis['primary_regime']}`: "
        f"{', '.join(analysis['pareto_nondominated_methods']) or 'none'}.",
        "",
        "## Group metrics (post-shock window)",
        "",
        "| Regime | Method | N | Quality | Tokens | Post Router Tok | Cost | Latency | Success | TPST | CPST | RRT |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in analysis["group_metrics"]:
        post_router = row.get("post_router_tokens_mean", row["router_tokens_mean"])
        tpst = f"{row['tokens_per_successful_task']:.0f}" if row.get("tokens_per_successful_task") else "n/a"
        cpst = f"{row['cost_per_successful_task']:.4f}" if row.get("cost_per_successful_task") else "n/a"
        lines.append(
            f"| {row['regime']} | {row['method']} | {row['trials']} | {_fmt(row['quality_mean'])} | "
            f"{row['tokens_mean']:.0f} | {post_router:.0f} | {_fmt(row['cost_mean'])} | "
            f"{row['latency_mean']:.0f} | {row['success_mean'] * 100:.1f}% | {tpst} | {cpst} | {_fmt(row['rrt_mean'])} |"
        )
    if analysis.get("secondary_baseline_contrasts"):
        lines.extend(
            [
                "",
                f"## Baseline contrasts at `{analysis['primary_regime']}` (Holm-Bonferroni adjusted)",
                "",
                "| Comparator | ΔQuality | ΔTokens (%) | Net Utility Diff | Effect Size (dz) | Raw p | Holm p |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for comp in analysis["secondary_baseline_contrasts"]:
            lines.append(
                f"| {comp['comparator']} | {_fmt(comp['delta_quality_mean'])} | "
                f"{comp['delta_tokens_relative'] * 100:.1f}% | {_fmt(comp['net_utility_diff_mean'])} | "
                f"{_fmt(comp['net_utility_cohens_dz'])} | {_fmt(comp['raw_p_value'])} | "
                f"{_fmt(comp['holm_adjusted_p_value'])} |"
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
            "- Always-low-compute can look efficient on tokens while failing quality on hard tasks; it is a control, not a target.",
            "- Biological mechanisms are falsifiable computational operators; any mechanism failing ablation should be disabled.",
            "- Non-confirmatory runs cannot promote a policy.",
            "",
        ]
    )
    report_path = output / "REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    return report_path
