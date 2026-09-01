# Resource Model — Mycelial Graph V2

Tokens, money, latency, calls, and failure risk are **attributes of graph elements**, not an after-the-fact dashboard. V2.0-alpha implements this in a synthetic, provider-agnostic simulator. Live APIs are out of scope.

## Units

A trial has a global budget cap `B_max(t)` in **composite resource units**. In alpha, one unit equals one token from the total ledger (including router and verification). Dollar cost and latency are tracked in parallel ledgers and may be used in the routing utility through configurable λ weights.

```text
Σ_e B_e(t) = B_max(t)
```

`B_max` is not necessarily distributed once at t=0. Translocation moves mass during the trial. Under `RESOURCE_SCARCITY`, `B_max` falls after the shock time; conservation is with respect to the *current* cap.

## Edge / node attributes

Each edge carries a latent vector (means) and, when traversed, an observation:

| Field | Meaning | Observed? |
|---|---|---|
| expected_quality | Latent mean quality in [0, 1] | No; noisy Q observed on use |
| uncertainty | Estimator variance / low counts | Derived |
| token_cost | Input+output+reasoning+local tool/retrieval | Observed on use |
| monetary_cost | `tokens/1000 * price(t,e)` | Observed on use |
| latency | Milliseconds | Observed on use |
| failure_risk | Bernoulli failure probability | Success/fail on use |
| reliability | `1 - failure_risk` | Derived |
| information_gain | Reduction in uncertainty after observation | Derived |
| historical_utility | EWMA of routing U | Derived |
| conductance | Policy state G | Internal |

Prices, availability, and quality means may drift. The agent never receives perfect future costs.

## Hard constraints (safety of resource optimization)

Cost reduction must not silently drop required checks. Alpha supports:

- `minimum_quality` — skip-verify forbidden if predicted Q is below threshold;
- `max_risk` — high inferred failure forces the safer local option;
- `mandatory_verification` (config flag) — verification edge required.

These constraints sit **outside** the soft utility. Violating them is a bug, not a savings.

## Marginal value of compute

```text
MVC = E[Q_expensive - Q_cheap] / max(R_expensive - R_cheap, ε)
```

Used at the verification layer (verify vs skip) and, descriptively, at the model-class layer. Threshold `τ` is a frozen config parameter.

## Composite utility vs Pareto

Routing may use a weighted U. Scientific reporting must still present quality, tokens, money, latency, and reliability separately, plus Pareto dominance. A method that wins U by collapsing quality is not a V2 success.

## Network maintenance cost

Scoring every outgoing edge costs `router_tokens_per_candidate`. Creating conceptual loops or extra branches (V2.1) would add explicit branch and sync costs. Alpha already forbids “explore everything for free.”
