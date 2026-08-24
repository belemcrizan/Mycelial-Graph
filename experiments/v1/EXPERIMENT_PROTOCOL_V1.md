# MG-EXP-V1: Hierarchical Structural Reuse Protocol

**Author:** Crizan Belem Ribeiro, Independent Researcher  
**Protocol version:** MG-EXP-V1  
**Freeze date:** 2026-08-24  
**Status:** Frozen for pilot; confirmatory execution locked pending sample-size addendum

## 1. Plain-language purpose

When one component of an AI pipeline changes, an edge-only router must update every affected connection separately. A hierarchical router may learn a shared node effect from one observation and reuse it across related connections. This could accelerate recovery when the disruption is genuinely shared. It could also spread a mistaken conclusion when only one edge changed.

This protocol tests both possibilities. It is designed to allow the hierarchical hypothesis to fail.

## 2. Scientific question

Under which controlled proportions of shared node shock does hierarchical node-edge partial pooling reduce recovery burden relative to independent edge conductance, without unacceptable negative transfer when the shock is edge-specific?

## 3. Formal setting

The environment is a non-stationary combinatorial semi-bandit on a layered directed acyclic graph. At each step, a method selects one complete source-to-sink path and receives local reward for every traversed edge. The environment changes once at a frozen shock time.

For edge `e=(u,v)` the hierarchical score is:

```text
score(e,t) = base + a[u,t] + b[v,t] + c[e,t]
```

The source, target, and interaction components use sum-to-zero projection and shrinkage. This is an experimental estimator, not a convergence theorem.

## 4. Controlled shock

Let `n` be a unit node-incidence pattern and `i` a disjoint unit edge-interaction pattern. For fixed magnitude `m`:

```text
d(rho) = -m * (sqrt(rho) * n + sqrt(1-rho) * i)
```

Because the supports are disjoint:

```text
||d(rho)||_2 = m
```

for every `rho`. The experiment changes the shared proportion without changing total L2 shock magnitude.

The grid is:

```text
rho in {0, 0.25, 0.50, 0.75, 1.0}
```

- `rho=0`: pure edge interaction and negative-transfer control;
- `rho=0.50`: primary mixed regime;
- `rho=1`: pure node-shared diagnostic control.

## 5. Immutable paired scenarios

Every `(seed, rho)` generates one scenario containing:

- graph topology;
- pre/post expected edge rewards;
- indexed potential local outcomes for every step and edge;
- fixed shock time and vector;
- unique certified pre/post optimal paths;
- minimum optimum margin.

For a given seed, all rho scenarios share the same topology, pre-shock means, and underlying potential-noise table. The complete rho family is accepted or rejected together, preventing the primary regime from being compared with a different pre-shock world.

Every method receives the same scenario but a read-only view. It observes only rewards on traversed edges. No method receives the shock location, latent expected rewards, future outcomes, or oracle path.

The oracle is used offline to certify expected optima, define regret, and evaluate recovery. It is not a competing method.

## 6. Methods

### 6.1 Edge-only Mycelial Graph

Independent bounded conductance per edge, temporal decay toward initial state, local reward update, temperature-controlled softmax, and explicit basal exploration.

### 6.2 Node-only ablation

Source and target node effects with the same Mycelial policy family and no edge interaction state.

### 6.3 Hierarchical Mycelial Graph

Source node, target node, and edge interaction state with shrinkage and sum-to-zero projection. Policy parameters and feedback contract match the Mycelial controls.

### 6.4 Structured sliding-window UCB

Linear UCB using source-node, target-node, and edge features with a fixed sliding observation window. This baseline receives the same local feedback and prevents hierarchical MG from winning solely because it owns the shared representation.

## 7. Outcomes

### 7.1 Recovery event

Recovery occurs at the earliest post-shock step `t` for which:

1. trailing mean expected selected-path utility over the frozen window is at least 90% of post-shock oracle expected utility; and
2. the trailing mean remains above the threshold for the frozen confirmation window.

Expected utility is available to the simulator for evaluation but not to the methods.

### 7.2 Individual restricted recovery time

```text
RRT_i = min(T_recovery_i, tau)
```

If recovery does not occur by `tau`, `recovery_time` is null, `censored=true`, and `RRT=tau`.

### 7.3 Primary estimand

At `rho=0.50`:

```text
delta_RRT = (E[RRT_hierarchical] - E[RRT_edge]) / E[RRT_edge]
```

Negative values favor the hierarchical method.

### 7.4 Secondary outcomes

- recovery probability;
- post-shock dynamic regret;
- final expected utility;
- decision CPU time;
- descriptive behavior across all rho values.

## 8. Hypotheses and decision gates

### 8.1 Primary superiority hypothesis

```text
H0: delta_RRT >= 0
H1: delta_RRT < 0
```

The primary analysis is a paired bootstrap over frozen scenarios. Superiority is supported when the frozen 95% one-sided upper confidence bound is below zero. The implementation also reports the bootstrap mass beyond the null as a descriptive tail probability, not as an exact frequentist p-value.

### 8.2 Engineering promotion gate

The proposed hierarchical state advances only if all hold:

1. the primary one-sided upper confidence bound is below zero;
2. point estimate `delta_RRT <= -0.20`;
3. the non-inferiority test at `rho=0` passes;
4. computational cost stays within the separately reported operational budget before product promotion.

The 20% threshold is an engineering decision: a smaller estimated improvement does not justify additional state, implementation surface, and future operational cost. It is not claimed as a statistically proven minimum unless its confidence interval supports that statement.

### 8.3 Negative-transfer non-inferiority

At `rho=0`, with margin `M=+0.10`:

```text
H0: delta_RRT >= +0.10
H1: delta_RRT < +0.10
```

Non-inferiority passes when the frozen one-sided upper confidence bound is below `+0.10`.

### 8.4 Interpretation matrix

| Outcome | Scientific interpretation | Engineering action |
|---|---|---|
| Superior, >=20% estimated gain, non-inferior at rho=0 | Broad supporting evidence | Promote hierarchical state |
| Benefit only at high rho | Conditional shared-structure effect | Keep as specialized/adaptive option |
| Node benefit plus interaction harm | Positive and negative transfer boundary | Study adaptive pooling selector |
| Adequately powered equivalence/no relevant benefit | Hypothesis unsupported in tested regime | Archive hierarchy |
| Wide interval containing relevant benefit and harm | Inconclusive | Improve measurement/design; do not promote |
| Worse in favorable regimes | Hypothesis refuted under protocol | Stop this direction |

## 9. Seeds and execution phases

- Development: five seeds for implementation verification; no evidence.
- Pilot: twenty disjoint seeds for variance and sample-size planning; no confirmatory claim.
- Confirmatory: first `N` entries from the precommitted pool, selected mechanically after `N` is recorded in the addendum.

Development and pilot results cannot be pooled into the primary confirmatory analysis.

## 10. Determinism and failure handling

- Scenario and method RNG streams are independently namespace-derived.
- Potential outcomes are indexed by step and edge.
- Serial and parallel execution must produce identical canonical scientific payloads.
- Infrastructure failure invalidates the complete paired scenario and is logged before rerun.
- A method-level failure or timeout is retained as an outcome under the pre-specified rule.
- Atomic checkpoints never silently overwrite a completed canonical result.
- Timestamps, hostnames, and CPU duration are provenance, not deterministic payload.

## 11. Prohibited confirmatory actions

- hyperparameter changes after observing confirmatory results;
- adaptive temperature, exploration, or early termination not specified here;
- live price or latency queries;
- seed removal based on method performance;
- replacing censored recovery times with fabricated event times;
- changing the primary contrast or metric after data inspection;
- presenting pilot results as confirmatory.

## 12. Amendments

This file is never silently overwritten after data collection starts. Necessary changes require a dated `PROTOCOL_AMENDMENT_NNN.md` stating the reason, whether any relevant outcomes were observed, and which analyses become exploratory.

## 13. Scope boundary

MG-EXP-V1 does not test multicloud deployment, real provider economics, distributed consensus, graph discovery, causal attribution, production safety, or theoretical regret bounds. Those require separate evidence and protocols.
