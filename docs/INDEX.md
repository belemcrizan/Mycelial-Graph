# Master Documentation Index

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Artifact class:** navigation layer (additive). Permitted-Now.
**Rule:** this index **adds** navigation over the existing document sprawl. Nothing is deleted,
merged-destructively, or archived-by-removal. Deduplication here means **cross-linking**, never
removal.

---

## 0. Single source of truth

| Kind | Canonical file | Notes |
|---|---|---|
| **Machine-readable state** | [`research/state.json`](../research/state.json) | authoritative; points to runtime, receipt, freeze |
| **Runtime metrics glossary** | [`research/runtime.json`](../research/runtime.json) | canonical decision-CPU vs replay vs wall-clock |
| **Ledger (append-only)** | [`research/ledger/ledger.jsonl`](../research/ledger/ledger.jsonl) | every unit of work |
| **Canonical result** | `REFUTED` (V1 confirmatory) | sealed; see below |

If any document disagrees with `research/state.json`, `state.json` wins and the other document
should get an additive correction note (never a silent overwrite).

## 1. Canonical scientific state (do not contradict)

- **V1 confirmatory: `REFUTED`.** At ρ=0.50, hierarchical recovered **+42.1% slower** than edge-only
  (95% CI +11.9% to +79.1%, n=97). ρ=0 safety gate also failed.
  → [`experiments/v1/artifacts/confirmatory/REPORT.md`](../experiments/v1/artifacts/confirmatory/REPORT.md),
  [`analysis.json`](../experiments/v1/artifacts/confirmatory/analysis.json)
- **EQ-B triage:** post-confirmatory attribution limit; does **not** alter `REFUTED`.
  → [`research/diagnostics/EQ_B_REPORT.md`](../research/diagnostics/EQ_B_REPORT.md),
  [`equalization.json`](../experiments/v1/artifacts/diagnostics/equalization.json)
- **Paper A (TMLR):** written, **not submitted** (OpenReview login is a human gate).
  → [`paper/tmlr/paper.tex`](../paper/tmlr/paper.tex)
- **Moratorium:** active until Paper A submitted + receipt recorded.
  → [`research/state.json`](../research/state.json)

## 2. Freeze & governance (immutable / gated)

| Topic | Files |
|---|---|
| Confirmatory freeze | [`CONFIRMATORY_FREEZE.json`](../experiments/v1/artifacts/CONFIRMATORY_FREEZE.json), [`..._SUPPLEMENT.json`](../experiments/v1/artifacts/CONFIRMATORY_FREEZE_SUPPLEMENT.json), [`FREEZE_CONTRACT.md`](../experiments/v1/FREEZE_CONTRACT.md) |
| Amendments (V1) | [`AMENDMENT_001`](../experiments/v1/AMENDMENT_001.md), [`002`](../experiments/v1/AMENDMENT_002.md), [`003`](../experiments/v1/AMENDMENT_003.md), [`PROTOCOL_AMENDMENT_001`](../experiments/v1/PROTOCOL_AMENDMENT_001.md) |
| Moratorium amendment (proposal) | [`experiments/PROTOCOL_AMENDMENT_002_PROPOSAL.md`](../experiments/PROTOCOL_AMENDMENT_002_PROPOSAL.md) |
| Master prompt / governance | [`research/MASTER_PROMPT.md`](../research/MASTER_PROMPT.md) |

## 3. Experiments

| Track | Entry points |
|---|---|
| V1 (confirmatory, `REFUTED`) | [`README`](../experiments/v1/README.md), [`EXPERIMENT_PROTOCOL_V1`](../experiments/v1/EXPERIMENT_PROTOCOL_V1.md), [`ANALYSIS_PLAN`](../experiments/v1/ANALYSIS_PLAN.md), [`HYPOTHESIS_MATRIX`](../experiments/v1/HYPOTHESIS_MATRIX.md), [`SAMPLE_SIZE_ADDENDUM`](../experiments/v1/SAMPLE_SIZE_ADDENDUM.md) |
| V1 — ρ=0 power (added) | [`POWER_ANALYSIS_RHO0.md`](../experiments/v1/POWER_ANALYSIS_RHO0.md) |
| V1.5 equalized re-run (frozen, added) | [`PROTOCOL_EQUALIZED_RERUN.md`](../experiments/v1_5/PROTOCOL_EQUALIZED_RERUN.md), [`config.equalized.yaml`](../experiments/v1_5/config.equalized.yaml) |
| V2 / V2.1 (frozen, moratorium) | [`v2/`](../experiments/v2/), [`v2_1/`](../experiments/v2_1/) |
| Pooling / Real (frozen) | [`pooling/`](../experiments/pooling/), [`real/`](../experiments/real/) |

## 4. External validation (infrastructure, not evidence)

| Topic | Files |
|---|---|
| Plan / pyramid | [`research/EXTERNAL_VALIDATION_PLAN.md`](../research/EXTERNAL_VALIDATION_PLAN.md) |
| Validity ladder (added) | [`docs/EXTERNAL_VALIDATION_LADDER.md`](EXTERNAL_VALIDATION_LADDER.md) |
| OPE pre-registration (frozen, added) | [`external/protocols/EXTERNAL_OPE_PREREG.md`](../external/protocols/EXTERNAL_OPE_PREREG.md) |
| Estimand bridge (added) | [`docs/ESTIMAND_BRIDGE.md`](ESTIMAND_BRIDGE.md) |
| Data sources / provenance / licenses | [`external/DATA_SOURCES.md`](../external/DATA_SOURCES.md), [`external/PROVENANCE.md`](../external/PROVENANCE.md), [`external/LICENSES.md`](../external/LICENSES.md) |

## 5. Paper A (TMLR)

[`paper/tmlr/paper.tex`](../paper/tmlr/paper.tex) ·
[`SUBMISSION_CHECKLIST.md`](../paper/SUBMISSION_CHECKLIST.md) ·
[`ANONYMIZATION.md`](../paper/ANONYMIZATION.md) ·
[`ZENODO.md`](../paper/ZENODO.md) ·
[`SUBMISSION_RECEIPT.json`](../paper/SUBMISSION_RECEIPT.json) (not yet submitted)

## 6. Claims & honesty

[`docs/claim_evidence_matrix.yaml`](claim_evidence_matrix.yaml) ·
[`docs/CLAIM_EVIDENCE_MATRIX.md`](CLAIM_EVIDENCE_MATRIX.md) ·
[`research/DO_NOT_CLAIM.md`](../research/DO_NOT_CLAIM.md) ·
[`research/LIMITATIONS.md`](../research/LIMITATIONS.md) ·
[`research/CLAIMS.md`](../research/CLAIMS.md) ·
[`research/RELATED_WORK.md`](../research/RELATED_WORK.md)

## 7. Reproducibility

[`scripts/reproduce_v1.py`](../scripts/reproduce_v1.py) ·
[`scripts/audit_v1_readiness.py`](../scripts/audit_v1_readiness.py) ·
[`CITATION.cff`](../CITATION.cff) ·
[`paper/zenodo_metadata.json`](../paper/zenodo_metadata.json) ·
[`research/runtime.json`](../research/runtime.json)

## 8. Process/evidence ratio — an honest note

This repository has a **high process-to-evidence ratio**: the volume of governance, protocol, freeze,
and audit documentation greatly exceeds the volume of confirmed scientific evidence (one synthetic
V1 confirmatory result, `REFUTED`, with a disclosed EQ-B attribution limit). This is **intentional
and disclosed**, not accidental sprawl: the project's value is its honesty and total preservation of
history. The heavy scaffolding exists so that the *next* increment of evidence (equalized re-run,
powered ρ=0 test, external OPE) can be added under gate control without ever subtracting history.

Readers wanting evidence should go to §1; readers wanting the *rules that constrain* the evidence
should go to §2.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
