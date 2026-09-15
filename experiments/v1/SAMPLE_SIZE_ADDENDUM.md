# Sample Size Addendum - MG-EXP-V1

Status: **RECORDED FROM PILOT (CONFIRMATORY NOT EXECUTED)**

Pilot completion date: 2026-09-15 (UTC)

Pilot experiment id: `MG-EXP-V1-PILOT`

Pilot artifact hashes (see `experiments/v1/artifacts/`):

- analysis.json SHA-256: `bdd4e85d256a59124e16400a8f499340349cbfa18c1f5fe8a80bb21930e05135`
- sample_size.json is copied to `experiments/v1/artifacts/sample_size.json`
- bind-run contract: `experiments/v1/artifacts/PILOT_EVIDENCE.json`

## Frozen rule (unchanged)

1. Estimate the paired variance of restricted recovery time from the 20 pilot seeds.
2. Determine the sample size required for 80% power at one-sided alpha 0.05 for the pre-specified 20% relative-effect design target.
3. Record the implementation, assumptions, software version, calculated N, and date below.
4. Create `seeds.confirmatory.txt` from the first N entries of `seeds.confirmatory.pool.txt`, without filtering or reordering.
5. Preserve this addendum in version control before any confirmatory result is observed.

## Completed from the pre-specified procedure

- Pilot completion date: 2026-09-15
- Pilot pairs: 20 at `primary_rho = 0.50`
- Control (edge-only) mean RRT: 41.2
- Absolute design effect (20% of control mean): 8.24
- Paired difference SD (hierarchical − edge-only RRT): 32.52140995195561
- Power method: normal approximation for a paired mean difference (`src/mycelial_graph/analysis/power.py`); one-sided alpha 0.05; target power 0.80
- Software: Python 3.13.3, numpy 2.5.3, scipy 1.18.1
- Required N: **97**
- Confirmatory seed range: first 97 pool entries, `700000`–`700096` inclusive, written to `seeds.confirmatory.txt` without filtering
- Simulation-based power supplement: **not performed**
- Confirmatory execution: **not performed**
- Method hyperparameters after pilot: **unchanged** (no tuning)

## Post-execution note (does not change N)

On 2026-09-15 the confirmatory experiment was executed on these 97 seeds and sealed
as `REFUTED`. This addendum's N, formula, and "no tuning" record remain the
historical sample-size decision. They are not rewritten from confirmatory variance.
A post-confirmatory diagnostic found the confirmatory paired-difference SD to be
$1.72\times$ the pilot SD; that diagnostic is not a license to change $N$ after the fact.

## Pilot diagnostics (not confirmatory; not a promotion)

These numbers are recorded so negative and inconclusive directions are not hidden. They must not be used to retune V1 or to claim a confirmatory effect.

- Primary rho=0.50 relative RRT (hierarchical vs edge-only): −10.2% (bootstrap interval includes large positive and negative values; statistical superiority gate false).
- Engineering-gain gate false; promote-to-v1 false.
- Non-inferiority at rho=0 false (one-sided upper bound 0.180 > margin 0.10).
- Exploratory group means: at rho=0.25 and 0.75, hierarchical mean RRT was **worse** than edge-only in this pilot. Structured SW-UCB beat hierarchical at several rho values. These contrasts are not the primary estimand.

## Deviations

None from the pre-specified sample-size formula. The optional simulation-based power review requested by `power.py` was not added; N=97 is therefore the formula output, not a post-hoc tuned N.
