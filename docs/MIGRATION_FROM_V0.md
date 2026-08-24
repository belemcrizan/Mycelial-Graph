# Migration from the Three V0 Prototypes

The three V0 implementations were described as complementary but were not all available as source trees during this reconstruction. V1 therefore defines a clean integration contract instead of pretending that unseen code was merged.

## Selection rule

Do not combine repositories file by file. Inventory each V0 by responsibility:

| V0 capability | V1 destination | Acceptance requirement |
|---|---|---|
| Conductance and local update | `agents/edge_only.py` | Behavior characterized by regression tests |
| Graph/topology generation | `environment/graph.py` | Produces valid layered DAG without mutable global state |
| Shock/reward simulation | `environment/scenario.py` | Immutable, indexed outcomes and certified optima |
| Metrics/statistics | `analysis/` | Matches frozen estimand and censoring rules |
| Report generation | `reporting/` | Reads derived data only; does not alter trials |
| CLI utilities | `cli.py` | Maps to validate, experiment, analyze, report |

## Migration procedure

1. Tag or archive each original V0 before migration.
2. Record its commit, commands, dependencies, and known behavior.
3. Add characterization tests around any component selected for reuse.
4. Port one responsibility at a time behind the V1 interface.
5. Run deterministic and serial/parallel equivalence tests.
6. Compare development outputs; never tune using confirmatory seeds.
7. Keep rejected V0 components in their archived repositories rather than in the V1 runtime.

## Non-negotiable boundaries

- V0 edge-only behavior remains a named control, not silently rewritten to resemble the hierarchical proposal.
- No V0 may introduce privileged feedback or shared mutable RNG.
- A utility is reused only when its semantics match the frozen protocol.
- Differences that cannot be reconciled become explicit alternative methods or later experiments.

