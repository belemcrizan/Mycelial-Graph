# Resource Accounting Specification — Mycelial V2

## 1. Accounting Principle

Every token and resource unit consumed along an execution pathway **and** inside the routing controller itself is accounted for explicitly. A policy cannot claim token efficiency by hiding routing, retry, memory, verification, or state-maintenance overhead outside the ledger.

---

## 2. Token Buckets (`TokenUsage` & `TotalResourceLedger`)

Implemented in `src/mycelial_graph/v2/ledger/tokens.py` and verified step-by-step by `src/mycelial_graph/v2/audit.py`.

### 2.1 Billed Active Token Buckets (Additive Partition of `total_tokens`)

`total_tokens = path_tokens + overhead_tokens`, where:

- **`path_tokens`** (9 disjoint component buckets):
  1. `input_tokens` — prompt and model input tokens.
  2. `output_tokens` — model completion tokens.
  3. `reasoning_tokens` — extended chain-of-thought / reasoning tokens.
  4. `retrieval_tokens` — retriever query and passage injection tokens.
  5. `verification_tokens` — validator / guardrail inspection tokens.
  6. `tool_tokens` — tool invocation serialization and response tokens.
  7. `memory_tokens` — episodic/structural memory read-write tokens.
  8. `summarization_tokens` — context compression tokens.
  9. `retry_tokens` — extra tokens spent on local component retries.
- **`overhead_tokens`** (3 disjoint control-plane buckets):
  10. `router_tokens` — candidate scoring cost (`router_candidates * router_tokens_per_candidate`).
  11. `recovery_overhead_tokens` — explicit recovery/re-routing control tokens.
  12. `state_overhead_tokens` — graph state maintenance tokens per step.

### 2.2 Non-Double-Counted Telemetry Bucket

- `cached_tokens` — recorded separately in both `TokenUsage` and `TotalResourceLedger` for cache-hit auditing, and **never added twice** to `input_tokens` or `total_tokens`.

### 2.3 Non-Token Resource Counters & Efficiency Ratios

`TotalResourceLedger` additionally records:

- Invocation counts: `model_calls`, `tool_calls`, `retriever_calls`, `validator_calls`, `retry_count`, `fallback_count`.
- Continuous costs: `monetary_cost` (USD proxy), `latency_ms`, `policy_cpu_ms` (measured wall/CPU routing overhead in milliseconds).
- Post-shock window sub-totals: `post_shock_steps`, `post_shock_successes`, `post_shock_tokens`, `post_shock_cost`, `post_shock_latency_ms`.
- Task-normalized efficiency metrics:
  - **Tokens per Successful Task (`TPST`):** `total_tokens / max(successful_steps, 1)` (with `successful_steps == 0` flagged explicitly via `success_rate == 0.0`).
  - **Cost per Successful Task (`CPST`):** `monetary_cost / max(successful_steps, 1)`.

---

## 3. Hard Budget Reservation (`BudgetReservation`)

Implemented in `src/mycelial_graph/v2/resources/reservation.py`:

- Rejects `bool`, negative values, `NaN`, and `Inf` on creation, `reserve`, `commit`, and `release`.
- Enforces `spent + reserved <= cap` on every `reserve(amount)` call (`ReservationError` on violation).
- Computes `sustainable_step_allowance(steps_remaining) = remaining / max(steps_remaining, 1)` so `run_v2_method` and `MycelialResourceController` pace token expenditure across the horizon and automatically downgrade to minimal-token fallback pathways before exhausting `global_budget_tokens` or `scarce_budget_tokens`.

---

## 4. Candidate Routing Objectives

Mycelial V2 treats the scalarized objective as a **candidate formulation**, comparing it directly against constrained and Pareto-based alternatives (`src/mycelial_graph/v2/policies/controller.py`):

1. **Scalarized (`v2_mycelial`):**
   $$J_{\text{scalar}}(\pi) = \mathbb{E}[U(\pi)] - \lambda_t \mathbb{E}[\tilde{T}(\pi)] - \lambda_c \mathbb{E}[\tilde{C}(\pi)] - \lambda_l \mathbb{E}[\tilde{L}(\pi)] - \lambda_r \mathbb{E}[R(\pi)] - \lambda_f \mathbb{E}[F(\pi)] - \lambda_s \mathbb{E}[\tilde{S}(\pi)]$$
   where $\tilde{T} = T / 1000$, $\tilde{C} = C / 2.5$, $\tilde{L} = L / 1000$, $R = \min(1, \hat{f} + 0.35\,\hat{\sigma})$, and $F = \hat{f}$.
2. **Primal-Dual Constrained (`v2_constrained`):**
   Replaces fixed $\lambda_t$ with an online dual price $\mu_t \in [0.02, 4.0]$ updated via projected subgradient ascent $\mu_{t+1} = \Pi_{[0.02, 4.0]}(\mu_t + \eta_{\mu}(T_t - 0.85 B_{\text{step}}))$ to track changing budget pressure automatically.
3. **Pareto Non-Dominated Filter (`v2_pareto`):**
   Filters candidate transitions at each decision stage to the Pareto-efficient frontier over $(\hat{q} - \hat{f},\, -\tilde{T},\, -\tilde{C},\, -\tilde{L})$ before conductance-weighted tie-breaking.

In **all three** modes, safety constraints (`mandatory_verification`, `max_risk`, `minimum_quality`) and hard budget caps are enforced as **strict pre-routing filters**, never relaxed into soft penalty weights.

---

## 5. Mechanical Audit Invariants

Two CLI audits verify zero accounting drift on every experiment directory:

1. `mycelial-graph v2-resource-audit --output <dir>`: decompresses every `.jsonl.gz` trace and verifies exact equality across all 14 token buckets, `total_tokens`, `monetary_cost`, `latency_ms`, and step counts between step traces and trial `ledger` summaries.
2. `mycelial-graph waste-audit --output <dir>`: decomposes `ledger` tokens into `useful_tokens`, `avoidable_verification_tokens`, `unused_retrieval_tokens`, `failed_branch_tokens`, `retry_waste_tokens`, and `control_plane_tokens`, verifying the exact partition identity `useful_tokens + total_waste_tokens == ledger["total_tokens"]`.
