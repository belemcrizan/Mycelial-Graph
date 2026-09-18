# External OPE Pre-Registration (FROZEN, NOT AUTHORIZED)

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Protocol id:** `MG-EXP-EXTERNAL-OPE-001`
**Status:** `frozen` · `authorized: false` — scaffolding + pre-registration only.
**Interdict:** Infrastructure is not evidence. An adapter is not a reproduction. An OPE
*implementation* is not an OPE *result*. Nothing here promotes `external/` from infrastructure to
evidence until a human authorizes execution (MASTER_PROMPT §5.4).
**Existing infra referenced (read-only):** `src/mycelial_graph/external/ope.py`,
`src/mycelial_graph/external/adapters.py`, `external/schemas/logged_bandit.schema.json`,
`external/DATA_SOURCES.md`, `external/README.md`.
**Companion:** `docs/EXTERNAL_VALIDATION_LADDER.md`.

---

## 0. Purpose and hard limits

Convert `external/` from infrastructure into *bounded evidence* by pre-registering how logged-bandit
data would be replayed through the **existing IPS/SNIPS/DR estimators**, **without any paid provider
call and without collecting real user data**, until human authorization is recorded.

- **No paid calls. No real-data collection. No fixture-as-evidence.** Fixtures and dry-runs validate
  the pipeline; they never count as external validity.
- Each source below is annotated with **which sub-claim it can support** and **its explicit limit**.
- Execution on real logged data is a **human gate** (MASTER_PROMPT §5.4) and requires the moratorium
  amendment.

## 1. Estimand and estimators (pre-registered)

- **Target:** value/recovery of a routing policy under logged bandit feedback, estimated off-policy.
- **Estimators (already implemented in `ope.py`):** IPS, SNIPS (self-normalized IPS), and DR
  (doubly-robust). Chosen per source by **propensity availability** (see validity criteria §3).
- **Validity criteria (frozen, checked before any value is reported):**
  1. Logging propensities `p_t(a|x)` are known (true) or uniformly random — otherwise IPS/DR are
     invalid and the source is **replay-only / descriptive**, not OPE.
  2. Common support (overlap) between logging and target policies is checked and reported; ESS
     (effective sample size) and max importance weight are logged.
  3. Estimator agreement (IPS vs SNIPS vs DR) is reported; disagreement is a validity flag, not
     silently averaged.
  4. No method retuning against any single external source (overfitting control, per
     `research/EXTERNAL_VALIDATION_PLAN.md`).

## 2. Node/edge → logged-bandit mapping (pre-registered)

The MG routing DAG maps to a logged-bandit record via `external/schemas/logged_bandit.schema.json`:

- **context `x`** ← task/prompt features (source-specific).
- **action `a`** ← selected arm/route (an edge/path in the MG DAG).
- **propensity `p(a|x)`** ← logging policy probability (true, uniform, or ex-ante, per source).
- **reward `r`** ← logged outcome (click/CTR, quality, cost-adjusted quality).
- **time `t`** ← native timestamp / round index (for recovery and change-point analysis).

Semi-synthetic shock injection (Layer 2) is declared as such and never mixed with natural
change-points (Layer 1) in the same reported estimate.

## 3. Source → sub-claim → limit table (pre-registered)

### Layer 1 — Recovery (OPE-valid, free) — highest priority

| Source | Access | Propensity | Sub-claim it supports | Explicit limit |
|---|---|---|---|---|
| **Open Bandit Dataset (ZOZO)** | `obp` | **true** propensities | Valid IPS/DR value estimate; matches V1's structured SW-UCB condition | Fashion recommendation, not routing; no DAG/pooling structure; no hierarchical shock |
| **Yahoo! Front Page R6A/R6B** | gated request | **uniformly random** logging | Unbiased replay; **natural** change-points (article CTR rise/fall) → real recovery measurable | No ρ control; no shared-shock structure; news domain |
| **Criteo logged bandit** | public | ex-ante propensity | Scale backup for IPS | Display-ads, not routing; weak temporal/recovery structure |

### Layer 2 — Real reward geometry (semi-synthetic) — shock injected

| Source | Access | Sub-claim it supports | Explicit limit |
|---|---|---|---|
| **RouterBench** (~405k, 11 LLMs, 7 tasks, cost+quality) | public card | Real cost/quality geometry for the "model" node; controllable ρ via injected shock | Shock is **semi-synthetic** (injected); not a natural non-stationarity |
| **RouterEval** (~200M, ~8500 LLMs) | public card | Scale of real geometry | Same injected-shock limit; heavy |
| **SPROUT** (~44k prompts, 13 models) | public card | Real geometry, smaller | Injected shock; limited models |
| **LLMRouterBench** (~400k, 21 datasets, 33 models) | public card | Real geometry, broad tasks | Injected shock |
| **BEIR / MS MARCO** | public | Real geometry for the "retriever" node | IR relevance, not bandit reward; injected shock |

### Layer 3 — Pooling structure & shock topology

| Source | Access | Sub-claim it supports | Explicit limit |
|---|---|---|---|
| **HPO-B / YAHPO Gym / OpenML** | public | Real multi-stage pipelines with **shared components** → faithful structural ρ | Not routing reward; validates topology/ρ instantiation, not RRT estimand |
| **Cluster traces (Google Borg / Alibaba)** | public | Real shared-vs-local topology (zone failure = high ρ; node failure = ρ=0) | Validates topology only, **not** the reward estimand |
| **Vivo/Telefónica telemetry (ceiling option, author domain)** | governed | Highest-fidelity backbone/POP/zone (shared) vs single-link (local) distinction | Governance + anonymization required; **not** authorized; not in repo |

## 4. What is Permitted-Now vs Human-Authorization

- **Permitted-Now (this artifact):** the pre-registration, the mapping, the estimator/validity
  criteria, and the source→sub-claim→limit table. Pipeline dry-runs on **fixtures only**.
- **Human-Authorization (MASTER_PROMPT §5.4):** unfreezing `external/`, ingesting any real logged
  data, running OPE that produces a *reported value*, or any networked/paid access.

## 5. Anti-overclaim guard (pre-registered)

A reported external result may **not** claim: production readiness, universal superiority, a causal
mechanism, independent reproduction, or that a semi-synthetic shock is a natural one. Every reported
number carries its source's row from §3 (sub-claim + limit) attached.

## 6. Honest status

- **Added:** this pre-registration (frozen) + the ladder doc.
- **Staged:** real-data OPE execution (`authorized: false`).
- **Unchanged / preserved:** `external/` remains infrastructure; no data ingested; no paid call;
  the V1 freeze, `REFUTED`, and moratorium are untouched.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
