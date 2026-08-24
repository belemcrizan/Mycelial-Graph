# Results guide

## Files

`REPORT.md` is the readable narrative. `results.json` is the canonical analysis artifact. `frozen_config.yaml` is the exact configuration snapshot. `trials/*.json.gz` stores potential outcomes and an embedded digest.

## JSON shape

| Key | Meaning |
| --- | --- |
| `scope` | Graph size, seeds, steps, shock, and claim boundary |
| `trial_manifest` | Seed-to-digest mapping |
| `aggregate` | Method-level mean and approximate 95% confidence intervals |
| `runs` | One summary per method and seed |
| `trace_samples` | Four debug checkpoints for the first seed only |

## Interpretation rules

- Lower CPST, SRC, SER, decision time, and primitive operations are better, all else equal.
- Higher success, recovery probability, and utility are better.
- SRC means from recovered runs are conditional summaries. Always read them beside recovery probability and censored count.
- Approximate confidence intervals from 12 seeds are descriptive. They are not a substitute for the pre-registered H1-H3 analysis.
- A low routing time in this synthetic package says nothing about real network execution latency.
- The oracle is an unattainable descriptive reference and never receives a deployable-baseline label.

## Safe conclusion template

> In the V0 synthetic demonstration, method X had the lowest observed mean metric Y under the checked-in configuration. The run validates the software and reporting path but does not establish scientific or production superiority.

Avoid words such as “proves,” “guarantees,” “converges,” or “outperforms” until the relevant protocol is completed.

