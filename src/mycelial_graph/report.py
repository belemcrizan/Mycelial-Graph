"""Human-readable report generation for technical and non-technical readers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


LABELS = {
    "mycelial_v0": "Mycelial V0",
    "structured_semi_bandit": "Structured semi-bandit (reference)",
    "reactive_shortest_path": "Reactive shortest path (reference)",
}


def _number(value: float | None, digits: int = 3) -> str:
    return "n/a" if value is None else f"{value:.{digits}f}"


def _percent(value: float | None) -> str:
    return "n/a" if value is None else f"{100.0 * value:.1f}%"


def _mean(metric: dict[str, Any]) -> float | None:
    value = metric.get("mean")
    return None if value is None else float(value)


def write_report(results: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    scope = results["scope"]
    certification = scope["trial_certification"]
    aggregate = results["aggregate"]
    rows: list[str] = []
    for method, metrics in aggregate.items():
        src = metrics["sample_recovery_cost_recovered_only"]
        rows.append(
            "| {label} | {recovery} | {src} | {censored} | {cpst} | {success} | {post_utility} | {ser} | {decision} | {ops} |".format(
                label=LABELS.get(method, method),
                recovery=_percent(metrics["recovery_probability"]),
                src=_number(_mean(src), 1),
                censored=metrics["censored_runs"],
                cpst=_number(_mean(metrics["cpst_usd"]), 6),
                success=_percent(_mean(metrics["success_rate"])),
                post_utility=_number(_mean(metrics["postshock_mean_utility"]), 3),
                ser=_percent(_mean(metrics["structural_reexploration_rate"])),
                decision=_number(_mean(metrics["p95_decision_ms"]), 4),
                ops=_number(_mean(metrics["mean_primitive_operations"]), 1),
            )
        )

    trace_rows: list[str] = []
    shock_step = int(scope["shock_step"])
    for sample in results.get("trace_samples", []):
        for record in sample["records"]:
            step = int(record["step"])
            if step < shock_step - 1:
                phase = "initial"
            elif step == shock_step - 1:
                phase = "pre-shock"
            elif step == shock_step:
                phase = "shock"
            else:
                phase = "final"
            route = " -> ".join(
                node for node in record["node_ids"] if node not in {"source", "sink"}
            )
            trace_rows.append(
                "| {method} | {step} | {phase} | `{route}` | {utility} | {oracle} |".format(
                    method=LABELS.get(sample["method"], sample["method"]),
                    step=step,
                    phase=phase,
                    route=route,
                    utility=_number(record["expected_utility"], 3),
                    oracle=_number(record["oracle_expected_utility"], 3),
                )
            )

    cpst_candidates = {
        method: _mean(metrics["cpst_usd"])
        for method, metrics in aggregate.items()
        if _mean(metrics["cpst_usd"]) is not None
    }
    best_cpst = min(cpst_candidates, key=cpst_candidates.get) if cpst_candidates else None
    recovery_candidates = {
        method: metrics["recovery_probability"] for method, metrics in aggregate.items()
    }
    best_recovery_value = max(recovery_candidates.values()) if recovery_candidates else None
    best_recovery = [
        LABELS.get(method, method)
        for method, value in recovery_candidates.items()
        if value == best_recovery_value
    ]

    markdown = f"""# Mycelial Graph V0 - Demonstration Report

**Author:** Crizan Belém Ribeiro, Independent Researcher  
**Generated:** {results['generated_at_utc']}  
**Scientific status:** descriptive V0 engineering run; no H1, H2, or H3 validation claim

## Executive summary

This run shows that the proposed architecture can be executed end to end. A synthetic AI pipeline was routed repeatedly, one model component was degraded at step {scope['shock_step']}, each policy adapted only from the feedback made available to it, and the runner produced auditable metrics and frozen-trial hashes.

In plain language, the system behaves like a network of routes between service choices. Mycelial V0 gives every connection a local "conductance." Helpful observations strengthen a traversed connection, unhelpful observations weaken it, unused state decays, and a small explicit exploration rate keeps alternatives discoverable. Hard policy constraints are checked before any soft score.

Across this bounded demonstration, the lowest descriptive Cost per Successful Task (CPST) was produced by **{LABELS.get(best_cpst, best_cpst or 'n/a')}**. The highest recovery probability was shared by **{', '.join(best_recovery) if best_recovery else 'n/a'}**. These are observations from a synthetic V0, not evidence that one method is generally superior.

## What was executed

- {len(scope['seeds'])} immutable seeds, with {scope['steps_per_run']} tasks per policy and seed.
- A {scope['graph_paths']}-path DAG with {scope['nodes']} nodes and {scope['edges']} directed edges.
- One localized, abrupt degradation at task {scope['shock_step']}.
- Mycelial V0 plus two transparent reference baselines.
- Pre-generated potential outcomes shared across methods within every seed.
- Local feedback only: a router observes only the edges it traversed.
- The pre-shock optimum includes `{results['scope']['trial_certification']['pre_oracle_nodes'][3]}`; the post-shock optimum replaces it with `{results['scope']['trial_certification']['post_oracle_nodes'][3]}`.
- The certified optima share {_percent(certification['shared_edge_fraction'])} of their directed edges, with pre/post utility margins of {_number(certification['pre_oracle_margin'], 4)} and {_number(certification['post_oracle_margin'], 4)}.

## Representative trace - seed {scope['seeds'][0]}

This trace makes the POC visible at four checkpoints. It is a debugging view, not an aggregate result.

| Method | Step | Phase | Selected component route | Expected utility | Oracle utility |
| --- | ---: | --- | --- | ---: | ---: |
{chr(10).join(trace_rows)}

## Aggregate results

| Method | Recovery probability | SRC, recovered only | Censored runs | CPST (USD) | Success rate | Post-shock utility | SER | p95 decision (ms) | Mean primitive ops |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{chr(10).join(rows)}

### How to read the table

- **Recovery probability:** fraction of runs that met the sustained utility criterion before the horizon ended.
- **SRC:** local edge-feedback samples needed to recover. It is summarized only for recovered runs; non-recovery remains right-censored.
- **CPST:** total simulated execution cost divided by successful tasks.
- **SER:** post-shock samples spent on unaffected edges outside the post-shock oracle path, using one frozen external classifier.
- **Decision time and primitive operations:** routing overhead only, kept separate from simulated task latency.

## Reproducibility and fairness controls

Every seed produced a frozen compressed trial file before comparison. Its SHA-256 digest is recorded in `results.json`. The outcome for every edge and step was pre-generated, but a router could retrieve feedback only for its chosen path. Mycelial parameters were selected on disjoint development seeds {scope['development_seeds']} and frozen before this final run. The V0 seed set is an engineering demonstration set, not a publication-grade untouched holdout. Hard policy constraints were applied before routing.

## What this V0 proves

- The package builds the intended layered execution graph.
- Mycelial conductance, lazy temporal decay, local feedback, softmax routing, explicit exploration, and single-edge fallback execute together.
- Only traversed edges receive feedback updates.
- A localized shock can be injected reproducibly.
- Results, traces, trial hashes, recovery censoring, CPST, SER, and computational accounting are generated automatically.

## What this V0 does not prove

- It does not validate H1 (sparse-shock recovery), H2 (scaling), or H3 (structural reuse).
- It does not establish statistical or practical superiority over structured baselines.
- Its two reference baselines are inspectable V0 comparators, not certified reproductions of every research baseline.
- It does not use live cloud providers, real customer prompts, production traffic, or a global quality evaluator.
- It provides no convergence or regret guarantee.

## Next evidence gates

1. Freeze development and evaluation seed partitions, then tune on development seeds only.
2. Generate causal shared-fraction trials and verify unique pre- and post-shock optima with margins.
3. Run the H1 sparse-shock suite with at least 50 evaluation replications when computation is cheap.
4. Run H2 across depth, branching, and non-stationarity regimes.
5. Run H3 with trial-level shared fraction and censoring-aware analysis.
6. Execute the required decay/exploration ablations.
7. Only after local evidence is credible, validate one cloud at a time using the same adapter contract and frozen workload.

The detailed single-cloud sequence is defined in `docs/CLOUD_VALIDATION.md`. Production multi-cloud routing remains a later roadmap phase, not part of V0.
"""
    target.write_text(markdown, encoding="utf-8")
    return target
