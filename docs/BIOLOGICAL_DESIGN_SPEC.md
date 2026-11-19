# Biological Design Specification — Mycelial V2

Every bioinspired mechanism in Mycelial-Graph V2 is an **operational, falsifiable computational operator** over $G = (V, E, S, B, H)$. True fungal mycelia (filamentous hyphal networks in Basidiomycota/Ascomycota, distinct from amoeboid *Physarum* slime molds) inspire local decentralized rules, **not** claims of biological equivalence. Any mechanism that degrades performance in a regime is documented honestly and can be disabled via explicit controller flags.

All paired ablation results below come from `experiments/v2_2/config.ablation.yaml` (`N = 24` paired scenarios per regime, 80 steps/trial, shared common-random-numbers stream `agent:{regime}:v2_mycelial_family`, summarized in `experiments/v2_2/PILOT_SUMMARY.json`).

---

## Mechanism A — Hyphal Branching & Value-of-Information (VoI) Exploration

1. **Biological motivation:** Growing hyphal tips branch laterally into unexplored substrate to locate nutrients when local gradients are uncertain, while metabolically expensive foraging into barren zones is suppressed.
2. **Computational abstraction:** Controlled stochastic exploration weighted by epistemic edge uncertainty minus normalized token burden, replacing blind uniform $\varepsilon$-greedy jumps.
3. **Mathematical definition:**
   - Epistemic-empirical uncertainty for edge $e$ with visit count $n_e$ and EWMA quality variance $\hat{\sigma}_e^2$:
     $$u_e = 0.6 \frac{0.22}{\sqrt{n_e + 1}} + 0.4 \sqrt{\max(\hat{\sigma}_e^2, 10^{-6})}$$
   - Duringexploitation scoring: $\Delta s_e^{\text{VoI}} = \max(0,\, 0.22\,u_e - 0.12\,\lambda_t \tilde{T}_e)$.
   - On exploratory steps ($\text{Bernoulli}(p_{\text{exp}})$): sample candidate $e \in \mathcal{A}(v)$ from $\text{softmax}\big((u_e - 0.25\,\lambda_t \tilde{T}_e) / \max(0.08, \tau/2)\big)$ instead of uniform random.
4. **Implementation:** `HealthSignals.uncertainty` (`src/mycelial_graph/v2/graph_model.py`), `MycelialResourceController._edge_score` & `choose` (`src/mycelial_graph/v2/policies/controller.py`, flag `branching=True`).
5. **Measurable hypothesis:** VoI-guided branching reduces post-shock Restricted Recovery Time (RRT) and avoids wasting exploratory calls on `920`-token tier-2 edges compared to uniform exploration (`v2_no_branching`).
6. **Ablation experiment (`v2_mycelial` minus `v2_no_branching`, $N = 24$):**
   - `OUTAGE`: $\Delta\text{RRT} = -1.875$ steps (`4.42` vs `6.29`), $\Delta\text{tokens} = -396.2$.
   - `MIXED_CORRELATION`: $\Delta\text{RRT} = -1.875$ steps (`8.46` vs `10.33`).
   - `RESOURCE_SCARCITY`: $\Delta\text{RRT} = -1.458$ steps (`26.79` vs `28.25`), $\Delta\text{tokens} = -765.8$, $\Delta\text{cost} = -\$1.55$.
   - `PRICE_SHOCK`: $\Delta\text{RRT} = -1.250$ steps (`19.79` vs `21.04`), $\Delta\text{tokens} = -661.6$.
   - `QUALITY_SHOCK`: $\Delta\text{RRT} = -1.042$ steps (`4.58` vs `5.63`), $\Delta\text{tokens} = -1,128.1$.
7. **Documented failure condition:** Under isolated single-edge `LOCAL_OUTAGE` where most sibling edges remain healthy, continued VoI probing slightly delays trailing-window confirmation ($\Delta\text{RRT} = +2.667$ steps, $\Delta Q = -0.0027$) despite saving `1,164.1` tokens (`-\$2.78`).

---

## Mechanism B — Discrepancy-Gated Anastomosis

1. **Biological motivation:** Hyphal fusion (anastomosis) interconnects parallel hyphae to share signaling molecules and nutrients across a colony, accompanied by somatic incompatibility/septal gating that seals off damaged or incompatible filaments to prevent systemic necrosis.
2. **Computational abstraction:** Node-level pooling of incoming transition health estimates $(\hat{q}_v, \hat{c}_v, \hat{f}_v)$ into sibling edges $(u', v)$, gated by an exponential discrepancy kernel over observed incoming siblings so edge-specific faults do **not** corrupt healthy siblings (solving V1's $\rho = 0$ negative-transfer failure).
3. **Mathematical definition:**
   Let $\mathcal{I}_{\text{obs}}(v) = \{e \in \text{in}(v) : n_e > 0\}$. For $|\mathcal{I}_{\text{obs}}(v)| \ge 2$:
   $$D(v) = \max_{e \in \mathcal{I}_{\text{obs}}(v)} |\hat{q}_e - \bar{q}_v| + 0.25 \frac{\text{std}_{e \in \mathcal{I}_{\text{obs}}(v)}(\hat{c}_e)}{\max(0.05, \bar{c}_v)}, \qquad g(v) = g_{\max} \exp\!\left(-\left(\frac{D(v)}{\sigma_{\text{disc}}}\right)^2\right)$$
   with $g_{\max} = 0.45, \sigma_{\text{disc}} = 0.12$ (and cautious $g(v) = 0.55\,g_{\max}$ when $|\mathcal{I}_{\text{obs}}(v)| = 1$). Effective estimate: $\tilde{q}_e = (1 - g(v))\hat{q}_e + g(v)\hat{q}_v$.
4. **Implementation:** `HealthSignals.anastomosis_gate` (`src/mycelial_graph/v2/graph_model.py`), `MycelialResourceController._effective_estimates` (`src/mycelial_graph/v2/policies/controller.py`, flag `anastomosis=True`).
5. **Measurable hypothesis:** Accelerates sibling adaptation under shared component shocks (`OUTAGE`, `PRICE_SHOCK`) while holding negative transfer near zero under purely edge-specific `LOCAL_OUTAGE` ($\rho = 0$).
6. **Ablation experiment (`v2_mycelial` minus `v2_no_anastomosis`, $N = 24$):**
   - Unit verification (`test_anastomosis_gate`): $g(v) > 0.30$ under correlated node failure vs. $g(v) < 0.02$ under discordant single-edge failure.
   - `PRICE_SHOCK`: $\Delta\text{RRT} = -1.292$ steps (`19.79` vs `21.08`), $\Delta Q = +0.00081$, $\Delta\text{router\_tokens} = -19.4$.
   - `LOCAL_OUTAGE` ($\rho = 0$): **Zero negative transfer** — $\Delta\text{RRT} = -0.792$ steps (`18.29` vs `19.08`), $\Delta Q = +0.00011$, $\Delta\text{cost} = -\$0.52$.
   - `RESOURCE_SCARCITY` & `OUTAGE`: $\Delta\text{RRT} = -0.333$ and $-0.208$ steps, saving `-\$1.73` cost (`RESOURCE_SCARCITY`) and `-239.4` tokens (`OUTAGE`).
7. **Documented failure condition:** Under `MIXED_CORRELATION` ($50\%$ node / $50\%$ edge shock), initial sibling observations before discordant edges are sampled produce transient partial pooling ($\Delta Q = -0.0025$, $\Delta\text{RRT} = +0.375$ steps) while saving `523.1` tokens.

---

## Mechanism C — Reliable-Utility Cord Reinforcement

1. **Biological motivation:** Mycelial cords thicken selectively along persistent, productive nutrient-transport highways rather than along transient or unproductive exploratory filaments.
2. **Computational abstraction:** Positive structural conductance reinforcement fires **only** when a traversed transition succeeds (`obs.success == True`) and delivers net resource-adjusted utility strictly above the prior `initial_conductance`, weighted by empirical reliability $(1 - \hat{f}_e)$; unvisited edges decay smoothly back toward `initial_conductance` rather than collapsing to zero.
3. **Mathematical definition:**
   $$C_e(t+1) = \Pi_{[C_{\min}, C_{\max}]}\!\Big(C_0 + (1 - \gamma)(C_e(t) - C_0) + \mathbb{I}[e \in P_t]\big[\eta (U_e - C_0) + 0.06\,\kappa_e\big] - 0.10\,W_e\Big)$$
   where $\kappa_e = (1 - \hat{f}_e)\max(0, U_e - C_0)\,\mathbb{I}[\text{success}_e]$ when `cord=True` (and $0$ otherwise), and $W_e = \max(0, \text{burden}_e - q_e\,\mathbb{I}[\text{success}_e])$.
4. **Implementation:** `update_conductance` (`src/mycelial_graph/v2/biology/conductance.py`) and `MycelialResourceController.update` (`flag: cord=True`).
5. **Measurable hypothesis:** Prevents cheap failing paths from accumulating usage-frequency reinforcement and stabilizes post-shock routing onto reliable efficient corridors (`\Delta\text{RRT} \le 0`).
6. **Ablation experiment (`v2_mycelial` minus `v2_no_cord`, $N = 24$):**
   - `MIXED_CORRELATION`: $\Delta\text{RRT} = -2.000$ steps (`8.46` vs `10.46`), $\Delta Q = +0.00193$, $\Delta\text{cost} = -\$0.52$.
   - `RESOURCE_SCARCITY`: $\Delta\text{RRT} = -1.125$ steps (`26.79` vs `27.92`), $\Delta\text{cost} = -\$0.74$.
   - `OUTAGE`: $\Delta\text{RRT} = -0.083$ steps, $\Delta\text{tokens} = -714.2$, $\Delta\text{cost} = -\$0.79$.
   - `PRICE_SHOCK`: $\Delta\text{RRT} = -0.208$ steps, $\Delta\text{tokens} = -298.3$.
7. **Documented failure condition:** When a previously reliable highway suffers a pure `PRICE_SHOCK` (quality stays high while price spikes, so no failure event occurs on step 1), thickened pre-shock cord conductance adds 1–2 steps of price inertia (`\Delta\text{cost} = +\$2.75` vs `v2_no_cord`).

---

## Mechanism D — Connectivity-Preserving Cytoplasmic Retraction

1. **Biological motivation:** Fungal networks regress cytoplasm from persistently inefficient or dead hyphal branches and recycle resources into active corridors while preserving core colony connectivity.
2. **Computational abstraction:** Observation-gated persistence counter `prune_evidence[e]` over resource burden, sibling redundancy, and failure probability. Persistently dominated edges (`prune_evidence >= prune_persistence` after `>= min_prune_observations` real visits) are marked `pruned` (omitted from routine router candidate scoring, saving `router_tokens`), subject to a **strict out-degree connectivity invariant** (every node keeps $\ge 1$ active outgoing edge, proven via `hypothesis` to preserve `source -> sink` reachability) and a $3\%$ rehabilitation probe.
3. **Mathematical definition:**
   $$s_e^{\text{prune}} = 0.35\,\text{burden}_e + 0.30\,\max_{s \in \text{sib}(e)}(U_s - U_e)_+ + 0.25\,\hat{f}_e + 0.10\,\max(0, 0.5 - (q_e - \text{burden}_e))$$
   Evidence updates **only** for $e \in P_t$ with $n_e \ge n_{\min}$: $k_e(t+1) = k_e(t) + 1$ if $s_e^{\text{prune}} \ge \theta_{\text{prune}}$, else $\max(0, k_e(t) - 1)$. If all $e \in \text{out}(u)$ have $k_e \ge K_{\text{persist}}$, $\arg\min_{e \in \text{out}(u)} s_e^{\text{prune}}$ is forced unpruned.
4. **Implementation:** `prune_score`, `update_prune_evidence` (`src/mycelial_graph/v2/biology/pruning.py`, flag `pruning=True`).
5. **Measurable hypothesis:** Weakens persistently wasteful/expensive branches after shock, cutting monetary cost and token waste without severing graph connectivity.
6. **Ablation experiment (`v2_mycelial` minus `v2_no_pruning`, $N = 24$):**
   - `PRICE_SHOCK`: **Saves `-\$9.07` monetary cost** and **`-1,118.0` tokens** per trial by retracting price-shocked corridors permanently after `prune_persistence = 4` post-shock visits.
   - `MIXED_CORRELATION`: $\Delta Q = +0.00138$, $\Delta\text{RRT} = -0.750$ steps, $\Delta\text{tokens} = -962.8$, $\Delta\text{cost} = -\$1.98$.
   - `OUTAGE`: $\Delta Q = +0.00289$, $\Delta\text{RRT} = -0.958$ steps, $\Delta\text{tokens} = -421.9$, $\Delta\text{cost} = -\$1.53$.
7. **Documented failure / no-benefit condition:**
   - Under `RESOURCE_SCARCITY`, hard step-budget filtering already excludes expensive corridors before `min_prune_observations` accumulates (`\Delta = 0.0` across all metrics — exact no-op).
   - If a retracted corridor later heals silently without active-corridor failure, rediscovery relies on the $3\%$ rehabilitation probe (~33 multi-candidate steps expected delay).

---

## Mechanism E — Active Resource Translocation

1. **Biological motivation:** Mycelia actively translocate carbon, nitrogen, and phosphorus from nutrient-rich or low-demand zones toward high-efficiency growing fronts while keeping basal maintenance across surviving filaments.
2. **Computational abstraction:** Floor-preserving simplex projection distributing per-step token allowance `step_cap` across graph edges in proportion to efficiency-weighted conductance, coupled back into `_edge_score` via a bounded log-coverage ratio so corridors starved of budget are actively deprioritized.
3. **Mathematical definition:**
   Given floor $b_{\min} = \frac{B_{\text{step}}}{|E|} C_{\min}$ and efficiency weights $w_e = C_e \max(\hat{q}_e - \lambda_c \tilde{c}_e, 0.05)$:
   $$b^*_e = b_{\min} + (B_{\text{step}} - |E|\,b_{\min}) \frac{w_e}{\sum_j w_j}, \qquad b_e(t+1) = (1 - \beta_{\text{mix}})\,b_e^{\text{scaled}}(t) + \beta_{\text{mix}}\,b^*_e$$
   satisfying exact conservation $\sum_e b_e(t+1) = B_{\text{step}}$ and $b_e(t+1) \ge b_{\min}$ (`hypothesis` verified). Routing bias: $+0.08 \ln\,\text{clip}\!\big(\frac{3.5\,b_e}{\max(\hat{T}_e, 10)}, 0.25, 2.5\big)$.
4. **Implementation:** `translocate` (`src/mycelial_graph/v2/biology/translocation.py`), `MycelialResourceController._edge_score` & `update` (`flag: transfer=True`).
5. **Measurable hypothesis:** Shifts token expenditure away from 920-token low-marginal-gain routes toward 90–240-token efficient routes, reducing total tokens across regimes and speeding adaptation under `RESOURCE_SCARCITY`.
6. **Ablation experiment (`v2_mycelial` minus `v2_no_transfer`, $N = 24$):**
   - **Reduces post-shock tokens across all 6 regimes:** `-2,219.7` (`OUTAGE`), `-1,992.7` (`LOCAL_OUTAGE`), `-1,830.6` (`QUALITY_SHOCK`), `-1,754.3` (`PRICE_SHOCK`), `-1,728.5` (`MIXED_CORRELATION`), and `-1,091.5` (`RESOURCE_SCARCITY`).
   - `RESOURCE_SCARCITY`: $\Delta\text{RRT} = -2.208$ steps (`26.79` vs `29.00`), $\Delta\text{cost} = -\$1.44$.
7. **Documented failure condition:** When global budgets are generous and quality margin is tight, translocation's preference for token-lean corridors trades `-0.0032` to `-0.0088` raw expected quality for `-1,100` to `-2,200` token savings.

---

## Mechanism F — Damage Resilience & Surprise-Triggered Shock Memory

1. **Biological motivation:** Local mechanical severing or toxic shock in hyphae triggers rapid Woronin-body/septal pore plugging and localized wall remodeling, preventing prolonged leakage through a ruptured segment while preserving intact upstream/downstream network memory.
2. **Computational abstraction:** Standardized surprise detection on quality and cost residuals ($z > 2.5$) or unexpected failure on previously reliable edges ($\hat{f}_e < 0.20$). Firing a shock flag boosts local EWMA adaptation rate ($\alpha_{\text{shock}} = 0.55$ vs $\alpha_{\text{base}} = 0.22$) and immediately dampens stale conductance inertia ($C_e \leftarrow 0.5 C_e + 0.5 C_{\min}$) on **only** the affected transition without resetting unaffected graph state.
3. **Mathematical definition:**
   $$\text{shock}_e = \mathbb{I}\!\left[n_e > 2 \land \left(\frac{|q_t - \hat{q}_e|}{\sqrt{\max(\hat{\sigma}_e^2, 10^{-4})}} > 2.5 \;\lor\; \frac{|c_t - \hat{c}_e|}{\max(0.05, 0.5\hat{c}_e)} > 2.5 \;\lor\; (\neg\text{success}_t \land \hat{f}_e < 0.20)\right)\right]$$
4. **Implementation:** `HealthSignals.observe` (`src/mycelial_graph/v2/graph_model.py`) and `MycelialResourceController.update` (`flag: shock_memory=True`).
5. **Measurable hypothesis:** Dramatically shortens post-shock recovery time (`RRT`) and improves post-shock quality without requiring a global policy reset.
6. **Ablation experiment (`v2_mycelial` minus `v2_no_shock_memory`, $N = 24$):**
   - `RESOURCE_SCARCITY`: **$\Delta\text{RRT} = -8.750$ steps** (`26.79` vs `35.54`), **$\Delta Q = +0.00886$**, $\Delta\text{router\_tokens} = -30.7$.
   - `MIXED_CORRELATION`: **$\Delta\text{RRT} = -2.833$ steps** (`8.46` vs `11.29`), **$\Delta Q = +0.00808$**, $\Delta\text{router\_tokens} = -100.1$.
   - `LOCAL_OUTAGE`: **$\Delta\text{RRT} = -2.750$ steps** (`18.29` vs `21.04`), $\Delta Q = +0.00217$, $\Delta\text{cost} = -\$0.79$.
   - `PRICE_SHOCK`: **$\Delta\text{RRT} = -2.167$ steps** (`19.79` vs `21.96`), $\Delta Q = +0.00340$, $\Delta\text{router\_tokens} = -66.2$.
   - `QUALITY_SHOCK`: **$\Delta\text{RRT} = -1.417$ steps** (`4.58` vs `6.00`), $\Delta Q = +0.00106$, $\Delta\text{router\_tokens} = -81.3$.
7. **Documented failure condition:** Under high observation noise ($\sigma_q \ge 0.16$) or single-outlier tail draws, false-positive surprise events can prematurely dampen a healthy high-tier edge, and rapid post-shock rerouting away from broken low-tier edges shifts traffic onto healthier mid-tier corridors (`+1,907` to `+3,115` path tokens vs remaining stuck on a failing `90`-token edge).
