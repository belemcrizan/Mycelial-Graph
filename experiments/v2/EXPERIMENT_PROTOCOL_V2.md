# MG-EXP-V2: Adaptive Resource Allocation Protocol

**Author:** Crizan Belem Ribeiro, Independent Researcher  
**Protocol version:** MG-EXP-V2  
**Status:** Frozen for development/pilot design; confirmatory execution locked pending `SAMPLE_SIZE_ADDENDUM_V2.md`

## 1. Purpose

V1 tests structural reuse after local disruption. V2 tests whether a mycelial resource controller can keep quality non-inferior to a high-compute policy while reducing accounted resources under non-stationary prices, quality, latency, outages, and scarcity.

The hypothesis is **not** that fewer tokens are always better.

## 2. Questions

Primary: under which frozen regimes is V2 quality non-inferior to always-high-compute within margin `ε`, while total ledger tokens (including router overhead) are lower?

Secondary: monetary cost, latency, recovery tokens, route churn, ablation of cord/prune/transfer.

## 3. Environment

Layered DAG:

```text
Task → Retriever {light, heavy} → Model {cheap, standard, frontier} → Verify {skip, verify} → Output
```

Each edge has latent quality, token means, latency, failure probability, and a price path. Potential outcomes for quality, tokens, latency, and failure uniforms are indexed by step and edge. Methods receive a read-only scenario.

Task difficulty ∈ {easy, medium, hard} is sampled per seed and **not** shown to methods. Methods may infer difficulty from observations.

## 4. Regimes

Reproducible by seed:

`STATIC`, `PRICE_SHOCK`, `QUALITY_SHOCK`, `LATENCY_SHOCK`, `OUTAGE`, `RESOURCE_SCARCITY`, `MIXED_SHOCK`

Development may use a subset. All listed regimes exist in the generator.

Shock time is frozen. Pre/post means and prices are part of the immutable scenario.

## 5. Methods

See implementation plan. Primary treatment: `v2_mycelial`. Primary control: `always_high_compute`. Additional controls: always-low, fixed-budget, random, epsilon-greedy, transplanted `v1_edge_only`.

Thompson Sampling, cost-sensitive bandits, and Structured SW-UCB on the V2 vector are deferred: an underspecified caricature would not be a fair baseline. This is a protocol limitation, not a hidden win.

## 6. Outcomes

Vector per trial (means over post-shock steps unless noted):

- quality_score (expected quality, simulator-known for evaluation)
- task_success (1 - failure)
- total_tokens and category breakdown
- monetary_cost, latency
- restricted recovery time (quality vs post-shock quality oracle)
- recovery_tokens, quality_loss, route_switches, prune_count, resource_transfer_l1
- ledger identity hash

Oracle quality path is evaluation-only.

## 7. Hypotheses and interpretation

Quality non-inferiority at primary regime (development default: `PRICE_SHOCK`):

```text
H0: ΔQ ≤ -ε
H1: ΔQ > -ε
```

with `ε` frozen in config (`quality_noninferiority_margin`).

If non-inferiority fails, resource reductions are exploratory only.

Interpretation: PASS / CONDITIONAL / INCONCLUSIVE / REFUTED as in the analysis plan. No gate exists to “prove” V2.

## 8. Phases

Development, pilot, and confirmatory are separate populations. Confirmatory seeds are the first N of the precommitted pool after N is recorded. No pooling.

## 9. Prohibited confirmatory actions

Same spirit as V1: no post-hoc metric swaps, no seed dropping, no live prices, no presenting pilot as confirmatory, no hiding router tokens.

## 10. Scope boundary

MG-EXP-V2 does not test live providers, production safety certification, or biological truth of fungi. Anastomosis and dynamic topology branching are specified but not confirmatory endpoints in alpha.
