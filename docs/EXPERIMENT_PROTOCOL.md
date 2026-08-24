# Experimental protocol

## V0 purpose

The included experiment is a protocol rehearsal. It verifies the software and measurement chain under one graph, one abrupt sparse shock, and a small replication set. It does not test H1, H2, or H3 completely.

## Frozen trial

For a seed `s`, a trial contains the graph, shock schedule, noise, and every edge-level potential outcome across time. It is serialized before comparison and identified by SHA-256. A trial is identical across methods, while observation access remains path-restricted.

## Common utility

All methods are judged using one fixed-length-path utility: the mean of the normalized local edge utilities for quality, latency, cost, failure, and load. This additive factorization keeps the common objective aligned with local feedback. End-to-end success and CPST still use total latency, total cost, the task quality threshold, and any realized component failure. The same frozen utility identifies the descriptive oracle and evaluates routed paths; routers do not receive the oracle or future utility.

## Shock

At `shock_step`, only the configured component changes. V0 simultaneously changes that component's quality, latency, cost, reliability, and load to make the initial behavior visible. The scientific H1 suite must separate shock dimensions and severity levels rather than relying on this combined demonstration.

## Metrics

### Sample Recovery Cost

Recovery requires the rolling mean selected-path expected utility over `recovery_window` consecutive tasks to be within `recovery_tolerance` of the rolling oracle mean. This avoids defining a stochastic router as unrecovered merely because one exploratory task occurs inside an otherwise stable window. SRC counts scored local edge-feedback observations from the shock through the end of the first qualifying sustained window.

A run that never meets the window is right-censored. Its SRC is `null`; the post-shock horizon is not substituted as if it were an observed recovery time.

### Cost per Successful Task

```text
CPST = total simulated path cost / number of successful tasks
```

A task succeeds only if it has no realized component failure, reaches the minimum average quality, and remains inside the latency SLA.

### Structural Re-exploration Rate

The frozen V0 classifier counts a post-shock scored observation when its edge:

1. is not incident on the shocked component; and
2. is not part of the post-shock oracle path.

SER is that count divided by all scored post-shock edge observations. Internal `explore` labels are diagnostic and are not used as the classifier.

### Computational accounting

Routing wall time, p95 routing wall time, and primitive edge/path evaluations are reported separately from simulated service latency.

## Full hypothesis gates

### H1 - sparse-shock recovery

Use single-component shocks with separate severity and noise strata. Compare recovery probability, censoring-aware SRC, CPST, SER, and decision cost. Require material effects and uncertainty intervals; a p-value alone is insufficient.

### H2 - scaling and non-stationarity

Vary depth, branching factor, and non-stationarity while keeping perturbations sparse relative to graph size. Do not claim scaling from the current 48-path graph.

### H3 - structural reuse

Generate pre- and post-shock optima with target shared fractions, then analyze realized shared fraction continuously at trial level. Verify that both optima are unique under one utility and exceed the runner-up by a frozen minimum margin. Use a censoring-aware time-to-event model when non-recovery is material.

## Required ablations

1. conductance without temporal decay;
2. conductance with decay but without basal exploration;
3. conductance with exploration but without decay;
4. full V1 dynamics.

## Final-evaluation discipline

- Tune only on development seeds.
- Freeze configuration, generator, seed partitions, trial assertions, baselines, classifier, and analysis code.
- Use 50 or more independent evaluation replications when computation is cheap.
- Report all excluded invalid trials and the exact reason for exclusion.
- Preserve censored observations.
- Do not promote a V0 descriptive table into a paper claim.
