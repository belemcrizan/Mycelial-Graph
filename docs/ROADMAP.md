# Evidence-Gated Roadmap

The roadmap separates scientific evidence from product capability. Features advance only when a measured bottleneck or validated hypothesis justifies them.

## Parallel track: V2.2 Resource-Aware Mycelial Graph

MG-EXP-V2.2 extends V2.0-alpha and V2.1 with explicit $G = (V, E, S, B, H)$ graph and health modeling, hard budget reservations, discrepancy-gated anastomosis, reliable-utility cord reinforcement, connectivity-preserving cytoplasmic retraction, active resource translocation, and constrained/Pareto routing objectives. Pilot and ablation benchmarks run on disjoint seeds; V2.2 confirmatory remains locked.

## Parallel track: V2.1 Evidence Bridge

MG-EXP-V2.1 does not replace V2.0-alpha. It adds iso-model allocation, VOC calibration, stronger baselines, and a local executable smoke track. Confirmatory remains locked.

## Parallel track: V2.0-alpha resource allocation

V2 is a separate protocol (MG-EXP-V2). Alpha is simulation-only. It does not replace V1 evidence gates and does not authorize live provider spend.

## Parallel tracks (do not contaminate V1)

- Track A — V1 evidence: pilot → power → freeze → confirmatory.
- Track B — theory: `theory/` (conjectures, not theorems).
- Track C — external data: `external/` adapters; MG-EXP-REAL-001 not executed.

## Current: V1 research edition

Goal: determine whether hierarchical node-edge state has a measurable recovery advantage under controlled shared shocks.

Exit evidence:

- independent pilot completed (2026-09-15, not confirmatory);
- sample size recorded (N=97);
- frozen confirmatory experiment executed (`REFUTED` at rho=0.50; post-confirmatory triage `EQ-B`);
- Paper A manuscript prepared (`paper/tmlr/paper.tex`, not yet submitted; submission moratorium active);
- limitations and negative/exploratory directions reported.

## Next: single-cloud POC

Choose one cloud only after V1. The first cloud POC should use two or three interchangeable model endpoints behind a narrow task contract.

Recommended sequence:

1. capture immutable price, latency, availability, and quality traces;
2. replay those traces locally using the V1 runner;
3. execute a bounded live canary with spending and safety limits;
4. compare fixed routing, structured SW-UCB, and the evidence-supported MG variant;
5. publish cost per successful task, quality, p95 latency, failure rate, and recovery behavior.

Cloud choice criteria:

- credits or low experimental cost;
- reproducible model/version pinning;
- telemetry export;
- straightforward budget limits;
- availability of at least two meaningful routing alternatives;
- minimal operational work for one researcher.

## Later: composite pipelines

If the single-cloud POC validates operational value, extend the graph to retrievers, tools, caches, guardrails, and local/cloud compute. Add hard policy constraints outside the soft utility function.

## Later: multicloud execution fabric

Multicloud is not the next step. It becomes justified only after the project demonstrates provider-specific value and identifies a real availability, sovereignty, or cost risk that one cloud cannot address.

Possible later capabilities:

- provider adapters and frozen trace ingestion;
- fallback and rollback boundaries;
- capacity and quota constraints;
- auditable policy enforcement;
- graph discovery;
- distributed state and consensus;
- interactive operations dashboard.

## Orchestration gate

Do not add an external orchestrator until at least one condition is observed:

- local execution cannot meet the planned experiment duration;
- partial infrastructure failure loses meaningful work despite atomic checkpoints;
- more than one compute node is required;
- dependency-aware pipelines become more complex than independent trial maps.

Until then, `ProcessPoolExecutor` is sufficient.

