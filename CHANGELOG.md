# Changelog

## 0.2.2 - 2026-08-31

- Replaced the V2.1 coding smoke known-fix shortcut (`apply_fix=True`) with an autonomous local agent loop: read, search, retrieve, reason, test, inspect, edit, verify, escalate, stop.
- Quality is now the executable grader on an isolated workspace copy. Oracle patches are evaluation metadata only and are never injected into the agent path.
- Action traces carry `action_id` and `context_id` hashes. This is still not a live coding-agent or SWE-bench result.

## 0.2.1 - 2026-08-31

- Added MG-EXP-V2.1 Evidence Bridge as an additive layer (VOC difference+ratio, counterfactual VOC bench, iso-model generator flag, budget curves, waste proxies, strong allocation baselines, local executable smoke tasks, claim audit).
- Left MG-EXP-V1 and MG-EXP-V2 (V2.0-alpha) protocols, confirmatory locks, and CLI meaning unchanged.
- Documented unimplemented alpha ablation aliases and a verified literature snapshot.

## 0.2.0 - 2026-08-31

- Added Mycelial Graph V2.0-alpha as an additive scientific layer (resource ledger, synthetic environment, resource controller, Pareto and quality non-inferiority reporting).
- Left MG-EXP-V1 configs, CLI, agents, and confirmatory lock unchanged.
- Added `mycelial-graph v2-*` commands and `experiments/v2/` with a separate confirmatory lock.
- Fixed git provenance decoding on Windows paths that are not cp1252-encodable (scientific payloads unchanged).

## 0.1.0 - 2026-08-24

- Reframed the core experiment as a non-stationary graph semi-bandit benchmark.
- Added immutable paired scenarios and indexed potential outcomes.
- Added node-only and hierarchical node-edge representations.
- Added structured sliding-window UCB with the same feature family.
- Added controlled shared-shock fraction with constant L2 magnitude.
- Added restricted recovery time, dynamic regret, paired bootstrap, and decision gates.
- Added atomic results, compressed traces, manifests, static figures, and reports.
- Added development, pilot, and confirmatory workflow with an execution lock.
- Added English documentation for technical and non-technical readers.

