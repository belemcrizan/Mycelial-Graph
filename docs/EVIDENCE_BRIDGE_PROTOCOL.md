# Evidence Bridge Protocol (MG-EXP-V2.1)

**Status:** Development protocol. Not confirmatory. Does not mutate MG-EXP-V2 alpha estimands.

## Grand question (operational)

How should an autonomous agent allocate finite computational resources across a changing execution network when the value of additional compute is uncertain?

Mycelial is tested on the vector:

quality × resource efficiency × robustness × recovery × generalization

relative to **strong conventional allocators**, not only always-high/always-low.

## Quality first

```text
H0: ΔQ = Q_M − Q_H ≤ −ε
H1: ΔQ > −ε
```

ε is frozen in YAML (`quality_noninferiority_margin`, alpha default 0.05).

Resource claims become primary only after NI. Then:

```text
ResourceSaving = 1 − T_M / T_H
require: lower_CI(ResourceSaving) > MMRR
```

**MMRR** default 0.05 for development. Pilot must re-justify and freeze before confirmatory. Detectable 1–2% savings are not success.

Tokens **T** are ledger totals including router and state overhead. Monetary **C** and latency **L** are reported in parallel and not scalarized into the scientific estimand.

## Counterfactual VOC design

For verification skip vs spend, frozen potential outcomes supply both **a_stop** and **a_more_compute**.

```text
VOC_diff(a|s) = E[ΔQ|s,a] − λ E[ΔT|s,a]
MVC(a|s)       = E[ΔQ|s,a] / max(E[ΔT|s,a], ε)
```

Metrics: MAE of ΔQ, MAE of MVC (stable pairs only), ranking accuracy, Brier, ECE, Spearman, false-stop, false-spend.

The allocation **oracle** uses expected path quality from frozen means and is **evaluation-only**. `AllocationRegret = U_oracle − U_policy`.

## Iso-model design

`environment.iso_model: true` equalizes latent quality, tokens, latency, fail, and price of **model-class edges**. Policies may still pick different retrieval/verification alternatives. This asks whether Mycelial can save compute without a cheaper model.

Multi-model remains the V2.0-alpha track and must be reported separately.

## Budget curves

Sweep B ∈ {5k, 10k, 20k, 40k, 80k} (development may use a subset). Estimate Q(B). Report B_70, B_80, B_90 when attained. Pre-specified integration: mean quality versus log budget; no post-hoc axis swap.

## Waste schema

Exclusive accounted buckets: input, output, reasoning, retrieval, verification, tool, summarization, router, state overhead.

Proxies **not** added to the total: unique_context, reingested_context, unused_retrieval, successful_trajectory, cacheable, cache_hit_equivalent.

Identity test: sum of exclusive buckets = ledger `total_tokens`.

## Real coding smoke

Two local Python fixtures, executable tests, no network. High-compute applies the fix and runs tests; low-compute does not. **Not SWE-bench.** Official graders are required before any SWE-bench wording.

Shadow mode records a non-intervening recommendation.

## Statistical plan

- Development / pilot / confirmatory remain disjoint.  
- V2.1 confirmatory is **not** unlocked.  
- Paired methods at scenario level for synthetic tracks.  
- Effect sizes and CIs, not p-values alone.  
- No sequential peeking of a future confirmatory sample.  
- Subgroup (easy/medium/hard) is exploratory.  
- Claims in `docs/claim_evidence_matrix.yaml` are machine-audited for wording, not for truth.

## Hyperparameter fairness

V2.1 development must not tune only Mycelial. Strong baselines use the same YAML utility lambdas where they consume λ. Dedicated extra search on Mycelial is a protocol violation.
