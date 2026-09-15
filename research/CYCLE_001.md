# Cycle 001 — evidence integrity and independent planning

## A. Current State

V1 has a frozen synthetic paired protocol and four methods. V2 is a separate alpha. The audit began at commit 4966daf with 32 passing tests and no independent pilot or confirmatory artifact in the repository.

## B. Scientific Gap

The analysis could accept an incomplete or mislabeled cohort, and the confirmatory lock could be bypassed by creating a seed file. Exceptions were not retained. No reviewed sample size or complete failure estimand exists.

## C. Proposed Change

Enforce population/provenance checks across run/analyze/power/report, committed confirmatory freeze, immutable buffers/maps, stable trace compression, validated numeric contracts, persistent failure diagnostics, sealed outputs and an experiment ledger. Preserve all 118 prompt sections in a prioritized register. Execute the original pilot after committing code, subject to fail-closed checks.

## D. Why It Matters

Classifications: REPRODUCIBILITY, EXPERIMENTAL, STATISTICAL, ENGINEERING, DOCUMENTATION. These P0 fixes prevent a false inferential claim from incomplete, altered or misclassified data. They do not aim to improve MG's benchmark score.

## E. Files Affected

See `research/CYCLE_001_FILES.txt` for the exact changed/new file list, including code, tests, scientific records and produced evidence. Protected original experiment files are listed separately in V1_AUDIT.md.

## F. Compatibility Risk

V0/V2 algorithms are untouched. V1 algorithms, seeds, metrics and thresholds are preserved. Completed manifests are now immutable on resume; validation rejects previously accepted invalid inputs. Legacy artifacts without matching bytes cannot be analyzed as verified data. The demo default moves to `outputs/v1-development` to preserve the historical checked-in demo. Confirmatory execution now requires the documented committed freeze contract.

## G. Tests

Original suite plus meaningful corruption, missing-pair, duplicate-method, phase-leakage, exception-retention, false-promotion, stale-report, immutable-state, deterministic-compression, degenerate-power and CLI-exit regression cases. A baseline/current canonical comparison checks unchanged scientific behavior; scientific CI executes and seals a development artifact.

## H. Evidence Generated

Test execution, source regression checks, and the original independent pilot/planning artifact if it completes. Actual counts/outcomes are recorded in `research/VALIDATION.md` and the sealed evidence, not inferred from implemented capability.

## I. Evidence Not Generated

No universal superiority, confirmatory success, real provider/cloud behavior, validity phase transition, calibrated causal inference, regret/sample-complexity theorem, production readiness or independent external reproduction. The entire long-term roadmap is not implemented in this iteration.

## J. Next Gate

Review pilot information and power, and close any failure-estimand requirements. If a defensible N cannot be frozen, keep the original confirmatory seeds absent and publish the planning limitation. A changed measurement or design requires a numbered amendment with fresh planning data; never tune using confirmatory outcomes.
