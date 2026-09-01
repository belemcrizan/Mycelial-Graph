# Baseline fairness

A skeptical reviewer should be able to see whether Mycelial received special treatment.

| Method | Source / objective | Assumptions | Adaptation in this repo | Hyperparameters | Why the adaptation is fair | Limitations |
|---|---|---|---|---|---|---|
| always_high_compute | Engineering control | Frontier+heavy path is feasible | Greedy on alternative index 2 | None | Upper quality/cost envelope | Not adaptive |
| always_low_compute | Engineering control | Cheap path is feasible | Greedy on index 0 | None | Lower envelope | Quality collapse expected |
| fixed_budget | Static allocation | Standard class is the mean policy | Index 1 | None | Natural midpoint | No learning |
| random_router | Uniform exploration | Feasible paths only | ε=1 softmax | None | Floor on intelligence | High variance |
| epsilon_greedy | Classic bandit | Quality-only | Quality hats, ε≈0.15 | Shares temperature floor | Intentionally cost-blind | Weak vs cost-aware methods |
| v1_edge_only | V1 identity transplant | Quality conductance | Same update family, ignore cost | Controller YAML | Isolates “just V1 in a new env” | Not a 2024 TTC method |
| thompson_sampling | Thompson 1933 / modern Gaussian TS | Independent edges, Gaussian noise caricature | Sample Q, subtract λT | λ from YAML | Same λ as Mycelial utility | Not a full contextual model |
| cost_sensitive_bandit | LinUCB-like linear score | Local hats are features | Q−λT−λC | YAML λ | Same cost weights | No fancy features |
| structured_sw_ucb | V1 SW-UCB family | Sliding window stationarity | Window=12 on edge quality | Window fixed | Same representation grain as V1 | Not the exact V1 linear features |
| uncertainty_threshold | Heuristic TTC | High uncertainty → frontier | 1/√n | threshold=0.12 | Cheap observable only | Crude |
| adaptive_early_stop | CALM-like stop, not CALM | Verify is the expensive option | VOC difference at verify, model locked to standard | YAML λ | Isolates stop vs Mycelial graph state | Not sequence-level risk control |
| lagrangian_budget | Dual ascent / constrained MDPs | Soft token target | Dual on path tokens | target=400, step 0.002 | Conventional constrained allocator | Target not tuned per regime |
| static_cascade | Cascade literature | Escalate after failure | Quality floor 0.62 | floor | Common production pattern | Myopic |
| eval oracle | Potential-outcome quality max | Sees means | `allocation_regret` only | None | **Forbidden as a treatment** | Upper bound only |

**Tuning budget.** Development seeds only. V2.1 must not grid-search Mycelial while leaving TS/Lagrangian at defaults unless the same budget is recorded for all. This document records that the **first** implementation used shared YAML λ and **no** extra Mycelial-only search.

**Known fairness risks.** (1) Mycelial has more internal state (prune/transfer/cord). That is the hypothesis, not an excuse to hide extra knobs. (2) `epsilon_greedy` is still a weak cost-unaware control; it is retained as a historical alpha baseline, not as the strongest adversary. (3) Window and dual step-sizes were not cross-validated; they are disclosed defaults.
