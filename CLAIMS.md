# Claims and evidence

Source of truth: [research/claims.json](research/claims.json). Claim status only rises when an identified artifact supports it. Evidence labels are not interchangeable.

| Claim | Current evidence | Required evidence | Status | Priority |
|---|---|---|---|---|
| C1: Hierarchical sharing improves V1 recovery at rho=.50. | No verified supporting artifact | Complete frozen confirmatory paired bootstrap superiority test | NOT YET VALIDATED | P0 |
| C2: Hierarchical recovery is non-inferior at rho=0 within +.10. | No verified supporting artifact | Complete frozen confirmatory NI upper bound < .10 | NOT YET VALIDATED | P0 |
| C3: Benefit increases with shared structure; a validity region exists. | No verified supporting artifact | Independent rho x magnitude sweep with uncertainty and negative-transfer regions | PLANNED | P1 |
| C4: The effect generalizes across topologies/regimes/noise. | No verified supporting artifact | Unseen topology/regime/noise benchmark | PLANNED | P2 |
| C5: The method benefits real AI routing workloads. | No verified supporting artifact | Licensed immutable real traces plus bounded live validation | PLANNED | P3 |
| C6: Adaptive sharing improves robustness. | No verified supporting artifact | V3 adaptive gate, ablations, calibration and identification tests | PLANNED | P5 |
| E1: V1 rejects incomplete/mixed/corrupted evidence before automatic inference. | tests/test_evidence_integrity.py | Integrity regression tests and executed development artifact | IMPLEMENTED | P0 |

## Do not claim yet

- Production readiness or universal superiority.
- Multicloud resilience or real-world generalization from simulation.
- Causal fault localization or identified latent causes.
- Reduced sample complexity or regret bounds without proof.
- A sharp phase transition or a calibrated optimal degree of sharing.
- Confirmatory support from development or pilot results.
- Independent reproduction, a DOI or live provider validation.

Allowed evidence levels: CONCEPT, IMPLEMENTED, UNIT-TESTED, SIMULATION-VALIDATED, PILOT-VALIDATED, CONFIRMATORY-VALIDATED, REAL-TRACE-VALIDATED, LIVE-VALIDATED, EXTERNALLY-REPRODUCED, THEORETICALLY-PROVED. A level describes a specific claim, not the whole repository.
