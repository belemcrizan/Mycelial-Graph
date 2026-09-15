# MG-EXP-V1 Confirmatory Readiness Report

**Decision:** `GO`

**Generated:** 2026-09-15T02:54:49.113616Z  
**Command:** `python scripts/audit_v1_readiness.py`

This report is generated. Do not edit it by hand; rerun the audit.

## Repository state

- Commit: `acedef91559a81e2ff15606d3c13dd6a113be390`
- Branch: `feat/p0-v1-pilot-theory-external`
- Working tree dirty: True
- Python 3.13.3, numpy 2.2.6

## Frozen artifacts

| Artifact | Exists | SHA-256 |
|---|:-:|---|
| `experiments/v1/EXPERIMENT_PROTOCOL_V1.md` | True | `6137bd649870d317…` |
| `experiments/v1/ANALYSIS_PLAN.md` | True | `9e28c7b4a6a2a735…` |
| `experiments/v1/SAMPLE_SIZE_ADDENDUM.md` | True | `2031e4238f7d5480…` |
| `experiments/v1/AMENDMENT_001.md` | True | `6b9f431db2121d27…` |
| `experiments/v1/AMENDMENT_002.md` | True | `28ac77a90752c05f…` |
| `experiments/v1/HYPOTHESIS_MATRIX.md` | True | `7b684952f4828e78…` |
| `experiments/v1/config.confirmatory.yaml` | True | `3b2ce024eb2f7689…` |
| `experiments/v1/config.pilot.yaml` | True | `0623dcf8fc0a7a59…` |
| `experiments/v1/seeds.confirmatory.txt` | True | `8ef4c6b0dc481fea…` |
| `experiments/v1/seeds.confirmatory.pool.txt` | True | `a47e95c0c042843b…` |
| `experiments/v1/seeds.pilot.txt` | True | `3068ffef39ea5670…` |
| `experiments/v1/seeds.development.txt` | True | `64e087317ce70f2d…` |
| `experiments/v1/artifacts/CONFIRMATORY_FREEZE.json` | True | `7a176e64e004f244…` |
| `experiments/v1/artifacts/PILOT_EVIDENCE.json` | True | `94455ca327803d0e…` |
| `experiments/v1/artifacts/analysis.json` | True | `bdd4e85d256a5912…` |
| `experiments/v1/artifacts/sample_size.json` | True | `87ddf13e8f4531e0…` |
| `src/mycelial_graph/analysis/aggregate.py` | True | `2f4e38b7e10b7bfa…` |
| `src/mycelial_graph/analysis/bootstrap.py` | True | `044eb79fc4c98a63…` |
| `src/mycelial_graph/analysis/result_state.py` | True | `bc089ba8391d7857…` |
| `src/mycelial_graph/reporting/report.py` | True | `1399ccce0a204e43…` |
| `src/mycelial_graph/science/claim_guard.py` | True | `a95c81d242beae49…` |

Validation status: **OK**. Full hashes are in `CONFIRMATORY_READINESS_REPORT.json` and `experiments/v1/artifacts/CONFIRMATORY_FREEZE_SUPPLEMENT.json`.

## Seed audit

- Expected N: **97**, observed N: **97**
- Unique: True; ascending: True; range `700000`–`700096`
- Unfiltered prefix of the 500-entry precommitted pool: **True**
- Overlap with pilot seeds: `[]`; with development seeds: `[]`
- SHA-256 `8ef4c6b0dc481fea70054b6d7cbc9ecc2663f63b4523f3f55bb374a0339ee00c` matches the freeze: **True**
- Serialisation: CRLF, 776 bytes (the hash depends on line endings)
- Confirmatory config validation errors: `[]`
- Deterministic selection verified: **True**; cherry-picking detected: **False**

## Power audit

- Powered contrast: hierarchical vs edge_only at rho=0.50 on the relative difference in mean restricted recovery time (the frozen primary estimand)
- Variability source: paired SD from 20 pilot scenarios at rho=0.5
- Control mean RRT 41.2, relative design effect -0.2, absolute design effect 8.24
- Paired difference SD 32.52140995195561
- One-sided alpha 0.05, target power 0.8, direction: one-sided, H1: delta_RRT < 0
- Censoring assumption: administrative censoring at tau = post_shock_steps only
- Recorded N 97, recomputed N 97, freeze N 97 — reproduces: **True**
- Pilot and confirmatory share the design: `{'graph': True, 'horizon': True, 'environment': True, 'mycelial': True, 'structured_sw_ucb': True, 'analysis': True, 'methods': True}`
- Post-pilot method tuning declared: False

> N=97 provides the planned power for the primary contrast only. It does NOT imply adequate power for the rho=0 non-inferiority gate, for any other rho, or for estimating or establishing a crossover rho*.

## Hypothesis matrix

Enumerated in [`experiments/v1/HYPOTHESIS_MATRIX.md`](experiments/v1/HYPOTHESIS_MATRIX.md): one PRIMARY contrast (rho=0.50 hierarchical vs edge-only), one SAFETY GATE (rho=0 non-inferiority, margin +0.10), plus SECONDARY, EXPLORATORY, and DIAGNOSTIC rows that carry no error control.

## Multiplicity

- Policy already frozen: **True** (`ANALYSIS_PLAN.md` §5)
- Confirmatory family size: 1; adjustment required: False
- The confirmatory family contains exactly one superiority hypothesis (rho=0.50 hierarchical vs edge-only). The rho=0 contrast is a pre-specified safety gate that can only restrict, never create, a positive claim. No alpha split or step-down procedure is required, and none is introduced.

## Freeze audit

- Config hash matches: **True** (`5d7e92d2ec2805418f2b07e641188814282d544de55eb8c1461f4400b025452a`)
- Bound fields: `{'protocol_version': True, 'confirmatory_config_hash': True, 'seeds_file': True, 'seeds_sha256': True, 'required_confirmatory_pairs': True, 'sample_size_method': True, 'pilot_code_commit': True, 'post_pilot_method_tuning_declared': True, 'execution_status': True}`
- Not bound by the freeze: EXPERIMENT_PROTOCOL_V1.md content hash, ANALYSIS_PLAN.md content hash, analysis and reporting code hashes, bootstrap RNG seeds (hard-coded in analysis/bootstrap.py and analysis/aggregate.py)
- Amendments: AMENDMENT_001.md, AMENDMENT_002.md

## Reproducibility validation

- deterministic scenario generation: **True**
- shock l2 constant across rho: **True**
- certified distinct pre post optima: **True**
- paired rho family shares pre shock world: **True**
- distinct post shock world per rho: **True**
- oracle expected regret zero: **True**
- bootstrap rng frozen: **True**
- bootstrap reproducible: **True**
- seed population separation: **True**
- probe seeds: `[700000, 700048, 700096]`
- All reproducibility checks passed: **True**

## Provenance and environment drift

- Pilot environment: `{'numpy': '2.5.3', 'python': '3.13.3 (tags/v3.13.3:6280bb5, Apr  8 2025, 14:47:33) [MSC v.1943 64 bit (AMD64)]', 'pyyaml': '6.0.3', 'scipy': '1.18.1'}`
- Current environment: numpy 2.2.6, scipy 1.15.3, pyyaml 6.0.2
- Drift: `{'numpy': {'pilot': '2.5.3', 'current': '2.2.6'}, 'scipy': {'pilot': '1.18.1', 'current': '1.15.3'}, 'pyyaml': {'pilot': '6.0.3', 'current': '6.0.2'}}`
- Sealed pilot scenarios regenerated identically: **5/5**
- V1 simulator source unchanged since the pilot commit `2c0a9630ae97`: **True**

## Claim audit

- Wording consistency: ok=True, 12 claims
- V1 readiness invariants: ok=True, 25 checks across 8 invariants
- README machine-verifiable state: `{'states_seed_count_97': True, 'states_seed_hash': True, 'states_primary_rho': True, 'states_ni_margin': True, 'declares_cannot_establish_crossover': True, 'declares_no_independent_reproduction': True, 'single_seed_file_description': True, 'stale_missing_seed_file_statements': []}`

## Reporting and claim containment

- Result states: `['SUPPORTED', 'CONDITIONAL', 'INCONCLUSIVE', 'REFUTED', 'PROTOCOL_INVALID']`
- Claim guard patterns: `['V1-CROSSOVER-EXISTENCE', 'V1-CROSSOVER-LOCATION', 'V1-PHASE-TRANSITION', 'V1-RHO-GENERALISATION', 'V1-PRODUCTION', 'V1-EXTERNAL-VALIDITY', 'V1-CAUSAL', 'V1-THEORY', 'V1-INDEPENDENT-REPRODUCTION', 'V1-PILOT-PROMOTION']`
- Guard applied to the generated report: True
- Exploratory labelling present: True

## Historical artifact integrity

`{'artifact': 'outputs/demo', 'classification': 'historical artifact - preserved but not verified evidence', 'files_declared': 125, 'hash_mismatches': [], 'missing_files': [], 'regenerated': False}`

## Findings

| ID | Class | Finding | Action |
|---|:-:|---|---|
| `F-POWER-03` | **A** | Optional simulation-based power supplement was not performed | DOCUMENT: record as a limitation of the power calculation. |
| `F-POWER-04` | **A** | The rho=0 safety gate is not separately power-analysed | DOCUMENT: state the limitation in the report and hypothesis matrix. |
| `F-FREEZE-02` | **B** | The freeze binds configuration and seeds but not protocol text or analysis code | AMEND/DOCUMENT: record the additional hashes in CONFIRMATORY_FREEZE_SUPPLEMENT.json before execution, leaving the original freeze contract untouched. |
| `F-MULT-02` | **A** | Multiplicity control was already frozen and is left unchanged | DOCUMENT: no amendment to the multiplicity policy is required. |
| `F-REPORT-02` | **B** | Report generator required claim containment, role labels, and a result-state taxonomy | AMEND/DOCUMENT: recorded in AMENDMENT_002.md before confirmatory execution. |
| `F-PROV-03` | **A** | Software environment differs from the one recorded for the pilot | DOCUMENT: record the executing environment in the confirmatory manifest. |
| `F-CLAIM-03` | **A** | README seed-file contradiction resolved | DOCUMENT: verified mechanically by invariant I01. |

### Detail

**`F-POWER-03` (Class A) — Optional simulation-based power supplement was not performed**

power.py requests an optional simulation-based check before locking N. It was not run, so N=97 is the pre-specified formula output rather than a simulation-verified value. The formula was the pre-specified procedure, so this changes nothing about what was promised.

**`F-POWER-04` (Class A) — The rho=0 safety gate is not separately power-analysed**

ANALYSIS_PLAN.md section 7 powers the design for the primary contrast only. The rho=0 non-inferiority gate was pre-specified with a +0.10 margin but no power target. A gate failure is therefore interpretable, while a gate pass carries unquantified type-II risk. This was frozen before the pilot and must not be repaired by changing N.

**`F-FREEZE-02` (Class B) — The freeze binds configuration and seeds but not protocol text or analysis code**

CONFIRMATORY_FREEZE.json binds the confirmatory config hash, the seed file and its hash, N, the protocol version, and the pilot code commit. It does not bind the hash of EXPERIMENT_PROTOCOL_V1.md, ANALYSIS_PLAN.md, or the analysis/reporting code, so those could in principle change without invalidating the freeze. Closing this gap adds evidence only: it changes no hypothesis, estimand, sample size, seed, or method.

**`F-MULT-02` (Class A) — Multiplicity control was already frozen and is left unchanged**

ANALYSIS_PLAN.md section 5 already designates one primary contrast, one safety gate, and everything else as secondary/exploratory. The enumeration in HYPOTHESIS_MATRIX.md restates that policy without replacing it.

**`F-REPORT-02` (Class B) — Report generator required claim containment, role labels, and a result-state taxonomy**

Before this cycle the report emitted a binary promotion verdict, unlabelled rho curves, and no containment check, so exploratory rho evidence could read as confirmatory and the frozen interpretation matrix had no machine-readable outcome. The added result states, role labels, and claim guard are deterministic functions of already-frozen quantities and change no hypothesis, estimand, threshold, or sample.

**`F-PROV-03` (Class A) — Software environment differs from the one recorded for the pilot**

The pilot manifest records {"numpy": {"pilot": "2.5.3", "current": "2.2.6"}, "scipy": {"pilot": "1.18.1", "current": "1.15.3"}, "pyyaml": {"pilot": "6.0.3", "current": "6.0.2"}}. All 5 sampled sealed pilot scenarios regenerate to identical scientific hashes in the current environment, so the frozen RNG streams, scenario construction, and potential-outcome tables are unaffected by the version difference. The confirmatory manifest records the actual versions used.

**`F-CLAIM-03` (Class A) — README seed-file contradiction resolved**

The README previously asserted that seeds.confirmatory.txt exists with the first 97 pool entries, while docs/GETTING_STARTED.md and docs/V2_IMPLEMENTATION_PLAN.md still described it as deliberately missing. The file exists, contains exactly 97 unique seeds equal to the unfiltered pool prefix, and its SHA-256 matches the freeze. The documentation now carries one internally consistent description of that state.

## Decision

### `GO`

No Class C findings. 5 Class A finding(s) documented and 2 Class B finding(s) resolved transparently before confirmatory execution. The frozen seed selection, sample size, configuration binding, multiplicity policy, and reproducibility invariants all reproduce mechanically.

**Next permitted action:** EXECUTE V1 CONFIRMATORY (see CONFIRMATORY_RUNBOOK.md)
