# MG-EXP-ABLATION-001 — Mechanistic Ablation Program (FROZEN, NOT AUTHORIZED)

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Serves:** Master Prompt Part II §5 · Kernel gate: **GATE-FROZEN** (prepare only; do not run).
**Status:** `frozen` · `authorized: false`. Ready-to-authorize; incapable of self-execution.
**Unblock artifact:** a committed `authorized: true` + signed authorization record; additionally
subject to the moratorium (`GATE-H07`) for any V2/pooling-track mechanism.

---

## 0. Scientific objective (falsification-first)

> Determine **which mechanisms contribute, under which conditions, and at what cost** — not to find a
> flattering ordering. A result showing a *simpler* ablation explains any apparent advantage is a
> **valid success** (INV-10).

This program does **not** touch the sealed V1 `REFUTED` result. It is a new, additive, pre-registered
study whose outcome cannot retroactively edit V1.

## 1. Ablation matrix (each row = a real mechanistic intervention, not a rename)

| Ablation | Mechanism removed | Existing implementation to reuse (if valid) |
|---|---|---|
| `full` | none (reference) | full controller |
| `no_hierarchy` | hierarchical node-edge decomposition | edge-only baseline |
| `no_pooling` | cross-node pooling | `v2_no_pooling`-style config |
| `no_transfer` | resource translocation | `biology/translocation.py` off |
| `no_pruning` | edge pruning | `biology/pruning.py` off |
| `no_uncertainty` | uncertainty bonus | SW-UCB bonus off |
| `no_shock_memory` | temporal shock memory | decay-only |
| `no_cost_awareness` | cost term | cost weight = 0 |
| `no_branching` | branching / anastomosis | static candidate set |
| `static_topology` | topology adaptation | frozen graph |
| `decay_ablation` | temporal decay sweep | `temporal_decay` grid |
| `edge_only` | all structure | V1 edge-only |
| `node_only` | edge structure | V1 node-only (if meaningful) |

**Integrity rule (INV-03/§5):** an ablation must correspond to an actual code path being disabled.
Renaming a config to look like an ablation is forbidden. Each row binds to the module it disables.

## 2. Pre-specified measurements (per ablation × condition)

RRT · final quality · dynamic regret (where applicable) · cost · token usage · latency · failure
rate · route switches · resource transfer volume · pruning activity · policy entropy ·
uncertainty/calibration quality (where applicable). Reported as a **machine-readable table**
(`analysis.json`) plus `REPORT.md`.

## 3. Design controls (predefined before any outcome inspection)

- Estimand and primary contrast per ablation fixed in advance.
- Seeds disjoint from V1/V1.5 and drawn mechanically; not regenerable after inspection (INV-02).
- Confirmatory vs exploratory labels fixed (§10). No exploratory ordering promoted to confirmatory.
- Multiplicity: one primary contrast per ablation family; FWER/FDR strategy per `docs/STATISTICAL_ROBUSTNESS.md`.
- Calibration/development data separated from confirmatory data.

## 4. What this does NOT authorize

Running anything; drawing seeds; touching V1 artifacts; treating a favorable ablation as V1 rescue;
any moratorium-frozen (V2/pooling) execution. Each remains **STAGED** until human authorization.

## 5. Evidence-class of outputs (INV-05, §P6)

All outputs are **SYNTHETIC** unless a matched external dataset is used (then labeled per
`docs/EXTERNAL_VALIDATION_LADDER.md`). No ablation result is external evidence.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
