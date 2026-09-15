# Data sources

Inspected 2026-09-14. Cards must be re-checked at download time. Nothing here was downloaded into the repo.

## Decision record template

Each source answers: why; which hypothesis; observed vs latent; missingness; transforms; bias; redistribution; commercial use; temporal / OPE / recovery / shared-shock support.

## 1. LMSYS-Chat-1M

- **Why:** Real prompts and model identities, not designed around Mycelial.
- **Hypothesis:** Can structure-aware routing be evaluated on wild conversations? Mostly a **workload** source, not a preference bandit.
- **Observed:** conversation id, model name, conversation JSON, language, moderation tag.
- **Latent:** true quality, user intent, cost, latency, routing propensity.
- **Missing:** pairwise winner, prices, timestamps suitable for recovery, graph topology.
- **Transforms:** schema map to `routing_record` only after gated access; strip PII-sensitive fields.
- **Bias:** Vicuna demo / Arena users 2023; English-heavy; model mix obsolete.
- **Redistribution:** No. Gated LMSYS-Chat-1M Dataset License Agreement.
- **Commercial:** Conditional on that agreement.
- **Temporal / OPE / recovery / shared shock:** weak / no / no / no.

## 2. Chatbot Arena conversations (lmsys/chatbot_arena_conversations)

- **Why:** Human preference over two models for the same prompt.
- **Hypothesis:** Static routing quality, not non-stationary recovery.
- **Observed:** two models, votes, timestamp in original card, language.
- **Latent:** true quality, cost, latency, propensity of a logging policy.
- **Missing:** $p_t(a|x)$ unless a logging policy is reconstructed (usually impossible).
- **Transforms:** winner coding; timezone normalization.
- **Bias:** self-selected arena users; prompt contamination risk vs later models.
- **Redistribution:** Do not commit. Prompts CC-BY-4.0; model outputs CC-BY-NC-4.0 on the original card.
- **Temporal:** timestamps exist in the original description; still not an incident process.
- **OPE:** no propensities.
- **Recovery / shared shock:** no.

## 3. Arena human preference 55k (lmarena-ai/arena-human-preference-55k)

- **Why:** Compact preference table used by routing papers.
- **Hypothesis:** pairwise quality signal for candidate models.
- **Card license snapshot:** Apache-2.0 on the Hugging Face card. **This is not permission to vendor the corpus.** Third-party model outputs remain.
- **OPE / recovery:** no / no.
- **Contamination:** battle dates vs later model training must be recorded if used.

## 4. RouteLLM (software + datasets)

- **Why:** Independent routing methods as **adversaries**, not a Mycelial-designed benchmark.
- **Code license:** Apache-2.0 (`lm-sys/RouteLLM`).
- **Datasets:** inspect each `routellm/*` card. `routellm/gpt4_dataset` card snapshot Apache-2.0; GPT-4 judge terms still apply. **Do not commit.**
- **Hypothesis:** Does Mycelial beat published routers on *their* distribution?
- **Missing for our identity:** correlated non-stationarity, recovery time, hierarchical shocks.

## 5. RouterArena (RouteWorks/RouterArena)

- **Why:** External router leaderboard distribution (accuracy, cost, optimality, robustness, latency).
- **Code license snapshot:** Apache-2.0. **Dataset license is not assumed identical.**
- **Paper:** Lu et al., arXiv:2510.00202 (also an ICLR 2026 poster record on OpenReview).
- **Hypothesis:** external validity of routing quality/cost — **not** V1 RRT.
- **Do not** reshape their tasks into hierarchical shocks without documenting the transform as a new dataset.

## 6. Provider status histories

- **Why:** real temporal non-stationarity annotations.
- **Observed:** public incident windows, component names if published.
- **Not observed:** request-level latency, quality, causal labels.
- **Role:** `external_incident_annotation_not_causal_truth`.
- **Redistribution:** depends on each status-page ToS; default adapter-only.

## 7. Non-LLM traces (candidates, not ingested)

- Google Borg / cluster traces and Alibaba cluster traces can test structure-aware adaptation **outside** LLM routing if a service-dependency graph can be ethically reconstructed.
- Reject a trace that only adds volume without alternative actions, a reward proxy, and temporal order.

## First external priority

Prefer sources with many of: alternative actions, time, quality/reward, cost, latency, failures, structure, human preference, propensities, incident windows.

None of the LLM datasets above currently provide propensities **and** recovery **and** shared-shock labels. MG-EXP-REAL-001 must therefore start as **replay of preference or router-bench quality**, not as a fake V1 clone.
