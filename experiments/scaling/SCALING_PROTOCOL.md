# MG-EXP-SCALING-001 — Scaling Behavior Protocol (FROZEN, NOT AUTHORIZED)

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Serves:** Master Prompt Part II §9 · Kernel gate: **GATE-FROZEN**.
**Status:** `frozen` · `authorized: false`.
**Runtime-metric anchor:** `research/runtime.json` (canonical decision-CPU vs replay vs wall-clock).

---

## 0. Objective

Test whether the method remains operational as problem size grows, and characterize algorithmic
scaling — **without** conflating distinct cost quantities into one misleading runtime number (§9).

## 1. Scaling axes

nodes · edges · paths · horizon · providers · candidate branching · state size · workload ·
concurrency (where relevant). Each varied on a pre-registered grid with fixed seeds.

## 2. Metrics, kept strictly separate (per `runtime.json` glossary)

| Class | Definition | Never mix with |
|---|---|---|
| **scientific compute** | `decision_cpu_seconds` inside `run_method` | replay/orchestration |
| **replay/serialization overhead** | cost of `--full` replay / (de)serialization | scientific compute |
| **wall-clock orchestration** | `perf_counter` of an invocation | the two above |

Also record: memory · storage · trace volume · token usage · monetary cost (if any) · latency ·
empirical complexity fit · failure rate.

## 3. Reporting

Scaling curves with the three cost classes plotted separately and labeled. An empirical
complexity estimate (e.g., fitted exponent) reported with uncertainty, never as a proved bound
(INV-05: no unearned complexity claim).

## 4. Gate & evidence class

Execution **GATE-FROZEN** (and **GATE-H04** if it would incur meaningful paid compute). Outputs
**SYNTHETIC**.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
