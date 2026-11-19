"""Optional lightweight visualization helpers for Mycelial-Graph V2.

Visualization is strictly decoupled from simulation and policy execution:
core V2 modules never import this module.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Mapping, Sequence

from .graph_model import ComputationalGraph


def render_topology_svg(
    graph: ComputationalGraph,
    *,
    conductances: Sequence[float] | None = None,
    pruned_edges: Sequence[bool] | None = None,
    failed_edges: Sequence[bool] | None = None,
    active_edges: Sequence[int] = (),
    title: str = "Mycelial V2 Computational Graph",
) -> str:
    """Render a deterministic standalone SVG of graph topology and adaptive state."""
    comps = list(graph.components.values())
    max_layer = max((comp.layer for comp in comps), default=0)
    by_layer: dict[int, list[int]] = {}
    for comp in sorted(comps, key=lambda c: (c.layer, c.tier, c.id)):
        by_layer.setdefault(comp.layer, []).append(comp.id)
    max_width = max((len(nodes) for nodes in by_layer.values()), default=1)

    svg_w = max(720, 180 * (max_layer + 1))
    svg_h = max(360, 110 * max_width + 110)
    pad_x = 90
    pad_y = 75
    usable_w = max(1, svg_w - 2 * pad_x)
    usable_h = max(1, svg_h - pad_y - 65)

    coords: dict[int, tuple[float, float]] = {}
    for layer, nodes in sorted(by_layer.items()):
        x = pad_x + (usable_w * layer / max(1, max_layer))
        for idx, nid in enumerate(nodes):
            y = pad_y + usable_h * ((idx + 0.5) / max(1, len(nodes)))
            coords[nid] = (x, y)

    c_vals = list(conductances) if conductances is not None else [1.0] * graph.edge_count
    c_max = max(max(c_vals, default=1.0), 1e-6)
    pruned_set = {idx for idx, flag in enumerate(pruned_edges or ()) if flag}
    failed_set = {idx for idx, flag in enumerate(failed_edges or ()) if flag}
    active_set = set(int(eid) for eid in active_edges)

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        f'<text x="24" y="34" font-family="sans-serif" font-size="16" font-weight="bold" fill="#0f172a">{escape(title)}</text>',
    ]

    for edge in graph.dag.edges:
        x1, y1 = coords[edge.source]
        x2, y2 = coords[edge.target]
        c_norm = max(0.05, min(1.0, float(c_vals[edge.id]) / c_max)) if edge.id < len(c_vals) else 0.5
        stroke_w = 1.2 + 4.0 * c_norm
        dash = ""
        if edge.id in failed_set:
            color = "#dc2626"
            dash = ' stroke-dasharray="6,4"'
            opacity = 0.85
        elif edge.id in pruned_set:
            color = "#94a3b8"
            dash = ' stroke-dasharray="4,4"'
            opacity = 0.45
        elif edge.id in active_set:
            color = "#059669"
            stroke_w += 1.2
            opacity = 0.95
        else:
            color = "#3b82f6"
            opacity = 0.25 + 0.65 * c_norm
        lines.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{color}" stroke-width="{stroke_w:.2f}" stroke-opacity="{opacity:.2f}"{dash}/>'
        )

    role_colors = {
        "source": "#0f766e",
        "prompt": "#0369a1",
        "retriever": "#0284c7",
        "model": "#4f46e5",
        "tool": "#7c3aed",
        "memory": "#0891b2",
        "validator": "#b45309",
        "guardrail": "#be123c",
        "fallback": "#475569",
        "sink": "#15803d",
    }
    for comp in comps:
        x, y = coords[comp.id]
        fill = role_colors.get(comp.role, "#334155")
        lines.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="20" fill="{fill}" stroke="#ffffff" stroke-width="2"/>'
        )
        lines.append(
            f'<text x="{x:.1f}" y="{y + 4:.1f}" text-anchor="middle" font-family="sans-serif" '
            f'font-size="11" font-weight="bold" fill="#ffffff">{comp.id}</text>'
        )
        lines.append(
            f'<text x="{x:.1f}" y="{y + 34:.1f}" text-anchor="middle" font-family="sans-serif" '
            f'font-size="10" fill="#334155">{escape(comp.name)}</text>'
        )

    legend_y = svg_h - 22
    lines.append(
        f'<text x="24" y="{legend_y}" font-family="sans-serif" font-size="11" fill="#475569">'
        "Legend: emerald=active route | blue width=conductance | gray dashed=retracted | red dashed=failed"
        "</text>"
    )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def render_trace_dashboard(
    trace_records: Sequence[Mapping[str, Any]],
    output_path: str | Path,
    *,
    shock_step: int | None = None,
    budget_cap: int | None = None,
    title: str = "Mycelial V2 Resource & Adaptation Trace",
) -> Path:
    """Render a 3-panel Matplotlib PNG dashboard from step-level V2 trace records."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    steps = [int(rec["step"]) for rec in trace_records]
    tokens = [int(rec["total_tokens"]) for rec in trace_records]
    cum_tokens: list[int] = []
    running = 0
    for tok in tokens:
        running += tok
        cum_tokens.append(running)
    qualities = [float(rec["realized_quality"]) for rec in trace_records]
    expected_q = [float(rec["expected_quality"]) for rec in trace_records]
    candidates = [int(rec.get("router_candidates", 0)) for rec in trace_records]

    fig, axes = plt.subplots(3, 1, figsize=(9, 8.5), sharex=True)
    fig.suptitle(title, fontsize=12, fontweight="bold")

    axes[0].plot(steps, cum_tokens, color="#1d4ed8", linewidth=1.8, label="Cumulative tokens")
    if budget_cap is not None:
        axes[0].axhline(budget_cap, color="#dc2626", linestyle="--", linewidth=1.2, label="Global budget cap")
    axes[0].set_ylabel("Tokens")
    axes[0].legend(loc="upper left", fontsize=8)
    axes[0].grid(alpha=0.25)

    axes[1].plot(steps, expected_q, color="#059669", linewidth=1.6, label="Expected route quality")
    axes[1].scatter(steps, qualities, s=10, alpha=0.35, color="#64748b", label="Realized quality")
    axes[1].set_ylabel("Quality")
    axes[1].legend(loc="lower right", fontsize=8)
    axes[1].grid(alpha=0.25)

    axes[2].step(steps, candidates, where="mid", color="#7c3aed", linewidth=1.5, label="Active candidate paths")
    axes[2].set_ylabel("Candidates")
    axes[2].set_xlabel("Execution Step")
    axes[2].legend(loc="upper right", fontsize=8)
    axes[2].grid(alpha=0.25)

    if shock_step is not None:
        for ax in axes:
            ax.axvline(shock_step, color="#ea580c", linestyle=":", linewidth=1.2)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
