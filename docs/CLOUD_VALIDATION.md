# Single-cloud validation plan

## Why the clouds are tested separately

V0 must first distinguish algorithm behavior from provider differences. AWS, Azure, and Google Cloud therefore receive independent POCs. Each POC uses one cloud account, one region, one frozen workload, one observation contract, and no cross-cloud failover. Multi-cloud routing begins only after each adapter passes the same gates.

This plan is intentionally future work. The current package makes no network call and needs no credential.

## Provider-neutral adapter contract

Every live adapter must return one observation per invocation:

```json
{
  "trace_id": "opaque-id",
  "cloud": "aws|azure|gcp",
  "region": "configured-region",
  "component_id": "allowlisted-model-alias",
  "provider_model_version": "provider-returned-or-deployment-version",
  "started_at": "ISO-8601",
  "latency_ms": 0.0,
  "input_tokens": 0,
  "output_tokens": 0,
  "estimated_cost_usd": 0.0,
  "billing_cost_usd": null,
  "quality": 0.0,
  "success": true,
  "failure_class": null,
  "rate_limited": false,
  "policy_decision_id": "opaque-id"
}
```

Estimated request cost and reconciled billing cost remain separate. Quality comes from one frozen, domain-appropriate evaluator and cannot be silently replaced by provider success. Prompt and response bodies are excluded from default telemetry.

## Common workload

1. Select one narrow task with an owned or redistributable evaluation set.
2. Freeze prompts, expected properties, evaluator, minimum quality, latency SLA, retry budget, and hard policy.
3. Use identical semantic tasks across clouds, while allowing provider-specific request formatting.
4. Warm up endpoints outside the measured set and label warm-up traffic.
5. Run a static baseline before enabling adaptation.
6. Store immutable workload ids and trace correlations, not raw sensitive content.

## Common gates for each cloud

### Gate A - adapter conformance

- Validate the observation schema and monotonic timestamps.
- Verify timeout and cancellation behavior.
- Verify token extraction and estimated cost calculation.
- Confirm model, deployment, region, and identity allowlists.
- Prove that hard-policy denial occurs before invocation.

### Gate B - static live baseline

- Run every allowlisted alternative independently.
- Measure quality, latency distribution, failure classes, token usage, and estimated CPST.
- Reconcile estimates against provider billing when billing data becomes available.
- Freeze the valid alternative set before the adaptive run.

### Gate C - controlled local shock

Use an adapter-side fault-injection wrapper to add a declared delay, failure probability, or synthetic price multiplier to one alternative. Do not describe this as a real provider outage. Replay the same frozen workload and shock schedule for every policy.

### Gate D - shadow adaptation

Let Mycelial Graph choose a route, but send the user-visible request through the static control route. Execute sampled shadow calls only within an approved budget. Compare decisions, policy compliance, CPST estimate, quality, and recovery without affecting users.

### Gate E - staged execution and recovery

- Start with a small canary budget and explicit stop conditions.
- Test timeout, retry exhaustion, single-provider fallback, rollback to static routing, and kill switch.
- Verify that no soft score can bypass residency, identity, content, or model allowlists.
- Restore the prior state and reproduce the report from immutable traces.

### Gate F - acceptance

An adapter passes only if telemetry reconciles, all policy tests pass, no forbidden content is logged, static rollback works, trial reruns are explainable, and any observed benefit remains after quality and failure constraints.

## AWS POC

**Execution target:** Amazon Bedrock runtime in one approved AWS Region.  
**Identity:** workload IAM role with least-privilege invocation and telemetry permissions.  
**Operational telemetry:** Amazon CloudWatch metrics and logs; AWS CloudTrail for API audit where applicable.  
**Invocation data:** keep Bedrock model invocation body logging disabled by default; if a controlled test enables it, use synthetic content, a dedicated destination, encryption, and short retention.

AWS documents CloudWatch metrics, CloudTrail, and invocation logging as observability options for the Bedrock runtime. Invocation logging can include full inputs and outputs and is disabled by default, which is why the POC treats content logging as an explicit privacy decision rather than a prerequisite.

**AWS exit artifact:** provider config with aliases rather than hard-coded public model ids, adapter conformance results, CloudWatch-to-trace reconciliation, billing reconciliation note, fault-injection run, rollback proof, and generated MG report.

## Azure POC

**Execution target:** model deployments in Microsoft Foundry Models within one Azure region.  
**Identity:** managed identity and role-based access.  
**Operational telemetry:** Azure Monitor metrics and diagnostic logs; Application Insights only for the application trace data explicitly approved.  
**Cost:** retain request estimates, then reconcile with Azure Cost Management rather than treating near-real-time estimates as invoices.

Microsoft documents automatic Azure Monitor metrics for Foundry model deployments and links deployment monitoring to Cost Management. Its documentation also notes that billing views can lag the billing event, reinforcing the need to keep estimated and billed cost separate.

**Azure exit artifact:** deployment-alias config, role matrix, Azure Monitor-to-trace reconciliation, delayed cost reconciliation, fault-injection run, rollback proof, and generated MG report.

## Google Cloud POC

**Execution target:** an allowlisted Gemini or other foundation-model endpoint in the Google Cloud AI platform, pinned to one project and location.  
**Identity:** dedicated service account or workload identity with minimum roles.  
**Operational telemetry:** Cloud Monitoring dashboards and metrics, plus adapter traces with request correlation.  
**Usage:** capture provider-returned usage metadata and validate token estimation against the applicable count-tokens operation when supported.

Google Cloud documents model-observability dashboards for usage, throughput, latency, and 429 diagnosis, with metrics available through Cloud Monitoring. Because product naming and model lifecycles change, the adapter must pin endpoint, publisher, model/deployment version, project, and location in every run manifest.

**GCP exit artifact:** endpoint-alias config, service-account role matrix, Cloud Monitoring-to-trace reconciliation, token and billing reconciliation, fault-injection run, rollback proof, and generated MG report.

## Comparison after all three POCs

Use one table with the same fields: success definition, evaluator version, quality, p50/p95/p99 latency, failures by class, token counts, estimated cost, reconciled cost, CPST, policy denials, recovery probability, censored runs, SRC, SER, routing overhead, and rollback result. Do not rank clouds if task semantics, model capability, quotas, or billing coverage are not comparable.

## Promotion to a multi-provider gateway

Promotion requires all three single-cloud gates plus:

- a cross-provider model-capability contract;
- currency and price-version normalization;
- residency and transfer policy review;
- independent circuit breakers and budgets;
- correlated-failure tests;
- idempotency and duplicate-charge handling;
- provider-neutral rollback to a frozen safe route.

## Official references checked for this plan

- [Amazon Bedrock runtime observability](https://docs.aws.amazon.com/bedrock/latest/userguide/monitoring.html)
- [Amazon Bedrock model invocation logging](https://docs.aws.amazon.com/bedrock/latest/userguide/model-invocation-logging.html)
- [Monitor model deployments in Microsoft Foundry Models](https://learn.microsoft.com/en-us/azure/foundry/foundry-models/how-to/monitor-models)
- [Monitor generative AI applications with Azure Monitor Application Insights](https://learn.microsoft.com/en-us/azure/foundry-classic/how-to/monitor-applications)
- [Google Cloud generative AI release notes - model observability](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/release-notes)
- [Count tokens for Gemini sample](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/samples/generativeaionvertexai-gemini-token-count-multimodal)

Cloud APIs and product names change. Re-check these primary sources immediately before implementing an adapter; do not infer a stable API from this roadmap alone.
