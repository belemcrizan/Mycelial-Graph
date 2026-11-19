# Architecture — V1 Recovery Benchmark & Mycelial V2 Resource-Aware Graph

## 1. Two Coexisting, Strictly Isolated Layers

Mycelial-Graph maintains two isolated architectural layers so historical V1 confirmatory artifacts remain byte-reproducible while V2 advances resource-aware adaptive routing:

1. **V1 Core (`src/mycelial_graph/{environment,agents,runner,analysis,reporting}`):** Frozen non-stationary graph semi-bandit benchmark answering whether hierarchical node-edge pooling accelerates post-shock recovery relative to independent edge state (`REFUTED` at $\rho = 0.50$, $N = 97$, classified `EQ-B` post-confirmatory due to update-scale mismatch).
2. **Mycelial V2 (`src/mycelial_graph/v2/`):** Additive protocol-oriented computational graph architecture $G = (V, E, S, B, H)$ optimizing validated task utility under explicit token, cost, latency, risk, and hard budget constraints.

Core V1 source files are never imported mutably or modified by V2 evolution; shared primitives (`LayeredDAG`, `stable_softmax`, `load_seeds`) are consumed read-only.

---

## 2. V1 Architecture (Preserved Unchanged)

### Boundaries

```text
Frozen YAML + seed list
          |
          v
Immutable Scenario Generator
  - DAG topology
  - latent edge means
  - node/interaction shock
  - indexed potential outcomes
  - certified pre/post optima
          |
          +-------------------------------+
          |               |               |
      Edge-only       Node-only      Hierarchical      Structured SW-UCB
          |               |               |                    |
          +---------------+---------------+--------------------+
                                  |
                         Paired raw trial records
                                  |
                         Frozen paired analysis
                                  |
                       Markdown report + figures
```

### Why scenarios are immutable

Running two agents sequentially against one mutable environment is not a paired experiment. V1 pre-generates indexed potential outcomes (`rewards[step, edge_id]`). If two policies traverse the same edge at the same step, they observe identical local feedback; diverging routes query their respective pre-committed outcomes without mutating RNG state.

### Shock construction

Let `n` be a unit-length pattern supported on edges incident to a selected node, and `i` be a unit-length edge-interaction pattern with disjoint support:

$$d(\rho) = -\text{magnitude} \cdot \left(\sqrt{\rho}\, n + \sqrt{1 - \rho}\, i\right)$$

Because $n \perp i$, total $L_2$ shock magnitude is invariant across $\rho \in [0, 1]$.

---

## 3. Mycelial V2 Architecture: $G = (V, E, S, B, H)$

### Before vs. After Engineering Recovery

| Architectural Concern | V2.0-alpha / V2.1 State (Before) | Evolved Mycelial V2 State (After) |
|---|---|---|
| **Graph model** | Implicit `3`-layer index math hardcoded to node `4` for verification | Explicit `ComputationalGraph` $G = (V, E, S, B, H)$ supporting $2\text{--}6$ internal layers and arbitrary per-layer widths (`heterogeneous_pipeline`) with Kahn DAG & source-to-sink reachability checks |
| **Component health $H$** | Ad-hoc arrays inside `MycelialResourceController` | First-class `HealthSignals` tracking EWMA quality/variance, token/cost/latency/failure estimates, surprise $z$-scores, and discrepancy-gated anastomosis |
| **Resource budget $B$** | `BudgetReservation` existed as an unused helper; `translocate` wrote dead `self.budget` | Hard `BudgetReservation` enforced in `run_v2_method` and `run_local_agent`; corridor `self.budget` actively modulates candidate feasibility and translocation log-ratio preference |
| **Hard guardrails** | Softmax/exploration overrode `mandatory_verification` and `max_risk` | Hard pre-routing feasibility filter at every verification/model transition before soft scoring or exploration |
| **Ablation surface** | 5 `v2_no_*` methods mapped to `{}` clones differing only by RNG namespace | All 9 `v2_*` ablations map to distinct boolean flags sharing a paired `v2_mycelial_family` RNG stream (`UNIMPLEMENTED_ALPHA_ALIASES = frozenset()`) |
| **External boundary** | Direct simulator coupling | Clean `@runtime_checkable` protocols (`GraphEngine`, `RoutingPolicy`, `ResourceLedger`, `ProviderAdapter`) + zero-network `DeterministicMockProvider` |
| **Visualization** | Coupled report figures only | Optional decoupled `v2/viz.py` (`render_topology_svg`, `render_trace_dashboard`) never imported by core simulation |

### Clean Module Boundaries (`src/mycelial_graph/v2/`)

```text
                       +-----------------------------------+
                       |     YAML Config & Validation      |
                       |  (v2/types.py, config.py,         |
                       |   validation.py)                  |
                       +-----------------+-----------------+
                                         |
          +------------------------------+------------------------------+
          |                              |                              |
          v                              v                              v
+-------------------+        +-----------------------+      +-----------------------+
| Graph & Health    |        |Immutable V2 Scenarios |      | Hard Budget & Ledger  |
| v2/graph_model.py |        | v2/environment/       |      | v2/resources/         |
| - ComponentSpec V |        | - 8 shock regimes     |      | - BudgetReservation B |
| - AdaptiveState S |        | - read-only arrays    |      | v2/ledger/tokens.py   |
| - HealthSignals H |        | - failure-adj optima  |      | - 14 token buckets    |
+---------+---------+        +-----------+-----------+      +-----------+-----------+
          |                              |                              |
          +------------------------------+------------------------------+
                                         |
                                         v
                       +-----------------------------------+
                       |     Routing Policy Layer          |
                       |  v2/policies/ + v2/biology/       |
                       |  - Scalarized / Constrained /     |
                       |    Pareto objectives              |
                       |  - 6 feature-flagged mechanisms   |
                       |  - V1 & bandit/heuristic baselines|
                       +-----------------+-----------------+
                                         |
                                         v
                       +-----------------------------------+
                       |   Deterministic Trial Runner      |
                       |  v2/runner/{trial,experiment}.py  |
                       |  - Explainable V2DecisionRecord   |
                       |  - mtime=0 gzip + atomic fsync    |
                       +-----------------+-----------------+
                                         |
                     +-------------------+-------------------+
                     |                                       |
                     v                                       v
       +---------------------------+           +---------------------------+
       | Audit & Paired Statistics |           | Optional Adapters & Viz   |
       | v2/audit.py, analysis.py, |           | v2/interfaces.py (Mock)   |
       | evaluation/{waste,voc}    |           | v2/viz.py (SVG / PNG)     |
       +---------------------------+           +---------------------------+
```

### Decision Cycle per Task Step

1. **Allowance check:** `BudgetReservation.sustainable_step_allowance(steps_left)` combined with any active regime cap (`RESOURCE_SCARCITY`) sets `effective_step_cap`.
2. **Stage-by-stage feasibility filtering:**
   - **Cytoplasmic retraction filter:** omits persistently inefficient edges (`self.pruned`) from candidate scoring to save `router_tokens`, while retaining connectivity invariants and a $3\%$ rehabilitation probe.
   - **Verification & risk guardrails:** enforces `mandatory_verification`, `minimum_quality`, and `max_risk` *before* soft scoring; enters `safety_fallback` selecting minimum-risk transition if all candidates breach `max_risk`.
   - **Step token feasibility:** filters candidates whose estimated tokens plus downstream reserve exceed `step_cap`, or downgrades to minimum-token fallback (`budget_downgrade`).
   - **Objective filter:** applies scalarized utility, online primal-dual `dual_price` (`v2_constrained`), or non-dominated vector filtering (`v2_pareto`).
3. **Controlled branching vs. exploitation:** selects via VoI-weighted exploration (`branching_exploration`) with probability `exploration_probability`, or temperature-scaled softmax over conductance + expected net utility + active translocation corridor log-ratio.
4. **Execution & accounting:** queries immutable scenario (or `ProviderAdapter`), commits exact token buckets and call counts to `TotalResourceLedger` and `BudgetReservation`, and emits a fully explainable `V2DecisionRecord`.
5. **Local feedback update:** updates `HealthSignals` (with surprise-triggered shock damping), updates `conductance` (reliable-utility cord reinforcement + prior-centered decay), updates observation-gated `prune_evidence`, and applies floor-preserving `translocate`.
