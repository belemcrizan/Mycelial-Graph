# V1 confirmatory reproduction report

Mode: **verification_or_reanalysis**
Reproduction level achieved: **analysis_recomputed_from_local_raw**
Wall-clock of this invocation: **0.380 seconds**
Process CPU of this invocation: **0.234 seconds**
Measured decision CPU-hours from confirmatory raw trials: **0.12155381944444445**
n_trials: **1940**
Failures: 0
Full re-execution requested: False

## Scientific result verification

Scientific result: **VERIFIED**
Historical result state: **REFUTED**
Primary estimate: **0.42112797022616655**

A verified REFUTED result is a valid scientific outcome. Verification is not acceptance.

## Frozen inputs

N: **97**
Seeds: frozen SHA-256 is the CRLF-sealed identity; Git blob is LF; values identical
Config: parsed semantic ``config_hash`` against the freeze

scientific_job_count = N × rho = 97 × 5 = **485**
method-level trials = jobs × methods = 485 × 4 = **1940**

## Artifact integrity

PNG artifacts: **EXACT**
- REPORT.md: EXACT
- manifest.json: EXACT
- processed/analysis.json: EXACT

Scientific-content mutation detected: **NO**

## Reproduction depth

Raw confirmatory trials available locally: **YES**
Analysis recomputed from raw trials: **YES**
Full re-execution performed: **NO**

Sealed-hash verification is not a full independent reproduction.
Reproduction status remains: internal / automated; no independent external reproduction.

## Provenance

- Historical evidence: `experiments/v1/artifacts/confirmatory/CONFIRMATORY_EVIDENCE.json` (immutable).
- Historical freeze: `experiments/v1/artifacts/CONFIRMATORY_FREEZE.json` (pre-execution schema; not `schema_version=1`).
- Freeze supplement: `experiments/v1/artifacts/CONFIRMATORY_FREEZE_SUPPLEMENT.json` (additive).
- Reproduction supplement: `experiments/v1/artifacts/confirmatory/CONFIRMATORY_REPRODUCTION_SUPPLEMENT.json`.
- Code revision at execution/seal: `5f314d2dfb15f508dfd4e630e8c0e49031e60c6a`.
- Historical text seals captured CRLF bytes; the repository stores LF. Byte representation changed; scientific textual content did not.

Default `python reproduce_confirmatory.py` is verification of sealed evidence.
`python reproduce_confirmatory.py --full` is canonical full re-execution from frozen inputs.
Hardware assumption: ordinary x86-64 CPU, no GPU, no network.
The sealed confirmatory execution used Python 3.13.3, numpy 2.2.6, scipy 1.15.3, PyYAML 6.0.2.
This invocation: Python 3.13.3, Windows-11-10.0.26200-SP0.

All verification checks passed at the reproduction level stated above.
The V1 confirmatory result remains **REFUTED**.
