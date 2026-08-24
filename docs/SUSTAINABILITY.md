# Sustainability

Mycelial Graph uses “sustainable” in four concrete senses.

## Scientific sustainability

- Claims are versioned separately from code releases.
- Development, pilot, and confirmatory seeds are disjoint.
- Raw results remain immutable.
- Protocol amendments preserve the original version and disclose timing.
- Negative and inconclusive outcomes have explicit decisions.

## Technical sustainability

- The core uses small, typed Python modules and standard file formats.
- No cloud, database, or workflow engine is required for V1.
- Immutable scenarios separate the environment from policy implementations.
- Provider adapters can be added later without rewriting analysis.
- A package version is not treated as a scientific protocol version.

## Financial sustainability

- Synthetic experiments run locally before paid cloud calls.
- A live POC starts with one cloud and strict budget limits.
- The principal product metric is cost per successful task, not token price alone.
- Additional infrastructure requires a measured bottleneck.

## Environmental sustainability

- The experiment reports decision CPU time and avoids redundant reruns through checkpoints.
- Sample size is justified rather than chosen by maximum available compute.
- Sensitivity sweeps remain post-confirmatory and bounded.
- Future live testing should report task volume, model usage, and available energy/carbon proxies without presenting uncertain estimates as exact measurements.

## Governance boundary

Cost or energy optimization never overrides hard safety, privacy, security, compliance, or human-approval constraints. Those belong to an execution boundary, not to a soft reward term.

