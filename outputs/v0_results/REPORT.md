# Mycelial Graph V0 - Demonstration Report

**Author:** Crizan Belém Ribeiro, Independent Researcher  
**Generated:** 2026-08-24T14:17:40.381954+00:00  
**Scientific status:** descriptive V0 engineering run; no H1, H2, or H3 validation claim

## Executive summary

This run shows that the proposed architecture can be executed end to end. A synthetic AI pipeline was routed repeatedly, one model component was degraded at step 100, each policy adapted only from the feedback made available to it, and the runner produced auditable metrics and frozen-trial hashes.

In plain language, the system behaves like a network of routes between service choices. Mycelial V0 gives every connection a local "conductance." Helpful observations strengthen a traversed connection, unhelpful observations weaken it, unused state decays, and a small explicit exploration rate keeps alternatives discoverable. Hard policy constraints are checked before any soft score.

Across this bounded demonstration, the lowest descriptive Cost per Successful Task (CPST) was produced by **Reactive shortest path (reference)**. The highest recovery probability was shared by **Reactive shortest path (reference), Structured semi-bandit (reference)**. These are observations from a synthetic V0, not evidence that one method is generally superior.

## What was executed

- 12 immutable seeds, with 240 tasks per policy and seed.
- A 48-path DAG with 13 nodes and 24 directed edges.
- One localized, abrupt degradation at task 100.
- Mycelial V0 plus two transparent reference baselines.
- Pre-generated potential outcomes shared across methods within every seed.
- Local feedback only: a router observes only the edges it traversed.
- The pre-shock optimum includes `model_balanced`; the post-shock optimum replaces it with `model_economy`.
- The certified optima share 66.7% of their directed edges, with pre/post utility margins of 0.0103 and 0.0103.

## Representative trace - seed 101

This trace makes the POC visible at four checkpoints. It is a debugging view, not an aggregate result.

| Method | Step | Phase | Selected component route | Expected utility | Oracle utility |
| --- | ---: | --- | --- | ---: | ---: |
| Mycelial V0 | 0 | initial | `prompt_compact -> retriever_hybrid -> model_economy -> guardrail_standard -> output_concise` | 0.416 | 0.468 |
| Mycelial V0 | 99 | pre-shock | `prompt_compact -> retriever_hybrid -> model_economy -> guardrail_standard -> output_concise` | 0.416 | 0.468 |
| Mycelial V0 | 100 | shock | `prompt_compact -> retriever_hybrid -> model_balanced -> guardrail_standard -> output_concise` | 0.324 | 0.453 |
| Mycelial V0 | 239 | final | `prompt_structured -> retriever_keyword -> model_premium -> guardrail_strict -> output_concise` | 0.410 | 0.453 |
| Structured semi-bandit (reference) | 0 | initial | `prompt_structured -> retriever_keyword -> model_premium -> guardrail_strict -> output_detailed` | 0.420 | 0.468 |
| Structured semi-bandit (reference) | 99 | pre-shock | `prompt_structured -> retriever_hybrid -> model_economy -> guardrail_strict -> output_concise` | 0.443 | 0.468 |
| Structured semi-bandit (reference) | 100 | shock | `prompt_structured -> retriever_keyword -> model_premium -> guardrail_strict -> output_detailed` | 0.420 | 0.453 |
| Structured semi-bandit (reference) | 239 | final | `prompt_structured -> retriever_hybrid -> model_economy -> guardrail_strict -> output_concise` | 0.443 | 0.453 |
| Reactive shortest path (reference) | 0 | initial | `prompt_structured -> retriever_hybrid -> model_balanced -> guardrail_strict -> output_detailed` | 0.468 | 0.468 |
| Reactive shortest path (reference) | 99 | pre-shock | `prompt_structured -> retriever_hybrid -> model_balanced -> guardrail_strict -> output_detailed` | 0.468 | 0.468 |
| Reactive shortest path (reference) | 100 | shock | `prompt_structured -> retriever_hybrid -> model_balanced -> guardrail_strict -> output_detailed` | 0.361 | 0.453 |
| Reactive shortest path (reference) | 239 | final | `prompt_structured -> retriever_hybrid -> model_economy -> guardrail_strict -> output_detailed` | 0.453 | 0.453 |

## Aggregate results

| Method | Recovery probability | SRC, recovered only | Censored runs | CPST (USD) | Success rate | Post-shock utility | SER | p95 decision (ms) | Mean primitive ops |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Mycelial V0 | 66.7% | 436.9 | 4 | 0.003746 | 89.4% | 0.408 | 60.5% | 0.0262 | 12.0 |
| Reactive shortest path (reference) | 100.0% | 50.4 | 0 | 0.002731 | 97.3% | 0.452 | 0.2% | 0.1393 | 288.0 |
| Structured semi-bandit (reference) | 100.0% | 297.1 | 0 | 0.005241 | 92.5% | 0.425 | 40.8% | 0.0173 | 12.0 |

### How to read the table

- **Recovery probability:** fraction of runs that met the sustained utility criterion before the horizon ended.
- **SRC:** local edge-feedback samples needed to recover. It is summarized only for recovered runs; non-recovery remains right-censored.
- **CPST:** total simulated execution cost divided by successful tasks.
- **SER:** post-shock samples spent on unaffected edges outside the post-shock oracle path, using one frozen external classifier.
- **Decision time and primitive operations:** routing overhead only, kept separate from simulated task latency.

## Reproducibility and fairness controls

Every seed produced a frozen compressed trial file before comparison. Its SHA-256 digest is recorded in `results.json`. The outcome for every edge and step was pre-generated, but a router could retrieve feedback only for its chosen path. Mycelial parameters were selected on disjoint development seeds [17, 29, 43, 59, 71] and frozen before this final run. The V0 seed set is an engineering demonstration set, not a publication-grade untouched holdout. Hard policy constraints were applied before routing.

## What this V0 proves

- The package builds the intended layered execution graph.
- Mycelial conductance, lazy temporal decay, local feedback, softmax routing, explicit exploration, and single-edge fallback execute together.
- Only traversed edges receive feedback updates.
- A localized shock can be injected reproducibly.
- Results, traces, trial hashes, recovery censoring, CPST, SER, and computational accounting are generated automatically.

## What this V0 does not prove

- It does not validate H1 (sparse-shock recovery), H2 (scaling), or H3 (structural reuse).
- It does not establish statistical or practical superiority over structured baselines.
- Its two reference baselines are inspectable V0 comparators, not certified reproductions of every research baseline.
- It does not use live cloud providers, real customer prompts, production traffic, or a global quality evaluator.
- It provides no convergence or regret guarantee.

## Next evidence gates

1. Freeze development and evaluation seed partitions, then tune on development seeds only.
2. Generate causal shared-fraction trials and verify unique pre- and post-shock optima with margins.
3. Run the H1 sparse-shock suite with at least 50 evaluation replications when computation is cheap.
4. Run H2 across depth, branching, and non-stationarity regimes.
5. Run H3 with trial-level shared fraction and censoring-aware analysis.
6. Execute the required decay/exploration ablations.
7. Only after local evidence is credible, validate one cloud at a time using the same adapter contract and frozen workload.

The detailed single-cloud sequence is defined in `docs/CLOUD_VALIDATION.md`. Production multi-cloud routing remains a later roadmap phase, not part of V0.
