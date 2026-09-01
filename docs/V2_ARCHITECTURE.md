# V2 Architecture

V2 is an **additive package** (`mycelial_graph.v2`). V1 modules keep answering the recovery-representation question. V2 asks how an agent should allocate finite cognitive resources on a changing execution graph.

## Conceptual pipeline

```text
Task
  |
  v
Task Signal Extractor   (observable quality, fail, tokens, latency — not the difficulty label)
  |
  v
Mycelial Resource Controller
  |
  +------------------+------------------+
Cheap Route     Standard Route    Frontier Route
  |                  |                  |
Retriever           Retriever         Retriever
  |                  |                  |
Model               Model             Model
  |                  |                  |
  +-------- verification / skip --------+
  |
Output

Feedback: quality, tokens, cost, latency, uncertainty, failure, information gain
  -> Resource Controller
  -> Graph state (conductance, prune evidence)
  -> Resource ledger
```

## Package boundaries

| Package | Responsibility |
|---|---|
| `v2.ledger` | TokenUsage, observations, conservation of accounted totals |
| `v2.environment` | Immutable resource scenarios and shock regimes |
| `v2.biology` | Conductance, prune, translocation, stop, metabolism invariants |
| `v2.policies` | Baselines and the resource controller |
| `v2.metrics` | Recovery, Pareto, non-inferiority |
| `v2.runner` | Paired execution, traces, manifests |

Live providers, dashboards, and orchestrators stay outside this tree until a later protocol says otherwise.

## Randomness

V2 namespaces: `mycelial-graph-v2:{seed}:{namespace}`. They must not share streams with V1.

## What V2 is not

Not a FinOps dashboard, not a prompt compressor, not a vendor selector. Those may appear as *measurements* on the graph. The object of study remains adaptive structure and resource flow under non-stationarity.
