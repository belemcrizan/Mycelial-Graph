# Analysis Plan - MG-EXP-V2

## Populations

Development, pilot, and confirmatory are separate. Primary analysis uses only confirmatory pairs, once unlocked.

## Estimands

Let `Q` be mean post-shock expected quality. For treatment `v2_mycelial` and control `always_high_compute`:

```text
ΔQ = mean(Q_treatment) - mean(Q_control)
```

Paired by `scenario_id`.

Tokens `T` are ledger totals including router tokens. Conditional estimand after quality non-inferiority:

```text
ΔT = mean(T_treatment) - mean(T_control)
```

Negative ΔT favors treatment (fewer tokens).

## Bootstrap

Paired resample of scenarios. Frozen bootstrap seed unrelated to trial seeds. Percentile intervals. Quality non-inferiority uses the one-sided **lower** bound versus `-ε`. Token reduction uses one-sided **upper** bound on ΔT versus 0 as a descriptive conditional test.

Do not treat bootstrap tail mass as an exact p-value.

## Pareto

A method's mean vector `(Q, -T, -C, -L)` is non-dominated if no other method is at least as good in all coordinates and strictly better in one. Report the non-dominated set. Do not collapse to success/tokens alone.

## Ablations

Exploratory unless a future amendment promotes a family. Compare full controller vs no-pruning, no-transfer, no-cord, no-cost-awareness.

## Decision labels

| Label | Rule (confirmatory only is decisive) |
|---|---|
| PASS | Quality NI holds and ΔT upper bound < 0 |
| CONDITIONAL | Quality NI holds but token reduction is mixed across regimes or ablations |
| INCONCLUSIVE | Intervals include both material harm and benefit |
| REFUTED | Quality lower bound ≤ -ε in the primary regime, or treatment dominated on quality and resources |

Development runs must print that they are non-confirmatory regardless of numbers.

## Multiplicity

Only the primary quality NI contrast is confirmatory. Everything else is secondary or exploratory until amended.
