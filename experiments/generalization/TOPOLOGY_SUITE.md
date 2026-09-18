# MG-EXP-TOPOLOGY-001 — Structural Generalization Suite (FROZEN, NOT AUTHORIZED)

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Serves:** Master Prompt Part II §7 · Kernel gate: **GATE-FROZEN**.
**Status:** `frozen` · `authorized: false`.

---

## 0. Objective

Estimate **where behavior changes** across graph structure — not average across graphs (§7). The
V1 result used a single topology (3 internal layers × 3 alternatives); one topology cannot support a
structural-generalization claim.

## 1. Pre-specified topology suite

| Topology | Descriptor emphasis |
|---|---|
| shallow | small depth |
| deep | large depth |
| wide | large width / alternatives-per-layer |
| sparse | low edge density |
| dense | high edge density |
| modular | community structure |
| hub-heavy | centralization |
| random DAG | control |
| bottleneck | single shared cut-edge (high structural ρ) |
| redundant-path | many parallel paths (low structural ρ) |
| correlated-provider | shared upstream provider across paths |

## 2. Recorded topology descriptors (per graph)

nodes · edges · depth · width · density · branching factor · path count · redundancy ·
centralization · modularity (where meaningful). Stored in `analysis.json` so results are indexed by
structure, enabling a **topology × method × regime** evidence surface.

## 3. Design controls

Pre-registered generation seeds (disjoint), fixed estimand per topology, exploratory/confirmatory
labels fixed in advance, deterministic graph generation with tests for reproducibility (§19).

## 4. Gate & evidence class

Execution is **GATE-FROZEN**. Outputs are **SYNTHETIC**. No structural claim is made until executed
under authorization.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
