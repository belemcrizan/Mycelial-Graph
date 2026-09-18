# EQ-B Diagnostic Report — Effective Policy-Scale Mismatch (Post-Confirmatory)

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Artifact class:** post-confirmatory diagnostic (additive). Permitted-Now.
**Status:** `POST_CONFIRMATORY_DIAGNOSTIC` — does **not** alter the sealed `REFUTED` result.
**Machine-readable source:** `experiments/v1/artifacts/diagnostics/equalization.json`
**Related:** `experiments/v1/AMENDMENT_002.md`, `experiments/v1/HYPOTHESIS_MATRIX.md`,
`experiments/v1_5/PROTOCOL_EQUALIZED_RERUN.md` (frozen, not authorized to run)

---

## 0. What this document is, and is not

This report characterizes the **EQ-B confound** — a *material mismatch in effective policy scale*
between the two frozen confirmatory arms (edge-only vs. hierarchical) — as a **diagnostic** that
runs *after* and *on top of* the sealed confirmatory result.

- It **does not** re-run, re-analyze, re-weight, or re-equalize the confirmatory experiment.
- It **does not** reclassify, soften, requalify, or reframe the sealed outcome. The confirmatory
  result remains **`REFUTED`** at ρ=0.50, and the ρ=0 safety gate remains failed, exactly as
  sealed under `CONFIRMATORY_FREEZE.json` at commit `5f314d2`.
- It **is** a statement about the *limit of mechanistic attribution*: the sealed result is a valid
  comparison of *the two methods as implemented*, not proof that the *hierarchical representation
  itself* was isolated as the causal variable.

> **Guiding principle (from `equalization.json`): "Parameter parity is not policy parity."**
> The two arms shared nominal hyperparameters (exploration probability 0.08, temperature 0.20,
> identical local traversed-edge feedback contract), yet realized behavior differed enough that
> the comparison cannot be read as a clean isolation of representation.

---

## 1. Canonical result being contextualized (unchanged, sealed)

| Quantity | Value | Source |
|---|---|---|
| Primary contrast, ρ=0.50 (rel. Δ mean RRT, hier vs edge) | **+42.1%** slower | `confirmatory/analysis.json` `primary_contrast.estimate = 0.42112797` |
| 95% interval | +11.9% to +79.1% | `confidence_low 0.11899`, `confidence_high 0.79088` |
| One-sided upper bound | +72.1% | `one_sided_upper_bound 0.72138` |
| Paired pairs (N) | 97 | `frozen_contrast_integrity.primary_pairs` |
| ρ=0 safety gate | **failed** (`NEGATIVE_TRANSFER_NOT_EXCLUDED`) | `result_state.safety_gate_state` |
| Result state | **`REFUTED`** | `result_state.state` |

Nothing in §2–§6 changes any cell of this table.

---

## 2. Operational definition of "effective policy scale"

The confirmatory arms were parameterized to *look* matched, but the update machinery differs
structurally:

- **edge-only:** clipped conductance and a single `learning_rate`; scores are bounded.
- **hierarchical:** unbounded additive scores decomposed into `node_learning_rate`,
  `interaction_learning_rate`, `shrinkage`, and a sum-to-zero projection.

"Effective policy scale" is therefore defined operationally, from realized traces (not from nominal
knobs), by the following observable proxies, each computed per arm from selected-action traces:

1. **Path-entropy fraction of max** — realized exploration spread over the path space.
2. **Selection concentration** — Herfindahl index and max-path probability over realized paths.
3. **Effective temperature proxy** — a softmax temperature *inferred from path entropy* (a proxy,
   not a fitted temperature; see §5 trace limitation).
4. **Optimal-pre-path rate** — fraction of pre-shock decisions landing on the pre-shock optimum.
5. **Exploration-step rate** — realized fraction of exploration steps.
6. **Selected-score dispersion** — standard deviation of the selected-edge scores.

These are exactly the quantities recorded per (method × ρ) in `equalization.json`.

---

## 3. Quantified mismatch (pre-shock warm-up, from `equalization.json`)

The gaps below are stable across ρ ∈ {0.0, 0.5, 1.0}; the pre-shock warm-up is shared across ρ, so
one representative comparison suffices. Values are means over the 97 confirmatory trials.

| Proxy | edge-only | hierarchical | Gap / ratio | EQ tolerance | Verdict |
|---|---:|---:|---:|---:|---|
| Path-entropy fraction of max | 0.629 | 0.969 | gap 0.341 | 0.20 | **exceeded** |
| Herfindahl (selection concentration) | 0.262 | 0.044 | ~6× | — | large |
| Max path probability | 0.463 | 0.075 | ~6× | — | large |
| Effective temperature proxy | 0.370 | 0.030 | ~12× | — | large |
| Selected-score std | 0.515 | 0.043 | **ratio 12.08** | 2.0 | **exceeded** |
| Optimal-pre-path rate | 0.148 | 0.045 | gap 0.094 | 0.15 | within |
| Exploration-step rate | 0.217 | 0.224 | gap 0.003 | 0.05 | within |
| Unique paths | 22.9 | 26.9 | — | — | comparable |

**Reading.** The two arms share the *exploration-step rate* (0.003 gap, well within tolerance) and
remain in a comparable, non-degenerate exploration regime (neither collapses to a single path;
both explore ~23–27 unique paths). But the hierarchical arm operates at a **much flatter realized
policy** (path-entropy fraction 0.97 vs 0.63; ~12× lower selected-score dispersion; ~6× lower
selection concentration). That is the EQ-B signature: **the arms are matched on nominal parameters
and on raw exploration frequency, but not on the effective scale/sharpness of the induced policy.**

Two proxies (optimal-pre-path rate, exploration-step rate) are *within* tolerance; three
(path-entropy fraction, selected-score std ratio, and the concentration family) are *outside*. The
classification is **EQ-B**: a material but bounded mismatch — enough to limit attribution, not
enough to declare the arms operating in different regimes (which would be EQ-C).

---

## 4. What EQ-B does and does not license

**Does (attribution limit).**
- The sealed `REFUTED` outcome compares the *implemented* edge-only and hierarchical methods.
- It **cannot** be read as "the hierarchical *representation* is what caused the slower recovery",
  because the hierarchical arm also ran a flatter, differently-scaled effective policy. The
  representation and the effective policy scale are **entangled** in the frozen implementation.

**Does not (no anulment).**
- EQ-B is **not** an "error" that "invalidates" the result. It is a boundary on *mechanistic
  interpretation*, not on the *comparative fact*.
- EQ-B does **not** re-equalize the experiment retroactively, change N=97, touch the seeds, or move
  any threshold.
- EQ-B is **not** grounds to reopen or rewrite `REFUTED`. Per the project interdict, the sealed
  confirmatory result is not subject to overwrite even with authorization.

---

## 5. Trace limitation (honest scope of the diagnostic)

Stored traces contain **selected-edge scores only**, not the full candidate-score vector. As a
consequence:

- Action entropy, layer-conditional entropy, selection concentration, exploration rate, and
  optimal-path rate are computed from **realized actions**, not from full policy distributions.
- The "effective temperature" is a **proxy** derived from path entropy, not a temperature fit to a
  softmax over all candidates.

This means the EQ-B *magnitude* is estimated under a realized-action approximation. It is
sufficient to establish the *existence and direction* of the mismatch (which is large and
consistent), but a fully-resolved policy-scale equalization requires re-instrumented traces — which
is precisely what the frozen equalized re-run protocol (§6) is designed to capture.

---

## 6. Staged remedy (frozen, NOT authorized to run)

The forward path to *separate* representation from effective policy scale is a **pre-registered,
equalized re-run**, prepared as a frozen artifact and gated behind explicit human authorization:

- Protocol: `experiments/v1_5/PROTOCOL_EQUALIZED_RERUN.md`
- Config: `experiments/v1_5/config.equalized.yaml` (`status: frozen`, `authorized: false`)

That protocol pairs the arms on **effective** policy scale (matched realized path-entropy fraction
and selected-score dispersion targets), keeps the same estimand (RRT), the same gates, and draws
**new sealed seeds with no overlap**. It is ready to authorize and incapable of running on its own.
Executing it is a **human gate** (see MASTER_PROMPT §5.2) and additionally requires the moratorium
amendment (`experiments/PROTOCOL_AMENDMENT_002_PROPOSAL.md`).

---

## 7. Figures

Figure assets for this diagnostic are the pre-shock warm-up comparisons already sealed in the
paper's figure set (`paper/tmlr/figures/equalization_warmup.png`). No figure is deleted or
regenerated here; this report cross-links the existing sealed figure rather than duplicating it.

---

## 8. Honest status

- **Added:** this report + cross-links; no data recomputed, no artifact modified.
- **Unchanged / preserved:** `REFUTED`, the freeze, the moratorium, all sealed artifacts and
  hashes. `equalization.json` is read-only input here.
- **Claim boundary:** EQ-B is an attribution limit, disclosed prominently; it is *not* a
  reclassification and *not* evidence about real-world systems.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
