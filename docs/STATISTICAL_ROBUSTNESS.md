# Statistical Robustness & Multiplicity Plan

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Serves:** Master Prompt Part II §10 · Kernel gate: **GATE-SAFE** (analysis/plan documentation).

---

## 0. Scope

A statistical audit framework for the whole experimental program. It **describes** the rules; it does
not re-run or re-analyze any sealed experiment (INV-02). The sealed V1 analysis (paired bootstrap,
one-sided 95% bound, N=97) is referenced as-is.

## 1. Estimand & design assumptions (per experiment)

Each experiment declares: estimand, paired vs unpaired design, unit of analysis, seed independence,
repeated-measures handling, censoring rule, missing-data rule, and method-failure handling — all
**before** outcome inspection.

## 2. Multiplicity policy

- **One primary confirmatory contrast per experiment family.** Additional confirmatory claims within
  a family require a pre-registered **FWER** (e.g., Holm) or **FDR** (Benjamini–Hochberg) control
  strategy, declared in that experiment's analysis plan.
- Cross-experiment: each experiment carries its own error budget; results are not pooled into a
  single implicit family without an explicit correction plan.
- The ρ=0 safety gate is a pre-specified secondary gate that can only *restrict* a positive claim,
  never create one (consistent with V1 `AMENDMENT_002`).

## 3. Mandatory labels (§10, §P6)

Every reported quantity is labeled exactly one of: **confirmatory · secondary confirmatory ·
exploratory · diagnostic · descriptive**. Exploratory discoveries never silently become confirmatory
(INV-03/INV-06). Underpowered contrasts are labeled **UNDERPOWERED**, never "evidence of absence"
(INV-04).

## 4. Preferred reporting

Estimation + uncertainty over binary p-value storytelling: effect sizes, uncertainty intervals,
paired-difference distributions, robustness checks, sensitivity analyses (variance, effect
assumptions), and power curves. Bootstrap procedures are seeded and reproducible (tested per §19).

## 5. Interpretation trichotomy (safety / non-inferiority)

Always distinguish: (1) evidence of non-inferiority; (2) failure to establish non-inferiority
(possibly underpowered); (3) evidence of inferiority/harm. These are not interchangeable (§3, INV-04).
The V1 ρ=0 outcome is case (2), underpowered — see `experiments/v1/POWER_ANALYSIS_RHO0.md`.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
