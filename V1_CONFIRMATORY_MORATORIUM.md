# V1 Confirmatory Moratorium

**Start date:** 2026-09-14 (UTC-3)
**Start commit:** `acedef91559a81e2ff15606d3c13dd6a113be390`
**Protocol under moratorium:** `MG-EXP-V1`
**Status:** **ACTIVE** — confirmatory execution is complete (`REFUTED`); the moratorium remains
in force until Paper A is submitted.

```text
MORATORIUM EXIT CONDITION:
Paper A has been submitted and submission state/receipt has been recorded.
```

A completed confirmatory result alone does NOT unlock the broader program.
A compiled PDF, a draft OpenReview forum, or a README edit cannot disable this freeze.
Only `paper/SUBMISSION_RECEIPT.json` with `submitted: true` and a real submission ID may
set `paper_a.submitted = true`. Canonical machine-readable state is `research/state.json`.

## Scientific justification

The repository has accumulated substantially more research engineering than published
confirmatory evidence. The frozen V1 question has now been executed and classified
`REFUTED`, but Paper A has not been submitted. Expanding the programme before submission
would move the target that the manuscript is supposed to report.

Scientific progress in this cycle is measured by a submitted, claim-bounded report of the
frozen test, not by commits, features, agents, adapters, schemas, tests or lines of code.

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
- new benchmarks, experimental families, theoretical branches, or product features;
- V1.5 implementation, equalization-audit productization, Paper B packaging,
  open harness work, and repository splits of `external/` / V2.1 / V2.1-A.

Existing work in those areas stays in the tree, keeps its tests, and keeps its documentation.
Nothing is removed.

## Allowed changes

Only changes strictly necessary for:

1. V1 protocol integrity;
2. V1 reproducibility;
3. V1 evidence validation;
4. V1 claim containment and scientific-state consistency;
5. Paper A manuscript correctness, anonymization, and submission packaging;
6. fixing contradictions or defects that could invalidate interpretation;
7. deterministic execution of already-frozen procedures;
8. scientific CI directly supporting the above.

Every change must answer yes to: *is this necessary to submit or defend Paper A?*

## Forbidden changes

- new functionality in any frozen area listed under **Scope**;
- architectural cleanup, package redesign, framework replacement, large renames;
- premature optimisation, infrastructure migration, statistical-library replacement;
- any change to frozen scientific parameters: hypothesis, primary estimand, `rho=0.50`
  primary contrast, `N=97`, the `+0.10` non-inferiority margin, the seed population,
  method definitions, outcome definitions, censoring rules;
- promoting exploratory endpoints to confirmatory ones;
- overwriting `REFUTED` with an EQ-B reclassification;
- weakening tests or skipping failures to obtain green CI;
- scope creep framed as "small improvement", "useful abstraction", "while we are here",
  "future-proofing", "cleanup", "easy win", or "useful for later".

## Exit condition

The moratorium ends when and only when:

- Paper A has been submitted to TMLR/OpenReview; and
- `paper/SUBMISSION_RECEIPT.json` records venue, timestamp, submission ID, and artifact
  hashes; and
- `research/state.json` has `paper_a.submitted = true`.

The earlier confirmatory-result exit branch is **closed**. The confirmatory experiment
reaching `REFUTED` is recorded below as a completed scientific fact. It is not an unlock
key for V1.5, Paper B, equalization productization, or repository splits.

"Enough improvements were made" is explicitly **not** an exit condition.
"The paper is ready" and "the PDF compiles" are also **not** exit conditions.

## Confirmatory terminal-state record

**Recorded on 2026-09-15 (UTC).** This records the confirmatory outcome. It does not exit
the moratorium.

The frozen V1 confirmatory experiment was executed at commit
`5f314d2dfb15f508dfd4e630e8c0e49031e60c6a` on the 97 pre-selected paired scenarios, validated,
reported inside its claim boundary, and published in-repo with result state **`REFUTED`**: at
ρ=0.50 the fixed hierarchical routing update recovered 42.1% slower than the edge-only
comparator under the frozen V1 configuration (95% CI +11.9% to +79.1%), and the ρ=0
non-inferiority safety gate failed. Evidence is sealed in
[`experiments/v1/artifacts/confirmatory/`](experiments/v1/artifacts/confirmatory/) and recorded in
`research/ledger/ledger.jsonl`.

Post-confirmatory equalization triage classified the comparison as `EQ-B`. That limits
mechanistic attribution to hierarchical representation alone. It does not erase `REFUTED`
and it does not unlock this freeze.

## After legitimate submission

Only after the exit condition above is met may the programme resume — selectively, with the
V1 refutation as its starting fact rather than as a problem to route around. The first
permitted scientific implementation is then the equalization-audit *pre-freeze gate*, which
is a different object from the retrospective EQ-B triage. Concretely:

- V2.1-A evidence still may not be used to support any V1-style claim about hierarchical
  non-stationary routing.
- `theory/` statements about ρ* and hierarchical regret remain CONJECTURE / OPEN_PROBLEM; the
  refutation is one empirical data point in one environment, not a proof either way.
- `external/` still contains no external evidence.

See `paper/SUBMISSION.md` and `POST_SUBMISSION_PROPOSALS.md`.

## Related artifacts

- [`research/state.json`](research/state.json) — canonical scientific state.
- [`paper/SUBMISSION_RECEIPT.json`](paper/SUBMISSION_RECEIPT.json) — submission lock.
- [`CONFIRMATORY_READINESS_REPORT.md`](CONFIRMATORY_READINESS_REPORT.md) — audit and decision.
- [`CONFIRMATORY_RUNBOOK.md`](CONFIRMATORY_RUNBOOK.md) — the single canonical execution path.
- [`experiments/v1/EXPERIMENT_PROTOCOL_V1.md`](experiments/v1/EXPERIMENT_PROTOCOL_V1.md) — frozen rules.
- [`experiments/v1/ANALYSIS_PLAN.md`](experiments/v1/ANALYSIS_PLAN.md) — frozen statistics and multiplicity policy.
- [`experiments/v1/HYPOTHESIS_MATRIX.md`](experiments/v1/HYPOTHESIS_MATRIX.md) — hypothesis roles and permitted claims.
- [`experiments/v1/artifacts/CONFIRMATORY_FREEZE.json`](experiments/v1/artifacts/CONFIRMATORY_FREEZE.json) — execution contract.
