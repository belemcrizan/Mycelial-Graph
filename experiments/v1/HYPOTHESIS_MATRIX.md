# MG-EXP-V1 Hypothesis and Claim-Control Matrix

**Status:** derived artifact. It does not create, remove, or reinterpret any hypothesis.
Every row restates what is already frozen in
[`EXPERIMENT_PROTOCOL_V1.md`](EXPERIMENT_PROTOCOL_V1.md) (sections 4, 7, 8) and
[`ANALYSIS_PLAN.md`](ANALYSIS_PLAN.md) (sections 2–6), and names the artifact field that carries it.

**Purpose:** enumerate every hypothesis and contrast that can appear in a V1 confirmatory
report, so that no exploratory quantity can be read as confirmatory.

Frozen multiplicity policy (`ANALYSIS_PLAN.md` §5, unchanged): *the only primary confirmatory
contrast is hierarchical versus edge-only at `rho=0.50`; the `rho=0` non-inferiority contrast is
the pre-specified secondary safety gate; all other rho values, node-only comparisons, SW-UCB
comparisons, dynamic regret, and ablations are secondary or exploratory.* Because the
confirmatory family contains exactly one superiority hypothesis, no alpha split or step-down
procedure is required, and none is introduced here.

## Matrix

| ID | Hypothesis / contrast | rho | Method comparison | Role | Error control | Claim allowed |
| -- | --------------------- | --: | ----------------- | ---- | ------------- | ------------- |
| H1 | `H0: delta_RRT >= 0` vs `H1: delta_RRT < 0` on the frozen primary estimand | 0.50 | hierarchical vs edge-only | **PRIMARY** | one-sided alpha 0.05; single hypothesis, no adjustment needed; `N=97` powered at 0.80 for `delta_RRT = -0.20` | Superiority in restricted recovery time at `rho=0.50`, in the tested graph, observation contract, shock construction, and parameter ranges only |
| H2 | `H0: delta_RRT >= +0.10` vs `H1: delta_RRT < +0.10` | 0.00 | hierarchical vs edge-only | **SAFETY GATE** | one-sided alpha 0.05; pre-specified single gate; **not separately power-analysed** | Absence of negative transfer beyond `+0.10` at `rho=0`, or failure thereof. Never a superiority claim |
| H3 | Engineering promotion threshold `point estimate <= -0.20` | 0.50 | hierarchical vs edge-only | SECONDARY | none — deterministic threshold on a point estimate | An engineering decision about whether extra state is worth its cost. Not a statistical claim, and not "a proven minimum effect" unless H1's interval supports it |
| H4 | Operational cost budget (protocol §8.2 requirement 4) | all | hierarchical vs controls | DIAGNOSTIC | none; **not automated** | Nothing. No cost budget is frozen, so this requirement is evaluated outside the automated gate |
| H5 | Mean RRT, recovery probability, dynamic regret, final expected utility | 0.50 | node-only, structured SW-UCB vs Mycelial arms | SECONDARY | none | Descriptive comparison only. A baseline beating hierarchical is reportable and must be reported; it does not license a reversed confirmatory claim |
| H6 | Mean RRT and all group metrics | 0.25, 0.75 | any | **EXPLORATORY** | none | Description of the observed sample. No inference, no trend claim |
| H7 | Mean RRT and all group metrics | 1.00 | any | DIAGNOSTIC | none | Behaviour under a pure node-shared shock, used as a construct check that shared structure is learnable at all |
| H8 | `G(rho) = (RRT_hier(rho) - RRT_edge(rho)) / RRT_edge(rho)` across the rho grid; any crossover `rho*` | 0, .25, .50, .75, 1 | hierarchical vs edge-only | **EXPLORATORY** | none | Nothing about `rho*`. V1 is not powered or designed to establish the existence, location, or shape of a crossover. Plots must carry the exploratory label |
| H9 | Decision CPU time (mean, p95) | all | all | DIAGNOSTIC | none | Computational cost description on this machine. Not a latency or throughput claim |
| H10 | Censoring and recovery counts | all | all | DIAGNOSTIC | none | Integrity check. Non-administrative censoring suspends the automated primary conclusion (`ANALYSIS_PLAN.md` §6) |

## Result-state mapping for H1 and H2

Deterministic function of the frozen bootstrap outputs, pre-specified before any confirmatory
outcome was observed (see [`AMENDMENT_002.md`](AMENDMENT_002.md)). `U` is the frozen one-sided
95% upper bound, `L` the lower end of the two-sided 95% interval, `E` the point estimate.

| Result state | Condition | Frozen source |
| --- | --- | --- |
| `PROTOCOL_INVALID` | non-administrative censoring, or paired-integrity failure | `ANALYSIS_PLAN.md` §6, §8 |
| `SUPPORTED` | `U_primary < 0` and `E_primary <= -0.20` and `U_safety < +0.10` | protocol §8.2 requirements 1–3 |
| `CONDITIONAL` | `U_primary < 0`, but the engineering threshold or the safety gate fails | protocol §8.4 rows 2–3 |
| `REFUTED` | `U_primary >= 0` and `L_primary > -0.20` (the pre-specified relevant benefit is excluded) | protocol §8.4 rows 4, 6; `ANALYSIS_PLAN.md` §10 |
| `INCONCLUSIVE` | `U_primary >= 0` and `L_primary <= -0.20` (interval still contains the relevant benefit) | protocol §8.4 row 5; `ANALYSIS_PLAN.md` §10 |

`SUPPORTED`, `CONDITIONAL`, `INCONCLUSIVE`, `REFUTED`, and `PROTOCOL_INVALID` are all legitimate
terminal states. None of them may be rewritten into success language.

## Claim boundary of the strongest possible V1 narrative

> In a partially shared shock regime at `rho=0.50`, hierarchical node-edge pooling was tested
> against edge-only adaptation for restricted recovery time on 97 pre-selected paired
> scenarios, while a separately pre-specified `rho=0` safety gate evaluated whether hierarchical
> sharing caused negative transfer beyond a `+0.10` non-inferiority margin.

Even when both H1 and H2 succeed, this does **not** establish all-rho superiority, a crossover,
a universal structural-sharing benefit, production benefit, real-provider generalisation, a
causal mechanism, or any theoretical guarantee.
