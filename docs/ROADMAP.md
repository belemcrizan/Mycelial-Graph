# Evidence-gated roadmap

## Gate 0 - V0 executable demonstrator

**Included:** local simulation, frozen YAML, immutable trials, Mycelial dynamics, reference comparators, hard-policy boundary, tests, metrics, report generation.

**Exit condition:** all invariant and integration tests pass; the multi-seed run is reproducible; limitations are explicit.

## Gate 1 - Scientific V1

**Add:** verified unique optima, causal shared-fraction generator, disjoint development/evaluation seeds, strong reviewed baselines, H1-H3 matrix, ablations, confidence intervals, effect sizes, and survival analysis when required.

**Exit condition:** results survive baseline review and the hypotheses are supported, qualified, or falsified without changing the frozen protocol after inspection.

## Gate 2 - Single-cloud POCs

Run AWS, Azure, and GCP separately. Each cloud receives the same adapter interface, workload, hard policy, task success definition, and observation schema. Do not route between clouds yet.

**Exit condition:** metrics reconcile with provider telemetry and billing; failure injection, fallback, kill switch, privacy controls, and reruns are auditable in each environment.

## Gate 3 - Narrow multi-provider gateway

Route one well-defined task type among a small allowlist of models. Optimize CPST subject to quality, latency, reliability, policy, residency, and budget constraints.

**Exit condition:** shadow-mode evidence and staged canary tests show material value without policy violations or unacceptable tail risk.

## Gate 4 - Composite AI pipelines

Extend the graph to prompt strategies, retrieval, caches, tools, guardrails, parsers, and local/cloud compute. Add capacity constraints and production observability.

## Gate 5 - Enterprise execution fabric

Only after earlier evidence may the project consider hierarchical multi-cloud graphs, forecasting, architecture-level recommendations, or additional learning mechanisms. These are roadmap possibilities, not current claims.

