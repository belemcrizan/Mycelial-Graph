# Token Accounting — Mycelial Graph V2

Misleading claim to prevent:

> “We saved 40% of the main-model tokens”

while the router, verifier, and retriever spent the missing 30% off-books.

## Provider-agnostic types

```text
TokenUsage
  input_tokens
  output_tokens
  cached_tokens          # not added again into total
  reasoning_tokens
  estimated_tokens      # unused when observed counts exist
  router_tokens
  verification_tokens
  tool_tokens
  retrieval_tokens
  summarization_tokens
  provider_metadata     # empty in the mock provider
```

```text
total_counted = input + output + reasoning
              + router + verification + tool
              + retrieval + summarization
```

Cached tokens are a subset of input for future live providers; the simulator does not double-count them.

`ResourceObservation` attaches token usage, latency, monetary cost, success, quality, and uncertainty.

## TotalResourceLedger

The ledger is the only allowed source of published resource totals. Categories:

- path tokens (model/retriever/verify as assigned by the edge);
- router tokens every step;
- model calls and tool/retrieval calls;
- latency sum;
- monetary API cost (simulated prices);
- parallel branch cost (zero in alpha while topology is static);
- state serialization proxy (optional small per-step overhead if enabled).

If a number cannot be placed in a ledger field, it must not influence a published savings claim.

## Interfaces, not vendors

V2.0-alpha ships a **mock provider** that fills `TokenUsage` from immutable potential outcomes. Future adapters (OpenAI, Anthropic, Gemini, local) must map native usage into `TokenUsage` without changing the ledger contract. No API keys belong in this repository.

## Audit command

`mycelial-graph v2-resource-audit` recomputes category sums from traces and checks equality with trial-level ledger totals.
