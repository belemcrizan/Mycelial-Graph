# Paper A post-confirmatory diagnostics

Status of every number below: `POST_CONFIRMATORY_DIAGNOSTIC` unless marked `MEASURED`.
None of these analyses overwrites the frozen V1 result `REFUTED`.

## Equalization triage

Classification: **EQ-B**

Action: revise claims -> disclose prominently -> submit

Principle: parameter parity is not policy parity.

Reasons:
- warm-up path-entropy fraction edge=0.629 hierarchical=0.969 gap=0.341
- optimal-pre-path rate gap=0.094
- exploration-step rate gap=0.003
- selected-score std ratio=12.080
- Realized action distributions differ enough to limit mechanistic interpretation, but both arms remain in a comparable non-degenerate exploration regime. The frozen REFUTED outcome stands as a comparison of the implemented methods, not as proof that representation was isolated.

## Variance diagnostic

Confirmatory / pilot paired-difference SD ratio: **1.72x**

A 20-pair pilot produced an unstable variance estimate relative to the confirmatory paired-difference dispersion. Future protocols should not rely on a normal approximation from a small pilot unless a bootstrap or simulation-based procedure confirms stability. This lesson is local to this environment and is not a general theorem.

## Censoring

Non-administrative censoring (all methods, all rho): 0
Primary hierarchical minus edge-only censoring gap: 0.010309278350515464

Restricted recovery time is a thresholded, right-censored functional. It is the frozen primary outcome and is not replaced here. Sensitivity statements about tau are diagnostic only.

## Dynamic range / regret

RRT vs regret sign disagreements on the frozen rho grid: 1
Any rho where hierarchical mean RRT is better: True
rho=1 detectable sharing advantage under the frozen one-sided rule: False

A mean RRT advantage at rho=1, if present, is a construct/dynamic-range check, not a confirmatory finding. Failure to see a clear sharing advantage even at rho=1 is compatible with implementation weakness, sharing-mechanism weakness, or insufficient environmental dynamic range; this diagnostic cannot separate those three explanations.

## Runtime

Measured CPU-hours from confirmatory raw trials: **0.121554**
Wall-clock of original run: NOT_IN_MANIFEST

