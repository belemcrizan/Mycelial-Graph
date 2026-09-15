# Reproducibility

## Exact commitments

The original V1 protocol, analysis plan, schema, configurations and ordered seed populations are preserved. Method selection/update rules, scenario generation probabilities, indexed outcomes, RNG namespaces, recovery definition, paired-bootstrap percentiles, primary rho=.50, NI rho=0/M=.10 and point-gain threshold .20 are unchanged.

`PROTOCOL_AMENDMENT_001.md` records enforcement/containment changes before the independent pilot. It does not turn development or pilot into confirmatory evidence.

## Commands

```sh
python -m pip install -e .
python -m unittest discover -s tests -v
python scripts/reproduce_v1.py --kind development --output outputs/reproduced-v1 --workers 2
python -m mycelial_graph verify-seal --output outputs/reproduced-v1
```

A pilot uses the same command with `--kind pilot` and a new output directory, after committing the source and recording any prior planning exposure. It runs all 20 prescribed seeds, all five rho values and all four frozen methods. Never use pilot/development data to replace a confirmatory population.

For a verified run, `sample-size` requires a complete pilot and reports an explicitly approximate planning estimate. Zero paired variance yields `unestimable`, with no chosen N. A point estimate is not a reviewed sample-size addendum.

## Identity and immutability

Each artifact stores code revision and SHA-256 of source bytes, canonical config hash, seed-file hash, protocol snapshots and hashes, Python/NumPy/SciPy/PyYAML versions, OS/CPU descriptors and execution mode. Source digest is freshly computed, including uncommitted source bytes; a commit SHA alone is not claimed to identify a dirty tree.

Canonical scientific comparisons exclude timestamps, CPU duration and trace path. Trace gzip headers omit timestamps and temporary filenames. Floating-point behavior across different BLAS/Python/NumPy implementations may still differ. Bitwise cross-platform identity is NOT YET VALIDATED.

A completed manifest is never rewritten on resume. Partial checkpoints need valid raw/trace checksums and the same execution identity. A single-writer lock protects the directory. After analysis/report, `seal-artifact` hashes every delivered file; verify it before using the artifact. Reanalysis belongs in a new versioned directory with its original source artifact/analysis revision documented.

The source/config/seed/protocol snapshots and a git commit are available; a maintained dependency lock, container digest, signed attestation and DOI are PLANNED. Do not invent them in metadata.

## Failure recovery

Failures are saved under `failures/` with scenario, method, exception and already completed methods. No fabricated recovery time or utility is assigned. Automatic inference and silent retry are blocked. Classify infrastructure vs method failure and record a numbered amendment/rerun decision. A hard-killed process can leave a lock: inspect the original process and evidence before an explicitly documented recovery. Never remove seeds according to outcomes.

## Claim ledger

`research/claims.json` maps claims to evidence levels. `research/experiment_ledger.jsonl` is populated only from verified sealed experiments via `python scripts/record_evidence.py --output <artifact>`. Entries are hash-linked and idempotent by seal. Retain git history/external anchors: hashes alone are not a signature.
