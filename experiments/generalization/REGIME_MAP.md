# MG-EXP-REGIME-001 — Regime Generalization / Boundary-of-Validity Map (FROZEN, NOT AUTHORIZED)

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Serves:** Master Prompt Part II §8 · Kernel gate: **GATE-FROZEN**.
**Status:** `frozen` · `authorized: false`.

---

## 0. Objective

Produce a **boundary-of-validity map**, not a leaderboard (§8). Do not collapse regimes into a single
mean. For each method × regime, classify into exactly one of: **improves / statistically unresolved /
degrades**, per predefined statistical rules (§10) — never eyeballed.

## 1. Regime set

Primary: STATIC · DRIFT · PRICE_SHOCK · QUALITY_SHOCK · LATENCY_SHOCK · OUTAGE · MIXED_SHOCK ·
RESOURCE_SCARCITY · BURST_LOAD · ADVERSARIAL_COST · CORRELATED_PROVIDER_FAILURE ·
TASK_DIFFICULTY_SHIFT.
Legacy (where relevant): SHOCK · OSCILLATORY · ADVERSARIAL.

## 2. Classification rule (predefined)

For each (method, regime): the primary contrast vs the pre-registered comparator is evaluated with a
one-sided/two-sided interval at the frozen α, with the effect direction and the relevant-effect
threshold both fixed in advance. **"statistically unresolved"** is the honest default when the
interval does not clear the threshold — this is *not* "no effect" and *not* "harm" (INV-04).

## 3. Outputs

A machine-readable regime map (`analysis.json`): rows = (method, regime, topology), columns =
{estimate, interval, class, n, power_flag}. Underpowered cells are flagged, never reported as
evidence of absence (INV-04).

## 4. Gate & evidence class

Execution **GATE-FROZEN**; outputs **SYNTHETIC** unless externally grounded per the validation
ladder. Feeds Paper B §9 (regime map) and the failure taxonomy (§17).

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
