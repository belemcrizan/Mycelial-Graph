# Claim–evidence matrix

Machine-readable companion: [`claim_evidence_matrix.yaml`](claim_evidence_matrix.yaml).

Audit: `mycelial-graph claim-audit`.

Passing the audit means **internal consistency of wording**, not empirical truth.

The audit also verifies machine-checkable V1 readiness and result state (`v1_readiness_invariants`
in the YAML): seed count and hash against the freeze, pool-prefix selection, population
disjointness, config binding, and the sealed confirmatory result state.

| ID | Claim | Allowed wording status |
|---|---|---|
| C01 | V1 confirmatory recovery advantage | CONFIRMATORY_REFUTED |
| C02 | V2.0-alpha quality+token success | DEVELOPMENT_ONLY |
| C03 | Real coding-agent token reduction | NOT_SUPPORTED |
| C04 | Fungi prove the algorithm | NOT_SUPPORTED |
| C05 | VOC calibrated on synthetic POs | SYNTHETIC_ONLY |
| C06 | Iso-model is not cheaper-model routing | SYNTHETIC_ONLY |
| C07 | rho* law | NOT_SUPPORTED |
| C08 | Proved hierarchical sample-complexity advantage | NOT_SUPPORTED |
| C09 | Adaptive pooling superiority | NOT_SUPPORTED |
| C10 | Causal fault localization | NOT_SUPPORTED |
| C11 | Real-provider generalization | NOT_SUPPORTED |
| C14 | MG-EXP-REAL-001 completed | NOT_SUPPORTED |
| C15 | Attribution of the V1 performance difference to hierarchical representation alone | NOT_SUPPORTED |

Any paper-like sentence of the form “Mycelial makes agents X% more efficient” is forbidden until a frozen confirmatory real-workload protocol exists.
