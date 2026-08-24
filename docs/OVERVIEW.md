# Plain-language overview

## The business problem

Imagine an AI product with several ways to prepare a prompt, retrieve information, call a model, apply a safety check, and format the answer. There may be dozens or millions of possible end-to-end routes. The route that worked yesterday may become expensive, slow, overloaded, or unreliable today.

A central optimizer can repeatedly compare complete routes. That can waste past knowledge when only one local component changed. Mycelial Graph explores a different approach: store useful experience on the connections between components, then update only the connections that were actually used.

## Why “mycelial”?

Fungal transport networks inspired the design intuition: local reinforcement, degradation, and alternate routes can produce adaptive transport without one controller recomputing everything. This project does not claim biological fidelity. The metaphor is useful only if the computational hypothesis survives controlled comparison.

## What happens during one task

1. Hard rules remove prohibited choices.
2. At each stage, the router checks the conductance of feasible outgoing connections.
3. It either follows a conductance-weighted choice or performs explicitly logged exploration.
4. The selected mock components produce local cost, latency, quality, failure, and load measurements.
5. Only traversed connections are updated from their own observations.
6. The report records task success, cost, utility, routing work, and recovery behavior.

## The demonstration story

The simulation runs normally for 100 tasks. Then `model_balanced` suffers a localized quality, latency, reliability, cost, and load shock. Other components do not change. The system continues for 140 tasks and must discover a better post-shock route without reading future outcomes.

All compared methods receive the same pre-generated world for each seed. This matters: if every method saw different noise, the comparison would be ambiguous.

## What a successful V0 means

V0 succeeds if the package runs, respects invariants, reproduces trials, applies a shock, records censoring correctly, and generates an understandable report. A Mycelial win is not required. A tie or loss is informative because the research hypothesis is allowed to fail.

## Product value, if later evidence supports it

The eventual engineering objective is simple: complete more successful AI tasks per unit of cost while preserving quality, latency, reliability, policy, and provider redundancy. Real-provider routing begins only after controlled local evidence is credible.

