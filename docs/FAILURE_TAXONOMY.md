# Failure Taxonomy

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Serves:** Master Prompt Part II §17 · Kernel gate: **GATE-SAFE**.

---

## 0. Principle

Failure cases are scientific outputs, not noise to hide in logs (§17, INV-03/INV-10). Every major
experiment preserves and classifies its failures. This document defines the structured taxonomy;
each executed experiment attaches observed failures to these codes in its `analysis.json`.

## 1. Taxonomy

| Code | Failure mode | Typical signature |
|---|---|---|
| `F01` | adaptation failure | never recovers within horizon |
| `F02` | negative transfer | pooling worsens vs edge-only (V1 ρ=0.50 exemplar) |
| `F03` | policy flattening | path-entropy fraction → ~1.0 (EQ-B signature) |
| `F04` | instability | divergent scores / oscillating selection |
| `F05` | oscillation | periodic re-routing without settling |
| `F06` | pruning error | prunes a needed edge |
| `F07` | resource starvation | transfer starves an active path |
| `F08` | cost explosion | cost grows superlinearly |
| `F09` | latency explosion | decision latency grows with size |
| `F10` | topology sensitivity | behavior flips across topologies |
| `F11` | regime sensitivity | improves in one regime, degrades in another |
| `F12` | uncertainty miscalibration | bonus mis-scaled vs realized variance |
| `F13` | OPE support violation | insufficient overlap / huge importance weights |

## 2. Cross-links

- `F02`/`F03` are already **observed** in V1 (`REFUTED`) and its EQ-B diagnostic
  (`research/diagnostics/EQ_B_REPORT.md`) — preserved, not hidden.
- `F13` gates any external OPE reporting (`external/protocols/EXTERNAL_OPE_PREREG.md`).

## 3. Use

Executed experiments must emit a `failures` array keyed by these codes with counts and exemplar
seeds. Absence of failures is itself reported (not assumed).

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
