# Power Analysis of the ρ=0 Non-Inferiority Safety Gate — MG-EXP-V1

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Artifact class:** post-confirmatory power diagnostic (additive). Permitted-Now.
**Status:** does **not** change N=97, the seeds, the sealed `REFUTED` result, or any frozen
threshold. It is a planning calculation *about* the sealed result, not a re-analysis of it.
**Inputs (sealed, read-only):** `experiments/v1/artifacts/confirmatory/analysis.json`,
`experiments/v1/SAMPLE_SIZE_ADDENDUM.md`.

---

## 1. Claim

**N=97 was sized to power the primary contrast at ρ=0.50 only. It does not power the ρ=0
non-inferiority safety gate.** As a consequence, the ρ=0 outcome should be read as
**"inconclusive as to non-inferiority (underpowered)"**, which is *not* the same as
"negative transfer proven at ρ=0."

This does not touch the primary result. The **primary** contrast is `REFUTED` on its own terms
(hierarchical +42.1% *slower* at ρ=0.50, interval +11.9% to +79.1%, entirely above zero); that
conclusion needs no ρ=0 evidence and is unaffected by anything here.

## 2. How N=97 was derived (from `SAMPLE_SIZE_ADDENDUM.md`)

- Target: 80% power at one-sided α=0.05 to detect a **20% relative** RRT effect at the **primary
  ρ=0.50** contrast.
- Pilot paired-difference SD (hier − edge RRT at ρ=0.50): 32.52; control mean RRT 41.2; absolute
  design effect 8.24.
- Normal-approximation paired power formula ⇒ **N=97**.

The formula's inputs are entirely the *ρ=0.50 superiority* design. The ρ=0 non-inferiority test
(H0: δ ≥ +0.10 vs H1: δ < +0.10) was **never** an input to the sample-size calculation. N=97 is
adequate for what it was designed for and silent about the safety gate.

## 3. Observed ρ=0 dispersion (sealed confirmatory, `analysis.json`)

| Quantity | Value |
|---|---|
| ρ=0 relative-difference estimate (hier vs edge) | +0.0152 |
| 95% interval | −0.137 to +0.197 |
| One-sided 95% upper bound | +0.163 |
| Frozen non-inferiority margin M | +0.10 |
| Gate result | **failed** — upper bound 0.163 > 0.10 (`NEGATIVE_TRANSFER_NOT_EXCLUDED`) |

Note the estimate itself (+1.5%) is *near zero* and the interval is wide and straddles zero. The
gate failed because the **interval is too wide to exclude a +0.10 excess**, i.e. an
imprecision/power problem — not because a large positive transfer penalty was estimated.

## 4. Illustrative power calculation (normal-theory, planning only)

From the sealed one-sided upper bound, the standard error of the ρ=0 relative-difference estimate
at N=97 is recovered as:

```
SE_97 = (upper_bound - estimate) / z_0.95
      = (0.163 - 0.0152) / 1.645
      ≈ 0.0898
```

The implied per-pair SD of the relative-difference statistic:

```
sd_pair = SE_97 * sqrt(97) ≈ 0.0898 * 9.849 ≈ 0.885
```

Required N to establish non-inferiority (one-sided α=0.05, power 0.80) when the **true** relative
difference is 0 and the margin is M=0.10:

```
N_req ≈ ((z_0.95 + z_0.80) * sd_pair / M)^2
      = ((1.645 + 0.842) * 0.885 / 0.10)^2
      = (2.487 * 8.85)^2 / 1
      ≈ (22.0)^2
      ≈ 4.8 × 10^2   →  on the order of ~450–490 paired scenarios
```

**Interpretation.** Establishing ρ=0 non-inferiority at the frozen +0.10 margin would need roughly
**~4.6–5.0× the N=97** used, assuming a true effect near zero and the observed dispersion. N=97 is
therefore **substantially underpowered** for the safety gate. All numbers here are approximate
normal-theory planning figures derived from the sealed dispersion; they are not a re-analysis and
do not alter any sealed statistic.

## 5. Textual downgrade (Permitted-Now, by ADDITION)

The following clarification is added — by annotation, not replacement — wherever the ρ=0 gate is
described (README, paper, reports):

> **ρ=0 safety gate — power annotation (added).** The frozen N=97 powers the ρ=0.50 primary
> contrast only. The ρ=0 non-inferiority gate is **underpowered** (≈4.6–5.0× N would be required to
> test the +0.10 margin at 80% power under the observed dispersion). The correct reading of the
> failed ρ=0 gate is therefore **"inconclusive as to non-inferiority (underpowered)"**, *not*
> "negative transfer at ρ=0 has been demonstrated." The prior phrasing "did not establish
> non-inferiority" is preserved above; this note refines, not replaces, it.

The original text (e.g. `NEGATIVE_TRANSFER_NOT_EXCLUDED`) is **kept verbatim**; this is a
contextualizing addition.

## 6. Staged remedy (frozen, NOT authorized)

A properly-sized ρ=0 safety test is pre-registered as a frozen, ready-to-authorize artifact:

- It reuses the frozen margin M=+0.10, the same estimand, the same paired-bootstrap machinery.
- Its N is set by the power procedure above (target 80% power at M=0.10), materialized before any
  seeds are drawn.
- It draws **new sealed seeds disjoint** from all existing V1 seed sets.
- It is folded into `experiments/v1_5/config.equalized.yaml` (the equalized re-run already carries
  the full ρ grid including ρ=0) and/or may be run as a standalone safety re-test.

**Gate:** running any properly-sized ρ=0 test is a **human authorization** (MASTER_PROMPT §5.3) and
requires the moratorium amendment (`experiments/PROTOCOL_AMENDMENT_002_PROPOSAL.md`). This document
prepares it and stops.

## 7. Honest status

- **Added:** this power diagnostic and the ρ=0 downgrade annotation.
- **Staged:** the properly-sized ρ=0 safety test (frozen, `authorized: false`).
- **Unchanged / preserved:** N=97, seeds, the sealed `REFUTED` primary result, the frozen margin,
  and all sealed artifacts. Nothing was recomputed from raw data or removed.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
