# Mycelial Graph V2.0-alpha Implementation Plan

**Status:** Additive scientific layer. V1 remains frozen and executable.  
**Branch:** `feat/mycelial-v2-resource-allocation`  
**Milestone:** V2.0-alpha — Adaptive Bio-Inspired Resource Allocation for Agentic Systems  
**Does not claim:** production readiness, biological optimality, or confirmatory superiority.

This document is the audit-first plan required before V2 code. It records what exists, what must not break, and what V2.0-alpha actually delivers.

---

## 1. Current architecture (V1, frozen)

Mycelial Graph V1 is a reproducible research edition for a non-stationary combinatorial semi-bandit on a layered DAG.

Scientific question:

> Can an AI execution system recover from a local disruption without relearning everything?

More precisely (MG-EXP-V1): under which shared-shock fractions `rho` does hierarchical node-edge state reduce restricted recovery time relative to independent edge conductance, without unacceptable negative transfer when the shock is edge-specific?

### Data flow

```text
Frozen YAML + seed list
        |
        v
Immutable Scenario Generator
  DAG, latent edge means, node/interaction shock,
  indexed potential outcomes, certified pre/post optima
        |
  edge-only | node-only | hierarchical | Structured SW-UCB
        |
Paired raw trial records -> frozen paired analysis
        |
Markdown report + figures + manifest + hashes
```

### Code map (do not relocate)

| Area | Location | Role |
|---|---|---|
| CLI | `src/mycelial_graph/cli.py` | `validate`, `experiment`, `analyze`, `report`, `sample-size`, `demo` |
| V1 types/config | `src/mycelial_graph/types.py` | Frozen YAML contract |
| Environment | `src/mycelial_graph/environment/` | Layered DAG, immutable scenarios |
| Agents | `src/mycelial_graph/agents/` | Four methods, isolated RNG |
| Runner | `src/mycelial_graph/runner/` | Paired trials, atomic checkpoints |
| Analysis | `src/mycelial_graph/analysis/` | RRT, regret, paired bootstrap, power |
| Reporting | `src/mycelial_graph/reporting/` | REPORT.md + figures |
| Protocol | `experiments/v1/` | Protocol, analysis plan, configs, confirmatory lock |
| V0 demo path | `graph.py`, `routing.py`, `trial.py`, `configs/v0_demo.yaml` | Preserved V0 demonstrator |

V0 and V1 coexist. V2 must not absorb or rewrite either.

---

## 2. Invariants that must not be broken

These are scientific contracts, not style preferences.

1. **V1 CLI and configs remain valid.** Existing commands, YAML keys, and `experiments/v1/` files are unchanged in meaning.
2. **Immutable scenarios.** Methods never mutate the shared world. Potential outcomes are indexed by `(step, edge)`.
3. **Paired methods.** All configured methods see the same scenario; they differ only in action and therefore in which frozen outcomes they query.
4. **Independent RNG namespaces.** V1 continues to derive seeds as `mycelial-graph-v1:{master}:{namespace}`. V2 uses a distinct prefix `mycelial-graph-v2:`.
5. **Shock L2 identity (V1).** `||d(rho)||_2 = magnitude` for every `rho` via orthogonal node and interaction patterns.
6. **Certified unique pre/post optima** with configured margin; entire rho family accepted or rejected together.
7. **Censoring-aware RRT.** Unrecovered trials have `recovery_time=null`, `censored=true`, `RRT=tau`.
8. **Primary V1 contrast** remains hierarchical vs edge-only at `rho=0.50`. V2 analysis must not overwrite that pipeline.
9. **Confirmatory lock.** Missing `seeds.confirmatory.txt` is intentional. V2 confirmatory is locked the same way, in a separate directory.
10. **Atomic checkpoints.** Completed canonical results are never silently overwritten.
11. **Provenance isolation.** Timestamps, hostname, and CPU duration are not part of scientific hashes.
12. **No live APIs.** No keys, no required providers. Simulation first.
13. **V1 tests stay green.** Including serial/parallel payload identity and checkpoint idempotence.
14. **Claim discipline.** Development results are not confirmatory. Negative results are valid.

---

## 3. Gaps that V2 must fill (without replacing V1)

V1 measures **recovery of path utility after a mean shock**. It does not:

- treat tokens, money, or latency as conserved resources;
- expose a total resource ledger (including router overhead);
- allocate budget dynamically during a trial;
- test quality non-inferiority jointly with resource reduction;
- model hyphal-style metabolism (reinforce, retract, translocate);
- provide V2 regimes (price shock, outage, scarcity, difficulty shift);
- report Pareto frontiers.

Those are additive questions. Token efficiency is a new dimension, not a replacement identity.

---

## 4. Evolution strategy

- Add `src/mycelial_graph/v2/` as a new package.
- Add `experiments/v2/` and `docs/*V2*` / biological/resource docs.
- Extend CLI with `v2-*` subcommands only.
- Leave `src/mycelial_graph/environment/`, `agents/`, `analysis/` (V1), and `experiments/v1/` untouched except where a shared utility is imported (atomic write, LayeredDAG).
- Reuse `LayeredDAG` and `atomic_write_json` by import. Do not fork the graph type.
- Advanced branching and anastomosis are specified scientifically in V2.0-alpha and implemented as **hooks + ablations stubs**; full fusion/branch topology search is deferred to V2.1.

---

## 5. Biology → computation map (falsifiable)

Physarum polycephalum is **not** a fungus. V2 fungal mechanisms are separate from any later slime-mold transport algorithm. See `docs/BIOLOGICAL_DESIGN_SPEC.md`.

| Biological observation | Computational abstraction | V2.0-alpha mechanism | Ablation | Failure condition |
|---|---|---|---|---|
| Hyphal branching in heterogeneous media | Open an alternative route when VoI exceeds branch cost | Spec + costed exploration; topology remains the frozen DAG (no free extra edges) | `-no-uncertainty` / later `-no-branching` | Exploration explosion; router overhead dominates |
| Anastomosis / fusion | Controlled state sharing across routes | Specified; not fully enabled in alpha | `no_anastomosis` default | Negative transfer |
| Cord formation | Reinforce high utility/resource corridors | Bounded conductance update + demand term | `-no-cord-reinforcement` | Runaway reinforcement |
| Cytoplasmic retraction | Retract budget from persistently useless routes | Persistence-window pruning | `-no-pruning` | Premature pruning |
| Resource translocation | Move budget along expected utility/deficit | Conservative reallocation with mix coefficient | `-no-resource-transfer` | Budget thrashing |
| Damage response | Reroute after non-stationary shocks | V2 shock regimes + recovery metrics | `-no-shock-memory` (later) | Oscillation / lock-in |
| Foraging | Cheap probes then concentrate compute | MVC / stop at verification layer | vs always-high / always-low | Quality collapse |

---

## 6. Proposed file structure

```text
docs/V2_IMPLEMENTATION_PLAN.md
docs/BIOLOGICAL_DESIGN_SPEC.md
docs/RESOURCE_MODEL.md
docs/TOKEN_ACCOUNTING.md
docs/V2_ARCHITECTURE.md
docs/V2_RESEARCH_QUESTIONS.md
docs/V2_FAILURE_MODES.md
docs/V2_MIGRATION.md

experiments/v2/
  README.md
  EXPERIMENT_PROTOCOL_V2.md
  ANALYSIS_PLAN_V2.md
  SAMPLE_SIZE_ADDENDUM_V2.md
  config.development.yaml
  config.pilot.yaml
  config.confirmatory.yaml          # locked
  seeds.development.txt
  seeds.pilot.txt
  seeds.confirmatory.pool.txt
  # seeds.confirmatory.txt ABSENT until addendum

src/mycelial_graph/v2/
  types.py, config.py, validation.py, seeding.py
  ledger/          TokenUsage, ResourceObservation, TotalResourceLedger
  environment/     resource attributes, shocks, immutable scenarios
  biology/         conductance, pruning, translocation, stop, metabolism
  policies/        baselines + Mycelial Resource Controller
  metrics/         recovery, Pareto, non-inferiority
  runner/          paired trials, experiment, traces
  analysis.py, reporting.py
```

V1 files stay in place.

---

## 7. Initial mathematical specification

### Edge resource vector (partially observed)

For edge `e` at time `t`:

```text
a_e(t) = (Q, u, T, C, L, r_fail, reliability, IG, U_hist, G)
```

Only traversed edges yield observations. Means and prices may drift. Estimates carry uncertainty.

### Scalar routing utility (decision only)

```text
U = Q
  - λ_t T
  - λ_c C
  - λ_l L
  - λ_r Risk
  - λ_f FailurePenalty
  - λ_s StateOverhead
```

This scalar is **not** the scientific estimand. Evaluation always reports the vector `(Q, T, C, L, success, recovery, ledger totals)` and Pareto relations.

### Marginal value of compute

```text
MVC = E[ΔQ] / max(ΔR, ε)
```

where `ΔR` is additional tokens (or composite units) of the more expensive local option (e.g. verify vs skip). Allocate the extra option iff `MVC > τ` and hard constraints allow it.

### Conductance (bounded, justified)

Runaway literal sums are rejected. Alpha uses a normalized, decaying, clipped update:

```text
target_e = Q_obs - λ_t T_norm - λ_c C_norm
G_e ← clip(
    (1-δ) G_e + α (target_e - 0.5) + β demand_e - η waste_e,
    G_min, G_max
)
```

`G_min` is an exploration floor. Caps prevent cord runaway.

### Budget conservation

```text
Σ_e B_e(t) = B_max(t)
```

`B_max` may drop under `RESOURCE_SCARCITY` but the sum still equals the current cap. Translocation is a convex mix toward utility-weighted shares so the constraint is an invariant, not a hope.

### Pruning

```text
PruneScore_e = T_norm + C_norm + redundancy + fail_rate - MVC_hat
```

Prune (set `B_e` to the floor, keep `G_min`) only after `K` consecutive windowed exceedances. One bad draw is not enough.

### Network maintenance

Every decision adds `router_tokens` proportional to considered outgoing edges. Dense scoring is never free in the ledger.

---

## 8. Experimental design

Protocol: **MG-EXP-V2** (separate from MG-EXP-V1).

Phases: development → pilot → sample-size addendum → locked confirmatory.

**Primary scientific order**

1. Quality non-inferiority vs always-high-compute (and vs the quality-optimal oracle gap as descriptive).
2. Conditional on (1), test resource reduction (tokens and money), with router overhead included.
3. Robustness under shock regimes.
4. Ablations of biological mechanisms.

**H0 / H1 (quality)**

```text
H0: ΔQ = Q_v2 - Q_high ≤ -ε
H1: ΔQ > -ε
```

Non-inferiority passes when the frozen one-sided lower confidence bound exceeds `-ε`.

Gates may conclude `PASS`, `CONDITIONAL`, `INCONCLUSIVE`, or `REFUTED`. They are not designed to force a win.

Immutable V2 scenarios include: topology, latent attributes, difficulty label (hidden from methods), indexed resource outcomes, price path, shock time, regime identity.

---

## 9. Baselines (V2.0-alpha)

| Method | Role |
|---|---|
| `always_high_compute` | Frontier model + heavy retrieval + verify |
| `always_low_compute` | Cheap model + light retrieval + skip verify |
| `fixed_budget` | Always standard compute (static allocation) |
| `random_router` | Uniform feasible path |
| `epsilon_greedy` | Quality-greedy with ε exploration, no cost |
| `v1_edge_only` | V1-style quality-only conductance transplanted into the V2 env |
| `v2_mycelial` | Resource controller (reinforce, prune, translocate, MVC stop) |

Documented but **not** first-class alpha implementations: Thompson Sampling, cost-sensitive bandit, Structured SW-UCB on the V2 resource vector. Reason: they need a specified feature map and prior; adding a weak caricature would bias the comparison. They remain protocol baselines for V2.1 once specified.

---

## 10. Ablations (alpha)

| Ablation | Disabled |
|---|---|
| `v2_mycelial` | none (full alpha controller) |
| `v2_no_pruning` | persistence pruning |
| `v2_no_transfer` | translocation mix = 0 |
| `v2_no_cord` | demand/cord term = 0 |
| `v2_no_cost_awareness` | λ_t = λ_c = λ_l = 0 (quality-only scores) |

Branching/anastomosis full topology operators: specified, default off, V2.1.

---

## 11. Scientific risks

- Optimizing tokens without quality control selects always-low-compute (weak claim).
- Scalar utility hides Pareto trade-offs; reports must keep vector metrics.
- Hidden router/summarization tokens can fake savings — the ledger is mandatory.
- Difficulty labels leaking to the agent would allow memorization, not inference.
- Overfitting prices in PRICE_SHOCK without testing STATIC.
- Declaring alpha development plots as evidence.
- Incorrect fungal/Physarum claims.

---

## 12. Engineering risks

- Changing V1 RNG namespaces or config schema.
- `source_tree_hash` includes all `src/**/*.py`; new V2 files change *future* V1 `code_commit` provenance. Historical `outputs/demo` remain valid archives. This is honest, not a silent invalidation of stored results.
- God-class controller — split biology modules.
- Slow experiments — development config stays small.
- Float drift in budget sums — test conservation with tight tolerance.
- CLI breakage — only additive subcommands.

---

## 13. Milestone V2.0-alpha — exact definition

**In scope**

- V2 specification documents listed above.
- Biological design spec with falsifiable hypotheses.
- Resource model + provider-agnostic token/resource types.
- Total resource ledger with no unaccounted buckets used by the simulator.
- Synthetic immutable environment with task difficulty (hidden) and shock regimes: `STATIC`, `PRICE_SHOCK`, `QUALITY_SHOCK`, `LATENCY_SHOCK`, `OUTAGE`, `RESOURCE_SCARCITY`, `MIXED_SHOCK`.
- Baselines: always high/low, fixed budget, random, epsilon-greedy, transplanted V1 edge-only.
- Mycelial Resource Controller: conductance reinforcement, pruning, translocation, MVC stop, hysteresis/switch penalty.
- Deterministic paired experiment runner, manifests, traces.
- Pareto and quality-cost reporting.
- V2 protocol/analysis/sample-size lock files.
- CLI `v2-demo`, `v2-validate`, `v2-experiment`, `v2-analyze`, `v2-report`, `v2-ablate`, `v2-pareto`, `v2-resource-audit`.
- Tests: budget conservation, ledger identity, replay, pruning persistence, translocation, V1 regression suite still green.

**Out of scope (V2.1+)**

- Live OpenAI/Anthropic/Gemini adapters.
- Dynamic extra-edge branching that mutates topology mid-trial.
- Full anastomosis / shared working-state fusion.
- Confirmatory execution and publication claims.
- Structured working-state vs full history live LLM experiment.

**Exit criterion for alpha:** the development demonstrator runs, V1 tests pass, V2 invariants pass, reports refuse confirmatory language, confirmatory config stays locked.
