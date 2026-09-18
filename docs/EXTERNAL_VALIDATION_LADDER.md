# External Validation Ladder

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Artifact class:** navigation + governance doc (additive). Permitted-Now.
**Companions:** `external/protocols/EXTERNAL_OPE_PREREG.md` (frozen pre-registration),
`research/EXTERNAL_VALIDATION_PLAN.md` (existing pyramid), `external/DATA_SOURCES.md`,
`docs/ESTIMAND_BRIDGE.md`.

---

## 0. Why this ladder exists

`external/` today is **infrastructure** (adapters, schemas, OPE estimators, collectors). This
document states, rung by rung, exactly **what evidence each rung would buy** and **where it stops**,
so that no one mistakes an adapter, a fixture, or a dry-run for external validity. It refines the
existing E0–E8 ladder in `research/EXTERNAL_VALIDATION_PLAN.md` by attaching a sub-claim and a limit
to each external rung.

**Interdict:** climbing any rung that requires real data or paid access is a human gate
(MASTER_PROMPT §5.4). This doc prepares; it does not climb.

## 1. The three layers (from the frozen pre-registration)

| Layer | Question it answers | Reward geometry | Shock | ρ control | Propensity |
|---|---|---|---|---|---|
| **1 — Recovery** | Does structure-aware routing recover under **real** non-stationarity? | logged (real) | **natural** (Yahoo R6) or none | no | true/uniform (OPE-valid) |
| **2 — Real reward geometry** | Given **real** cost/quality, does pooling help under controlled ρ? | **real** (RouterBench et al.) | **injected** (semi-synthetic) | yes | source-dependent |
| **3 — Pooling & topology** | Is the structural ρ / shared-shock topology **realistic**? | n/a (structure only) | real topology | structural | n/a |

No single public dataset provides real geometry **+** real shock **+** DAG structure **+**
propensities together. This gap is the subject of `docs/ESTIMAND_BRIDGE.md`.

## 2. Rung status (current)

| Rung | Description | Status | Sub-claim if climbed | Hard limit |
|---|---|---|---|---|
| E0 | pooling toy | implemented | mechanism illustration | not evidence of real effect |
| E1 | synthetic controlled (V1) | executed → `REFUTED` | comparison of implemented methods | synthetic; EQ-B attribution limit |
| E2 | complex synthetic (V2) | development only | — | frozen under moratorium |
| E3 | external static dataset | **adapter ready, no data ingested** | — | infrastructure, not evidence |
| E4 | real-trace replay (Layer 1) | **not executed** (frozen prereg) | real recovery under natural change-points | no ρ control; domain ≠ routing |
| E5 | real geometry + injected shock (Layer 2) | **not executed** | pooling effect on real cost/quality | shock is semi-synthetic |
| E6 | realistic pooling/topology (Layer 3) | **not executed** | ρ / shared-shock realism | validates topology, not RRT |
| E7–E8 | governed high-fidelity (Vivo/Telefónica) | **not authorized** | highest-fidelity shared-vs-local | governance + anonymization gate |

## 3. Overfitting control (carried forward)

At least one external source is held **untouched** until a real evaluation begins; method changes in
response to a single benchmark turn it into development data. (Restates
`research/EXTERNAL_VALIDATION_PLAN.md`.)

## 4. What would move a rung from "infrastructure" to "evidence"

1. Human authorization recorded (MASTER_PROMPT §5.4) + moratorium amendment in force.
2. Propensity validity satisfied (true/uniform), overlap + ESS reported.
3. IPS/SNIPS/DR agreement reported; source row (sub-claim + limit) attached to the number.
4. Ledger entry with data provenance and hashes.

Until all four hold, every rung above E3 remains **prepared, not climbed**.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
