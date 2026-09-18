# MG-EXP-V1.5 — Equalized Re-Run Protocol (FROZEN, NOT AUTHORIZED)

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Protocol id:** `MG-EXP-V1_5-EQUALIZED`
**Status:** `frozen` · `authorized: false` — pre-registered, ready-to-authorize, **incapable of
running until a human flips `authorized` to `true`** and the moratorium amendment is in force.
**Depends on human gates:** MASTER_PROMPT §5.2 (authorize equalized re-run) and §5.5
(moratorium amendment `experiments/PROTOCOL_AMENDMENT_002_PROPOSAL.md`).
**Motivating diagnostic:** `research/diagnostics/EQ_B_REPORT.md`,
`experiments/v1/artifacts/diagnostics/equalization.json`.

---

## 0. Interdict and scope

This protocol prepares a **new** experiment. It does not touch, reopen, or reinterpret the sealed
V1 confirmatory result.

- The V1 `REFUTED` outcome is **sealed and final**. This re-run does **not** replace it, and its
  future result — whatever it is — cannot overwrite or requalify V1's `REFUTED`.
- The purpose is **completing the confirmatory science** (isolating representation from effective
  policy scale), not expanding the program. It is V1 closure, not V2.

## 1. Scientific question

Does hierarchical node-edge pooling reduce restricted recovery time (RRT) relative to edge-only
adaptation at ρ=0.50, **when the two arms are matched on effective policy scale** (not merely on
nominal hyperparameters)?

This directly addresses the EQ-B attribution limit: the V1 arms shared nominal parameters but
differed in realized policy sharpness (path-entropy fraction 0.63 vs 0.97; selected-score std ratio
12.08). V1.5 asks the same comparative question with that confound controlled.

## 2. Estimand (identical to V1)

`delta_RRT = (E[RRT_hier] - E[RRT_edge]) / E[RRT_edge]` at ρ=0.50, estimated by paired bootstrap,
one-sided 95% upper bound. Same definition, same transformation (none), same confidence level.

## 3. Equalization design (the only substantive addition vs V1)

Arms are paired on **effective** policy scale using pre-registered target bands, measured from
**re-instrumented full candidate-score traces** (not selected-edge-only traces; see EQ-B §5):

| Effective-scale target | Band | Rationale |
|---|---|---|
| Realized path-entropy fraction of max | matched within ±0.05 across arms | closes the 0.341 V1 gap |
| Selected-score dispersion (std), normalized | ratio ≤ 2.0 (the EQ tolerance) | closes the 12.08× V1 ratio |
| Exploration-step rate | matched within ±0.05 | already satisfied in V1 (0.003), preserved |
| Local feedback contract | identical (traversed-edge rewards only) | unchanged from V1 |

Equalization is achieved by **calibrating the temperature / score-scaling of each arm to hit the
matched effective-scale bands**, calibrated on **development seeds only**, then frozen. No
per-confirmatory-seed tuning. The calibration procedure, its acceptance bands, and the resulting
frozen scaling constants are bound into `config.equalized.yaml` before any confirmatory seed runs.

## 4. Gates (identical to V1, re-used unchanged)

- Superiority at ρ=0.50: one-sided α=0.05, engineering threshold −0.20.
- ρ=0 non-inferiority safety gate: margin +0.10 (see also the properly-powered variant in
  `experiments/v1/POWER_ANALYSIS_RHO0.md`).
- Same result-state taxonomy (`SUPPORTED` / `CONDITIONAL` / `INCONCLUSIVE` / `REFUTED` /
  `PROTOCOL_INVALID`) from `HYPOTHESIS_MATRIX.md`.

## 5. Sample size

To be fixed **before** execution by the same frozen power procedure as V1
(`src/mycelial_graph/analysis/power.py`), estimated from a V1.5 **equalized pilot** on development
seeds. It is **not** copied from V1's N=97, because the equalized arms may have different paired
variance. The N and its derivation must be written into a `SAMPLE_SIZE_ADDENDUM` before confirmatory
seeds are drawn. Placeholder in config: `sample_size_n: null` (must be filled pre-execution).

## 6. Seeds (new, sealed, non-overlapping)

- New confirmatory pool `seeds.equalized.pool.txt` drawn mechanically, **disjoint** from
  `seeds.confirmatory.txt`, `seeds.pilot.txt`, and `seeds.development.txt`.
- Confirmatory seeds = first N pool entries, no filtering, no reordering, SHA-256 recorded in the
  freeze supplement before execution.
- Until authorized, **no seed file is generated**; this protocol only specifies the rule.

## 7. Freeze-ready metadata (enforced by schema)

`config.equalized.yaml` carries `schema_version`, `status: frozen`, `authorized: false`. Any runner
must refuse to execute while `authorized == false`. Flipping the flag is a human action recorded in
the ledger.

## 8. What this protocol does NOT authorize

- Running anything. Drawing seeds. Choosing N from V1 variance.
- Any change to the sealed V1 confirmatory artifacts.
- Treating a future V1.5 result as retroactively editing V1's `REFUTED`.
- Any paid call or real-data collection (this is synthetic-simulator only).

## 9. Definition of ready-to-authorize (met by this artifact)

1. Nothing deleted; V1 freeze and moratorium intact.
2. Estimand, gates, and taxonomy identical to V1 and cross-linked.
3. Equalization bands defined operationally and tied to `equalization.json` gaps.
4. Config is frozen and cannot self-run.
5. Ledger entry recorded on addition.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
