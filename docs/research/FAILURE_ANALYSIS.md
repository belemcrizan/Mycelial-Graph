# Mechanistic Failure Analysis of the Frozen MG-EXP-V1 `REFUTED` Result

- **Protocol Analyzed:** `MG-EXP-V1` (`MG-EXP-V1-CONFIRMATORY`)
- **Sealed Execution Commit:** `5f314d2dfb15f508dfd4e630e8c0e49031e60c6a` (`2026-09-15T03:02:03Z`)
- **Terminal Outcome (Immutable):** **`REFUTED`** (`equalization_triage = EQ-B`; $\rho = 0$ safety gate: `NEGATIVE_TRANSFER_NOT_EXCLUDED`)
- **Authoritative Sources:** [`experiments/v1/artifacts/confirmatory/CONFIRMATORY_EVIDENCE.json`](../../experiments/v1/artifacts/confirmatory/CONFIRMATORY_EVIDENCE.json), [`experiments/v1/artifacts/confirmatory/analysis.json`](../../experiments/v1/artifacts/confirmatory/analysis.json), [`experiments/v1/artifacts/diagnostics/equalization.json`](../../experiments/v1/artifacts/diagnostics/equalization.json), [`experiments/v1/artifacts/diagnostics/dynamic_range.json`](../../experiments/v1/artifacts/diagnostics/dynamic_range.json), [`experiments/v1/artifacts/diagnostics/variance.json`](../../experiments/v1/artifacts/diagnostics/variance.json), [`experiments/v1/artifacts/diagnostics/censoring.json`](../../experiments/v1/artifacts/diagnostics/censoring.json), [`research/diagnostics/EQ_B_REPORT.md`](../../research/diagnostics/EQ_B_REPORT.md).

> [!IMPORTANT]
> **Scientific Integrity Statement.** Nothing in this document alters, softens, reclassifies, or reinterprets the historical V1 confirmatory outcome. Under the pre-registered protocol `MG-EXP-V1`, the implemented `hierarchical` policy recovered **42.1% slower** than `edge_only` at $\rho = 0.50$ ($N = 97$ paired scenarios, 95% bootstrap CI $[+11.9\%, +79.1\%]$) and failed its $\rho = 0$ non-inferiority safety gate (one-sided upper bound $+16.31\% > +10.0\%$ margin). Post-hoc diagnostics below explain *why* the frozen mechanism failed; they are **retrospective mechanistic diagnostics**, not confirmatory evidence for an alternative method.

---

## 1. Verification of the Authoritative Historical Result

Direct inspection and deterministic verification (`python reproduce_confirmatory.py` and full scenario replay) confirm every number in the sealed confirmatory record:

### 1.1 Primary & Safety-Gate Contrasts ($N = 97$ Paired Scenarios, $B = 10{,}000$ Resamples)

| Contrast | Role | `edge_only` Mean RRT (SD) | `hierarchical` Mean RRT (SD) | Relative $\Delta\text{RRT}$ | Two-Sided 95% CI | One-Sided 95% UB | Verdict |
|---|---|---:|---:|---:|---|---:|---|
| $\rho = 0.50$ | **PRIMARY** | `36.010` (`23.973`) | `51.175` (`50.525`) | **`+42.11%`** (`+0.42113`) | `[+11.90%, +79.09%]` | `+72.14%` (need `< 0%`) | **`REFUTED`** (excludes `-20%` gain) |
| $\rho = 0.00$ | **SAFETY GATE** | `17.649` (`7.920`) | `17.918` (`11.849`) | **`+1.52%`** (`+0.01519`) | `[-13.69%, +19.71%]` | `+16.31%` (need `< +10%`) | **FAILED** (`NEGATIVE_TRANSFER_NOT_EXCLUDED`) |

### 1.2 Full 20-Cell Sealed Performance Summary ($N = 97$ per Cell; Non-Primary Rows Exploratory/Diagnostic)

| $\rho$ | `edge_only` RRT / Regret | `hierarchical` RRT / Regret | `node_only` RRT / Regret | `structured_sw_ucb` RRT / Regret (Censored) |
|---:|---:|---:|---:|---:|
| `0.00` | `17.649` / `6.001` | `17.918` / `11.755` (`+95.9%` regret) | `27.278` / `13.648` | `24.515` / `8.727` (`3.1%`) |
| `0.25` | `24.175` / `7.208` | `40.680` / `14.881` (`+106.4%` regret) | `75.216` / `16.852` | `81.134` / `12.390` (`22.7%`) |
| `0.50` | `36.010` / `8.393` | `51.175` / `16.002` (`+90.7%` regret) | `92.990` / `17.624` | `70.938` / `11.831` (`17.5%`) |
| `0.75` | `43.113` / `9.329` | `65.103` / `16.184` (`+73.5%` regret) | `86.485` / `17.618` | `55.959` / `11.124` (`7.2%`) |
| `1.00` | `34.021` / `7.799` | `31.000` / `14.029` (`+79.9%` regret) | `36.258` / `14.779` | `42.000` / `9.765` (`7.2%`) |

Two empirical patterns stand out immediately:
1. Even at $\rho = 1.00$ (purely shared node shock), where `hierarchical` achieved a slightly lower exploratory mean RRT (`31.000` vs `34.021`, `-8.88%`, one-sided UB `+10.25%`, non-significant), its post-shock dynamic regret remained **`+79.88%` worse** (`14.029` vs `7.799`), and final utility remained lower (`0.5970` vs `0.6239`).
2. Censoring at $\tau = 300$ was `0 / 485` (`0.0%`) for `edge_only` and `1 / 97` (`1.03%`) for `hierarchical` at $\rho = 0.50$ (`censoring.json`); administrative censoring did **not** drive the `+42.1%` RRT gap. Instead, paired differences $D_i = \text{RRT}_{\text{hier},i} - \text{RRT}_{\text{edge},i}$ exhibited strong right-skew (`skewness = +1.630`, median `+6.0` steps, mean `+15.165` steps, SD `55.945`, `1.72x` pilot SD; `variance.json`).

---

## 2. Exact Mathematical & Code-Level Root Causes

Inspecting [`edge_only.py`](../../src/mycelial_graph/agents/edge_only.py), [`hierarchical.py`](../../src/mycelial_graph/agents/hierarchical.py), [`node_only.py`](../../src/mycelial_graph/agents/node_only.py), [`_routing.py`](../../src/mycelial_graph/agents/_routing.py), and [`scenario.py`](../../src/mycelial_graph/environment/scenario.py) establishes three interacting mathematical mechanisms behind the failure.

### Mechanism M1 — Update-Target & Scale Asymmetry (`EQ-B` Effective-Policy-Scale Confound)

Both policies share nominal parameters (`initial_conductance` $g_0 = 0.50$, `temporal_decay` $\lambda = 0.015$, `temperature` $T = 0.20$, `exploration_probability` $\varepsilon = 0.08$), yet implement fundamentally different dynamical systems:

1. **`EdgeOnlyAgent` (`edge_only.py:21-25, 46-53`) is a leaky integrator relative to a fixed constant `0.50`:**
   $$g_e^{(t+1)} = \operatorname{clip}\!\Big(g_0 + (1 - \lambda)(g_e^{(t)} - g_0) + \eta_{\text{edge}}(r_{t,e} - 0.50),\; 0.01,\; 2.00\Big)$$
   Because pre-shock edge means are drawn from $\operatorname{clip}(0.62 + \mathcal{N}(0, 0.035^2), 0.45, 0.80)$, good edges have $\mu_e \approx 0.66 > 0.50$. Under selection probability $p_e \approx 0.70$ and $\eta_{\text{edge}} = 0.22$, the fixed point without clipping is:
   $$g_e^* = 0.50 + \frac{p_e \eta_{\text{edge}}}{\lambda}(\mu_e - 0.50) \approx 0.50 + \frac{0.70 \times 0.22}{0.015}(0.16) = 2.14 \implies \operatorname{clip}(g_e^*) = \mathbf{2.00}$$
   At $T = 0.20$, `edge_only` builds logit gaps $\Delta g / T \approx (1.97 - 0.50)/0.20 = \mathbf{7.35}$ ($e^{7.35} \approx 1556:1$ exploitation sharpness).

2. **`HierarchicalAgent` (`hierarchical.py:45-48, 66-76`) is a self-limiting prediction-error (Rescorla–Wagner) mean estimator:**
   $$\text{err}_{t,e} = r_{t,e} - \operatorname{clip}(s_e^{(t)}, 0, 1), \qquad s_{(u,v)} = g_0 + a_u + b_v + c_{(u,v)}$$
   Because `HierarchicalAgent` subtracts its own current score $s_e^{(t)}$ (and applies both `temporal_decay = 0.015` and `shrinkage = 0.002`, i.e. $\lambda_{\text{eff}} = 1 - 0.985 \times 0.998 = 0.01697$ per step across all parameters), its scores **cannot exceed $\mu_e \approx 0.65$**. Across the 97 confirmatory trials (`equalization.json` at $\rho = 0.50$):
   - `selected_score_std`: `0.5100` (`edge_only`) vs **`0.0422`** (`hierarchical`) — a **`12.08x`** dispersion mismatch.
   - `path_entropy_fraction_of_max`: `0.6289` (`edge_only`) vs **`0.9695`** (`hierarchical`, almost uniform over all 27 paths!).
   - `optimal_pre_path_rate`: `13.64%` (`edge_only`) vs **`4.29%`** (`hierarchical`, barely above uniform guessing $1/27 = 3.70\%$).

3. **Direct effect on post-shock `RRT`:** At $\rho = 0.50$, 7 of 24 edges are degraded (`1` interaction edge by `-0.3889` and `6` edges incident to `shock_node` by `-0.1588`), contaminating $15 / 27 = \mathbf{55.6\%}$ of all source-to-sink paths. Under $T = 0.20$, a score drop of `-0.1588` changes softmax logits by only $-0.794$, still routing $\sim 18.4\%$ of traffic through `shock_node` at Layer 1! Because `sustained_recovery_time` requires the 10-step trailing expected utility to stay $\ge 0.90 \cdot \mu_{\text{post}}^*$ for **20 consecutive steps**, `HierarchicalAgent`'s near-uniform sampling repeatedly dips below the `0.90` bar.

### Mechanism M2 — Softmax Cancellation of `source_effect` & Collateral Node Poisoning

In `stochastic_local_route` (`_routing.py:24-34`), at any visited node $u$, **every candidate edge $e = (u, v) \in \text{outgoing}[u]$ shares the exact same source node $u$**. Because `stable_softmax` is translation-invariant (`exp((s - max(s))/T)`):
$$s_{(u, v_1)} - s_{(u, v_2)} = (g_0 + a_u + b_{v_1} + c_{(u, v_1)}) - (g_0 + a_u + b_{v_2} + c_{(u, v_2)}) = (b_{v_1} - b_{v_2}) + (c_{(u, v_1)} - c_{(u, v_2)})$$

**`self.source_effect` ($a_u$) cancels out 100% identically in every routing decision across the entire graph.** Worse, updating `source_effect` actively degrades credit assignment:
- **50% wasted node learning rate:** Half of `node_learning_rate` (`0.14 / 2 = 0.07`) is written into `source_effect[u]` on every traversed edge, where it can never influence candidate selection at $u$.
- **Invisible outgoing node shocks + healthy-target poisoning:** `shock_node` $v^* \in L_2$ has 3 incoming shocked edges $(u, v^*)$ and 3 outgoing shocked edges $(v^*, w)$. When a path traverses outgoing shocked edge $(v^*, w)$, `HierarchicalAgent` writes $-0.07|\text{err}|$ into `source_effect[v*]` (invisible at $L_1$ when deciding whether to enter $v^*$, and cancelled out at $v^*$!) and writes $-0.07|\text{err}|$ into **`target_effect[w]`**, falsely penalizing healthy $L_3$ node $w$ when reached from healthy $L_2$ nodes!
- **Per-edge shock dilution at $\rho = 0.50$:** Because `node_pattern` is L2-normalized across $|\mathcal{I}(v^*)| = 6$ edges (`scenario.py:78-85, 114-127`), at $\rho = 0.50$ each shared node edge receives $-0.55\sqrt{0.50}/\sqrt{6} = \mathbf{-0.1588}$, whereas the single unshared `interaction_edge` receives $-0.55\sqrt{0.50} = \mathbf{-0.3889}$ (**$2.45\times$ larger**). Thus even at $\rho = 0.50$, the dominant per-edge shock is unshared, and writing half its node update into `target_effect[v_ie]` and `source_effect[u_ie]` depresses healthy sibling edges.

### Mechanism M3 — Global Mean-Projection Drift (`_project()`)

`HierarchicalAgent._project()` (`hierarchical.py:29-33`) subtracts `np.mean(...)` globally across all 11 nodes and all 24 edges on every step—including structural coordinates that can **never** receive gradient updates (`target_effect[source=0]` and `source_effect[sink=10]`) and coupling unrelated layers via `np.clip(score, 0, 1)` inside prediction-error computation.

---

## 3. Systematic Evaluation of Candidate Failure Hypotheses

Every hypothesis required by the research audit was tested against sealed confirmatory artifacts (`equalization.json`, `dynamic_range.json`, `censoring.json`, `variance.json`, `runtime.json`) and controlled retrospective mechanism-isolation probes on the V1 simulator:

### Counterfactual Mechanism-Isolation Diagnostic (Retrospective Only — Does Not Alter `REFUTED`)

To separate update-scale confounding (M1) from representation/credit-assignment defects (M2/M3), five controlled variants were evaluated read-only across the 97 V1 scenario families:
1. **`edge_only` (Frozen baseline):** Mean RRT `36.010` ($\rho=0.50$), `17.649` ($\rho=0.0$), `34.021` ($\rho=1.0$); Regret `8.393` ($\rho=0.50$).
2. **`hierarchical` (Frozen treatment):** Mean RRT `51.175` ($\rho=0.50$), `17.918` ($\rho=0.0$), `31.000` ($\rho=1.0$); Regret `16.002` ($\rho=0.50$).
3. **`edge_only_td_error` (Zero node sharing; `edge_only` modified solely to use `HierarchicalAgent`'s `r - clip(score, 0, 1)` TD update at $T=0.20$):** Mean RRT jumps from `36.010` to **`47.526`** at $\rho=0.50$ (`+11.516` steps, **75.9% of the entire `+15.165`-step confirmatory RRT penalty!**) and dynamic regret jumps from `8.393` to **`16.020`** (**100.2% of the confirmatory regret penalty**), with zero hierarchy present!
4. **`hier_temp_matched` (Frozen `HierarchicalAgent` with temperature scaled to `0.025` to match `edge_only`'s effective score-to-temperature ratio):** Mean RRT drops from `51.175` to **`11.732`** ($\rho=0.50$), `10.052` ($\rho=0.0$), `11.258` ($\rho=1.0$); Regret `5.402` ($\rho=0.50$).
5. **`hier_unified_node_lookahead_matched` (Unified internal node health $h_v$ + 1-step backward value propagation eliminating `source_effect` cancellation, temperature-matched):** Mean RRT **`10.814`** ($\rho=0.50$), `10.010` ($\rho=0.0$), `10.258` ($\rho=1.0$); Regret **`4.190`** ($\rho=0.50$). *(Strict caveat: retrospective diagnostic on V1 scenarios; V2 designs and tests gated anastomosis on completely separate V2 scenarios and seeds.)*

### Hypothesis-by-Hypothesis Verdict Table

| # | Candidate Hypothesis | Empirical / Diagnostic Metric | Verdict & Magnitude |
|---|---|---|---|
| **H1** | **Negative transfer between nodes and edges** | Healthy sibling-edge score change ($t=199 \to 220$) around shocked `interaction_edge` ($n=25$ seeds): at $\rho=0.0$, `edge_only` **`+0.0278`** vs `hierarchical` **`-0.0131`** and `node_only` **`-0.0600`**; at $\rho=0.50$, `edge_only` **`+0.0115`** vs `hierarchical` **`-0.0080`**. At $\rho=0.50$, `hierarchical` (`51.175`) is `3.649` steps slower than scale-matched non-sharing `edge_only_td_error` (`47.526`). | **CONFIRMED SECONDARY CAUSE (~24% of RRT gap at $\rho=0.50$).** Unconditional node pooling leaks negative errors from unshared edge shocks onto healthy sibling edges and healthy downstream $L_3$ targets. |
| **H2** | **Excessive hierarchical update overhead** | Per-trial `decision_cpu_seconds` at $\rho=0.50$ (`confirmatory/analysis.json`): `edge_only` `0.0446 s` vs `hierarchical` `0.0578 s` (`+13.2 ms` over 500 steps = `+26.4 µs/step`); `RRT` counts discrete steps, independent of wall/CPU time. | **REFUTED AS CAUSE OF RRT LOSS (CPU overhead is $+29.6\%$ / $+26\,\mu\text{s}$ per step, benign).** Compare `structured_sw_ucb` at `0.7112 s/trial` ($16\times$ slower due to $46 \times 46$ matrix inverse). |
| **H3** | **Poor adaptation timescales & effective policy scale (`EQ-B`)** | `equalization.json`: selected-score std `0.0422` vs `0.5100` (`12.08x` mismatch); path-entropy fraction `0.9695` vs `0.6289`; `edge_only_td_error` probe reproduces `75.9%` of RRT loss and `100%` of regret loss without node sharing. Plus per-step decay+shrinkage $\lambda_{\text{eff}} = 0.01697 > p_e \eta_{\text{int}} \approx 0.011$ attenuates rare-edge memory. | **CONFIRMED PRIMARY CAUSE (~76% of RRT gap and ~100% of regret gap).** Bounded TD-error scores under an uncalibrated $T=0.20$ softmax keep `hierarchical` near-uniform random, delaying sustained `0.90 × oracle` confirmation. |
| **H4** | **Incorrect credit assignment** | Exact algebraic cancellation of `source_effect[u]` in `stable_softmax` across `outgoing[u]`; outgoing shocked edges $(v^*, w)$ penalize healthy $L_3$ node `target_effect[w]` while `source_effect[v*]` has zero effect on Layer-1 entry into $v^*$. | **CONFIRMED STRUCTURAL DEFECT.** 75% of node-level gradient updates along a 2-hop traversal of `shock_node` are either cancelled in softmax (`source_effect`) or misassigned to healthy downstream targets (`target_effect[w]`). |
| **H5** | **Unnecessary structural reinforcement** | `exploration_reinforcement = 0.0` in `config.confirmatory.yaml` (dormant); pre-shock `optimal_pre_path_rate` of `hierarchical` was only `4.29%` (vs `13.64%` for `edge_only`). | **REFUTED FOR `hierarchical` IN V1.** `hierarchical` suffered from *under*-reinforcement (flat policy), not over-reinforcement of the pre-shock path. (`edge_only` reinforced pre-shock paths to `1.97`, explaining why `edge_only`'s RRT rose from `17.65` at $\rho=0$ to `36.01` at $\rho=0.50$ as multiple alternatives degraded.) |
| **H6** | **Insufficient exploration** | `equalization.json`: `exploration_step_rate` was `0.2213` (`hierarchical`) vs `0.2244` (`edge_only`); `unique_paths` visited in 200 steps was `26.97 / 27` (`hierarchical`) vs `23.04 / 27` (`edge_only`). (By contrast, `structured_sw_ucb` suffered severe under-exploration due to zero-prior pessimism `0.35 < 0.45`, censoring `17.5%` at $\rho=0.50$.) | **REFUTED FOR `hierarchical` (OPPOSITE: EXCESSIVE DIFFUSE ENTROPY); CONFIRMED FOR `structured_sw_ucb`.** `hierarchical` explored almost all 27 paths continuously (`H/H_max = 0.970`) and failed to *exploit* healthy routes once discovered. |
| **H7** | **Overreaction to correlated failures** | At $\rho = 1.00$ (purely correlated node shock), `hierarchical` achieved its *fastest* post-shock RRT across $\rho > 0$ (`31.000` steps, `0%` censored, vs `51.175` at $\rho=0.50$ and `65.103` at $\rho=0.75$). | **REFUTED.** Correlated node failure ($\rho=1.00$) was the one regime where node pooling partially helped `hierarchical`; worst performance occurred at intermediate $\rho \in \{0.25, 0.50, 0.75\}$ where mixed node + unshared edge shocks collided. |
| **H8** | **Delayed fault detection** | No explicit change-point / surprise detector exists in V1; `edge_only` must erode accumulated conductance from `~1.97` down below `0.50`, whereas `hierarchical` moves quickly per-observation on visited nodes but fails to concentrate traffic afterward (`post_opt_hit_last50 = 5.52%` vs `21.12%`). | **PARTIALLY CONFIRMED FOR BOTH ARMS (DIFFERENT MECHANISMS).** `edge_only` experiences conductance-inertia delay when a saturated `2.00` edge fails; `hierarchical` detects reward drops locally without inertia but lacks exploitation sharpness and upstream propagation of outgoing-edge faults. |
| **H9** | **Instability caused by shared state** | Confirmatory paired-difference SD jumped `1.72x` above pilot (`55.945` vs `32.521`, skewness `+1.630`, max delay `+250` steps); `node_only` (100% shared state) degraded to `92.990` RRT at $\rho=0.50$ and `3.09%` censoring (`7.22%` at $\rho=0.75$). | **CONFIRMED.** Ungated node sharing (`node_only` and `hierarchical` without discrepancy gating) amplifies cross-path variance and right-tail recovery delays when shocks are partially edge-specific. |
| **H10** | **Resource allocation inefficiency** | V1 accounts zero token, monetary, or latency budgets (`Scenario` emits unitless scalar `[0,1]` edge rewards). Meanwhile `hierarchical` spent `51.18` post-shock task executions at degraded utility (`regret = 16.002`, `+90.7%` wasted utility loss vs `edge_only`) before recovering. | **CONFIRMED ARCHITECTURAL GAP.** V1 is completely blind to token/compute cost, spending expensive degraded executions indiscriminately during diffuse exploration—motivating V2's explicit resource ledger and gated VoI/anastomosis design. |

---

## 4. Design Requirements Derived for Mycelial V2

Every design choice in the V2 evolution (`src/mycelial_graph/v2/`) directly addresses a verified V1 failure mode while keeping V1 frozen and intact:

1. **Consistent Estimator & Policy Scale (Fixes M1 / H3):** Keep component quality, cost, token, latency, and failure estimators on calibrated physical/probability scales using recency-weighted EWMA estimators, paired with normalized multi-resource utility/conductance updates that decay toward neutral prior conductance $g_0$ rather than zero.
2. **Unified Node Health + Discrepancy-Gated Anastomosis (Fixes M2 / H1 / H4 / H9):** Represent shared structural memory on **components (nodes)** rather than redundant `source_effect` parameters that cancel in softmax; propagate downstream node health/feasibility into transition scoring; and **gate anastomosis (structural state transfer)** by consistency across incident edges (suppressing node-level blame when only a single edge degrades while sibling edges remain healthy, preventing $\rho=0$ negative transfer!).
3. **Hard Feasibility & Safety Filtering Before Soft Routing (Fixes H10 & `AUD-CRIT-02/04`):** Enforce hard token/cost reservations, `max_risk`, `minimum_quality`, and `mandatory_verification` / guardrail constraints *before* stochastic exploration or conductance softmax.
4. **Connectivity-Preserving Cytoplasmic Retraction & Active Resource Translocation (Fixes H6 / H10 & `AUD-CRIT-02/03`):** Retract persistently wasteful edges only upon observed evidence while preserving `source -> sink` fallback connectivity, reducing router-evaluation overhead and translocating exploration/compute budgets toward reliable high-efficiency pathways.
