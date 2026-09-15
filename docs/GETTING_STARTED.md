# Getting Started

This guide assumes no prior knowledge of bandits, survival analysis, or graph optimization.

## What the demonstration does

The program creates several synthetic AI execution graphs. For every graph, it creates a disruption after an initial stable period. Four routing methods then face exactly the same potential outcomes. Each method only observes the connections it actually uses.

The final report answers:

1. Did each method recover within the allowed horizon?
2. How long did it remain below the recovery target?
3. How much expected utility did it lose after the disruption?
4. Did the hierarchical representation appear helpful in this development run?

The last answer is diagnostic only. The frozen confirmatory experiment has been executed
and is `REFUTED`; do not read a demo as confirmatory evidence.

## Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock.txt
python -m pip install -e .
python -m unittest discover -s tests -v
python reproduce_confirmatory.py
mycelial-graph demo
```

## Windows PowerShell

Open the project folder in VS Code. Then select **Terminal > New Terminal** and run:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.lock.txt
python -m pip install -e .
python -m unittest discover -s tests -v
python reproduce_confirmatory.py
mycelial-graph demo
```

PowerShell does not use `source .venv/bin/activate`; that command is for Bash on Linux and macOS.

## Understanding the output

```text
outputs/demo/
├── raw/             one immutable paired result per seed and rho
├── processed/       analysis.json
├── traces/          compressed step-by-step decisions
├── figures/         static plots
├── manifest.json    file hashes and environment versions
└── REPORT.md        human-readable result
```

`rho` describes how much of the disruption is shared through a node:

- `rho = 0`: the disruption is edge-specific;
- `rho = 0.5`: node and edge-specific components contribute equally in squared magnitude;
- `rho = 1`: the disruption is fully node-shared.

## What “recovered” means

After the shock, the program compares the expected utility of the selected path with the expected utility of the oracle path. Recovery is recorded at the earliest point where:

1. the trailing-window average reaches at least 90% of the post-shock oracle utility; and
2. the condition remains satisfied for the frozen confirmation window.

If this never happens before the horizon, the trial is right-censored and restricted recovery time equals the horizon.

## Troubleshooting

### `not a git repository`

Run `git status` in the folder that actually contains `.git`. Activating `.venv` does not change or create a Git repository.

### PowerShell cannot activate `.venv`

Make sure the environment exists and include `& .\`:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\.venv\Scripts\Activate.ps1
```

### Confirmatory configuration fails validation

Before the pilot this was intentional: `experiments/v1/seeds.confirmatory.txt` was deliberately
absent so `config.confirmatory.yaml` could not run.

That lock has been released. The pilot completed, `SAMPLE_SIZE_ADDENDUM.md` fixed `N=97`, and the
seed file was created mechanically from the first 97 pool entries, so
`mycelial-graph validate --config experiments/v1/config.confirmatory.yaml` now passes. If it fails
today, the seed file is missing or modified relative to the hash bound in
`experiments/v1/artifacts/CONFIRMATORY_FREEZE.json`; run `python scripts/audit_v1_readiness.py`
to see which invariant broke. Do not regenerate the seed file to make validation pass.

