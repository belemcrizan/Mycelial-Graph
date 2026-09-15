# V1 Confirmatory Moratorium

**Start date:** 2026-09-14 (UTC-3)
**Start commit:** `acedef91559a81e2ff15606d3c13dd6a113be390`
**Protocol under moratorium:** `MG-EXP-V1`
**Status:** **SATISFIED** — see [Exit record](#exit-record). The moratorium held for the whole
cycle; nothing outside the V1 confirmatory path was developed.

## Scientific justification

The repository has accumulated substantially more research engineering than confirmatory
evidence. The frozen V1 question — whether hierarchical node-edge pooling reduces restricted
recovery time relative to edge-only adaptation at `rho=0.50` without unacceptable negative
transfer at `rho=0` — has never been submitted to its own experiment. Adding infrastructure
does not move that question forward, and every additional layer increases the chance that
the eventual confirmatory execution is interpreted against a moving target.

Scientific progress in this cycle is measured by claims that survive a serious attempt at
falsification, not by commits, features, agents, adapters, schemas, tests or lines of code.

## Scope

The moratorium covers the whole repository. Development is frozen — not deleted — in:

- MG-EXP-V2 / V2.0-alpha;
- MG-EXP-V2.1 (Evidence Bridge);
- MG-EXP-V2.1-A (autonomous local repair loop);
- `external/` (adapters, collectors, incidents, replay, schemas);
- `theory/` (conjectures, toy models, lower-bound attempts, rho-crossover reasoning);
- `experiments/pooling/` (MG-EXP-POOLING-001);
- `experiments/real/` (MG-EXP-REAL-001);
- contextual, combinatorial and multicloud routing; causal bandits; SCM extensions;
- new graph topologies, provider integrations, dashboards, Kubernetes, distributed
  infrastructure, graph discovery, orchestration systems, agent frameworks;
- new benchmarks, experimental families, theoretical branches, or product features.

Existing work in those areas stays in the tree, keeps its tests, and keeps its documentation.
Nothing is removed.

## Allowed changes

Only changes strictly necessary for:

1. V1 protocol integrity;
2. V1 reproducibility;
3. V1 confirmatory execution;
4. V1 evidence validation;
5. V1 claim containment;
6. fixing contradictions or defects that could invalidate interpretation;
7. deterministic execution of already-frozen procedures;
8. generation of the confirmatory report;
9. scientific CI directly supporting the above.

Every change must answer yes to: *is this necessary to execute or defend the frozen
confirmatory experiment?*

## Forbidden changes

- new functionality in any frozen area listed under **Scope**;
- architectural cleanup, package redesign, framework replacement, large renames;
- premature optimisation, infrastructure migration, statistical-library replacement;
- any change to frozen scientific parameters: hypothesis, primary estimand, `rho=0.50`
  primary contrast, `N=97`, the `+0.10` non-inferiority margin, the seed population,
  method definitions, outcome definitions, censoring rules;
- promoting exploratory endpoints to confirmatory ones;
- weakening tests or skipping failures to obtain green CI;
- scope creep framed as "small improvement", "useful abstraction", "while we are here",
  "future-proofing", "cleanup", "easy win", or "useful for later".

## Exit condition

The moratorium ends when **either**:

- the V1 confirmatory result is executed under `CONFIRMATORY_FREEZE.json`, validated,
  reported inside its claim boundary, and published as one of
  `SUPPORTED` / `CONDITIONAL` / `INCONCLUSIVE` / `REFUTED`; **or**
- a legitimate `STOP` or `PROTOCOL_INVALID` outcome is documented in
  `CONFIRMATORY_STOP_REPORT.md`.

"Enough improvements were made" is explicitly **not** an exit condition.

## Exit record

**Met on 2026-09-15 (UTC) by the first branch of the exit condition.**

The frozen V1 confirmatory experiment was executed at commit
`5f314d2dfb15f508dfd4e630e8c0e49031e60c6a` on the 97 pre-selected paired scenarios, validated,
reported inside its claim boundary, and published with result state **`REFUTED`**: at ρ=0.50
hierarchical pooling recovered 42.1% slower than edge-only (95% CI +11.9% to +79.1%), and the ρ=0
non-inferiority safety gate failed. Evidence is sealed in
[`experiments/v1/artifacts/confirmatory/`](experiments/v1/artifacts/confirmatory/) and recorded in
`research/ledger/ledger.jsonl`.

The confirmatory question therefore reached a legitimate terminal state, and the broader research
programme may resume — selectively, and with the V1 refutation as its starting fact rather than as
a problem to route around. Concretely, the next question is no longer *does structural sharing
help?* but *when, if ever, does it help*, which requires its own protocol, power calculation, ρ
grid, multiplicity strategy, freeze, and seeds. Reusing V1 as a crossover study is not permitted.

Unfreezing any track requires stating, in that track's own protocol, what the V1 refutation implies
for it. In particular:

- V2.1-A evidence still may not be used to support any V1-style claim about hierarchical
  non-stationary routing.
- `theory/` statements about ρ* and hierarchical regret remain CONJECTURE / OPEN_PROBLEM; the
  refutation is one empirical data point in one environment, not a proof either way.
- `external/` still contains no external evidence.

## Paper A submission gate

The V1 confirmatory terminal state is satisfied. A separate gate now applies to
research expansion: **Paper A submitted**. Until an OpenReview receipt exists, do not
start V1.5 implementation, equalization productization, Paper B packaging, or
harness/benchmark work. Manuscript, diagnostics, reproduction, and anonymization
work remain in scope. See `paper/SUBMISSION.md`.

## Related artifacts

- [`CONFIRMATORY_READINESS_REPORT.md`](CONFIRMATORY_READINESS_REPORT.md) — audit and decision.
- [`CONFIRMATORY_RUNBOOK.md`](CONFIRMATORY_RUNBOOK.md) — the single canonical execution path.
- [`experiments/v1/EXPERIMENT_PROTOCOL_V1.md`](experiments/v1/EXPERIMENT_PROTOCOL_V1.md) — frozen rules.
- [`experiments/v1/ANALYSIS_PLAN.md`](experiments/v1/ANALYSIS_PLAN.md) — frozen statistics and multiplicity policy.
- [`experiments/v1/HYPOTHESIS_MATRIX.md`](experiments/v1/HYPOTHESIS_MATRIX.md) — hypothesis roles and permitted claims.
- [`experiments/v1/artifacts/CONFIRMATORY_FREEZE.json`](experiments/v1/artifacts/CONFIRMATORY_FREEZE.json) — execution contract.
