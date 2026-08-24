# MG-EXP-V1 Execution Guide

## Files

- `EXPERIMENT_PROTOCOL_V1.md`: frozen scientific rules.
- `ANALYSIS_PLAN.md`: frozen statistical analysis.
- `experiment.schema.json`: raw paired-result contract.
- `config.development.yaml`: short executable demonstrator.
- `config.pilot.yaml`: independent 20-seed pilot.
- `config.confirmatory.yaml`: locked until sample size is known.
- `seeds.confirmatory.pool.txt`: precommitted ordered seed pool.
- `SAMPLE_SIZE_ADDENDUM.md`: post-pilot sample-size record.

## Required order

1. Run unit tests and the development configuration.
2. Freeze code and method hyperparameters.
3. Run the pilot once.
4. Calculate N and complete the addendum.
5. Create `seeds.confirmatory.txt` from the first N pool entries.
6. Commit the addendum and seed list.
7. Run validation on `config.confirmatory.yaml`.
8. Execute confirmatory scenarios with no tuning.
9. Generate and archive the report.

Do not modify the original protocol after confirmatory data collection begins. Use a numbered amendment instead.

