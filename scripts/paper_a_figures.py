"""Generate Paper A figures from confirmatory/pilot raw trials and diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper" / "tmlr" / "figures"
DIAG = ROOT / "experiments" / "v1" / "artifacts" / "diagnostics"

plt.rcParams.update(
    {
        "font.size": 9,
        "axes.titlesize": 10,
        "figure.dpi": 160,
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)


def _paired(raw_dir: Path, rho: float = 0.5) -> np.ndarray:
    diffs = []
    for path in sorted((raw_dir / "raw").rglob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))["scientific_payload"]
        if abs(float(payload["rho"]) - rho) > 1e-9:
            continue
        by_method = {row["method"]: row["restricted_recovery_time"] for row in payload["results"]}
        if "hierarchical" in by_method and "edge_only" in by_method:
            diffs.append(by_method["hierarchical"] - by_method["edge_only"])
    return np.array(diffs, dtype=float)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    dyn = json.loads((DIAG / "dynamic_range.json").read_text(encoding="utf-8"))
    eq = json.loads((DIAG / "equalization.json").read_text(encoding="utf-8"))
    pilot = _paired(ROOT / "outputs" / "pilot")
    conf = _paired(ROOT / "outputs" / "confirmatory")

    fig, axes = plt.subplots(1, 2, figsize=(6.5, 2.6), sharey=False)
    axes[0].hist(pilot, bins=10, color="#4c78a8", edgecolor="white")
    axes[0].axvline(0, color="black", linewidth=1)
    axes[0].set_title("Pilot paired RRT difference (n=20)")
    axes[0].set_xlabel(r"RRT$_{\mathrm{hier}}$ $-$ RRT$_{\mathrm{edge}}$")
    axes[0].set_ylabel("Scenarios")
    axes[1].hist(conf, bins=18, color="#f58518", edgecolor="white")
    axes[1].axvline(0, color="black", linewidth=1)
    axes[1].set_title("Confirmatory paired RRT difference (n=97)")
    axes[1].set_xlabel(r"RRT$_{\mathrm{hier}}$ $-$ RRT$_{\mathrm{edge}}$")
    fig.suptitle("Post-confirmatory diagnostic: paired-effect distributions", y=1.05)
    fig.savefig(OUT / "paired_differences.pdf")
    fig.savefig(OUT / "paired_differences.png")
    plt.close(fig)

    def _row(rho: float, method: str) -> dict:
        for item in eq["summaries"]:
            if item["method"] == method and abs(item["rho"] - rho) < 1e-9:
                return item
        raise KeyError((rho, method))

    labels = ["path entropy\n(frac. of max)", "max path\nprobability", "optimal-path\nrate"]
    edge = _row(0.5, "edge_only")
    hier = _row(0.5, "hierarchical")
    edge_vals = [
        edge["path_entropy_fraction_of_max"]["mean"],
        edge["max_path_probability"]["mean"],
        edge["optimal_pre_path_rate"]["mean"],
    ]
    hier_vals = [
        hier["path_entropy_fraction_of_max"]["mean"],
        hier["max_path_probability"]["mean"],
        hier["optimal_pre_path_rate"]["mean"],
    ]
    x = np.arange(len(labels))
    width = 0.36
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    ax.bar(x - width / 2, edge_vals, width, label="edge-only", color="#4c78a8")
    ax.bar(x + width / 2, hier_vals, width, label="hierarchical", color="#f58518")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Warm-up mean")
    ax.set_title(r"Equalization triage at $\rho=0.50$ (POST-CONFIRMATORY DIAGNOSTIC)")
    ax.legend(frameon=False)
    fig.savefig(OUT / "equalization_warmup.pdf")
    fig.savefig(OUT / "equalization_warmup.png")
    plt.close(fig)

    rhos = [row["rho"] for row in dyn["rows"]]
    rrt_est = [row["rrt_relative"]["estimate"] for row in dyn["rows"]]
    rrt_lo = [row["rrt_relative"]["confidence_low"] for row in dyn["rows"]]
    rrt_hi = [row["rrt_relative"]["confidence_high"] for row in dyn["rows"]]
    reg_est = [row["regret_relative"]["estimate"] for row in dyn["rows"]]
    roles = [row["role"] for row in dyn["rows"]]
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    yerr = np.vstack([np.array(rrt_est) - np.array(rrt_lo), np.array(rrt_hi) - np.array(rrt_est)])
    ax.errorbar(rhos, rrt_est, yerr=yerr, fmt="o-", color="#4c78a8", label="relative RRT")
    ax.plot(rhos, reg_est, "s--", color="#e45756", label="relative dynamic regret")
    ax.axhline(0, color="black", linewidth=1)
    ax.axvline(0.5, color="gray", linestyle=":", linewidth=1)
    ax.set_xlabel(r"Shared-shock fraction $\rho$")
    ax.set_ylabel("Hierarchical vs edge-only")
    ax.set_title("Frozen $\\rho$ grid (only $\\rho=0.50$ RRT is confirmatory)")
    for rho, role in zip(rhos, roles):
        if role != "PRIMARY":
            continue
        ax.annotate("PRIMARY", (rho, rrt_est[rhos.index(rho)]), textcoords="offset points", xytext=(8, 8))
    ax.legend(frameon=False)
    fig.savefig(OUT / "rho_grid_diagnostic.pdf")
    fig.savefig(OUT / "rho_grid_diagnostic.png")
    plt.close(fig)
    print(f"wrote figures in {OUT}")


if __name__ == "__main__":
    main()
