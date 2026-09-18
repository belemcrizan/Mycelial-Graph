# Estimand Bridge — RRT ↔ Real Logs

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Artifact class:** navigation + honesty doc (additive). Permitted-Now.
**Companions:** `docs/EXTERNAL_VALIDATION_LADDER.md`,
`external/protocols/EXTERNAL_OPE_PREREG.md`, `research/EXTERNAL_VALIDATION_PLAN.md`.

---

## 0. The problem this bridges

The V1 confirmatory estimand is **restricted recovery time (RRT)** under a *controlled* correlated
shock parameter ρ, on a synthetic DAG with known propensities. Real logs never hand you all four of:
**real reward geometry**, **real (natural) shock**, **DAG/pooling structure**, and **logging
propensities** simultaneously. This document states the two honest routes from RRT to real data and
exactly what each one can and cannot support. It is descriptive; it authorizes nothing.

## 1. Route A — Natural change-points (real shock, no ρ control)

- **Exemplar:** Yahoo! Front Page R6A/R6B (uniformly-random logging → unbiased replay), where
  article CTR genuinely rises and falls over time.
- **Supports:** *end-to-end recovery under real non-stationarity* — a real analog of "how fast does
  the policy re-optimize after the world shifts?"
- **Cannot support:** the ρ contrast. There is no correlated-shock knob; you observe *whatever*
  change-points nature produced, not a matched ρ=0.50 vs ρ=0 comparison. The V1 primary estimand is
  therefore **not** reproducible on Route A; only the recovery *phenomenon* is.

## 2. Route B — Injected shock on real geometry (ρ control, semi-synthetic shock)

- **Exemplars:** RouterBench, RouterEval, SPROUT, LLMRouterBench (real per-model cost/quality),
  BEIR/MS MARCO (real retrieval geometry).
- **Supports:** the *ρ contrast* on **real reward geometry** — you can dial correlated vs
  independent shocks over real per-arm rewards and measure RRT-like recovery.
- **Cannot support:** a claim that the shock is *natural*. The non-stationarity is **injected**
  (semi-synthetic). Any RRT measured here inherits a "shock is synthetic" caveat and cannot be
  presented as real-world non-stationarity.

## 3. The unavoidable gap (stated plainly)

> **There is no public dataset with real reward geometry + real (natural) shock + DAG/pooling
> structure + logging propensities, all at once.** Route A gives real shock but no ρ control and no
> pooling structure; Route B gives ρ control and real geometry but a synthetic shock. Layer-3
> sources (HPO-B, cluster traces, telemetry) supply realistic *structure/topology* but not the
> reward estimand. Bridging the full estimand would require either a governed proprietary trace
> (Vivo/Telefónica, ceiling option, not authorized) or a purpose-built collection — neither of
> which is done or authorized here.

## 4. Consequence for claims

- A future Route A result may claim **real recovery**, not a ρ contrast.
- A future Route B result may claim a **ρ contrast on real geometry**, not real non-stationarity.
- Neither route, alone, reproduces the *full* V1 estimand; combining them is triangulation, not a
  single reproduction.
- None of this changes the sealed V1 `REFUTED` result, which stands on its synthetic terms with the
  EQ-B attribution limit already disclosed.

## 5. Honest status

- **Added:** this bridge doc.
- **Unchanged / preserved:** no data ingested; no estimand redefined; `REFUTED`, the freeze, and the
  moratorium intact.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
