# Amendment 002 — Pre-confirmatory-outcome reporting and integrity clarification

**Type:** pre-confirmatory-outcome amendment. Pilot data **had already been observed** when this
amendment was written, so it is *not* a pre-data amendment and is not described as one.

**Date:** 2026-09-14 (UTC-3)
**Parent commit:** `acedef91559a81e2ff15606d3c13dd6a113be390`
**Branch:** `feat/p0-v1-pilot-theory-external`
**Author:** Crizan Belem Ribeiro (repository maintainer), prepared during the V1 confirmatory
convergence cycle with an AI coding assistant.
**Confirmatory outcomes observed at the time of writing:** **none.** `CONFIRMATORY_FREEZE.json`
recorded `confirmatory_executed: false`, no confirmatory raw scenario existed under
`outputs/`, and no confirmatory analysis had been produced.

## 1. What was already frozen

Frozen on 2026-08-24 in `EXPERIMENT_PROTOCOL_V1.md` and `ANALYSIS_PLAN.md`, before the pilot:

- the scientific question and the primary estimand
  `delta_RRT = (E[RRT_hier] - E[RRT_edge]) / E[RRT_edge]` at `rho=0.50` (protocol §7.3);
- `H0: delta_RRT >= 0` vs `H1: delta_RRT < 0`, paired bootstrap, one-sided 95% upper bound
  (protocol §8.1);
- the engineering promotion gate, including the `-0.20` point-estimate threshold (protocol §8.2);
- the `rho=0` non-inferiority safety gate with margin `M=+0.10` (protocol §8.3);
- the interpretation matrix mapping outcomes to scientific readings (protocol §8.4);
- the multiplicity policy: exactly one primary confirmatory contrast, the `rho=0` gate as the
  pre-specified secondary safety gate, everything else secondary or exploratory
  (`ANALYSIS_PLAN.md` §5);
- censoring, survival display, and suspension rules (`ANALYSIS_PLAN.md` §6);
- the sample-size procedure (`ANALYSIS_PLAN.md` §7), completed as `N=97` in
  `SAMPLE_SIZE_ADDENDUM.md` and Amendment 001;
- the confirmatory seed selection rule and the seed and configuration hashes bound in
  `CONFIRMATORY_FREEZE.json`.

**None of the above is changed by this amendment.**

## 2. What was absent or ambiguous

1. **No machine-readable result state.** Protocol §8.4 defines an interpretation matrix in prose,
   but the analysis emitted only a boolean `promote_to_v1`. A binary verdict cannot express
   `INCONCLUSIVE`, `REFUTED`, or `PROTOCOL_INVALID`, so any real outcome risked being narrated
   as a pass/fail.
2. **Automated gate scope was unstated.** Protocol §8.2 lists four requirements; the code
   evaluated three and never mentioned the fourth (operational cost budget), for which no budget
   value is frozen. A report could therefore print "promotion gate PASSED" while a frozen
   requirement had not been evaluated at all.
3. **No exploratory labelling.** The report listed all five rho values and all four methods in one
   undifferentiated table and plotted RRT across the whole rho grid with no label, so exploratory
   evidence could be read as confirmatory and a crossover could be eyeballed off a figure.
4. **No report-level claim containment.** Nothing prevented generated text from asserting a
   crossover, production readiness, causal mechanism, external generalisation, or independent
   reproduction.
5. **Integrity counters were not surfaced.** `ANALYSIS_PLAN.md` §6 suspends the automated primary
   conclusion when non-administrative censoring appears, but no artifact reported whether that
   condition held.
6. **The freeze bound configuration and seeds, but not protocol text or analysis code.**

## 3. Pilot information already available

The full pilot analysis was available and is recorded in `SAMPLE_SIZE_ADDENDUM.md` and
`experiments/v1/artifacts/analysis.json`: primary point estimate −10.2% with a one-sided upper
bound above zero, `rho=0` non-inferiority failing at an upper bound of 0.180 against the 0.10
margin, and hierarchical worse than edge-only at `rho=0.25` and `rho=0.75`.

This is stated explicitly because the direction of the pilot matters for judging opportunism: the
pilot was **unfavourable** to the hierarchical hypothesis. The clarifications below were not
selected to make a positive result more likely. Two of them (the `REFUTED`/`INCONCLUSIVE` states
and the automated-gate-scope disclosure) make a negative or partial outcome *harder* to narrate
as success, and none of them changes any threshold, statistic, or sample.

## 4. Why the clarification was necessary before execution

Claim containment must exist before the evidence exists. Retrofitting a result-state taxonomy or
an exploratory label after seeing a confirmatory outcome would allow the framing to be chosen to
fit the number. Writing it now, with the confirmatory result unobserved, fixes the framing in
advance.

## 5. The clarifications

### 5.1 Result-state taxonomy (deterministic, no new statistic)

Implemented in `src/mycelial_graph/analysis/result_state.py` and tabulated in
`HYPOTHESIS_MATRIX.md`. `U` is the frozen one-sided 95% upper bound, `L` the lower end of the
frozen two-sided 95% interval, `E` the point estimate, `g = 0.20` the frozen engineering
threshold, `M = 0.10` the frozen non-inferiority margin.

| State | Condition | Already-frozen source |
| --- | --- | --- |
| `PROTOCOL_INVALID` | non-administrative censoring, or a method failure inside a frozen contrast, or fewer executed pairs than `N=97` | `ANALYSIS_PLAN.md` §6, §8; protocol §9 |
| `SUPPORTED` | `U_primary < 0` and `E_primary <= -g` and `U_safety < M` | protocol §8.2 requirements 1–3 |
| `CONDITIONAL` | `U_primary < 0` and the engineering threshold or the safety gate fails | protocol §8.4 rows 2–3 |
| `REFUTED` | `U_primary >= 0` and `L_primary > -g` | protocol §8.4 rows 4, 6; `ANALYSIS_PLAN.md` §10 |
| `INCONCLUSIVE` | `U_primary >= 0` and `L_primary <= -g` | protocol §8.4 row 5; `ANALYSIS_PLAN.md` §10 |

Every input is a quantity the protocol already froze. No threshold is introduced, moved, or
reinterpreted, and the states partition the outcome space exhaustively and exclusively.

### 5.2 Automated gate scope disclosed

`promote_to_v1` continues to evaluate exactly protocol §8.2 requirements 1–3, unchanged. The
analysis and the report now state that requirement 4 (operational cost budget) is not automated
because no budget is frozen, so product promotion additionally requires a separate operational
decision. This narrows what the report may be read to assert.

### 5.3 Role labels and exploratory containment

Every group-metric row carries a role label (`CONFIRMATORY INPUT`, `SECONDARY`, `EXPLORATORY`,
`DIAGNOSTIC`) derived from `ANALYSIS_PLAN.md` §5 and protocol §4. Every multi-rho figure carries
"EXPLORATORY across rho — not powered to establish a crossover". No row is added or removed.

### 5.4 Report-level claim guard

`src/mycelial_graph/science/claim_guard.py` refuses to write a V1 report that asserts a crossover,
a rho* location, a phase transition, all-rho or universal superiority, production readiness, real
provider/real-world validity, causal mechanism, a theorem or guarantee, independent reproduction,
or the promotion of pilot evidence to confirmatory evidence. Documented limitations remain
sayable, because negated segments are exempt.

### 5.5 Integrity counters reported

The analysis reports non-administrative censoring counts, method failures inside frozen contrasts,
and the executed pair count, so the `ANALYSIS_PLAN.md` §6 suspension condition is visible rather
than implicit.

### 5.6 Additive freeze supplement

`experiments/v1/artifacts/CONFIRMATORY_FREEZE_SUPPLEMENT.json` records hashes of the protocol,
analysis plan, addendum, amendments, hypothesis matrix, seed files, configs, sealed pilot
artifacts, and the analysis/reporting/guard source, plus the frozen bootstrap RNG seeds. The
original `CONFIRMATORY_FREEZE.json` is **not modified**. The supplement adds evidence only; it
relaxes nothing.

## 6. Why this does not alter the scientific question

The question is still whether hierarchical node-edge pooling reduces restricted recovery time
relative to edge-only adaptation at `rho=0.50` without negative transfer beyond `+0.10` at
`rho=0`. Every change above concerns how an outcome is *labelled and contained*, not what is
measured or how it is tested.

## 7. Why this does not alter the estimand

`delta_RRT` is computed by the same code path with the same paired bootstrap, the same frozen RNG
seeds (`20260824` primary, `20260825` non-inferiority), the same `10000` resamples, and the same
`0.95` confidence level. No transformation, winsorisation, or reweighting is introduced.

## 8. Why this does not change N

`N=97` is untouched. The frozen pair count is now *enforced*: a confirmatory analysis with fewer
than 97 primary pairs is classified `PROTOCOL_INVALID` instead of being silently reported.

## 9. Why this does not alter the seed population

`seeds.confirmatory.txt` is byte-identical, SHA-256
`8ef4c6b0dc481fea70054b6d7cbc9ecc2663f63b4523f3f55bb374a0339ee00c`, still the unfiltered first 97
entries of `seeds.confirmatory.pool.txt`, still disjoint from pilot and development seeds.

## 10. Effect on error control

None. The confirmatory family still contains exactly one superiority hypothesis at `rho=0.50` at
one-sided alpha 0.05, plus the pre-specified `rho=0` safety gate, which can only restrict a
positive claim and never create one. No alpha is split, no additional hypothesis is promoted into
the confirmatory family, and no exploratory endpoint gains error control. The result-state map is
a relabelling of a single decision, not an additional test.

## 11. Before / after

| Aspect | Before | After |
| --- | --- | --- |
| Outcome vocabulary | `promote_to_v1: true/false` | `SUPPORTED` / `CONDITIONAL` / `INCONCLUSIVE` / `REFUTED` / `PROTOCOL_INVALID` plus the unchanged boolean |
| Gate reporting | "The promotion gate is PASSED/NOT PASSED" | same booleans, plus the explicit statement that only requirements 1–3 are automated |
| Group metrics | one undifferentiated table | identical numbers with role labels |
| Multi-rho figures | unlabelled | labelled "EXPLORATORY across rho — not powered to establish a crossover" |
| Out-of-boundary language | unconstrained | report generation fails on assertive out-of-boundary claims |
| Integrity | validated but not reported | censoring and failure counters reported; frozen pair count enforced |
| Freeze bindings | config hash, seed hash, N, protocol version, pilot commit | same, plus an additive supplement hashing protocol text, analysis plan, and analysis/reporting code |

## 12. What this amendment does not authorise

It does not authorise changing the hypothesis, the estimand, `rho=0.50`, `N=97`, the `+0.10`
margin, the seeds, the methods, the outcome definitions, or the censoring rules; promoting any
exploratory endpoint; using pilot outcomes to choose thresholds; or treating the pilot as
confirmatory. It does not make any analysis newly confirmatory.

## 13. Classification

Class **B** — pre-confirmatory clarification. Resolved transparently before execution; does not
block confirmatory execution. See `CONFIRMATORY_READINESS_REPORT.md`.
