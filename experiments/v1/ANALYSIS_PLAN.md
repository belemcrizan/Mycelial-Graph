# Analysis Plan - MG-EXP-V1

## 1. Analysis populations

Development, pilot, and confirmatory runs are separate populations. The primary result uses only confirmatory scenarios selected before execution.

All methods must be linked through the same `scenario_id`. A scenario with infrastructure corruption is excluded as a complete pair and rerun under the logged infrastructure rule. A method failure remains in the paired record.

## 2. Primary data transformation

For each method and scenario:

```text
RRT = recovery_time if recovered else tau
```

With administrative censoring only at `tau`, the group mean of RRT estimates restricted mean time without recovery. Lower values are better.

At `rho=0.50`, calculate:

```text
delta = (mean(RRT_hierarchical) - mean(RRT_edge_only)) / mean(RRT_edge_only)
```

## 3. Paired bootstrap

1. Keep each hierarchical/edge-only scenario pair together.
2. Resample scenario indices with replacement.
3. Calculate `delta` for every resample.
4. Use the frozen number of bootstrap samples and percentile confidence interval.
5. Calculate the frozen one-sided upper confidence bound.
6. Report the bootstrap mass at or above the null only as a descriptive tail probability, not as an exact p-value.

The implementation uses a frozen bootstrap RNG seed that is unrelated to trial seeds.

## 4. Non-inferiority

At `rho=0`, use the same paired procedure with null margin `+0.10`. Non-inferiority passes when the one-sided upper confidence bound is below the margin. This test protects against negative transfer in the pure edge-specific regime.

## 5. Multiplicity

The only primary confirmatory contrast is hierarchical versus edge-only at `rho=0.50`. The `rho=0` non-inferiority contrast is the pre-specified secondary safety gate. Other rho values, node-only comparisons, SW-UCB comparisons, dynamic regret, and ablations are secondary or exploratory unless an amendment establishes a separate controlled family before confirmatory outcomes are inspected.

No uncorrected exploratory result may be described as confirmatory.

## 6. Censoring and survival displays

- Report recovery probability at `tau`.
- Plot Kaplan-Meier curves descriptively when the reporting dependency is available.
- Do not use Cox regression by default.
- If non-administrative censoring appears, suspend the primary automated conclusion and document an amendment.

## 7. Power calculation

The pilot estimates paired variability for the design target `delta=-0.20`, one-sided alpha 0.05, and power 0.80. The calculation and assumptions are written to `SAMPLE_SIZE_ADDENDUM.md`. The effect threshold is not changed using pilot results.

If required `N` exceeds the 500-seed precommitted pool, the confirmatory run remains locked until a transparent amendment extends the pool without using method outcomes to choose seeds.

## 8. Sanity checks

- every scenario has unique pre/post optima with the configured margin;
- shock L2 norm equals the configured magnitude within numeric tolerance;
- all paired records share scenario, config, protocol, and code identifiers;
- Oracle expected regret is zero by construction;
- realized rewards may occasionally exceed oracle realized reward and are not used to reject a valid scenario;
- serial and parallel canonical payloads agree;
- no confirmatory seed overlaps development or pilot seeds.

## 9. Reporting requirements

Report:

- sample count and recovery count per method and rho;
- mean RRT/RMST estimate;
- relative effect, two-sided confidence interval, one-sided upper bound, and descriptive bootstrap tail probability;
- non-inferiority result;
- dynamic regret and final expected utility;
- decision-time distribution or at least mean and p95;
- all method failures, timeouts, infrastructure reruns, and amendments;
- full decision gate, including failed requirements;
- explicit run status: development, pilot, or confirmatory.

## 10. Interpretation boundary

A non-significant result is inconclusive unless the design has adequate power to exclude the pre-specified relevant effect. A development or pilot pass never promotes the method. A positive confirmatory result applies only to the graph, observation contract, shock construction, and parameter ranges tested.
