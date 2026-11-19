# Forensic Repository Audit — `Mycelial-Graph`

- **Repository:** `belemcrizan/Mycelial-Graph`
- **Baseline Commit Audited:** `ad3658c9c5f9698816c6553c3ae17de7a38e25b5` (`main`, clean working tree)
- **Audit Branch:** `feat/v2-engineering-recovery-evolution`
- **Audit Environment:** Python `3.13.3`, NumPy `2.2.6`, SciPy `1.15.3`, PyYAML `6.0.2`, pytest `9.1.1` (Windows `AMD64`, offline sandbox)
- **Baseline Test Execution:** `176 / 176` existing tests passing (`python -m pytest -v`)
- **Canonical V1 Confirmatory State (Verified & Preserved):** `confirmatory.executed = true`, `confirmatory.status = REFUTED` ($\Delta\text{RRT} = +42.1\%$ at $\rho = 0.50$, 95% CI $[+11.9\%, +79.1\%]$, $N = 97$ paired scenarios; $\rho = 0$ safety gate failed with upper bound $+16.31\% > +10.0\%$), `equalization_triage.status = EQ-B`, `paper_a.submitted = false`.

> **Methodological Rule:** Every finding below is verified directly against checked-out source files, committed JSON/YAML manifests, Git blob hashes, and executed commands. Confirmed software/mathematical defects are explicitly separated from frozen V1 design confounds (which are preserved untouched to protect historical confirmatory reproducibility) and suspected/open research limitations.

---

## 1. Architecture, Execution Entry Points & Stack Inventory

The repository (`src/mycelial_graph/`, version `0.2.2`) is not a single unified engine; it contains **three coexisting simulation/routing stacks** plus three auxiliary modules sharing a single Python package namespace:

### 1.1 Entry Points
- **CLI (`mycelial-graph` -> `src/mycelial_graph/cli.py:main` and `python -m mycelial_graph`)**:
  - **V1 lifecycle commands:** `validate`, `experiment`, `analyze`, `report`, `sample-size`, `validate-artifacts`, `seal-artifact`, `verify-seal`, `demo`, `bind-run`.
  - **V2 / V2.1 lifecycle commands:** `v2-validate`, `v2-experiment`, `v2-analyze`, `v2-report`, `v2-demo`, `v2-ablate`, `v2-pareto`, `v2-resource-audit`, `voc-bench`, `budget-curve`, `waste-audit`, `real-smoke`, `shadow-run`.
  - **Governance / auxiliary commands:** `claim-audit`, `collect`, `ope-check`, `pooling-toy`, `evidence-audit`.
- **Standalone verification & build scripts:**
  - `reproduce_confirmatory.py`: Sealed-hash verification (default) and `--full` 1,940-trial confirmatory replay.
  - `scripts/audit_v1_readiness.py`: Pre/post-confirmatory mechanical readiness audit.
  - `scripts/reproduce_v1.py`, `scripts/seal_v1_confirmatory.py`, `scripts/paper_a_diagnostics.py`, `scripts/paper_a_figures.py`, `scripts/record_evidence.py`, `scripts/generate_design_pdf.py`, `paper/submission/build_anonymous_zip.py`.

### 1.2 Stack Comparison & Module Duplication Map

| Subsystem | V0 Legacy Stack (Top-Level) | V1 Confirmatory Stack | V2 / V2.1 Experimental Stack | Duplication & Divergence Assessment |
|---|---|---|---|---|
| **Config & Types** | `config.py` (`FrozenConfig`, `load_config`, `validate_config`) | `types.py` (`ExperimentConfig`, `load_config`), `validation.py` (`validate_config`), `protocol.py` | `v2/types.py` (`V2ExperimentConfig`), `v2/config.py`, `v2/validation.py` | **Direct name collision** between `config.{load_config,validate_config}` and `types.load_config` / `validation.validate_config` with incompatible return types. V0 has no CLI entry point. |
| **Graph Model** | `graph.py` (`LayeredGraph`, `Component`, `Edge(str,str,str)`, `HardPolicy`) | `environment/graph.py` (`LayeredDAG`, `Edge(int,int,int)`) | Reuses V1 `LayeredDAG.complete_layered(3, k)` + positional labels in `v2/environment/roles.py` | V0 had heterogeneous component layers and `HardPolicy` pre-filtering; V1/V2 `LayeredDAG` restricts topology to uniform complete bipartite internal layers (`[1, k, ..., k, 1]`), with V2 hardcoding `internal_layers == 3`. |
| **Environment / Scenarios** | `trial.py` (`FrozenTrial`, `certify_trial`) | `environment/scenario.py` (`Scenario`, `generate_scenario_family`) | `v2/environment/scenario.py` (`ResourceScenario`, `generate_resource_scenario`) | V1 has immutable byte-backed NumPy potential-outcome arrays and certified unique optima across $\rho \in \{0, 0.25, 0.5, 0.75, 1.0\}$. V2 adds 12 named shock regimes (`PRICE_SHOCK`, `QUALITY_SHOCK`, `OUTAGE`, etc.) and token/latency/cost/failure draws, but omits optimum-margin certification and couples edge attributes solely to target alternative index $\in \{0,1,2\}$. |
| **Policies & Baselines** | `routing.py` (`MycelialRouter`, `StructuredSemiBanditRouter`, `ReactiveShortestPathRouter`) | `agents/` (`edge_only`, `node_only`, `hierarchical`, `structured_sw_ucb`, `_routing.py`) | `v2/policies/` (`controller.py`, `baselines.py`, `baselines_strong.py`, `factory.py`, `oracle.py`) + `v2/biology/` | V1 policies are behaviorally frozen for historical reproduction. V2 adds 16 baseline/ablation names plus 7 `baselines_strong.py` policies, but 5 ablations are unimplemented aliases and several baselines contain severe behavioral bugs (see Section 3). |
| **Resource Accounting** | Scalar `cost_usd` & `latency_ms` per component | Decision CPU seconds only (`decision_cpu_seconds`) | `v2/ledger/tokens.py` (`TokenUsage`, `TotalResourceLedger`), `v2/resources/reservation.py`, `v2/evaluation/waste.py`, `v2/audit.py` | `TokenUsage` tracks 9 token buckets (`input`, `output`, `cached`, `reasoning`, `estimated`, `router`, `verification`, `tool`, `retrieval`, `summarization`), monetary cost, and latency, but `BudgetReservation` is dead code and `TotalResourceLedger` drops `cached_tokens` / `estimated_tokens` and misaligns `state_overhead_tokens` per step. |
| **Orchestration & Analysis** | `experiment.py`, `report.py` | `runner/{seeding,checkpoint,trial,experiment}.py`, `analysis/`, `reporting/report.py`, `artifacts.py` | `v2/seeding.py`, `v2/runner/{trial,experiment}.py`, `v2/analysis.py`, `v2/reporting.py`, `v2/metrics/` | V1 has atomic checkpoints (`fsync` + `os.replace`), deterministic gzip (`mtime=0`), single-writer `.execution.lock`, and seal verification. V2 omits deterministic gzip `mtime=0`, `.execution.lock`, and per-bucket trace reconciliation. |
| **Auxiliary Modules** | — | `science/` (canonical bytes, claim guard, freeze, state invariants) | `v2/real/` (2-fixture local AST repair smoke), `pooling/` (Gaussian EB toy), `external/` (schema/adapter/IPS OPE) | Properly separated from V1 confirmatory inference, though `external/ope.py`, `external/schemas.py`, `pooling/`, and `v2/real/` contain confirmed mathematical/implementation defects. |

---

## 2. Scientific Integrity, Frozen Boundaries & Reproducibility Assessment

### 2.1 Immutable Artifacts & Behavioral Freeze Boundaries
To preserve scientific integrity and ensure `python reproduce_confirmatory.py` and all 176 baseline tests remain green, the following boundaries are enforced mechanically:
1. **Byte- & EOL-Locked V1 Confirmatory Artifacts (`DO NOT MODIFY`):**
   - `experiments/v1/artifacts/confirmatory/{CONFIRMATORY_EVIDENCE.json, CONFIRMATORY_REPRODUCTION_SUPPLEMENT.json, REPORT.md, analysis.json, manifest.json, figures/*.png}`
   - `experiments/v1/artifacts/{CONFIRMATORY_FREEZE.json, CONFIRMATORY_FREEZE_SUPPLEMENT.json, PILOT_EVIDENCE.json, analysis.json, sample_size.json}`
   - `experiments/v1/{config.confirmatory.yaml, config.pilot.yaml, config.development.yaml, seeds.confirmatory.txt, seeds.confirmatory.pool.txt, seeds.pilot.txt, seeds.development.txt, EXPERIMENT_PROTOCOL_V1.md, ANALYSIS_PLAN.md, SAMPLE_SIZE_ADDENDUM.md, AMENDMENT_001.md, AMENDMENT_002.md, HYPOTHESIS_MATRIX.md}`
2. **Behaviorally Frozen V1 Simulation Path (`DO NOT ALTER NUMERICAL OUTPUTS`):**
   - `src/mycelial_graph/{types.py, validation.py}`, `src/mycelial_graph/environment/{graph.py, scenario.py}`, `src/mycelial_graph/agents/*.py`, `src/mycelial_graph/runner/{seeding.py, trial.py, experiment.py}`, `src/mycelial_graph/analysis/{metrics.py, bootstrap.py, result_state.py, aggregate.py}`.
   - Moreover, `scripts/audit_v1_readiness.py` diffs `V1_SOURCE_PATHS` against `pilot_code_commit_at_execution` (`2c0a9630ae97`). Touching V1 simulator files without accounting for provenance checks triggers Class C `F-PROV-02` (see `AUD-CRIT-01`).
3. **Canonical State & Staged Gate Invariants (`tests/test_canonical_state_invariants.py`, `tests/test_scientific_state.py`):**
   - `research/state.json` and the `<!-- canonical-scientific-state ... -->` header in `README.md` must preserve `confirmatory.executed=true`, `confirmatory.status=REFUTED`, `confirmatory.n=97`, `equalization_triage.status=EQ-B`, `paper_a.submitted=false`, and `moratorium.active=true` (reflecting the Paper A OpenReview submission lock).
   - `experiments/v1_5/config.equalized.yaml`, `external/protocols/EXTERNAL_OPE_PREREG.md`, `experiments/PROTOCOL_AMENDMENT_002_PROPOSAL.md`, and `docs/claim_evidence_matrix.yaml` must keep their unauthorized/staged markers intact.

### 2.2 Reproducibility Guarantees & Historical Caveats
- **V1 Confirmatory Reproducibility:** Strong. `SeedSequence(seed).spawn(2)` separates world parameter generation from observation noise; SHA-256 namespace seeding (`mycelial-graph-v1:{seed}:agent:{rho:.8f}:{method}`) isolates agent RNG streams across methods and parallel workers (`test_parallel_matches_every_trace_byte`). Historical CRLF-vs-LF text seal differences (`REPORT.md`, `manifest.json`, `processed/analysis.json`, `seeds.confirmatory.txt`) are explicitly handled and verified by `science/canonical_bytes.py`.
- **Historical `outputs/demo/` Discrepancy (Verified, Preserved Untouched):** `outputs/demo/manifest.json` lists 125 files with Windows backslash paths; 100 `.jsonl.gz` traces match raw SHA-256 exactly, 25 `raw/rho-*/seed-*.json` files match after LF->CRLF normalization, and 8 extra files (`REPORT.md`, `processed/analysis.json`, 2 figures, `manifest.json`, plus 3 leftover V0 files `frozen_config.yaml`, `results.json`, `trials/trial_seed_101.json.gz`) sit alongside them. Per `README.md` and `ENGINEERING_DEBT.md` (`E08`), `outputs/demo/` is preserved untouched as a historical artifact.
- **V2 Reproducibility Gaps:** V2 `.jsonl.gz` traces use `gzip.open(..., "wt")` without `mtime=0`, embedding wall-clock timestamps into trace file bytes (`AUD-HIGH-06`), and unimplemented ablation names derive distinct RNG seeds from `method_name`, creating deterministic but scientifically spurious differences (`AUD-CRIT-03`).

---

## 3. Prioritized Issue Register — Confirmed Defects

### Summary Table

| ID | Severity | Subsystem | Summary | Fixable Without Touching Frozen V1? |
|---|---|---|---|---|
| `AUD-CRIT-01` | **Critical** | V1 Audit / CI | `scripts/audit_v1_readiness.py` fails (`decision: "STOP"`, exit code `3`) in any full Git clone due to post-pilot integrity merge diff (`F-PROV-02`), checks raw LF SHA-256 instead of canonical seed SHA-256, and writes CRLF dirtying tracked files on Windows | **Yes** (`scripts/audit_v1_readiness.py`) |
| `AUD-CRIT-02` | **Critical** | V2 Resource / Routing | Total absence of budget enforcement; `self.budget` and `translocate()` are 100% dead epiphenomenal state (`RESOURCE_SCARCITY`, `budget-curve`, and `v2_no_transfer` are no-ops; `BudgetReservation` is dead code) | **Yes** (V2 stack) |
| `AUD-CRIT-03` | **Critical** | V2 Ablations | Five `SUPPORTED_METHODS` ablations (`v2_no_branching`, `v2_no_anastomosis`, `v2_no_uncertainty`, `v2_static_topology`, `v2_no_shock_memory`) are `{}` clones of `v2_mycelial` producing spurious RNG-seed differences | **Yes** (V2 stack) |
| `AUD-CRIT-04` | **Critical** | V2 Safety / Guardrails | Hard safety constraints (`mandatory_verification`, `minimum_quality`, `max_risk`) are violated by softmax/exploration, checked on only 1 of 3 model nodes, and mutate `conductance` inside `choose()` | **Yes** (V2 stack) |
| `AUD-CRIT-05` | **Critical** | V2 Baselines | `AdaptiveEarlyStop` compares cross-node edge IDs (`12` and `20` while routing via node `5`'s edges `15..17`, degenerating to uniform random); `UncertaintyThresholdRouter` is permanently stuck on frontier compute; `StructuredSWUCBResource` lacks node-edge structure | **Yes** (V2 stack) |
| `AUD-CRIT-06` | **Critical** | V2.1 VOC / Real | $1000\times$ token-scale unit mismatch in `run_voc_benchmark` (`voc-bench`) and `v2/real/controller.py` passes raw tokens against per-1k `lambda_tokens`, making `voc.difference < -40` (`allocated=False` 100% of the time) | **Yes** (V2 stack) |
| `AUD-CRIT-07` | **Critical** | External OPE | `ips_estimate` (`external/ope.py`) drops zero-target-propensity samples from denominator $n$ and flags them as `support_violations`, inflating IPS estimates by $K\times$; `target_propensity=None` sets $\sum_a \pi(a) = K > 1$ | **Yes** (`external/ope.py`) |
| `AUD-HIGH-01` | **High** | V2 Estimand / Oracle | `ResourceScenario.expected_path_quality` and `_path_quality` ignore `fail_prob` (`quality *= 0.25` on failure), crediting `99%`-failing edges with full pre-failure quality in `post_quality` and `TotalResourceLedger` | **Yes** (V2 stack) |
| `AUD-HIGH-02` | **High** | V2 Adaptation | `MycelialResourceController` uses stationary $1/n$ sample means (`quality_hat`, `token_hat`, `cost_hat`, `latency_hat`, `fail_hat`), collapsing post-shock learning rate to $O(1/T_{\text{pre}})$ | **Yes** (V2 stack) |
| `AUD-HIGH-03` | **High** | V2 Pruning | `update_prune_evidence` increments evidence on unvisited steps without new observations, lacks an `s-t` connectivity / last-outgoing-edge guard, ignores monetary price shocks (`cost_norm`), and still bills full `router_tokens` | **Yes** (V2 stack) |
| `AUD-HIGH-04` | **High** | V2 Conductance / Translocation | `update_conductance` decays unvisited backup paths toward `0.0` (instead of `initial_conductance`) and rewards raw traversal frequency (`+0.05` even on failed edges); `translocate` multiplicative renormalization violates its own `floor` and runs twice per step | **Yes** (V2 stack) |
| `AUD-HIGH-05` | **High** | V2 Analysis Gates | `v2/analysis.py` ignores `engineering_token_gate` (`0.10`) and `mmrr` (`0.05`), and `_label()` mixes 90%/95% interval bounds causing misclassified `PASS`/`INCONCLUSIVE` states and dead code | **Yes** (V2 stack) |
| `AUD-HIGH-06` | **High** | V2 Ledger / Traces / Gzip | Trace `token_usage.total_tokens` omits `state_overhead_tokens` (mismatching `record.total_tokens` on every step); `TotalResourceLedger` drops `cached_tokens`/`estimated_tokens` and hardcodes `model_calls=1, tool_calls=1`; `_write_trace` omits `mtime=0` (non-deterministic `.jsonl.gz` bytes); `reporting.py` mixes post-shock and full-horizon token means | **Yes** (V2 stack) |
| `AUD-HIGH-07` | **High** | Claims & Docs Consistency | `CLAIMS.md` and `research/claims.json` still list V1 C1 and C2 as `NOT YET VALIDATED` / `No verified supporting artifact` (contradicting `REFUTED`); `research/CLAIMS.md` C01 says `CONFIRMATORY locked`; `CHANGELOG.md:19`, `FAILURE_MODES.md`, `docs/ROADMAP.md`, `REPRODUCIBILITY.md`, `docs/QUICKSTART.md`, and `CITATION.cff` contain confirmed contradictions or duplicate YAML keys | **Yes** (Docs / JSON) |
| `AUD-MED-01` | **Medium** | Windows Test Hygiene | `tests/test_scientific_state.py` rewrites `research/state.json` and `research/runtime.json` in `finally:` without `newline="\n"`, dirtying the Git working tree with CRLF on Windows every time `pytest` runs; `reproduce_confirmatory.py` overwrites tracked `REPRODUCTION_REPORT.md` on read-only runs | **Yes** (`tests/`, script) |
| `AUD-MED-02` | **Medium** | Pooling Module | `pooling/empirical_bayes.py` underestimates `within_var` (`ddof` over $Kn-1$ instead of $K(n-1)$); `pooling/toy_model.py` passes observation variance $\sigma^2$ instead of mean variance $\sigma^2/n$ into `pooling_weight_from_variances` ($40\times$ pooling inflation) and lacks `rho in [0,1]` validation | **Yes** (`pooling/`) |
| `AUD-MED-03` | **Medium** | External Schemas & Adapters | ISO-8601 lexicographic string comparison rejects valid fractional-second end timestamps (`"00:00:00.500000Z" < "00:00:00Z"`); negative UTC offsets rejected; Python `bool` accepted as `int`/`float` timestamp/propensity; `NaN`/`Inf` rewards accepted | **Yes** (`external/`) |
| `AUD-MED-04` | **Medium** | V2 Waste / Real Smoke | `waste.py` subtracts `input_tokens` from `retrieval // 2` (collapsing `reingested_context_tokens` to `0`); `v2/real/` executes without budget reservation, bills `STOP` after `BUDGET_EXHAUSTED`, and `hypothesize.py` emits broken indentation on multi-line functions and drops multi-arg signatures | **Yes** (`v2/`) |
| `AUD-MED-05` | **Medium** | Config Validation & CLI | `v2/validation.py` misses bounds on `temperature > 0`, probabilities $\in [0,1]$, budgets $> 0$, and `bool`-as-`int`; `cli.py` `voc-bench`/`budget-curve` crash on `#` seed comments, `collect --dry-run` cannot be disabled, and `validate`/`v2-validate` return exit code `1` (crash) instead of `2` (JSON) on malformed YAML | **Yes** (`v2/`, `cli.py`) |
| `AUD-LOW-01` | **Low** | Reporting / V0 / Scripts | `reporting/report.py` emits duplicate `**Run kind:**` and unseparated Markdown table; `runner/trial.py:source_tree_hash` uses OS-specific path separators (diverging from `artifacts.source_digest` outside Git); V0 `experiment.py` has survivorship bias on `cpst_usd = inf` and hardcoded `[3]` in `report.py`; `scripts/record_evidence.py` omits `encoding="utf-8"` and points to wrong ledger path | **Yes** (Targeted fixes) |

---

### Detailed Defect Records

#### `AUD-CRIT-01` — `scripts/audit_v1_readiness.py` Fails (`STOP`, Exit Code 3) in Full Clones & Corrupts Tracked Files on Windows
- **Severity:** Critical (Confirmed Defect)
- **Affected files:** `scripts/audit_v1_readiness.py` (L651–697, L824–828, L1183–1204)
- **Reproduction steps:**
  1. Clone the repository with full Git history (`git clone ...`) and run `python scripts/audit_v1_readiness.py`.
  2. Observe exit code `3` with `{"decision": "STOP", "findings": {"A": 6, "B": 2, "C": 1}}` (`F-PROV-02`), `"states_seed_hash": false` in `CONFIRMATORY_READINESS_REPORT.json`, and `git status` showing CRLF modifications to `CONFIRMATORY_READINESS_REPORT.{json,md}`.
- **Root cause:**
  1. GitHub Actions CI (`actions/checkout@v4`) uses shallow checkout (`fetch-depth: 1`), where `pilot_code_commit_at_execution` (`2c0a9630ae97`) is unreachable (`has_pilot_commit == False`), masking `F-PROV-02` in CI. In a full clone, `git diff 2c0a9630..HEAD` flags post-confirmatory evidence/reproduction hardening merges (`f8dd7ec`, `2f310a4`) even though confirmatory was already executed and sealed at `5f314d2` and all pilot/confirmatory scenario hashes reproduce identically.
  2. Line 824 uses raw `sha256_file(V1 / "seeds.confirmatory.txt")` (returning LF blob hash `2198ac5f...`) instead of canonical `frozen_text_input_sha256` (`8ef4c6b0...`), causing `states_seed_hash` (`seed_hash in readme`) to evaluate to `False`.
  3. Line 1186 claims `"Selective unfreezing may begin"`, contradicting `V1_CONFIRMATORY_MORATORIUM.md`, and lines 1197–1202 call `write_text()` without `newline="\n"` or `--write` opt-in.
- **Evidence:** Verified directly during Phase 0 baseline check (`task-47` / `step-79` diff).
- **Proposed correction:** Distinguish pre-confirmatory source changes (`pilot_commit..5f314d2`, which is empty!) from post-seal maintenance commits (`5f314d2..HEAD`) verified by scenario/evidence hash reproduction; check canonical `freeze["seeds_sha256"]` in `README.md`; align `next_permitted_action` with active moratorium state; write LF-only (`newline="\n"`) and add `--check` / non-mutating mode or deterministic LF output.
- **Regression test:** Test running `audit_v1_readiness` in the full Git clone asserting `decision == "GO"`, `states_seed_hash is True`, and LF-only output.
- **Scientific/operational impact:** Restores reproducibility of the canonical readiness audit in full Git clones without weakening pre-execution provenance checks.

---

#### `AUD-CRIT-02` — Unenforced Resource Budgets & Epiphenomenal `translocate()` State in V2
- **Severity:** Critical (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/policies/controller.py` (L50, L65–96, L129–159, L234–240), `src/mycelial_graph/v2/runner/trial.py` (L118–120), `src/mycelial_graph/v2/environment/scenario.py` (L246–248), `src/mycelial_graph/v2/evaluation/budget_curves.py` (L14–33), `src/mycelial_graph/v2/resources/reservation.py` (L1–57)
- **Reproduction steps:**
  1. Run `quality_at_budget(config, "v2_mycelial", budget=10, seed=7103, regime="STATIC", ...)` and `budget=1_000_000`: both return identical `quality` and identical `tokens` (`>> 10`).
  2. Instantiate two `MycelialResourceController` instances with identical `rng` seeds, one with `transfer=True` and one with `transfer=False`: every chosen path, edge score, and token expenditure is bit-for-bit identical.
- **Root cause:** `self.budget` is updated by `translocate()` and checked by `assert_budget_conserved()`, **but never read in `_score()`, candidate filtering, or `runner/trial.py`**. `trial.py:118` passes the static initial cap (`scenario.budget_cap(step)`) every step without subtracting spent tokens or reserving path upper bounds, and `BudgetReservation` (`v2/resources/reservation.py`) is never imported by any runner or policy.
- **Evidence:** Code inspection of `controller.py` and `trial.py`; `grep` across `src/` confirms zero call sites for `BudgetReservation` outside tests.
- **Proposed correction:** Wire `BudgetReservation` / remaining trial & per-step token/cost budgets into V2 graph execution (`G = (V, E, S, B, H)`), enforce hard feasible-path budget checks with safe low-compute fallback before action execution, and connect `translocate()` corridor allocations directly to per-pathway exploration/spend envelopes in V2 routing.
- **Regression test:** Unit tests proving (a) tightening `global_budget_tokens` monotonically bounds total spent tokens via `BudgetReservation` with zero silent overruns, (b) `RESOURCE_SCARCITY` shifts pathway selection relative to `STATIC`, and (c) `transfer=True` vs `transfer=False` produces distinct behavior under identical RNG seeds.
- **Scientific/operational impact:** Previously invalidated `v2_no_transfer`, `RESOURCE_SCARCITY`, and `budget-curve` claims by mistaking dead state and RNG-seed divergence for resource translocation.

---

#### `AUD-CRIT-03` — Unimplemented V2 Ablation Aliases Masquerading as Executed Treatments
- **Severity:** Critical (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/policies/factory.py` (L27–33, L75–85), `src/mycelial_graph/v2/validation.py` (L19–23), `src/mycelial_graph/v2/runner/trial.py` (L108, L194), `src/mycelial_graph/cli.py` (L207–223)
- **Reproduction steps:** Configure `methods: [v2_mycelial, v2_no_branching, v2_no_anastomosis]` and run `v2-experiment` + `v2-ablate`. `v2-ablate` outputs distinct quality/token metrics for all three methods even though all three instantiate `MycelialResourceController(config, len(graph.edges), rng, **{})`.
- **Root cause:** `UNIMPLEMENTED_ALPHA_ALIASES` instantiates vanilla `MycelialResourceController` and sets `agent.unimplemented_alias = True`, which is never checked anywhere, while `trial.py:108` hashes `method_name` into the RNG stream (`f"agent:{scenario.regime}:{method_name}"`).
- **Evidence:** `factory.py:75-85` and `trial.py:108`.
- **Proposed correction:** Implement genuine, mathematically defined, feature-flagged mechanisms (branching exploration, gated anastomosis, uncertainty bonus, shock-memory reset, connectivity-safe retraction) AND use paired policy RNG streams (`agent:{regime}:policy` or explicit ablation flags) for controlled mechanism ablations; reject any unimplemented alias in validation rather than silently running a clone.
- **Regression test:** Test asserting that every supported `v2_no_*` ablation toggles a real mechanism flag that measurably changes state/decisions on a fixed RNG seed, and zero `UNIMPLEMENTED_ALPHA_ALIASES` remain silent clones.
- **Scientific/operational impact:** Eliminates pseudo-ablation artifacts (INV-03: no rename-ablations).

---

#### `AUD-CRIT-04` — Hard Safety Constraints & Guardrails Violated in `MycelialResourceController`
- **Severity:** Critical (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/policies/controller.py` (L98–128, L138–145), `src/mycelial_graph/v2/biology/stop.py` (L16–29)
- **Reproduction steps:** Run `MycelialResourceController` with `ConstraintConfig(minimum_quality=0.95, max_risk=0.01, mandatory_verification=True)`. Observe `skip` verification edges (`alt == 0`) still selected frequently (~30%+ of steps).
- **Root cause:** `_apply_mvc_verification()` inspects only `verify_sources[0]` (ignoring model nodes `5` and `6`), performs a no-op when `should_spend()` is `True` (leaving `skip` active in softmax + $\epsilon$-exploration), and mutates `self.conductance[skip] += 0.08` inside `choose()` when `not spend_ok`.
- **Evidence:** `controller.py:108, 123-127, 139-145`.
- **Proposed correction:** Enforce hard constraints (`mandatory_verification`, guardrail pass, `max_risk`, `minimum_quality` when certified/estimated, and hard budget caps) via **pre-routing feasible-candidate filtering** across *all* relevant nodes before soft conductance/utility scoring, with explicit fallback path selection when primary candidates violate constraints, and remove state mutation from `choose()`.
- **Regression test:** Property/unit tests verifying 0% selection of `skip` verification when `mandatory_verification=True` across all model nodes and seeds, and `choose()` idempotence wrt persistent learned parameters when no observation occurs.
- **Scientific/operational impact:** Satisfies the non-negotiable requirement that safety constraints and hard budgets must never be converted into soft preferences.

---

#### `AUD-CRIT-05` — Broken Strong Baselines (`AdaptiveEarlyStop`, `UncertaintyThresholdRouter`, `StructuredSWUCBResource`)
- **Severity:** Critical (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/policies/baselines_strong.py` (L90–207)
- **Reproduction steps:**
  1. Run `AdaptiveEarlyStop` for 100 steps: `agent.last_mvc` remains `0.0` at every step and verification choice is uniform random over `(15, 16, 17)`.
  2. Run `UncertaintyThresholdRouter` for 1,000 steps: `uncertain` remains `True` on 100% of steps (`mean >= 20/24 = 0.833 > 0.12`).
  3. Inspect `StructuredSWUCBResource`: uses per-edge scalar lists with zero node features.
- **Root cause:**
  1. `AdaptiveEarlyStop` routes exclusively to model node `5` (outgoing edges `15, 16, 17`), but compares `min(verify_ids)=12` (from node `4`) and `max(verify_ids)=20` (from node `6`), which are never traversed and never match `(15, 16, 17)`.
  2. `UncertaintyThresholdRouter` averages `1/sqrt(counts + 1)` over all 24 graph edges while deterministically visiting only 4 edges, trapping 20 edges at `counts=0` forever.
  3. `StructuredSWUCBResource` omitted the node+edge linear design matrix used in V1.
- **Evidence:** `baselines_strong.py:99, 134, 166-188`.
- **Proposed correction:** Fix `AdaptiveEarlyStop` to evaluate outgoing verification edges from the active model node; fix `UncertaintyThresholdRouter` to track task/layer posterior uncertainty with initial coverage or active-path uncertainty; implement true node-edge sliding-window ridge UCB (and add `v1_node_only`, `v1_hierarchical`, and `resource_heuristic` comparators) for fair V2 baseline comparisons.
- **Regression test:** Dedicated baseline fidelity tests verifying non-trivial adaptation and policy switching for every baseline in `baselines.py` and `baselines_strong.py`.
- **Scientific/operational impact:** Prevents artificial V2 wins against crippled baselines ("preserve baseline fidelity").

---

#### `AUD-CRIT-06` — $1000\times$ Token-Scale Unit Mismatch in `voc-bench` & `v2/real/controller.py`
- **Severity:** Critical (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/evaluation/counterfactual.py` (L76–85), `src/mycelial_graph/v2/real/controller.py` (L62–71)
- **Reproduction steps:** Run `mycelial-graph voc-bench --config experiments/v2_1/config.development.yaml`. Every row reports `voc_difference` around `-46` to `-109` and `allocated = False`.
- **Root cause:** `lambda_tokens = 0.35` is defined per `TOKEN_SCALE = 1000.0` tokens, but `counterfactual.py:76` passes raw unscaled token differences (`~132–312` tokens) into `estimate_voc(predicted_dq, predicted_dt, lam)`, multiplying `0.35 * 132 = 46.2` against quality gains in `[0, 0.1]`. It also ignores failure penalties and path-length averaging when computing realized counterfactual gains.
- **Evidence:** `counterfactual.py:76-85`, `v2/policies/controller.py:23, 71`.
- **Proposed correction:** Normalize `extra_resource` by `TOKEN_SCALE` (`1000.0`) consistently across `voc.py` callers (`counterfactual.py`, `adaptive_early_stop`, `v2/real/controller.py`) and evaluate path-level failure-adjusted counterfactual quality.
- **Regression test:** Unit test in `test_v2_1.py` verifying `voc.difference > 0` when quality gain exceeds `lambda_tokens * (delta_tokens / 1000.0)` and `voc.difference < 0` when cost exceeds gain.
- **Scientific/operational impact:** Restores valid Value-of-Computation (VOC) calibration and stop/escalate decisions.

---

#### `AUD-CRIT-07` — Biased Inverse Propensity Scoring (`ips_estimate`) Dropping Zero-Propensity Target Actions
- **Severity:** Critical (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/external/ope.py` (L43–110), `src/mycelial_graph/cli.py` (L339–344)
- **Reproduction steps:** Evaluate `ips_estimate` on 100 uniform 2-arm logged records (`a`: 50 rows with `reward=1.0, propensity=0.5`; `b`: 50 rows with `reward=0.0, propensity=0.5`) for deterministic target policy `target_propensity={"a": 1.0, "b": 0.0}`. True policy value is `1.0`; `ips_estimate` returns `estimate = 2.0`, `weight_mean = 2.0`, and `support_violations = 50`.
- **Root cause:** Lines 70–72 treat `p_pi <= near_zero` as a `support_violation` and `continue` (excluding $w_i r_i = 0$ from `values`), computing $\mathbb{E}[w R \mid \pi(A) > 0]$ instead of $\frac{1}{n}\sum_{i=1}^n w_i r_i$. Also `target_propensity=None` sets `p_pi = 1.0` for all actions ($\sum_a \pi(a) = K$).
- **Evidence:** `external/ope.py:68-78, 102`.
- **Proposed correction:** Retain records where `p_pi == 0.0` (with `p_mu > near_zero`) as `weight = 0.0, value = 0.0` without incrementing `support_violations`; only count `support_violations` when `p_mu <= near_zero` (especially where `p_pi > 0`); validate `0 <= p_pi <= 1`; add Self-Normalized IPS (`snips`) diagnostic alongside `ips`; when `target_propensity is None`, evaluate the logging policy (`p_pi = p_mu`, weight `1.0`) rather than improper `p_pi = 1.0`.
- **Regression test:** Exact unbiasedness test in `tests/test_external.py` over multi-arm uniform/non-uniform logged datasets with deterministic and stochastic target policies.
- **Scientific/operational impact:** Prevents severe ($K\times$) positive bias in off-policy evaluation diagnostics.

---

#### `AUD-HIGH-01` — Failure-Blind Expected Quality & Oracle in V2 Scenarios
- **Severity:** High (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/environment/scenario.py` (L88–93, L102–104, L158–163), `src/mycelial_graph/v2/runner/trial.py` (L136, L149, L199)
- **Reproduction steps:** Construct a `ResourceScenario` where an edge has `quality_means_post = 0.85` and `fail_post = 0.92` (`quality *= 0.25` upon failure). `expected_path_quality` credits that edge with `0.85` rather than its true mathematical expectation `0.85 * ((1 - 0.92) + 0.25 * 0.92) = 0.2635`.
- **Root cause:** `expected_path_quality` and `_path_quality` ignore `fail_prob` entirely, and `trial.py` stores this failure-blind quantity as `post_quality` and `ledger.quality_sum`.
- **Proposed correction:** Compute true failure-adjusted expected edge utility $q_e \cdot ((1 - f_e) + 0.25 f_e)$ in `expected_path_quality` and `_path_quality` (and record both `expected_quality` and `realized_quality` clearly in `V2TrialResult` and `TotalResourceLedger`).
- **Regression test:** Test asserting that increasing `fail_prob` from `0.0` to `0.90` reduces `expected_path_quality` and shifts `optimal_post_path` away from failing nodes.
- **Scientific/operational impact:** Aligns the V2 oracle and primary utility metric with actual stochastic component reliability.

---

#### `AUD-HIGH-02` — Stationary $1/n$ Estimators Cripple Non-Stationary Shock Recovery in V2
- **Severity:** High (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/policies/controller.py` (L173–181)
- **Reproduction steps:** Run `MycelialResourceController` with `pre_shock_steps = 80` under `PRICE_SHOCK` or `OUTAGE`. After 80 pre-shock steps ($n \approx 70$), post-shock updates to `quality_hat`, `cost_hat`, `token_hat`, `latency_hat`, and `fail_hat` move by $< 1.5\%$ per observation.
- **Root cause:** Cumulative unweighted sample mean `(obs - hat) / n` assumes stationarity, contradicting shock/drift regimes.
- **Proposed correction:** Use recency-weighted exponential moving averages (EWMA with configurable `estimator_alpha` / forgetting factor) + optional surprise/shock-detection variance tracking (`shock_memory`) so health, cost, and utility estimates adapt on bounded timescales.
- **Regression test:** Post-shock adaptation test verifying `cost_hat` and `fail_hat` converge within 10 observations after a step-change at $t = 80$.
- **Scientific/operational impact:** Enables genuine post-shock recovery in `PRICE_SHOCK`, `LATENCY_SHOCK`, and `OUTAGE` regimes.

---

#### `AUD-HIGH-03` — Unobserved Pruning Drift, Missing Connectivity Guard & Price-Shock Blindness
- **Severity:** High (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/biology/pruning.py` (L8–32), `src/mycelial_graph/v2/policies/controller.py` (L149, L207–235)
- **Reproduction steps:** Observe an edge 3 times with noisy low quality (`score > 0.55`), then never traverse it for 4 steps: `prune_evidence` increments `+1` on each unvisited step and prunes the edge with zero new evidence. Under `CORRELATED_PROVIDER_FAILURE` or `ADVERSARIAL_COST`, all 3 outgoing edges from a node can be marked `pruned = True` simultaneously.
- **Root cause:** `update_prune_evidence` iterates over all edges every step regardless of whether `edge_id` was observed, has no `s-t` reachability / minimum-active-outgoing-edge invariant, omits `cost_norm` (`monetary_cost`) from `prune_score`, and still counts pruned edges in `router_candidates`.
- **Proposed correction:** Update prune evidence **only** on newly observed edges (with slow decay/rehabilitation potential on long-unvisited pruned edges if active paths degrade), include normalized monetary + latency + token cost in `prune_score`, enforce a strict **connectivity-preserving invariant** (never prune the best/last feasible outgoing edge of any reachable node), and skip pruned edges during routine candidate scoring (yielding measurable `router_tokens` savings while preserving bounded exploratory probe access).
- **Regression test:** Graph-invariant property test proving at least one unpruned `source -> sink` pathway remains reachable under arbitrary adversarial observations and `router_candidates` decreases when inefficient edges are retracted.
- **Scientific/operational impact:** Operationalizes cytoplasmic retraction safely without graph disconnection or phantom pruning.

---

#### `AUD-HIGH-04` — Conductance Decay-to-Zero, Raw-Usage Reinforcement & Floor-Violating Double Translocation
- **Severity:** High (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/biology/conductance.py` (L41–47), `src/mycelial_graph/v2/biology/translocation.py` (L20–28), `src/mycelial_graph/v2/policies/controller.py` (L130–137, L197, L236–240)
- **Reproduction steps:**
  1. Call `update_conductance` on an edge that failed (`target = -0.2, demand = 1.0`) vs unvisited backup edges over 80 steps: backup edges decay to `minimum_conductance = 0.05` (`conductance * (1 - decay)`), while `cord_enabled=True` adds `+0.05` unconditional usage bonus even on failed traversals!
  2. Call `translocate(budget=np.array([100.0, 0.0, 0.0]), weights=np.array([1.0, 0.0, 0.0]), cap=100.0, config_with_floor=0.30, enabled=True)`: `mixed.min()` drops below `floor = 10.0` after `mixed *= cap / mixed.sum()`.
- **Root cause:** Decay omitted baseline anchor `initial_conductance`; `cord_enabled` rewarded raw traversal (`demand = 1.0`) instead of reliable validated utility; `translocate` applied naive multiplicative scaling after clamping instead of water-filling / excess redistribution above `floor`, and `controller.py` called `translocate` twice per step.
- **Proposed correction:** Decay conductance toward `initial_conductance` (preserving neutral backup readiness); define cord reinforcement strictly as variance/reliability-weighted positive utility reinforcement (`reliable_utility > 0` and `success == True`); fix `translocate` to allocate `floor` first (`floor + (cap - n * floor) * weights / weights.sum()`), guaranteeing exact conservation AND `budget >= floor` in one update per step.
- **Regression test:** Property-based tests (`hypothesis`) verifying `np.isclose(budget.sum(), cap)` and `np.all(budget >= floor - 1e-12)` for all valid `cap >= 0` and `0 <= floor_budget_fraction <= 1`, plus negative-test verifying failed edges never receive positive cord reinforcement.
- **Scientific/operational impact:** Directly enforces Section 5.3 & 6.C ("Reinforce pathways based on reliable utility, not raw usage frequency").

---

#### `AUD-HIGH-05` — Ignored `engineering_token_gate` / `mmrr` & Interval Precedence Bug in `v2/analysis.py`
- **Severity:** High (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/analysis.py` (L76–85, L105–108)
- **Reproduction steps:** Pass a `-0.1%` token change with `engineering_token_gate = 0.10` (`10%`) and `mmrr = 0.05` (`5%`): `analysis.py` classifies `token_reduction = True` and `decision = "PASS"`. Pass quality bootstrap distribution with 2.5th percentile `-0.06`, 5th percentile `-0.04`, and `margin = 0.05`: `_label` returns `"PASS"` despite two-sided CI crossing `-margin`, and line 85 is dead code.
- **Root cause:** `analysis.py:106` tested `< 0.0` instead of `<= -max(engineering_token_gate, mmrr) * mean_baseline_tokens`, and `_label` mixed two-sided 95% and one-sided 95% bounds inconsistently.
- **Proposed correction:** Enforce relative token/cost reduction against `engineering_token_gate` / `mmrr`, use consistent one-sided non-inferiority (`one_sided_lower_bound > -margin`) + superiority + practical-effect gates (mirroring V1's rigorous 5-state classification `SUPPORTED/PASS`, `CONDITIONAL`, `INCONCLUSIVE`, `REFUTED`, `PROTOCOL_INVALID`), and report Holm-Bonferroni corrected p-values / CIs when comparing multiple regimes or baselines.
- **Regression test:** Unit tests covering all 5 terminal states and verifying a trivial `-0.5%` token difference returns `CONDITIONAL`/`INCONCLUSIVE`, never `PASS`.
- **Scientific/operational impact:** Prevents false-positive V2 superiority claims on negligible token differences.

---

#### `AUD-HIGH-06` — V2 Ledger/Trace Accounting Mismatches & Non-Deterministic Gzip Headers
- **Severity:** High (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/ledger/tokens.py` (L82–172), `src/mycelial_graph/v2/runner/trial.py` (L84–98, L143–175), `src/mycelial_graph/v2/audit.py` (L12–48), `src/mycelial_graph/v2/reporting.py` (L112–113), `src/mycelial_graph/v2/evaluation/budget_curves.py` (L29–31)
- **Reproduction steps:**
  1. Run `run_v2_method` twice at different wall-clock seconds on the same seed: `.jsonl.gz` trace SHA-256 differs because `gzip.open(..., "wt")` embeds `time.time()` in the gzip header!
  2. Read any trace line from `v2-demo`: `record["total_tokens"]` is `path_tokens + router_tokens + state_overhead`, whereas `record["token_usage"]["total_tokens"]` is `path_tokens + router_tokens` (off by `state_overhead_tokens` every step).
  3. Pass `TokenUsage(cached_tokens=50)` into `TotalResourceLedger.record_step`: `cached_tokens` vanishes; `model_calls` and `tool_calls` are hardcoded to `1` regardless of traversed component types.
- **Root cause:** Missing `gzip.GzipFile(..., mtime=0)`; `state_overhead_tokens` excluded from `TokenUsage`; omitted fields in `TotalResourceLedger`; post-shock vs full-horizon mixing in `reporting.py` and `budget_curves.py`.
- **Proposed correction:** Write V2 `.jsonl.gz` traces via `gzip.GzipFile(..., mode="wb", mtime=0)` + `fsync`; include `state_overhead_tokens`, `cached_tokens`, `estimated_tokens`, `retry_tokens`, `recovery_overhead_tokens`, `memory_tokens` in `TokenUsage` and `TotalResourceLedger`; count actual model/tool/retriever/validator invocations from traversed graph components; upgrade `v2/audit.py` to reconcile **every** token bucket, cost, latency, and call counter between traces and ledger; separate pre-shock and post-shock ledger sub-totals cleanly.
- **Regression test:** Bitwise trace-hash determinism test across delayed runs + full category-by-category `audit_resource_traces` test.
- **Scientific/operational impact:** Guarantees deterministic V2 artifact hashes and audit-grade resource accounting.

---

#### `AUD-HIGH-07` — Stale & Contradictory Scientific Claims Across Repository Docs
- **Severity:** High (Confirmed Documentation / Provenance Defect)
- **Affected files:** `CLAIMS.md` (L7–8, L25), `research/claims.json` (L5–23), `research/CLAIMS.md` (L9), `CHANGELOG.md` (L19), `FAILURE_MODES.md` (L7, L23), `docs/ROADMAP.md` (L27–28), `REPRODUCIBILITY.md` (L46, L54), `docs/QUICKSTART.md` (L16–35), `docs/GETTING_STARTED.md` (L55), `CITATION.cff` (L1–19)
- **Reproduction steps:** Read `CLAIMS.md:7-8` and `research/claims.json:5-23`: C1 (`Hierarchical sharing improves V1 recovery at rho=.50`) and C2 (`non-inferior at rho=0`) still state `"No verified supporting artifact"` and `"NOT YET VALIDATED"`, directly contradicting `README.md`, `research/state.json` (`REFUTED`), and `docs/claim_evidence_matrix.yaml` (`CONFIRMATORY_REFUTED`). Inspect `CITATION.cff`: contains two concatenated YAML documents with duplicate keys (`title`, `authors`, `license`, `repository-code`) and stale `version: "0.2.0"`.
- **Root cause:** Post-confirmatory updates patched `README.md`, `research/state.json`, and `docs/claim_evidence_matrix.yaml` without updating `CLAIMS.md`, `research/claims.json`, `research/CLAIMS.md` (row C01), `FAILURE_MODES.md`, `docs/ROADMAP.md`, `docs/QUICKSTART.md`, or deduplicating `CITATION.cff`.
- **Proposed correction:** Update all listed non-sealed files so every claim register consistently reflects V1 `REFUTED` (`EQ-B` attribution boundary) and $\rho=0$ `NEGATIVE_TRANSFER_NOT_EXCLUDED` (underpowered at $N=97$), fix `research/ledger/ledger.jsonl` path references, repair `docs/QUICKSTART.md` CLI commands, and deduplicate `CITATION.cff` (`0.2.2`), while keeping every guarded substring in `README.md`, `research/CLAIMS.md` (`C15`), and `V1_CONFIRMATORY_MORATORIUM.md` intact.
- **Regression test:** Cross-document consistency test asserting `research/claims.json`, `CLAIMS.md`, `research/CLAIMS.md`, `docs/claim_evidence_matrix.yaml`, `research/state.json`, and valid single-document YAML in `CITATION.cff` agree on V1 `REFUTED` status.
- **Scientific/operational impact:** Eliminates contradictory scientific claims across entry-point documents.

---

#### `AUD-MED-01` — Windows CRLF Working-Tree Pollution in `tests/test_scientific_state.py` & `reproduce_confirmatory.py`
- **Severity:** Medium (Confirmed Defect)
- **Affected files:** `tests/test_scientific_state.py` (L83–109), `reproduce_confirmatory.py` (L235, L256)
- **Reproduction steps:** Run `pytest tests/test_scientific_state.py` on Windows, then run `git status`: `research/state.json` and `research/runtime.json` emit CRLF working-copy warnings because `finally:` calls `write_text(original, encoding="utf-8")` without `newline="\n"` (or `read_bytes`/`write_bytes`). Similarly, running `python reproduce_confirmatory.py` modifies tracked `experiments/v1/artifacts/diagnostics/REPRODUCTION_REPORT.md` with host-specific timing.
- **Proposed correction:** In `tests/test_scientific_state.py`, test state/runtime mutations against a temporary copy of the repo metadata (or restore exact bytes via `read_bytes()`/`write_bytes()`). In `reproduce_confirmatory.py`, preserve default behavior when expected while ensuring LF-clean handling and adding `--no-write-report` / clean-check support.
- **Regression test:** Test asserting `research/state.json` and `research/runtime.json` raw SHA-256 bytes are identical before and after `test_scientific_state.py` executes on Windows.

---

#### `AUD-MED-02` — Empirical-Bayes Variance Scaling ($\sigma^2$ vs $\sigma^2/n$) & `ddof` Error in `pooling/`
- **Severity:** Medium (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/pooling/empirical_bayes.py` (L43–59), `src/mycelial_graph/pooling/toy_model.py` (L13–21, L40–52, L65)
- **Reproduction steps:** Run `evaluate(ToyConfig(k=6, post_n=10000, noise_std=0.2, rho=0.0))`: `pooling_weight` stays $> 0.25$ instead of converging to `0.0` as $n \to \infty$; `generate_means(ToyConfig(rho=-0.1))` produces `NaN`s.
- **Root cause:** `empirical_bayes.py:44` divides residual sum of squares by $Kn - 1$ instead of $K(n - 1)$, and `toy_model.py:65` passes per-observation variance $\hat{\sigma}^2$ instead of per-arm mean variance $\hat{\sigma}^2 / n$ into `pooling_weight_from_variances`.
- **Proposed correction:** Compute `within = float(np.sum(residual ** 2) / (k * (n - 1)))` when $n > 1$, pass `within / config.post_n` for arm-mean pooling weight, and validate `0.0 <= rho <= 1.0`, `k >= 3`, `post_n >= 1`, `noise_std > 0` in `ToyConfig`.
- **Regression test:** Asymptotic consistency test ($n=5000 \implies \text{weight} < 0.01$ at $\rho=0$), unbiased `within_var` check at $n=2$, and invalid-`rho` `ValueError` test in `tests/test_pooling.py`.

---

#### `AUD-MED-03` — Timestamp String-Ordering Bug, Negative TZ Rejection & `bool`/`NaN` Acceptance in `external/`
- **Severity:** Medium (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/external/schemas.py` (L73–85, L96–113), `src/mycelial_graph/external/adapters.py` (L13–25, L47, L88–107, L126–138)
- **Reproduction steps:** Pass `incident_start="2026-01-01T00:00:00Z"` and `incident_end=1767225600.5` (`"2026-01-01T00:00:00.500000Z"`) to `adapt_incident_row`: rejected with `"incident_end_utc precedes incident_start_utc"` because ASCII `'.' < 'Z'`. Pass `propensity=True, reward=float("nan")` to `validate_logged_bandit`: accepted without error.
- **Proposed correction:** Parse ISO-8601 timestamps (including `-HH:MM` offsets and fractional seconds) into timezone-aware `datetime` objects before ordering/overlap comparisons; reject `isinstance(x, bool)` and non-finite floats (`not math.isfinite`) across numeric schema fields.
- **Regression test:** Unit tests in `tests/test_external.py` covering fractional-second timestamps, `-03:00` offsets, `bool` values, epoch `0`, and `NaN`/`Inf` rewards.

---

#### `AUD-MED-04` — Broken Waste Proxy Formula & Unreserved/Malformed `v2/real/` Smoke Repairs
- **Severity:** Medium (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/evaluation/waste.py` (L61–62), `src/mycelial_graph/v2/real/agent.py` (L66–126), `src/mycelial_graph/v2/real/hypothesize.py` (L27–30), `src/mycelial_graph/v2/resources/reservation.py` (L38–48)
- **Reproduction steps:**
  1. Call `decompose_waste` when `input_tokens >= retrieval_tokens // 2`: `reingested_context_tokens` is identically `0` because `unique_context = retrieval // 2 + input_tokens` mixes unrelated buckets.
  2. Call `_empty_guard_source` on a 2-argument or multi-line function (`def f(a, b):\n    x = a + b\n    return x`): produces `def f(a):` (dropping `b`!) and unindented second statement (`SyntaxError` / wrong semantics).
  3. Run `run_real_task` with tight `token_budget`: loop executes action first, overrunning `envelope.token_budget`, and bills `STOP` afterwards.
- **Proposed correction:** Fix `waste.py` proxy definitions so `reingested_context_tokens` measures repeated/un-cached context cleanly without subtracting `input_tokens` from `retrieval`; preserve full `ast.unparse(node.args)` and `textwrap.indent` in `hypothesize.py`; enforce `BudgetReservation` pre-check before step execution in `v2/real/agent.py` and reject negative `actual` in `BudgetReservation.commit()`.
- **Regression test:** Unit tests in `test_v2_1.py` covering multi-argument/multi-line AST guard generation, strict budget cap adherence in `run_real_task`, and `BudgetReservation` negative/overrun handling.

---

#### `AUD-MED-05` — Configuration Validation Gaps & CLI Error-Handling Inconsistencies
- **Severity:** Medium (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/v2/validation.py` (L34–78), `src/mycelial_graph/v2/config.py` (L37–59), `src/mycelial_graph/cli.py` (L100–106, L137–156, L246, L258)
- **Reproduction steps:**
  1. Set `temperature: 0.0` or `exploration_probability: 1.5` or `global_budget_tokens: -10` in V2 YAML: passes `validate_v2_config` and crashes or misbehaves at runtime.
  2. Pass a seed file with `# comment` lines to `voc-bench` or `budget-curve`: crashes with `ValueError: invalid literal for int()`.
  3. Pass malformed YAML or `configs/v0_demo.yaml` to `mycelial-graph validate` / `v2-validate`: exits with code `1` (raw traceback string) instead of exit code `2` (`{"valid": false, "errors": [...]}`).
- **Proposed correction:** Add complete finiteness, range, and non-`bool` integer checks to `v2/validation.py` and `v2/config.py`; reuse `load_seeds()` in `cli.py`; support `BooleanOptionalAction` on `collect --dry-run`; return structured JSON with exit code `2` on config load errors in `validate` and `v2-validate`.
- **Regression test:** Validation matrix tests in `test_v2.py` and CLI exit-code tests in `test_v2_1.py`.

---

#### `AUD-LOW-01` — Portable Tree Hashing, V0 Survivorship/Report Indexing & Script Encoding Hygiene
- **Severity:** Low (Confirmed Defect)
- **Affected files:** `src/mycelial_graph/reporting/report.py` (L91–95, L155–165), `src/mycelial_graph/config.py` (L45–99), `src/mycelial_graph/experiment.py` (L164, L181–195), `src/mycelial_graph/report.py` (L118), `src/mycelial_graph/science/claim_guard.py` (L74–104), `scripts/record_evidence.py` (L10, L21–22, L40, L61)
- **Note on V1 Freeze Safety:** `src/mycelial_graph/runner/trial.py` and `src/mycelial_graph/config.py` are listed in `audit_v1_readiness.py:V1_SOURCE_PATHS`; keep frozen V1 simulator modules untouched unless strictly required, while safely fixing `scripts/record_evidence.py` (`encoding="utf-8"`, `sys.path`, canonical `research/ledger/ledger.jsonl`), V0 `experiment.py` / `report.py` (not in `V1_SOURCE_PATHS`), and clause-level negation in `claim_guard.py` (preserving all existing tests).
- **Regression test:** Unit tests covering 2-layer V0 `write_report`, non-ASCII UTF-8 `record_evidence`, and mixed-clause `claim_guard` detection.

---

## 4. Frozen V1 Design Confounds (Preserved — Analyzed in `docs/research/FAILURE_ANALYSIS.md`)

The following three findings in `src/mycelial_graph/agents/` are **confirmed mathematical/algorithmic causes of historical V1 behavior**, NOT bugs to be patched in-place in V1 (patching them in `agents/` would falsify historical V1 reproduction):

1. **`FRZ-V1-01` (`agents/edge_only.py` vs `agents/hierarchical.py`): Leaky Integrator vs. Bounded Prediction-Error Scale (`EQ-B`)** — `EdgeOnlyAgent` integrates `0.22 * (r - 0.50)` to steady state `~1.97` (`std = 0.510`), whereas `HierarchicalAgent` updates `error = r - clip(score, 0, 1)` (`std = 0.0422`), creating a `12.08x` score-dispersion mismatch under shared `temperature = 0.20`.
2. **`FRZ-V1-02` (`agents/hierarchical.py`, `agents/node_only.py`): Softmax Cancellation of `source_effect` & Downstream Collateral Node Poisoning** — At every node $u$, `source_effect[u]` is constant across `outgoing[u]` and cancels identically in `stable_softmax`, wasting 50% of `node_learning_rate` and attributing outgoing-edge failures $(v^*, w)$ from `shock_node` $v^*$ onto healthy downstream targets `target_effect[w]`.
3. **`FRZ-V1-03` (`agents/structured_sw_ucb.py`): Zero-Mean Ridge Prior Pessimism & Edge-Count Windowing** — Unvisited edges score `0 + 0.35 = 0.35 < 0.45` (below minimum possible reward), causing deterministic lock-in on the initial $t=0$ random path and `17.5%` censoring at $\rho = 0.50$, while `deque(maxlen=200)` stores 200 edges (`50` steps) rather than `200` steps.

All three are preserved intact in V1, documented with quantitative diagnostics in [`docs/research/FAILURE_ANALYSIS.md`](../research/FAILURE_ANALYSIS.md), and addressed cleanly in the additive V2 architecture (`src/mycelial_graph/v2/`).
