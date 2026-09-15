# External validation plan

Priority: independent data before MycelialBench.

```text
external adapters -> license gates -> (optional local download) -> MG-EXP-REAL-001 replay
-> lessons -> only then MycelialBench
```

MycelialBench remains on the roadmap and is not built in this cycle.

## Three-layer pyramid

- **A Synthetic:** V1/V2 simulators and the pooling toy. Mechanism isolation.
- **B Replay:** Arena/RouteLLM/RouterArena/status joins. External validity.
- **C Bounded live:** collector with caps. Not authorized here.

## Validity ladder (current)

| Level | Status |
|---|---|
| E0 toy | pooling toy implemented |
| E1 synthetic controlled | V1 development + (if executed) V1 pilot |
| E2 complex synthetic | V2 development only |
| E3 external static dataset | adapter ready, data not ingested |
| E4 real trace replay | not executed |
| E5–E8 | not achieved |

## Overfitting control

Repeated method changes in response to one external benchmark turn it into development data. Keep at least one untouched source when a REAL-001 evaluation begins.
