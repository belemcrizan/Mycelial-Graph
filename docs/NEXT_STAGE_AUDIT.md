# Next-Stage Audit — Mycelial Graph (MG-EXP-V2.1 Evidence Bridge)

**Audit date:** 2026-08-31  
**Repository:** belemcrizan/Mycelial-Graph  
**HEAD lineage at audit:** V0 demonstrator + V1 research edition + V2.0-alpha on `feat/mycelial-v2-resource-allocation`  
**This document is not a confirmatory result.**

Documentation was checked against implementation. They do not fully match.

---

## 1. Exact current repository state

| Layer | Location | Status |
|---|---|---|
| V0 | `graph.py`, `routing.py`, `trial.py`, `configs/v0_demo.yaml` | Preserved demonstrator |
| V1 | `src/mycelial_graph/{environment,agents,runner,analysis,reporting}` + `experiments/v1/` | Frozen protocol MG-EXP-V1; confirmatory seeds absent by lock |
| V2.0-alpha | `src/mycelial_graph/v2/` + `experiments/v2/` | Additive; confirmatory locked |
| Honest README status | No confirmatory run; no production claim; V2 is simulation-only | Matches code |

CLI: V1 commands plus `v2-*`. Tests: `tests/test_v1.py`, `test_v2.py`, plus older V0/V1 invariant tests.

## 2. What V1 does

V1 is a **non-stationary combinatorial semi-bandit** on a layered DAG with immutable indexed potential outcomes.

Question: under which shared-shock fractions `rho` does hierarchical node-edge state reduce **restricted recovery time** vs independent edge conductance, without unacceptable negative transfer when the shock is edge-specific.

Invariants observed in code: paired methods, isolated RNG (`mycelial-graph-v1:`), orthogonal shock L2 identity, censoring-aware RRT, atomic checkpoints, confirmatory lock, Structured SW-UCB as representation-aware baseline.

## 3. What V2.0-alpha actually implements

Implemented and used:

- `TokenUsage` / `TotalResourceLedger` with category identity tests  
- Synthetic resource DAG: Task → Retriever {3} → Model {cheap,standard,frontier} → Verify {skip,verify-scale} → Output  
- Hidden difficulty labels (not passed to agents as observations)  
- Shock regimes including STATIC, PRICE/QUALITY/LATENCY_SHOCK, OUTAGE, SCARCITY, MIXED, plus extra generator regimes (DRIFT, BURST_LOAD, …)  
- Baselines: always high/low, fixed budget, random, ε-greedy, transplanted V1 edge-only  
- Controller: decaying clipped conductance, windowed prune, convex translocation, ratio MVC at verification, hysteresis/switch penalty, router tokens ∝ candidates  
- Paired runner, traces, Pareto, quality NI vs always-high, resource audit CLI  
- Alpha ablations that actually change flags: `v2_no_pruning`, `v2_no_transfer`, `v2_no_cord`, `v2_no_cost_awareness`

Specified but **not mechanistically implemented** (factory aliases of `v2_mycelial`):

- `v2_no_branching`, `v2_no_anastomosis`, `v2_no_uncertainty`, `v2_static_topology`, `v2_no_shock_memory`

Deferred as documented: live providers, dynamic extra-edge branching, anastomosis fusion, confirmatory execution, structured working-state vs full history on live LLMs.

## 4. Documentation / implementation mismatches

| Claim | Documented? | Implemented? | Tested? | Measured? | Ablation? | Confirmatory? | Real-world? |
|---|---|---|---|---|---|---|---|
| V1 hierarchical recovery | Yes | Yes | Yes | Dev only | Partial (4 methods) | Locked | No |
| V2 ledger conservation | Yes | Yes | Yes | Traces | N/A | Locked | No |
| Quality NI then tokens | Yes | Analysis code yes | Unit/dev | Dev plots | Alpha flags | Locked | No |
| MVC as E[ΔQ]/ΔR | Yes | Ratio only | Indirect | `last_mvc` | vs cost-unaware | Locked | No |
| VOC difference form | Resource model no | **No (pre-bridge)** | No | No | No | — | No |
| Counterfactual VOC labels | No in alpha | **No (pre-bridge)** | No | No | No | — | No |
| Iso-model track | No in alpha | **No (pre-bridge)** | No | No | No | — | No |
| Q(B) budget sweep | No | **No (pre-bridge)** | No | Single B | No | — | No |
| Token waste categories | Coarse ledger | Coarse | Identity | Categories | No | — | No |
| Strong TS / SW-UCB / Lagrangian | Deferred honestly | **No (pre-bridge)** | No | No | — | — | No |
| Dynamic branching | Spec / stub names | Alias | No | No | Fake names | — | No |
| Anastomosis | Spec disabled | Alias | No | No | Fake names | — | No |
| Difficulty not leaked | Yes | Yes (not in obs) | Weak | N/A | N/A | — | No |
| Oracle path quality | Evaluation-only | `oracle_quality` recorded | Indirect | Gap not named AllocationRegret | No | — | No |
| Hard multi-resource polytope | Discussed | Scalar token cap only | Sum tokens | Money/latency parallel | No | — | No |
| Reservation/rollback | No | **No (pre-bridge)** | No | No | — | — | No |
| Real SWE tasks | Roadmap later | **No (pre-bridge)** | No | No | — | — | No |

Oracle **information in traces** (`oracle_quality` per step) is evaluation metadata. Treatment policies do not receive it in `choose()`. That is acceptable if analysis never trains on it. No learned VOC used oracle features in alpha.

## 5. Current experimental evidence

- V1: development demonstrator executable; **no confirmatory**.  
- V2.0-alpha: development demonstrator executable; **no confirmatory**.  
- No published PASS/REFUTED under frozen N.  
- No live coding-agent token evidence.

## 6. Unsupported claims (must remain unsupported)

- Real coding-agent token reduction  
- Biological optimality / “fungi prove the algorithm”  
- Production readiness  
- Universal superiority vs strong adaptive allocators  
- SWE-bench scores  
- That stub ablation names isolate branching/fusion

## 7. Strongest scientific gaps (ranked)

See section D in the implementation report companion list (top 20 below).

## 8–14. Engineering, stats, biology, related work, novelty, real-world

Covered in `docs/LITERATURE_REVIEW.md`, `docs/NOVELTY_AUDIT.md`, `docs/BASELINE_FAIRNESS.md`, and the Evidence Bridge protocol.

## Prioritized roadmap (this milestone)

Evidence Bridge only: VOC bench, iso-model, Q(B), waste proxies, strong baselines, local executable smoke, claim matrix, literature/novelty audit. **Not** dynamic topology, compatibility-gated fusion, colony-level budgets, or confirmatory unlock.

---

## A–T condensed answers

**A. Current-state audit.** This file.  
**B. Invariants to preserve.** V1 contracts listed in `docs/V2_IMPLEMENTATION_PLAN.md` §2; V2.0-alpha protocol/hash meaning; no confirmatory unlock; Physarum firewall.  
**C. Implemented-vs-documented matrix.** Table in §4.  
**D. Top 20 scientific gaps.** (1) No counterfactual VOC labels. (2) MVC ratio-only. (3) No iso-model. (4) Single budget point. (5) No MMRR freeze. (6) Weak adaptive baselines. (7) Stub ablations. (8) No false-stop/spend. (9) No waste identity beyond coarse buckets. (10) No Q(B) AUC pre-spec. (11) No real executable quality. (12) No matched-scaffold. (13) Difficulty ≠ compute-need. (14) No calibration (ECE/Brier) for stop. (15) Tail costs unreported. (16) Controller overhead break-even unmeasured. (17) No hierarchical repo clustering. (18) Drift vs shock under-used. (19) No phase diagram of advantage. (20) Biological C/D metaphors risk rhetorical upgrade.  
**E. Top 20 engineering gaps.** (1) God-adjacent controller still. (2) Scalar budget only. (3) No reservation. (4) Ledger schema unversioned (pre-bridge). (5) Alias ablations. (6) No decision-trace VOC fields complete. (7) No real adapter isolation. (8) Provider-agnostic cached tokens unused. (9) Performance vs |E| unbenchmarked. (10) No property tests on polytope. (11) CLI cannot voc-bench (pre-bridge). (12) Analysis ignores AllocationRegret. (13) State overhead is a constant. (14) Parallel branch cost always zero. (15) No OOD guard. (16) Control-plane vs task-text not tested. (17) Replay traces not a counterfactual engine. (18) Windows provenance already patched; keep. (19) Tree hash includes v2 in V1 provenance. (20) CI does not run V2.1 smoke (pre-bridge).  
**F–H.** See literature and novelty docs.  
**I–N.** See Evidence Bridge protocol.  
**O. Proposed file tree.** `v2/evaluation/`, `v2/policies/baselines_strong.py`, `v2/biology/voc.py`, `v2/resources/`, `v2/real/`, `experiments/v2_1/`, `research/references.yaml`.  
**P. Milestone boundaries.** Bridge now; branching/fusion later; confirmatory last.  
**Q. Do not build yet.** Dynamic extra-edge topology, vegetative incompatibility fusion, colony graphs, live paid APIs, Shapley over 2^k mechanisms, energy/CO2 from tokens.  
**R. Expected failures.** Strong bandit matches Mycelial; iso-model savings vanish; overhead > savings; NI fails on hard tasks; VOC miscalibrated.  
**S. Success/refutation gates.** Case-of-success gate in the prompt §158; refutation §166. Unmet until real + confirmatory evidence.  
**T. Branch.** `feat/evidence-bridge-adaptive-compute`. Additive commits. Do not merge automatically.
