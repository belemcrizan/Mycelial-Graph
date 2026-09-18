# QUALITY_LEAP_REPORT.md

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Scope:** Hardened Master Prompt (Part I Enforcement Kernel + Part II §0–§25).
**Posture:** additive-only; falsification-first; nothing deleted; `REFUTED`, freeze, and moratorium
intact. Every consequential item is classified EXECUTED / STAGED / BLOCKED / HUMAN_GATE.

---

## A. Executive summary

This leap added the *evidence-program scaffolding* the repository was missing and locked the
canonical scientific state behind a new regression test — **without executing any gated experiment
and without touching a single sealed artifact.** New protocols for V1.5 equalization, the powered
ρ=0 safety test, external OPE, mechanistic ablations, strong baselines, topology/regime
generalization, and scaling are now frozen and ready-to-authorize. A Paper B outline (no invented
results) and an independent-replication guide were added. All work is additive (INV-07).

## B. Historical state (immutable — INV-01/INV-02)

- V1 confirmatory: **`REFUTED`**. ρ=0.50 hierarchical **+42.1%** slower (95% CI +11.9%..+79.1%,
  N=97). ρ=0 non-inferiority **not** established.
- EQ-B effective-policy-scale mismatch present (attribution limit, not anulment).
- Paper A written, **not submitted**. Moratorium **active**.
- Verified unchanged by `tests/test_canonical_state_invariants.py` (6/6 pass) and existing
  `tests/test_scientific_state.py`.

## C. Evidence added (actually executed)

- **Scientific-invariant tests** (`tests/test_canonical_state_invariants.py`) — EXECUTED, 6/6 pass.
  This is engineering/verification evidence (§15), not a new empirical result.
- No new *empirical* evidence was produced: every experiment is gated (see D). Producing empirical
  evidence now would require crossing a human gate or the moratorium (INV forbids).

## D. Evidence staged (prepared, NOT executed)

| Artifact | Serves | Gate |
|---|---|---|
| `experiments/v1_5/PROTOCOL_EQUALIZED_RERUN.md` + `config.equalized.yaml` | §2 V1.5 | GATE-H01 |
| `experiments/v1/POWER_ANALYSIS_RHO0.md` (powered ρ=0 test) | §3 | GATE-H02 |
| `external/protocols/EXTERNAL_OPE_PREREG.md` | §4 | GATE-H03 |
| `experiments/ablation/PROTOCOL_ABLATION.md` | §5 | authorization + moratorium |
| `docs/BASELINE_SUITE.md` | §6 | authorization |
| `experiments/generalization/TOPOLOGY_SUITE.md` | §7 | authorization |
| `experiments/generalization/REGIME_MAP.md` | §8 | authorization |
| `experiments/scaling/SCALING_PROTOCOL.md` | §9 | authorization / GATE-H04 |
| `experiments/PROTOCOL_AMENDMENT_002_PROPOSAL.md` | §21 moratorium | GATE-H07 |

## E. V1.5 status

**STAGED / HUMAN_GATE (GATE-H01).** Protocol + config frozen (`authorized: false`); equalizes on
*effective* policy scale (matched path-entropy fraction, selected-score std ratio ≤ 2.0),
re-instrumented full candidate traces, new disjoint seeds, N derived from an equalized pilot
(not copied from 97). Ready to authorize; cannot self-run.

## F. ρ=0 powered test status

**STAGED / HUMAN_GATE (GATE-H02).** `POWER_ANALYSIS_RHO0.md` derives ~450–490 pairs at α=0.05,
power 0.80 from the sealed dispersion; frozen margin +0.10 unchanged (GATE-H08 to change it). Final N
must be fixed prospectively before outcomes are seen.

## G. External validation

**Infrastructure only → STAGED (GATE-H03).** Prereg + validity ladder + estimand bridge added;
source→sub-claim→limit table fixed. No real data ingested, no paid call (INV-05). Layers labeled
real / semi-synthetic / synthetic / planned.

## H. Ablation status

**STAGED.** Ablation matrix specified with real mechanistic interventions (no rename-ablations,
INV-03). Not executed.

## I. Baselines

**STAGED.** Strong-baseline suite with matched-budget fairness protocol specified; reuses existing
`baselines_strong.py`. Not executed.

## J. Generalization

**STAGED.** Topology suite (11 topologies + descriptors) and regime map (12+3 regimes,
improves/unresolved/degrades rule) specified. Not executed.

## K. Scaling

**STAGED.** Scaling protocol separating scientific compute / replay overhead / wall-clock (per
`runtime.json` glossary). No proved complexity bound (INV-05). Not executed.

## L. Paper A

**HUMAN_GATE (GATE-H05).** Written, not submitted; OpenReview login is the boundary. Readiness
artifacts already exist (`paper/SUBMISSION_CHECKLIST.md`, `ANONYMIZATION.md`). Submission not claimed.

## M. Paper B

**STAGED.** `paper/paper_b/OUTLINE.md` with placeholders only, no invented results; every results
section marked pending an executed, authorized experiment.

## N. Replication

`docs/REPLICATION.md` added: clean clone→install→test→reproduce→verify-seal workflow, pinned deps,
seed hash, expected `REFUTED` result, divergence detection. DOI/Zenodo minting is GATE-H06 (not done).

## O. Scientific limitations (no marketing language)

- Only one *synthetic* confirmatory result exists, and it is negative (`REFUTED`).
- EQ-B limits mechanistic attribution; V1 isolates *implemented methods*, not representation alone.
- ρ=0 is underpowered → "failure to establish non-inferiority", not "proof of harm".
- No external, real-data, ablation, baseline, topology, regime, or scaling *evidence* exists yet —
  only prepared protocols. Infrastructure is not evidence.

## P. Remaining blockers

Every non-executed workstream is blocked by either a human authorization gate (GATE-H01..H10) or the
active moratorium (GATE-H07). The CI-enforced claim matrix blocks in-place status extension → handled
via a separate `docs/claim_evidence_matrix.additions.yaml` pending validator support.

## Q. Next human decisions (only genuine ones)

1. Approve/reject the moratorium amendment proposal (GATE-H07) — enables V1-closure runs.
2. Authorize V1.5 (GATE-H01), powered ρ=0 (GATE-H02), external OPE (GATE-H03) individually.
3. Submit Paper A to OpenReview (GATE-H05).
4. Extend the `claim-audit` validator to accept the proposed statuses, then merge the additions file.

---

## §24 — Definition-of-Done checklist

| Workstream | State |
|---|---|
| V1.5 equalized study | HUMAN_GATE (GATE-H01) |
| Powered ρ=0 safety study | HUMAN_GATE (GATE-H02) |
| External validation | HUMAN_GATE (GATE-H03) |
| Mechanistic ablations | STAGED |
| Strong baselines | STAGED |
| Topology generalization | STAGED |
| Regime generalization | STAGED |
| Scaling | STAGED |
| Statistical robustness | STAGED (plan added; per-experiment application pending) |
| Paper A | HUMAN_GATE (GATE-H05) |
| Paper B package | STAGED |
| Independent replication | STAGED (guide EXECUTED; DOI HUMAN_GATE GATE-H06) |
| Claim/evidence matrix | STAGED (additions file added; merge pending validator) |
| Scientific CI invariants | EXECUTED (new test passes) |
| Artifact sealing | UNTOUCHED (existing seals preserved) |
| Failure analysis | STAGED (taxonomy EXECUTED; instances pending experiments) |
| Process-to-evidence improvement | ADVANCED via scaffolding; true reduction requires executed evidence (§16) |

No workstream dropped. No staged item labeled "done".

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
