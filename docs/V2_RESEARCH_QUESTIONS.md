# V2 Research Questions

V1 remains:

> Can an AI execution system recover from a local disruption without relearning everything?

V2 adds:

> Can an adaptive graph learn where additional inference resources are worth spending, preserving task-level utility while reducing token consumption, monetary cost, and latency under changing conditions?

General form:

> Can biologically inspired local adaptation improve the quality-cost-resilience frontier of agentic AI execution?

## What is not the hypothesis

“Using fewer tokens is always better” is rejected as a scientific claim. Always-low-compute will often win a naive success/tokens ratio by failing quietly or by scoring cheap garbage.

## Formal target (regime-specific)

Study whether there exist frozen regimes such that:

```text
Q_mycelial ≥ Q_baseline - ε
Tokens_mycelial < Tokens_baseline     (ledger totals)
Cost_mycelial < Cost_baseline         (when prices are non-degenerate)
Latency_mycelial ≤ Latency_baseline   (desirable, not always required)
RecoveryCost_mycelial < RecoveryCost_baseline
```

Success requires quality non-inferiority **first**, then resource reduction, then robustness and ablations. Router overhead must be inside the token totals.

## Statistical order (MG-EXP-V2)

1. Non-inferiority of quality vs `always_high_compute` (primary control).
2. Conditional resource reduction (tokens, then money).
3. Shock robustness.
4. Biological ablations.

Development and pilot runs cannot answer these questions. Confirmatory execution stays locked until the V2 sample-size addendum exists.

## Positioning

The contribution under test is an agentic architecture in which compute is not a fixed parameter but a resource distributed over a graph, using candidate mechanisms: growth/exploration, reinforcement, retraction, translocation, and damage adaptation.

Language allowed: “inspired by”, “tests whether”, “under these regimes”, “candidate mechanism”, “evidence suggests”, “not demonstrated outside this setting.”
