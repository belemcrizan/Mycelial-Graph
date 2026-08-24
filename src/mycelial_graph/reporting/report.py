from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..types import ExperimentConfig


METHOD_LABELS = {
    "edge_only": "MG edge-only",
    "node_only": "Node-only",
    "hierarchical": "MG hierarchical",
    "structured_sw_ucb": "Structured SW-UCB",
}


def _fmt(value: float) -> str:
    return f"{value:.3f}"


def _make_figures(analysis: dict, output: Path) -> list[Path]:
    figures = output / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in analysis["group_metrics"]:
        grouped[row["method"]].append(row)

    paths = []
    for metric, ylabel, filename in [
        ("restricted_recovery_time_mean", "Mean restricted recovery time", "recovery_by_rho.png"),
        ("dynamic_regret_mean", "Mean post-shock dynamic regret", "regret_by_rho.png"),
    ]:
        plt.figure(figsize=(7.2, 4.4))
        for method, rows in sorted(grouped.items()):
            rows = sorted(rows, key=lambda row: row["rho"])
            plt.plot(
                [row["rho"] for row in rows],
                [row[metric] for row in rows],
                marker="o",
                label=METHOD_LABELS.get(method, method),
            )
        plt.xlabel("Shared shock fraction (rho)")
        plt.ylabel(ylabel)
        plt.grid(alpha=0.25)
        plt.legend(frameon=False)
        plt.tight_layout()
        path = figures / filename
        plt.savefig(path, dpi=180)
        plt.close()
        paths.append(path)
    return paths


def generate_report(config: ExperimentConfig, output_directory: str | Path) -> Path:
    output = Path(output_directory).resolve()
    analysis_path = output / "processed" / "analysis.json"
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    figures = _make_figures(analysis, output)
    primary = analysis["primary_contrast"]
    gate = analysis["decision_gate"]
    status_warning = (
        "This is a confirmatory execution governed by MG-EXP-V1."
        if config.run_kind == "confirmatory"
        else "This is a development/pilot execution. It must not be presented as confirmatory evidence."
    )
    lines = [
        "# Mycelial Graph V1 - Experiment Report",
        "",
        f"**Protocol:** `{config.protocol_version}`  ",
        f"**Experiment:** `{config.experiment_id}`  ",
        f"**Run kind:** `{config.run_kind}`",
        "",
        f"> {status_warning}",
        "",
        "## Executive result",
        "",
        f"At rho={primary['rho']:.2f}, the estimated relative difference in mean restricted recovery time "
        f"for hierarchical versus edge-only was **{primary['estimate'] * 100:.1f}%** "
        f"(bootstrap {_fmt(primary['confidence_low'] * 100)}% to {_fmt(primary['confidence_high'] * 100)}%; "
        f"one-sided upper bound {_fmt(primary['one_sided_upper_bound'] * 100)}%).",
        "Negative values mean faster hierarchical recovery; positive values mean slower hierarchical recovery.",
        "",
        "The promotion gate is **{}**. This decision is meaningful only for a confirmatory run.".format(
            "PASSED" if gate["promote_to_v1"] else "NOT PASSED"
        ),
        "",
        "## Decision gate",
        "",
        "| Requirement | Result |",
        "|---|---:|",
        f"| Statistical superiority | {gate['statistical_superiority']} |",
        f"| Estimated engineering gain | {gate['engineering_gain']} |",
        f"| Non-inferiority at rho=0 | {gate['noninferiority_at_rho_0']} |",
        f"| Promote hierarchical state | {gate['promote_to_v1']} |",
        "",
        "## Group metrics",
        "",
        "| rho | Method | Trials | Mean RRT | Recovery | Dynamic regret | Final expected utility | CPU mean / p95 (s) |",
        "|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in analysis["group_metrics"]:
        lines.append(
            f"| {row['rho']:.2f} | {METHOD_LABELS.get(row['method'], row['method'])} | "
            f"{row['trials']} | {_fmt(row['restricted_recovery_time_mean'])} | "
            f"{row['recovery_probability'] * 100:.1f}% | {_fmt(row['dynamic_regret_mean'])} | "
            f"{_fmt(row['final_expected_utility_mean'])} | {_fmt(row['decision_cpu_seconds_mean'])} / "
            f"{_fmt(row['decision_cpu_seconds_p95'])} |"
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
            "- The experiment isolates representation under an identical local-feedback contract.",
            "- The structured SW-UCB baseline uses node-edge features and therefore does not give MG a representation monopoly.",
            "- The oracle defines expected optimal utility; it is not a deployable competitor.",
            "- Development and pilot executions are for debugging and sample-size planning only.",
            "- A failed gate does not prove absence of all effects; interpretation follows the frozen analysis plan.",
            "",
            "## Reproducibility",
            "",
            "Raw paired trials are under `raw/`, processed statistics under `processed/`, traces under `traces/`, "
            "and file hashes plus runtime versions are recorded in `manifest.json`.",
            "",
        ]
    )
    report_path = output / "REPORT.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path
