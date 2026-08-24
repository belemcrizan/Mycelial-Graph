# Alignment with the frozen specification

This document maps the August 2026 manuscript, *Mycelial Graph: Local Adaptation and Structural Reuse in Dynamic AI Execution Graphs*, to V0 code. It prevents the biological story, engineering POC, and scientific claim from drifting apart.

## Direct implementation map

| Frozen specification | V0 implementation | Status |
| --- | --- | --- |
| Typed layered execution DAG | `graph.LayeredGraph` and YAML layers | Implemented |
| Per-edge bounded conductance | `MycelialRouter.conductance` | Implemented |
| Lazy temporal decay | `MycelialRouter._apply_decay` | Implemented |
| Separate last-decay, last-use, last-feedback time | Three router state maps | Implemented and tested |
| Local reward from quality, latency, cost, failure, load | `trial.local_reward` | Implemented |
| Temperature-controlled local softmax | `routing._weighted_choice` and `MycelialRouter.select` | Implemented |
| Explicit basal exploration | `explicit-exploration` decision mode | Implemented and logged |
| Single-edge fallback | `single-edge-fallback` decision mode | Implemented and tested |
| Traversed-edge-only feedback update | `MycelialRouter.observe` | Implemented and tested |
| Hard safety/policy constraints outside rewards | `graph.HardPolicy` | Minimal V0 boundary implemented |
| Immutable paired trials | `trial.FrozenTrial` | Implemented, compressed, hashed |
| Unique pre/post optima with a margin | `trial.certify_trial` | Implemented for the V0 scenario |
| Shared edge fraction | Trial certification metadata | Implemented for one realized value |
| SRC with censoring | `experiment.run_router` | Implemented with rolling sustained recovery |
| CPST | Run summary and report | Implemented |
| SER external classifier | Frozen rule in experiment runner | Implemented for V0 |
| Decision/adaptation accounting | Wall time and primitive operations | Implemented |
| H3 trial-level model and survival analysis | Scientific V1 analysis | Deferred |
| Required decay/exploration ablations | Scientific V1 suite | Deferred |
| Depth/branching stress matrix | Scientific V1 suite | Deferred |
| Live cloud adapters | Single-cloud POC phase | Deferred |

## Deliberate V0 choices

The POC uses five scored layers with equal path length. Common utility is the mean of frozen edge-local utilities, so the end-to-end ranking is aligned with the factorized local feedback. Task success and CPST remain global: total cost, total latency, quality threshold, and realized failures.

Recovery uses a rolling 10-task mean rather than requiring every stochastic selection in a 10-task block to satisfy the threshold individually. Explicit exploration may therefore occur inside a stable window without automatically resetting recovery.

The two bundled baselines are transparent reference comparators. They exercise the fairness and reporting chain but are not claimed to satisfy the final paper's strong-baseline burden without independent review and expanded testing.

## Claims preserved

The V0 claim is limited to executable behavior, invariants, and reproducible descriptive observations. It does not claim empirical superiority, convergence, regret bounds, production readiness, biological fidelity, H1 support, H2 support, or H3 support.

## Features explicitly excluded

No reinforcement learning, graph neural network, predictive failure model, federated learning, live provider integration, automatic architecture recommendation, or multi-cloud execution is hidden behind an unused interface. Future capabilities remain documentation-only until the evidence gates are passed.
