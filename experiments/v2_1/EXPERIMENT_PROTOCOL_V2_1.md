# MG-EXP-V2.1 Evidence Bridge Protocol

**Status:** Frozen for development design. Confirmatory execution is not authorized.  
**Does not replace:** MG-EXP-V1 or MG-EXP-V2 (V2.0-alpha).  
**Estimand change:** iso-model allocation, counterfactual VOC, budget curves Q(B), waste proxies, strong adaptive baselines, local executable smoke tasks.

## Why a new protocol

V2.0-alpha remains a historical milestone. This protocol changes the scientific object: it separates **model routing** from **compute allocation**, and it treats VOC as a calibrated estimator rather than a local heuristic. Those are new estimands, so the version is **MG-EXP-V2.1**, not a silent mutation of alpha results and not a marketing V3.

## Primary order

1. Quality non-inferiority vs `always_high_compute`: H0: ΔQ ≤ −ε.  
2. Only then resource claims, with MMRR = 0.05 until a pilot freezes a different value. Success requires lower CI of `1 - T_M/T_H` > MMRR.  
3. Iso-model track is mandatory before multi-model claims.  
4. VOC calibration (false stop / false spend) is co-primary for any “knows when compute is worth it” wording.  
5. Strong adaptive baselines must be reported, not only static controls.

## Tracks

| Track | What may change | What is locked |
|---|---|---|
| Iso-model | retrieval, verification, stop | model-class latent attributes identical |
| Multi-model | model class | deferred; not confirmatory in V2.1 |
| Real smoke | matched scaffold, executable tests | no live providers; not SWE-bench |

## Forbidden claims

- “Mycelial uses fewer tokens, therefore it works.”  
- SWE-bench performance.  
- Confirmatory language on development curves.  
- Biological proof of the algorithm.

See `docs/EVIDENCE_BRIDGE_PROTOCOL.md` for the full statistical plan.
