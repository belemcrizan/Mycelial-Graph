# MG-EXP-V1 Confirmatory Runbook

This is the **only** supported path for executing the frozen V1 confirmatory experiment. There
are no alternative scripts, flags, or shortcuts. If a command here fails, stop and record the
failure; do not improvise around it.

Readiness decision: see [`CONFIRMATORY_READINESS_REPORT.md`](CONFIRMATORY_READINESS_REPORT.md).
Execution is permitted only while that report reads `GO`.

## Environment requirements

- Python 3.11 or 3.13 (the pilot and the first confirmatory execution used 3.13.3).
- The package installed in editable mode, which pulls PyYAML, numpy, scipy, and matplotlib.
- Git available on `PATH`, so `code_commit` records a real revision instead of a source-tree hash.
- No network access, API keys, providers, or credentials. The experiment is fully local and
  deterministic.
- Roughly 1.5 GB of free disk for `outputs/confirmatory/` (1940 compressed decision traces).

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

The executing environment's numpy, scipy, and PyYAML versions are recorded automatically in
`outputs/confirmatory/manifest.json`. Version drift relative to the pilot is acceptable only while
the readiness audit confirms that sealed pilot scenarios still regenerate to identical scientific
hashes; the audit checks this and reports it.

## Exact commands

Run them in this order, from the repository root.

```powershell
# 1. Readiness gate. Must print "GO"; exits non-zero otherwise.
python scripts/audit_v1_readiness.py

# 2. Confirm the frozen configuration validates.
mycelial-graph validate --config experiments/v1/config.confirmatory.yaml

# 3. Execute. 97 seeds x 5 rho values x 4 methods = 1940 trials in 485 paired scenarios.
mycelial-graph experiment --config experiments/v1/config.confirmatory.yaml --output outputs/confirmatory --workers 4

# 4. Frozen analysis: paired bootstrap, decision gate, integrity counters, result state.
mycelial-graph analyze --config experiments/v1/config.confirmatory.yaml --output outputs/confirmatory

# 5. Report generation. Fails closed if any sentence leaves the V1 claim boundary.
mycelial-graph report --config experiments/v1/config.confirmatory.yaml --output outputs/confirmatory

# 6. Claim audit: wording consistency plus machine-verifiable readiness invariants.
mycelial-graph claim-audit --matrix docs/claim_evidence_matrix.yaml

# 7. Bind hashes for the executed run.
mycelial-graph bind-run --config experiments/v1/config.confirmatory.yaml --output outputs/confirmatory --destination experiments/v1/artifacts/CONFIRMATORY_RUN_CONTRACT.json

# 8. Seal evidence into version control and append one ledger entry.
python scripts/seal_v1_confirmatory.py --output outputs/confirmatory
```

Do not pass `--workers` values that exceed the physical core count; serial and parallel execution
produce identical canonical payloads, so `--workers 1` is equally valid and only slower.

## Expected duration

Measured on the machine that ran the first confirmatory execution: about **1.3 seconds of wall
time per paired scenario** (four methods, 500 steps each) at `--workers 1`. 485 scenarios is
therefore roughly **11 minutes serial**, and proportionally less with parallel workers. Analysis
and report generation add well under a minute. These are measurements from one machine, not a
guarantee for other hardware.

## Expected outputs

```text
outputs/confirmatory/
  raw/rho-{0.00,0.25,0.50,0.75,1.00}/seed-7000NN.json   485 paired scenario payloads
  traces/*.jsonl.gz                                     1940 gzipped decision traces
  processed/analysis.json                               frozen analysis + result_state
  figures/recovery_by_rho.png, regret_by_rho.png        labelled EXPLORATORY across rho
  REPORT.md                                             claim-contained report
  manifest.json                                         per-file SHA-256 + environment
experiments/v1/artifacts/
  CONFIRMATORY_RUN_CONTRACT.json                        bound hashes for the executed run
  confirmatory/                                         sealed manifest, analysis, report, figures
research/ledger/ledger.jsonl                            one appended sealed entry
```

`outputs/` is git-ignored by design. Step 8 is what puts the evidence under version control.

## Checkpoint behaviour

Each paired scenario is written atomically to `raw/rho-<rho>/seed-<seed>.json`. On restart,
existing checkpoints are validated against the current code revision and config hash and skipped
if they match. If a checkpoint exists but was produced by a different revision or configuration,
the run **aborts** rather than overwriting scientific data. In that situation use a new output
directory; never delete or overwrite a completed canonical result.

## Interruption and resume

- Interrupting the run is safe. Rerun the identical command in step 3 to resume; completed
  scenarios are skipped.
- `manifest.json` records `scientific_job_count` (always 485) and
  `executed_job_count_this_invocation`, so a resumed run is visible in provenance.
- Do **not** inspect `processed/` or partial `raw/` results and then change seeds, `N`,
  hyperparameters, methods, censoring rules, estimands, tests, or report thresholds. That would
  void the confirmatory status of the run.
- If execution fails operationally, preserve the failure: keep the partial output directory, keep
  the logs, and record the failure, retries, reasons, environment, and timestamps. Do not rerun
  into a fresh directory until a clean dataset appears.

## Validation command

```powershell
python scripts/audit_v1_readiness.py
mycelial-graph claim-audit --matrix docs/claim_evidence_matrix.yaml
python -m pytest tests -q
```

The analysis itself enforces the frozen integrity rules: fewer than 97 primary pairs,
non-administrative censoring, or a method failure inside a frozen contrast all produce
`result_state = PROTOCOL_INVALID` rather than a primary interpretation.

## Reading the result

`processed/analysis.json` and `REPORT.md` carry exactly one of:

```text
SUPPORTED  CONDITIONAL  INCONCLUSIVE  REFUTED  PROTOCOL_INVALID
```

All five are legitimate terminal states. The mapping is fixed in
[`experiments/v1/HYPOTHESIS_MATRIX.md`](experiments/v1/HYPOTHESIS_MATRIX.md) and was pre-specified
in [`AMENDMENT_002.md`](experiments/v1/AMENDMENT_002.md) before any confirmatory outcome existed.
Nothing in the report may be restated as a crossover, all-rho, production, external-validity,
causal, or theoretical claim.
