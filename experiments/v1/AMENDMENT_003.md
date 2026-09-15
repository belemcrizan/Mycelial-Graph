# Amendment 003 — Reproducibility and provenance correction

**Classification:** reproducibility/provenance correction with **no change** to the
scientific result or claim boundary.

**Date:** generated with the corrective audit recorded in
`experiments/v1/artifacts/confirmatory/CONFIRMATORY_REPRODUCTION_SUPPLEMENT.json`

**Does not change:** scientific question, estimands, methods, shock construction,
analysis-plan gates, mycelial hyperparameters, confirmatory N, seed population,
frozen confirmatory configuration, primary estimate, result classification, or
claim boundary.

**Does record:** the byte-representation discrepancy between historically sealed
CRLF text artifacts and the repository LF representation, the separation of
pre-execution confirmatory authorization from post-execution historical
reproduction, and cross-platform frozen-input identity for the confirmatory
seed file.

## What was discovered

1. **Seed EOL/materialization.** The frozen confirmatory seed identity SHA-256
   `8ef4c6b0dc481fea70054b6d7cbc9ecc2663f63b4523f3f55bb374a0339ee00c` is the
   CRLF-sealed representation of `seeds.confirmatory.txt`. Git stores the same
   seed list as LF (content SHA-256 `2198ac5f…`). LF → CRLF reconstructs the
   frozen digest exactly. Seed *values* parsed by `load_seeds` are unchanged.
   The frozen hash is not altered.
2. **Historical text-seal EOL.** `CONFIRMATORY_EVIDENCE.json` stores SHA-256 values
   that reconstruct exactly from the repository LF files by the deterministic map
   LF → CRLF for `REPORT.md`, `manifest.json`, and `processed/analysis.json`.
   PNG hashes already match because they are binary. The historical hashes were
   valid for the CRLF representation that was sealed. They were not “wrong hashes”.
3. **Freeze-validation contract drift.** The historical freeze at
   `experiments/v1/artifacts/CONFIRMATORY_FREEZE.json` does not use
   `schema_version=1` / `status=frozen`. The pre-execution gate looked next to
   the YAML for a modern freeze and, if pointed at the historical file, rejected
   it for schema drift. Historical reproduction is not a new confirmatory unlock.
4. **Misleading diagnostics.** A failed `validate_config` check could print
   `[FAIL] validate: ok`.

## What was not affected

Frozen inputs (N=97, seed list, confirmatory config hash), the parsed scientific
content of the sealed report/manifest/analysis, the primary estimate
`0.42112797022616655`, the result state `REFUTED`, and the claim boundary.

The defect affected byte-level provenance verification of text artifacts and
cross-platform materialization of frozen text inputs. It did not alter the parsed
scientific content, frozen inputs, primary estimate, result classification, or
claim boundary.

## What this amendment authorises

Infrastructure to:

- hash frozen text inputs as canonical LF while preserving the historical hash;
- verify historical text seals as `EXACT` or `HISTORICAL_EOL_EQUIVALENT`, and
  fail on any other mutation;
- keep the pre-execution authorization gate strict for *new* confirmatory runs;
- verify historical reproduction against the historical freeze schema and sealed
  evidence, without fabricating a modern freeze.

## What this amendment does not authorise

It does not authorise changing `REFUTED` to `ACCEPTED`, retuning, reseeding,
changing N, rewriting `CONFIRMATORY_EVIDENCE.json`, moving or mutating
`CONFIRMATORY_FREEZE.json`, or treating sealed-hash verification as independent
external reproduction.

The V1 confirmatory result remains **REFUTED**.
