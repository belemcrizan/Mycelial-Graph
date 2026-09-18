# Strong Baseline Suite — Specification (STAGED)

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Serves:** Master Prompt Part II §6 · Kernel gate: **GATE-FROZEN** for execution; this spec doc is
**GATE-SAFE** (additive documentation).
**Existing code referenced (read-only):** `src/mycelial_graph/v2/policies/baselines.py`,
`src/mycelial_graph/v2/policies/baselines_strong.py`, `research/STRONG_BASELINES_PLAN.md`.

---

## 0. Principle

Weak baselines are unacceptable (§6). A negative V1 result is only interesting *against a fair,
strong comparator set*. No baseline may be intentionally under-tuned; no MG-specific tuning-budget
advantage is permitted. Hyperparameter budgets are **matched** and tuned on **separated validation
data** (§6, §10).

## 1. Baseline set, with justification and fairness note

| Baseline | Why appropriate for adaptive routing under non-stationarity | Tuning budget |
|---|---|---|
| ε-greedy | canonical exploration floor | matched grid |
| UCB1 / UCB-V | optimism under stationarity; reference | matched grid |
| Discounted-UCB / SW-UCB | **non-stationary** bandit standard; matches V1's structured SW-UCB | matched grid |
| Thompson Sampling | Bayesian posterior sampling; strong general baseline | matched priors |
| Contextual bandit (LinUCB) | uses context where present | matched features |
| Change-point detector + router | explicit shock detection then re-route | matched detector params |
| EXP3 | adversarial/worst-case regime | matched η |
| Fixed routing | lower bound / control | none |
| Random routing | floor | none |
| Oracle (best fixed / best dynamic) | **upper bound**, not a deployable competitor | n/a |
| Always-high / always-low compute | cost-extreme references | none |
| Cost-aware heuristic | practical operator baseline | matched |
| V1 edge-only | direct V1 comparator | frozen |

**Do not** add an algorithm merely because its name sounds strong (§6). Each row above states its
scientific role. Additions require a stated role.

## 2. Fairness protocol (predefined)

- Identical feedback contract, horizon, seeds, and environment across all methods.
- Matched HPO budget (same number of trials), validation data disjoint from confirmatory seeds.
- Report per-method tuning provenance; no post-hoc reselection of the best baseline seed.
- Oracle is reported as a bound, never as a "beaten competitor."

## 3. Outputs

Machine-readable comparison table (method × regime × topology) with effect sizes and uncertainty
intervals, feeding the regime map (§8) and Paper B (§12). All **SYNTHETIC** unless run on an
external dataset under `docs/EXTERNAL_VALIDATION_LADDER.md`.

## 4. Gate

Execution is **GATE-FROZEN/GATE-HUMAN**; this document only specifies the suite. Any run needs a
committed authorization and respects the moratorium.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
