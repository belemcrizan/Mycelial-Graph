# Quickstart and operations

## Install

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

## Run a short demonstration

```bash
mycelial-graph demo
```

This uses seed 101, saves the frozen trial, and writes `REPORT.md`, `results.json`, and `frozen_config.yaml` under `outputs/demo/`.

## Run the V0 evidence rehearsal

```bash
mycelial-graph experiment --output outputs/v0_results
```

The default configuration uses 12 seeds. This is an engineering rehearsal, not the minimum final scientific replication count.

## Freeze one trial separately

```bash
mycelial-graph freeze \
  --seed 101 \
  --output outputs/manual_trial_101.json.gz
```

The command prints the trial digest. A policy never reads the compressed file directly during a run; the runner controls which local observations are revealed.

## Change a configuration safely

Copy `configs/v0_demo.yaml`, change the copy, and pass it with `--config`. The validator rejects missing sections, duplicate components, invalid bounds, unknown shock targets, invalid hard-policy targets, and reward weights that do not sum to one.

Do not tune parameters using final evaluation seeds. A research run needs separate development and evaluation configurations with committed seed lists.

## Read an output

- Start with `REPORT.md`.
- Use `results.json` for analysis scripts.
- Match every seed to `trial_manifest[].digest`.
- Treat `sample_recovery_cost: null` as right-censored non-recovery, not as the horizon value.
- Use `trace_samples` only as a debug aid; it is not the full event log.

## Tests

```bash
python -m unittest discover -s tests -v
```

The suite checks configuration invariants, DAG shape, hard-policy filtering, fail-closed behavior, bounded conductance, traversed-edge-only feedback, separate timestamps, explicit fallback, deterministic trial generation, no pre-shock dependence on future shock severity, and report generation.

