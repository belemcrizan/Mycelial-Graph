# Security and governance boundary

## Principle

Safety, security, compliance, residency, authorization, and contractual constraints are not reward terms. A cheap or high-conductance edge cannot override them.

## V0 behavior

`HardPolicy` filters an edge if its destination component is explicitly blocked or its declared per-component cost exceeds the hard cap. Filtering occurs before every router decision. If filtering makes a route impossible, the system fails closed.

The V0 policy is intentionally minimal. It demonstrates boundary placement, not a complete enterprise policy language.

## Required before a live provider test

- Use workload identities or managed identities; do not place long-lived keys in YAML.
- Separate provider credentials by environment and cloud.
- Redact prompt and response content from default telemetry.
- Log policy decision, adapter identity, model/version identifier, region, latency, token counts, cost source, status, and trace correlation id.
- Define data-residency and model allowlists outside the adaptive score.
- Add rate, concurrency, and budget circuit breakers.
- Add explicit timeout, retry budget, single-provider fallback, rollback, and kill-switch procedures.
- Encrypt telemetry in transit and at rest and define retention limits.
- Threat-model prompt injection, tool misuse, evaluator manipulation, telemetry poisoning, and feedback gaming.

## Important limitation

V0 reads component characteristics from a trusted local configuration. A live system must authenticate telemetry and protect the feedback channel; otherwise an attacker could manipulate conductance by falsifying measurements.

