# Experimental Protocol V2 — `MG-EXP-V2.2`

## 1. Scientific Scope & Status

- **Protocol ID:** `MG-EXP-V2.2` (`experiments/v2_2/`)
- **Current Stage:** Development (`N = 10`) and Pilot/Ablation (`N = 24`) executed; Confirmatory **locked** (`experiments/v2_2/FREEZE_STATUS.json`: `"authorized": false`, `seeds.confirmatory.txt` unmaterialized).
- **Relationship to V1:** Additive layer. Preserves the frozen V1 `REFUTED` result (`+42.1%` RRT at $\rho = 0.50$, $N = 97$, `EQ-B`) and active submission moratorium (`research/state.json`) untouched.

---

## 2. Research Questions & Falsifiable Hypotheses

1. **H-V2-Resource (`PRICE_SHOCK` primary contrast vs. `always_high_compute`):** Can `v2_mycelial` reduce total post-shock token consumption by at least `10%` (`engineering_token_gate = 0.10`) while keeping expected task quality within a non-inferiority margin $\Delta_{\text{NI}} = 0.05$ of unconstrained `always_high_compute`?
2. **H-V2-Resilience (`OUTAGE`, `MIXED_CORRELATION`, `LOCAL_OUTAGE`, `RETRIEVER_COLLAPSE`):** Does combining local shock memory, discrepancy-gated anastomosis, and resource-aware conductance accelerate recovery (`RRT`) and reduce cost per successful task (`CPST`) relative to resource-blind V1 agents (`v1_edge_only`, `v1_node_only`, `v1_hierarchical`) without inducing negative transfer at $\rho = 0$ (`LOCAL_OUTAGE`)?
3. **H-V2-Scarcity (`RESOURCE_SCARCITY`):** Under hard post-shock token contraction (`scarce_budget_tokens = 15,000` over 50 steps = `300` tokens/step), do `BudgetReservation` and translocation maintain $\ge 85\%$ task success while respecting budget pacing?
4. **H-V2-Objectives:** How do scalarized (`v2_mycelial`), online primal-dual constrained (`v2_constrained`), and Pareto-filtered (`v2_pareto`) controllers trade off quality, tokens, cost, and recovery speed?

---

## 3. Experimental Design & Hygiene

### 3.1 Disjoint Seed Populations

- `seeds.development.txt`: `2201001..2201010` ($N = 10$) — scaling (`2x3`, `3x3`, `4x3`, `4x4`), noise (`0.02, 0.08, 0.16`), budget curve (`5k..80k`), and VOC calibration (`1,500` counterfactual steps).
- `seeds.pilot.txt`: `2202001..2202024` ($N = 24$) — 12-method baseline benchmark (`192` scenario-regime pairs = `2,304` trials) and 11-method biological ablation suite (`144` scenario-regime pairs = `1,584` trials).
- `seeds.validation.txt`: `2203001..2203020` ($N = 20$) — reserved untouched for pre-freeze validation.
- `seeds.confirmatory.pool.txt`: `2204001..2204100` ($N = 100$) — locked pre-committed pool.

### 3.2 Evaluated Policies (12 Baselines & Objectives)

1. `always_high_compute` — static max-tier route (quality ceiling, resource-unconstrained control).
2. `always_low_compute` — static min-tier route (token floor, quality-degraded control).
3. `fixed_budget` — static mid-tier route matching nominal per-step allowance.
4. `random_feasible` — uniform random routing over budget- and risk-feasible transitions.
5. `v1_edge_only` — quality-only edge conductance transplant.
6. `v1_node_only` — quality-only node-pooled conductance transplant.
7. `v1_hierarchical` — quality-only hierarchical node+edge transplant.
8. `structured_sw_ucb` — sliding-window linear UCB with resource-adjusted reward.
9. `resource_heuristic` — greedy non-biological quality-per-resource ratio router.
10. `v2_mycelial` — full Mycelial V2 controller (scalarized objective).
11. `v2_constrained` — Mycelial V2 controller with online primal-dual token price.
12. `v2_pareto` — Mycelial V2 controller with stage-wise Pareto non-dominated filtering.

### 3.3 Statistical Analysis & Multiplicity Control

- Paired scenario-level differences $\Delta_i = Y_{i,\text{treatment}} - Y_{i,\text{control}}$ across identical potential-outcome tensors.
- Nonparametric paired bootstrap ($B = 2,000$ resamples in pilot, $5,000$ in confirmatory) reporting 95% two-sided CIs, one-sided NI/reduction bounds, paired Cohen's $d_z$, and **Holm-Bonferroni** step-down adjusted $p$-values across all secondary baseline contrasts.

---

## 4. Non-Confirmatory Pilot Summary (`N = 24`, `experiments/v2_2/PILOT_SUMMARY.json`)

### 4.1 Primary Regime (`PRICE_SHOCK`) — Honest Gate Outcome

- **Token & Cost Reduction Passed:** `v2_mycelial` reduced post-shock tokens by **`-67.3%`** (`23,690.0` vs `72,501.5`, paired $\Delta = -48,811.5$, 95% CI `[-49,788.7, -47,840.9]`, $d_z = -18.94$) and reduced monetary cost by **`-92.0%`** (`\$26.03` vs `\$325.87`, $\Delta = -\$299.84$), achieving net-utility gain $d_z = +18.83$ ($p_{\text{Holm}} < 10^{-4}$).
- **Strict `0.05` Quality Non-Inferiority Gate Missed (`non-confirmatory:REFUTED`):** Mean post-shock expected quality was `0.7065` vs `0.7725` for unconstrained `always_high_compute` ($\Delta Q = -0.0660$, 95% CI `[-0.0776, -0.0542]`, missing the `-0.05` margin by `0.016`).
- **Diagnostic Cause:** `always_high_compute` spends `115,856` total tokens (`2.41x` the `48,000` global budget cap), whereas `v2_mycelial` enforces `48,000 / 80 = 600` tokens/step, precluding routine use of the `920`-token tier-2 model on `hard` tasks. Before unlocking any confirmatory run, protocol revision must either compare against a **budget-feasible oracle** or raise `global_budget_tokens` to allow selective tier-2 escalation on hard instances.

### 4.2 Cross-Regime Pilot Comparison (Selected Regimes, Post-Shock Means)

| Regime | Policy | Quality | Post Tokens | Cost (USD) | RRT | Success | TPST | CPST (USD) | Policy CPU |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `PRICE_SHOCK` | `always_high_compute` | `0.7725` | `72,501.5` | `325.866` | `4.00` | `0.914` | `1,586.2` | `7.1293` | `67.1 ms` |
| `PRICE_SHOCK` | `v1_edge_only` | `0.7478` | `50,207.1` | `216.559` | `4.54` | `0.888` | `1,130.4` | `4.8756` | `55.3 ms` |
| `PRICE_SHOCK` | `structured_sw_ucb` | `0.7165` | `25,977.8` | `21.360` | `15.71` | `0.882` | `589.3` | `0.4845` | `159.5 ms` |
| `PRICE_SHOCK` | `v2_mycelial` | `0.7065` | `23,690.0` | `26.026` | `19.79` | `0.879` | `538.9` | `0.5921` | `350.9 ms` |
| `PRICE_SHOCK` | `v2_pareto` | `0.7101` | `24,575.1` | `23.400` | `15.71` | `0.904` | `543.6` | `0.5176` | `341.2 ms` |
| `OUTAGE` ($\rho=1$) | `always_high_compute` | `0.5652` | `72,501.5` | `112.580` | `50.00` | `0.082` | `17,755.5` | `27.5705` | `55.3 ms` |
| `OUTAGE` ($\rho=1$) | `v1_edge_only` | `0.6866` | `33,936.4` | `23.583` | `18.08` | `0.733` | `925.5` | `0.6432` | `46.9 ms` |
| `OUTAGE` ($\rho=1$) | `v1_hierarchical` | `0.6807` | `31,893.2` | `23.186` | `16.46` | `0.723` | `881.8` | `0.6411` | `58.6 ms` |
| `OUTAGE` ($\rho=1$) | `structured_sw_ucb` | `0.7049` | `25,638.7` | `8.016` | `5.33` | `0.847` | `605.6` | `0.1894` | `147.8 ms` |
| `OUTAGE` ($\rho=1$) | `v2_mycelial` | `0.6952` | `22,618.3` | `6.707` | **`4.42`** | `0.843` | `536.9` | `0.1592` | `343.1 ms` |
| `OUTAGE` ($\rho=1$) | `v2_pareto` | `0.6924` | **`21,378.6`** | **`5.269`** | `6.67` | `0.858` | **`498.1`** | **`0.1228`** | `284.5 ms` |
| `MIXED_CORRELATION` | `v1_edge_only` | `0.6757` | `37,314.5` | `44.239` | `14.58` | `0.747` | `999.5` | `1.1850` | `60.6 ms` |
| `MIXED_CORRELATION` | `v2_mycelial` | `0.6877` | `21,617.0` | `8.451` | `8.46` | `0.850` | `508.6` | `0.1989` | `391.3 ms` |
| `MIXED_CORRELATION` | `v2_pareto` | **`0.6933`** | `21,889.2` | **`7.450`** | **`4.83`** | **`0.867`** | **`505.1`** | **`0.1719`** | `342.5 ms` |
| `RESOURCE_SCARCITY` | `v1_edge_only` | `0.7484` | `51,432.0` | `72.401` | `4.12` | `0.911` | `1,129.3` | `1.5898` | `35.8 ms` |
| `RESOURCE_SCARCITY` | `v2_mycelial` | `0.6833` | **`16,088.9`** | **`2.114`** | `26.79` | `0.895` | **`359.5`** | **`0.0472`** | `251.3 ms` |
| `RETRIEVER_COLLAPSE` | `always_high_compute` | `0.5905` | `83,337.8` | `112.796` | `50.00` | `0.244` | `6,826.3` | `9.2393` | `54.7 ms` |
| `RETRIEVER_COLLAPSE` | `v2_mycelial` | `0.6978` | `25,387.8` | `17.652` | `18.17` | `0.860` | `590.4` | `0.4105` | `331.4 ms` |
| `RETRIEVER_COLLAPSE` | `v2_pareto` | `0.6997` | `24,342.8` | `15.987` | `16.50` | `0.875` | `556.4` | `0.3654` | `309.9 ms` |

### 4.3 Graph Scaling (`2x3` to `4x4`, `PRICE_SHOCK`, $N = 10$ Dev Seeds)

- As graph size grows from `2x3` (`15` edges, `9` paths) to `4x4` (`56` edges, `256` paths), `v1_edge_only` post-shock token consumption rises from `34,662.5` to `40,598.4` (`\$144.70`), whereas `v2_mycelial` keeps post-shock tokens bounded at `14,993.3 -> 19,043.3` (`\$14.79`, **`-89.8%` cheaper**) with policy CPU overhead remaining sub-millisecond per step (`385.9 ms / 60 steps = 6.4 ms/step` in pure Python on `4x4`).
