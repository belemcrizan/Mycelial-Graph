# MG-EXP-V2 Execution Guide

V2 is independent of MG-EXP-V1. Do not mix seeds, outputs, or claims.

## Files

- `EXPERIMENT_PROTOCOL_V2.md`
- `ANALYSIS_PLAN_V2.md`
- `SAMPLE_SIZE_ADDENDUM_V2.md` (pending pilot)
- `config.development.yaml` / `config.pilot.yaml` / `config.confirmatory.yaml`
- Confirmatory seeds file is **absent** until the addendum records N.

## Order

1. Unit tests including V1.
2. `mycelial-graph v2-validate --config experiments/v2/config.development.yaml`
3. `mycelial-graph v2-demo`
4. Pilot (later), then addendum, then confirmatory.

Development plots are not confirmatory evidence.
