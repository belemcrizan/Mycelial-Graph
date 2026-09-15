from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from ..science.claim_guard import assert_claim_containment
from ..types import ExperimentConfig
from ..artifacts import ArtifactError, ensure_unsealed, load_validated_trials


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
        plt.title(
            "EXPLORATORY across rho - not powered to establish a crossover.\n"
            "Only rho=0.00 (safety gate) and rho=0.50 (primary) are pre-specified.",
            fontsize=9,
        )
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
    ensure_unsealed(output)
    _, provenance = load_validated_trials(config, output)
    analysis_path = output / "processed" / "analysis.json"
    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    if analysis.get("provenance") != provenance or analysis.get("run_kind") != config.run_kind:
        raise ArtifactError("Analysis does not belong to this verified experiment; analyze the original artifact first.")
    figures = _make_figures(analysis, output)
    primary = analysis["primary_contrast"]
    gate = analysis["decision_gate"]
    safety = analysis.get("noninferiority_contrast")
    state = analysis.get("result_state") or {}
    integrity = analysis.get("frozen_contrast_integrity") or {}
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
        f"**Run kind:** `{config.run_kind}`  ",
        f"**Result state:** `{state.get('state', 'UNKNOWN')}`",
        f"**Run kind:** `{config.run_kind}`",
        f"**Decision state:** `{analysis['decision_state']}`",
        "",
        f"> {status_warning}",
        "",
        "## Result state",
        "",
        f"**`{state.get('state', 'UNKNOWN')}`** - safety gate at rho=0 is "
        f"`{state.get('safety_gate_state', 'UNKNOWN')}`.",
        "",
        *(
            []
            if config.run_kind == "confirmatory"
            else [
                "This label describes this development/pilot sample only. It is not a V1 result "
                "and it does not resolve the frozen confirmatory question.",
                "",
            ]
        ),
        *[f"- {reason}" for reason in state.get("reasons", [])],
        "",
        "`SUPPORTED`, `CONDITIONAL`, `INCONCLUSIVE`, `REFUTED`, and `PROTOCOL_INVALID` are all "
        "legitimate terminal states of the frozen protocol. The mapping is fixed in "
        "`experiments/v1/HYPOTHESIS_MATRIX.md` and was pre-specified before any confirmatory "
        "outcome was observed.",
        "",
        "## Primary confirmatory contrast (CONFIRMATORY)",
        "",
        f"At rho={primary['rho']:.2f}, the estimated relative difference in mean restricted recovery time "
        f"for hierarchical versus edge-only was **{primary['estimate'] * 100:.1f}%** "
        f"(bootstrap {_fmt(primary['confidence_low'] * 100)}% to {_fmt(primary['confidence_high'] * 100)}%; "
        f"one-sided upper bound {_fmt(primary['one_sided_upper_bound'] * 100)}%; "
        f"{integrity.get('primary_pairs', 'n/a')} paired scenarios).",
        "Negative values mean faster hierarchical recovery; positive values mean slower hierarchical recovery.",
        "",
        "## Safety gate at rho=0 (SAFETY GATE)",
        "",
        (
            f"Relative difference **{safety['estimate'] * 100:.1f}%**, one-sided upper bound "
            f"{_fmt(safety['one_sided_upper_bound'] * 100)}% against the frozen non-inferiority "
            f"margin {safety['margin'] * 100:.1f}%. Gate result: "
            f"`{state.get('safety_gate_state', 'UNKNOWN')}`."
            if safety
            else "No rho=0 contrast is present in this run, so the safety gate was not evaluated."
        ),
        "",
        "## Decision gate",
        "",
        "| Requirement | Role | Result |",
        "|---|---|---:|",
        f"| Statistical superiority at rho=0.50 | PRIMARY | {gate['statistical_superiority']} |",
        f"| Estimated engineering gain <= -{config.analysis.engineering_gain_gate:.2f} | SECONDARY | {gate['engineering_gain']} |",
        f"| Non-inferiority at rho=0 | SAFETY GATE | {gate['noninferiority_at_rho_0']} |",
        f"| Promote hierarchical state (requirements 1-3) | ENGINEERING | {gate['promote_to_v1']} |",
        "",
        f"Automated coverage: {gate.get('automated_requirements', 'requirements 1-3')}. "
        f"{gate.get('operational_cost_budget_requirement', '')}",
        "",
        "## Integrity",
        "",
        f"- Censoring administrative only: {integrity.get('censoring_is_administrative_only')}",
        f"- Trials censored without reaching tau: {integrity.get('non_administrative_censoring')}",
        f"- Method failures inside a frozen contrast: {integrity.get('method_failures_in_frozen_contrasts')}",
        "| Requirement | Result |",
        "|---|---:|",
        f"| Statistical superiority | {gate['statistical_superiority']} |",
        f"| Estimated engineering gain | {gate['engineering_gain']} |",
        f"| Non-inferiority at rho=0 | {gate['noninferiority_at_rho_0']} |",
        f"| Scientific criteria met (descriptive outside confirmatory) | {gate['scientific_criteria_met']} |",
        f"| Confirmatory population | {gate['confirmatory_population']} |",
        "| Operational budget validated | False; not yet specified |",
        f"| Promote hierarchical state | {gate['promote_to_v1']} |",
        "",
        "## Group metrics",
        "",
        "Rows marked `EXPLORATORY`, `DIAGNOSTIC`, or `SECONDARY` carry no error control and cannot "
        "support an inferential claim.",
        "",
        "| rho | Method | Role | Trials | Mean RRT | Recovery | Dynamic regret | Final expected utility | CPU mean / p95 (s) |",
        "|---:|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in analysis["group_metrics"]:
        lines.append(
            f"| {row['rho']:.2f} | {METHOD_LABELS.get(row['method'], row['method'])} | "
            f"{row.get('role', 'EXPLORATORY')} | "
            f"{row['trials']} | {_fmt(row['restricted_recovery_time_mean'])} | "
            f"{row['recovery_probability'] * 100:.1f}% | {_fmt(row['dynamic_regret_mean'])} | "
            f"{_fmt(row['final_expected_utility_mean'])} | {_fmt(row['decision_cpu_seconds_mean'])} / "
            f"{_fmt(row['decision_cpu_seconds_p95'])} |"
        )
    lines.extend(
        [
            "",
            "## Figures (EXPLORATORY across rho)",
            "",
            "These curves span the whole rho grid. They are exploratory: this design is not powered "
            "to establish a crossover, and no rho* may be read off them.",
            "",
            *[f"![{path.stem}](figures/{path.name})" for path in figures],
            "",
            "## Interpretation boundary",
            "",
            "- The experiment isolates representation under an identical local-feedback contract.",
            "- The structured SW-UCB baseline uses node-edge features and therefore does not give MG a representation monopoly.",
            "- The oracle defines expected optimal utility; it is not a deployable competitor.",
            "- Development and pilot executions are for debugging and sample-size planning only.",
            "- A failed gate is not evidence for the absence of all effects; interpretation follows the frozen analysis plan.",
            "- The frozen sample size is powered for the rho=0.50 primary contrast only. It does not make "
            "any other contrast adequately powered.",
            "- This evidence is synthetic. It does not extend to real providers, deployment, or any causal mechanism.",
            "- Reproduction here is internal and automated, never independent.",
            "",
            "## Reproducibility",
            "",
            "Raw paired trials are under `raw/`, processed statistics under `processed/`, traces under `traces/`, "
            "and file hashes plus runtime versions are recorded in `manifest.json`.",
            "",
        ]
    )
    text = "\n".join(lines)
    assert_claim_containment(text, "V1 REPORT.md")
    report_path = output / "REPORT.md"
    report_path.write_text(text, encoding="utf-8")
    return report_path
