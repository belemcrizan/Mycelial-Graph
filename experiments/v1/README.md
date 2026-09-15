# MG-EXP-V1 Execution Guide

## Files

- `EXPERIMENT_PROTOCOL_V1.md`: frozen scientific rules.
- `ANALYSIS_PLAN.md`: frozen statistical analysis.
- `experiment.schema.json`: raw paired-result contract.
- `config.development.yaml`: short executable demonstrator.
- `config.pilot.yaml`: independent 20-seed pilot.
- `config.confirmatory.yaml`: confirmatory YAML, bound by hash to the freeze contract.
- `seeds.confirmatory.pool.txt`: precommitted ordered seed pool (500 entries).
- `seeds.confirmatory.txt`: the frozen confirmatory population, first `N=97` unfiltered pool entries.
- `SAMPLE_SIZE_ADDENDUM.md`: post-pilot sample-size record (N=97 from the pre-specified formula).
- `HYPOTHESIS_MATRIX.md`: every contrast that can appear in a report, its role, and the claim it permits.
- `AMENDMENT_001.md`, `AMENDMENT_002.md`, `AMENDMENT_003.md`: dated amendments.
  002 is a pre-confirmatory-outcome reporting clarification. 003 is a
  reproducibility/provenance correction after execution (EOL seals, freeze-gate
  separation). Neither changes hypothesis, estimand, N, seed, method, primary
  estimate, or `REFUTED`.
- `artifacts/`: sealed pilot analysis/sample-size copies, the freeze contract, its additive
  hash supplement, and (after execution) the sealed confirmatory evidence.

Execution status lives in `../../CONFIRMATORY_READINESS_REPORT.md` and
`research/ledger/ledger.jsonl`, not in this file.

## Required order

1. Run unit tests and the development configuration.
2. Freeze code and method hyperparameters.
3. Run the pilot once.
4. Calculate N and complete the addendum.
5. Create `seeds.confirmatory.txt` from the first N pool entries.
6. Commit the addendum and seed list.
7. Run validation on `config.confirmatory.yaml` and `python scripts/audit_v1_readiness.py`.
8. Execute confirmatory scenarios with no tuning, following `../../CONFIRMATORY_RUNBOOK.md`.
9. Generate, seal, and archive the report.

Do not modify the original protocol after confirmatory data collection begins. Use a numbered amendment instead.

