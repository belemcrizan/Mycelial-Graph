# Architecture

## Design goal

V1 must answer one scientific question without becoming a premature cloud platform:

> Under which shared-shock regimes does hierarchical node-edge state reduce recovery burden relative to independent edge state, without unacceptable negative transfer?

## Boundaries

```text
Frozen YAML + seed list
          |
          v
Immutable Scenario Generator
  - DAG topology
  - latent edge means
  - node/interaction shock
  - indexed potential outcomes
  - certified pre/post optima
          |
          +-------------------------------+
          |               |               |
      Edge-only       Node-only      Hierarchical      Structured SW-UCB
          |               |               |                    |
          +---------------+---------------+--------------------+
                                  |
                         Paired raw trial records
                                  |
                         Frozen paired analysis
                                  |
                       Markdown report + figures
```

## Why scenarios are immutable

Running two agents sequentially against one mutable environment is not a paired experiment. The first method could consume RNG state or mutate time. V1 instead creates a scenario containing indexed potential outcomes. If two methods traverse the same edge at the same step, they receive the same realized local reward. Different actions query different outcomes from the same frozen world.

## Randomness isolation

Stable SHA-256 namespaces derive independent seeds for:

- scenario parameters;
- potential-outcome noise;
- each method at every `(seed, rho)` pair.

No method shares a mutable RNG. Process completion order therefore cannot alter scientific results.

## Shock construction

Let `n` be a unit-length pattern supported on edges incident to a selected node, and let `i` be a unit-length edge-interaction pattern with disjoint support. The shock is:

```text
d(rho) = -magnitude * (sqrt(rho) * n + sqrt(1-rho) * i)
```

Because the patterns are orthogonal, the total L2 magnitude remains constant for all `rho`. Only the shared fraction changes.

## Method separation

| Method | Shared representation | Policy family | Purpose |
|---|---|---|---|
| Edge-only | None | Mycelial softmax + decay + exploration | Original mechanism/control |
| Node-only | Node effects | Same Mycelial policy family | Pooling ablation |
| Hierarchical | Source + target + interaction | Same Mycelial policy family | Proposed representation |
| Structured SW-UCB | Same node-edge features | Sliding-window linear UCB | Strong representation-aware baseline |

The first three help isolate representation. Structured SW-UCB tests whether the result is merely a generic benefit of shared features.

## Identifiability

The hierarchical score uses an additive decomposition:

```text
score(u, v, t) = base + source_effect[u] + target_effect[v] + interaction[u, v]
```

After online updates, every component family is projected to a sum-to-zero parameterization and shrunk toward zero. This makes the numerical decomposition reproducible. It does not imply that weakly observed components become strongly evidenced; uncertainty remains an empirical limitation.

## Atomicity and provenance

Each `(seed, rho)` result is written to a temporary file, flushed, and atomically renamed. Scientific values and volatile provenance are separated conceptually. Runtime duration, timestamps, and machine identity must not be used in deterministic hash comparisons.

## Extension ports

Future adapters may implement live model providers, graph discovery, policy constraints, or distributed state. They must remain outside `environment/` and `agents/` until a new protocol explicitly authorizes them. V1 has no runtime dependency on a cloud, database, queue, or orchestrator.

