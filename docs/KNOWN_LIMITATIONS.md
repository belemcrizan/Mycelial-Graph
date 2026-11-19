# Known Limitations & Scientific Boundaries

This document states what Mycelial-Graph **cannot** currently claim and documents known technical, statistical, and operational boundaries.

---

## 1. Frozen V1 Limitations (Preserved)

1. **Primary hypothesis `REFUTED`:** Under the frozen `MG-EXP-V1` protocol ($N = 97$, $\rho = 0.50$), `hierarchical` recovered `+42.1%` slower than `edge_only` (95% CI `[+11.9%, +79.1%]`), and failed the $\rho = 0$ non-inferiority gate (`+16.3% > +10.0%`).
2. **Effective policy scale confound (`EQ-B`):** As quantified in `docs/research/FAILURE_ANALYSIS.md`, `EdgeOnlyAgent` integrates unbounded centered rewards (`std = 0.510`) whereas `HierarchicalAgent` uses self-limiting clipped TD residuals (`std = 0.0422`, `12.08x` narrower) under an identical softmax `temperature = 0.20`, accounting for ~`76%` of the RRT gap, with `source_effect[u]` softmax cancellation and outgoing-edge shock leakage into `target_effect[w]` accounting for the remaining ~`24%`. Consequently, the V1 refutation applies to the **complete frozen policy mechanism**, not to hierarchical representation in isolation.
3. **Submission moratorium:** Under `V1_CONFIRMATORY_MORATORIUM.md` and `research/state.json`, Paper A (`paper/tmlr/paper.tex`) is **not yet submitted**, and `moratorium.active = true` remains in effect until Paper A has been submitted and submission state/receipt has been recorded.

---

## 2. Mycelial V2 (`MG-EXP-V2.2`) Limitations

1. **Pilot & development evidence only (non-confirmatory):** All `MG-EXP-V2.2` benchmarks (`experiments/v2_2/PILOT_SUMMARY.json`) are executed on `development` ($N = 10$) and `pilot` ($N = 24$) seed sets. `experiments/v2_2/seeds.confirmatory.txt` remains intentionally unmaterialized (`FREEZE_STATUS.json`: `"authorized": false`). No confirmatory claim is made for V2.
2. **Synthetic potential-outcome simulator:** V2 scenarios model heterogeneous prompt/retriever/model/validator/tool pipelines with controlled Beta/LogNormal noise and structured shock regimes (`STATIC`, `PRICE_SHOCK`, `QUALITY_SHOCK`, `OUTAGE`, `LOCAL_OUTAGE`, `MIXED_CORRELATION`, `RETRIEVER_COLLAPSE`, `RESOURCE_SCARCITY`). Synthetic effectiveness does **not** establish generalization to live commercial LLM APIs, production traffic distributions, or SWE-bench-scale repositories.
3. **Regime-dependent mechanism tradeoffs (no universal silver bullet):**
   - **Anastomosis (`v2_no_anastomosis` contrast):** Discrepancy gating blocks extreme negative transfer when sibling transitions diverge (`LOCAL_OUTAGE`), and accelerates sibling awareness under correlated component failure (`OUTAGE`), but provides near-zero lift in purely stationary or single-path price-only shocks (`STATIC`, `PRICE_SHOCK`) once initial exploration has visited alternatives.
   - **Cytoplasmic retraction (`v2_no_pruning` contrast):** Reduces `router_candidates` and `router_tokens` on larger/wider graphs by pruning persistently dominated corridors, while retaining a $3\%$ rehabilitation probe. If a previously retracted edge suddenly becomes the *only* newly healed optimum without triggering shock surprise on active edges, rehabilitation lags by up to expected $1 / 0.03 \approx 33$ multi-candidate steps.
   - **Branching exploration (`v2_no_branching` contrast):** VoI exploration discovers post-shock alternatives faster under `OUTAGE` and `QUALITY_SHOCK`, at the cost of non-zero exploratory token/quality regret during `STATIC` operation.
   - **Constrained & Pareto modes (`v2_constrained`, `v2_pareto`):** `v2_constrained` adapts its dual token price smoothly over medium horizons (`>= 40` steps) but exhibits transient dual-price lag over ultra-short horizons (`< 10` steps); `v2_pareto` preserves diverse non-dominated options without weight tuning on cost vs. latency, which can retain higher-token high-quality routes unless combined with hard step caps.
4. **Local coding smoke track (`v2/real/`):** `mycelial-graph real-smoke` executes genuine AST-based hypothesis generation and test grading in a temporary directory without oracle injection, but covers only small deterministic Python repair fixtures using a whitespace token proxy — not live LLM code generation.
5. **External adapters & OPE (`external/`):** `ProviderAdapter`, `DeterministicMockProvider`, and `external/ope.py` (IPS + SNIPS) provide verified offline interfaces and unbiased estimator math, **not** empirical live-provider or logged-bandit benchmarks.
6. **Cross-platform bitwise floating-point identity:** Byte-exact `.jsonl.gz` trace reproduction is verified within a fixed OS/Python/NumPy stack; cross-OS/cross-BLAS IEEE-754 transcendental rounding is not claimed to be bit-identical without tolerance.
7. **Not production-ready:** Mycelial-Graph is a research codebase for reproducible algorithmic auditing, not a hardened multi-tenant production serving gateway.
