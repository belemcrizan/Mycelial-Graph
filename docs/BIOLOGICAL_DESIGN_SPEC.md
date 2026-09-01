# Biological Design Specification — Mycelial Graph V2

**Claim discipline.** This document records *inspirations* and *testable computational hypotheses*. It does not claim that fungi prove an algorithm, that the design is biologically optimal, or that Physarum is a fungus.

**Physarum polycephalum is not a fungus.** It is a slime mold (Amoebozoa). If a later version imports Physarum-style shortest-path or flow algorithms, they must be labeled **slime-mold-inspired transport**, never fungal biology. V2.0-alpha implements **fungal-inspired** mechanisms only.

For each item: observation → abstraction → mechanism → hypothesis → ablation → failure condition.

---

## 1. Hyphal branching

**Biological observation.** Filamentous fungi explore heterogeneous substrates by apical growth and branching. New hyphae are not free; biomass and cytoplasm are spent.

**Computational abstraction.** When uncertainty, novelty, or disruption raises the value of information, the controller may select an alternative local option (retriever, model class, verification).

**Mathematical mechanism (alpha).** Topology is a frozen DAG (no free extra edges). Branching is expressed as *costed exploration* plus MVC at choice nodes. Opening a more expensive option requires `E[ΔQ] / ΔR > τ`. Router tokens scale with the number of scored candidates (`NetworkMaintenanceCost`).

**Hypothesis.** Under hidden task difficulty, costed MVC exploration reduces tokens on easy tasks without quality loss beyond `ε` relative to always-high-compute.

**Ablation.** `-no-uncertainty` (later); in alpha, `v2_no_cost_awareness` and always-high/low bounds.

**Failure.** Exploration explosion: router tokens erase endpoint savings; or premature cheap routing on hard tasks.

---

## 2. Anastomosis

**Biological observation.** Hyphae can fuse, forming loops and allowing cytoplasm/signal sharing.

**Computational abstraction.** Two routes may share verified artifacts (facts, tool results, compressed state). Blind sharing risks negative transfer.

**Mathematical mechanism (alpha).** Specified, **disabled**. Shared-state merge operators are V2.1. Default policy: `no_anastomosis`.

**Hypothesis.** Restricted anastomosis reduces duplicate retrieval tokens without lowering quality; full anastomosis increases negative transfer after QUALITY_SHOCK.

**Ablation.** `full_anastomosis` / `restricted_anastomosis` / `no_anastomosis` (alpha implements only none).

**Failure.** Contaminated working state after a corrupted route.

---

## 3. Cord formation

**Biological observation.** Frequently used, high-yield pathways can thicken into cords — structural reinforcement, not unbounded growth.

**Computational abstraction.** Routes with high utility per resource receive higher conductance and more budget, with saturation.

**Mathematical mechanism.**

```text
G ← clip((1-δ)G + α (U_obs - 0.5) + β demand - η waste, G_min, G_max)
```

**Hypothesis.** Cord reinforcement accelerates re-selection of a post-shock efficient corridor versus quality-only V1 conductance.

**Ablation.** `v2_no_cord`.

**Failure.** Runaway reinforcement / provider lock-in after a temporary price drop.

---

## 4. Cytoplasmic retraction / pruning

**Biological observation.** Low-yield hyphae can lose cytoplasm; retraction is typically persistent, not a single failed probe.

**Computational abstraction.** Persistently costly, redundant, or failing routes lose budget.

**Mathematical mechanism.** Windowed `PruneScore` with minimum evidence `K` and confidence via observation counts.

**Hypothesis.** Pruning reduces tokens after OUTAGE/PRICE_SHOCK without increasing quality loss beyond `ε`, whereas instantaneous pruning harms recovery.

**Ablation.** `v2_no_pruning`.

**Failure.** Premature pruning of a temporarily noisy high-quality route.

---

## 5. Resource translocation

**Biological observation.** Mycelial networks move resources toward demand and away from depleted or unproductive regions.

**Computational abstraction.** Budget is conserved globally and reallocated during execution, not only at t=0.

**Mathematical mechanism.**

```text
share_e ∝ max(ε, Ũ_e (1 + κ σ_e))
B ← (1-μ) B + μ B_max share
Σ B_e = B_max
```

**Hypothesis.** Dynamic transfer improves the quality-token frontier versus `fixed_budget` under RESOURCE_SCARCITY and MIXED_SHOCK.

**Ablation.** `v2_no_transfer`.

**Failure.** Budget thrashing (high route churn, oscillation).

---

## 6. Damage response / rerouting

**Biological observation.** Networks can recircuit around damage rather than rebuilding the entire colony.

**Computational abstraction.** After provider outage, price jump, or quality drift, local updates plus translocation should restore quality with lower recovery tokens than always-high-compute.

**Mathematical mechanism.** Same controller; environment supplies non-stationary indexed outcomes. Metrics: time-to-recovery, token-cost-to-recovery, quality-loss-during-recovery, route churn.

**Hypothesis.** V2 recovery token cost is lower than always-high-compute while remaining quality-non-inferior, in at least one frozen regime.

**Ablation.** Shock-memory off is V2.1; alpha tests the live adaptive state as-is.

**Failure.** Catastrophic adaptation (quality collapse) or freeze on a dead route.

---

## 7. Foraging: exploration front vs exploitation

**Biological observation.** Fungi often probe cheaply, then concentrate biomass where returns justify it.

**Computational abstraction.** Cheap probes → evaluate signals → infer difficulty → allocate compute → verify or stop → retract weak routes.

**Mathematical mechanism.** MVC stop at the verification layer; conductance + budget concentration on the model layer.

**Hypothesis.** Inferred difficulty (not leaked labels) predicts compute class: easy→cheap, hard→frontier, better than chance under label permutation of task IDs.

**Ablation.** vs always-high, always-low, random, epsilon-greedy, v1_edge_only.

**Failure.** Memorizing scenario seeds; no generalization across new seeds.

---

## Computational metabolism (fungal economy)

A trial has finite `B_max` (tokens or composite units). The controller must choose where to grow (explore), reinforce, maintain, retract, move resources, and stop. These are implemented as budget, conductance, prune, transfer, and stop operators — not as decorative names.

---

## What this document forbids

- “Fungi prove this algorithm is optimal.”
- “Biologically optimal routing.”
- Treating slime-mold flow as fungal cord formation.
- Using biology as rhetoric when an ablation cannot disable the mechanism.
