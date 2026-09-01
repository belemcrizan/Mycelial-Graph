# V2 Migration Notes

V2 does not replace V1. There is no required data migration.

## What stays

- All V0/V1 commands, configs, protocols, and tests.
- `experiments/v1/` confirmatory lock.
- Existing `outputs/demo` archives for MG-EXP-V1.
- Edge-only, node-only, hierarchical, Structured SW-UCB.

## What is added

- `mycelial-graph v2-*` commands.
- `experiments/v2/` with its own lock.
- `src/mycelial_graph/v2/`.

## Provenance note

V1 `code_commit` may use a hash of every `src/**/*.py` file when git metadata is unavailable. Adding V2 files therefore changes *future* tree hashes. Archived V1 results remain the record of the code that produced them. Re-running V1 after this commit is a new execution, not a continuation of the old archive.

## Integrating later live providers

Do not fold providers into `environment/` or V1 `agents/`. Add adapters that emit `TokenUsage` / `ResourceObservation`. Require a new protocol before live spend.
