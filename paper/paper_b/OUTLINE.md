# Paper B — Research Package Outline (PLACEHOLDERS ONLY; NO RESULTS)

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Serves:** Master Prompt Part II §12 · Kernel gate: **GATE-SAFE** (outline only).
**Hard rule:** Paper B **must not presuppose a positive answer** and contains **no invented
results**. Every results section is a placeholder pending an *executed, authorized* experiment.

---

## 0. Working question (open, not assumed)

> Under what conditions does structure-aware adaptive routing provide useful resource allocation or
> recovery behavior **once effective policy scale is controlled**?

A "no benefit" or "narrow-regime only" answer is an acceptable, publishable outcome (§25, INV-10).

## 1. Sections (with evidence status placeholders)

| # | Section | Depends on | Status |
|---|---|---|---|
| 1 | Motivation | — | draftable now |
| 2 | V1 falsification (`REFUTED`) | sealed V1 | citable now (immutable) |
| 3 | EQ-B identification problem | `research/diagnostics/EQ_B_REPORT.md` | citable now |
| 4 | V1.5 equalized protocol | `experiments/v1_5/` (frozen) | **STAGED** (needs GATE-H01) |
| 5 | Powered ρ=0 safety analysis | `experiments/v1/POWER_ANALYSIS_RHO0.md` | plan citable; run **STAGED** (GATE-H02) |
| 6 | Mechanistic ablations | `experiments/ablation/` | **STAGED** |
| 7 | Strong baselines | `docs/BASELINE_SUITE.md` | **STAGED** |
| 8 | Topology generalization | `experiments/generalization/TOPOLOGY_SUITE.md` | **STAGED** |
| 9 | Regime map | `experiments/generalization/REGIME_MAP.md` | **STAGED** |
| 10 | External validation | `external/protocols/EXTERNAL_OPE_PREREG.md` | **STAGED** (GATE-H03) |
| 11 | Scaling | `experiments/scaling/SCALING_PROTOCOL.md` | **STAGED** |
| 12 | Failure modes | `docs/FAILURE_TAXONOMY.md` | taxonomy now; instances STAGED |
| 13 | Limitations | — | draftable now |
| 14 | Reproducibility | `docs/REPLICATION.md` | draftable now |

## 2. Result placeholders

Each STAGED section ships with a `RESULTS: PENDING EXECUTION (GATE-Hxx)` marker and an empty results
table schema. No number enters a results table until the corresponding experiment is EXECUTED with
sealed artifacts (INV-06, §P6 EXECUTED).

## 3. Gate

No submission, no external release. Paper A must close first (§11, GATE-H05).

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
