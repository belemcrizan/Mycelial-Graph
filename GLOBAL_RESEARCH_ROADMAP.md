# Global research roadmap

This is the complete dependency-ordered program from the supplied master prompt, not a claim that its 118 sections have been delivered. The exact specification is preserved in [research/MASTER_PROMPT.md](research/MASTER_PROMPT.md). No requirement is removed.

Central question: **when should local evidence become shared structural belief?** In V1, rho is the fraction of squared L2 shock energy in the node-incidence component, not an estimated Pearson correlation or a demonstrated critical phase transition.

## Execution gates

| Phase | Priority | Deliverable and exit criterion | Current disposition |
|---|---|---|---|
| A — V1 evidence | P0 | Audited pipeline → independent 20-seed pilot → reviewed power → committed N/addendum/first-N seeds/freeze → confirmatory result, regardless of sign | Integrity hardening implemented; pilot is the next execution. Confirmatory stays locked until the statistical gate is satisfied. |
| B — robustness | P1/P2 | Strong baselines, full ablations, rho × magnitude curves, topology/regime/noise tests; map a bounded validity region | PLANNED; new exploratory protocol and disjoint seeds after A |
| C — MycelialBench | P2 | Algorithm-independent environment, interfaces, metrics, external router; another method runs without MG internals | PLANNED after A/B evidence |
| D — external validity | P3 | Licensed workload, immutable provider traces, replay, bounded canary; at least one claim survives outside simulation | PLANNED; no live provider measurements or collection budget |
| E — resource-aware V2 | P3 | Uncertainty, VoI, STOP, hard budgets and Pareto evaluation | Existing V2 alpha is separate synthetic implementation; further expansion gated |
| F — structure-inference V3 | P5 | CPD, latent cause inference, adaptive sharing, uncertainty and active diagnosis | PLANNED, requires identification and calibration experiments |
| G — theory | P1/P5 | Explicit assumptions and a proved result or bounded characterization in a shared-parent Gaussian model | PLANNED; may proceed independently without delaying A |
| H — global artifact | P3/P4 | Manuscript, benchmark/data, SDK, container, DOI, preregistration, external reproduction and demo | PLANNED; internal tests do not establish independent reproduction |

P0 blocks validity; P1 strengthens the core contribution; P2 strengthens robustness; P3 establishes external validity/adoption; P4 improves engineering/product; P5 is speculative research. Unresolved P0 takes precedence.

## Current iteration

Classifications: **REPRODUCIBILITY, EXPERIMENTAL, STATISTICAL, ENGINEERING, DOCUMENTATION**. The change validates the entire planned cohort before statistics, records failures, prevents misleading promotion, seals artifacts, and preserves the frozen estimands/algorithms. See [research/CYCLE_001.md](research/CYCLE_001.md) and [research/V1_AUDIT.md](research/V1_AUDIT.md).

## Full requirement register

Every row links to the original requirement by section number. “Active / partial” means an existing invariant, policy, or part of the implementation; it does not mean its full research goal is demonstrated. All future experiments require a design, stopping rule, seeds, fair baseline budget, metrics and evidence artifact before any claim.

| Section | Requirement | Priority | Status | Next evidence/gate |
|---:|---|---|---|---|
| 0 | NON-NEGOTIABLE PRINCIPLES | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 1 | CENTRAL SCIENTIFIC THESIS | P1 | ACTIVE / PARTIAL | A → B or bounded theory |
| 2 | FORMALIZE THE PROBLEM | P1 | ACTIVE / PARTIAL | A → B or bounded theory |
| 3 | PRIMARY QUESTION | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 4 | FINISH V1 BEFORE MAJOR EXPANSION | P0 | PLANNED | A: integrity and pre-outcome commitments |
| 5 | PRESERVE AND STRENGTHEN EXISTING STATISTICS | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 6 | BUILD MYCELIALBENCH | P2 | PLANNED | A → B/C: exploratory validity map |
| 7 | MAKE RHO A FIRST-CLASS SCIENTIFIC VARIABLE | P1 | PLANNED | A → B or bounded theory |
| 8 | EXTEND TO TWO-DIMENSIONAL PHASE MAPS | P1 | PLANNED | A → B or bounded theory |
| 9 | NEGATIVE TRANSFER MUST BE A PRIMARY PHENOMENON | P1 | PLANNED | A → B or bounded theory |
| 10 | FORMALIZE KNOWLEDGE RETENTION | P1 | PLANNED | A → B or bounded theory |
| 11 | LEARN HOW MUCH TO SHARE | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 12 | LATENT CAUSE INFERENCE | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 13 | CHANGE-POINT DETECTION | P2 | PLANNED | A → B/C: exploratory validity map |
| 14 | STRONG BASELINES | P1 | ACTIVE / PARTIAL | A → B or bounded theory |
| 15 | FULL ABLATION PROGRAM | P1 | PLANNED | A → B or bounded theory |
| 16 | MULTIPLE TOPOLOGIES | P2 | PLANNED | A → B/C: exploratory validity map |
| 17 | HARDER NON-STATIONARY REGIMES | P2 | PLANNED | A → B/C: exploratory validity map |
| 18 | PARTIAL OBSERVABILITY | P2 | PLANNED | A → B/C: exploratory validity map |
| 19 | DELAYED AND MISSING FEEDBACK | P2 | PLANNED | A → B/C: exploratory validity map |
| 20 | REAL WORKLOADS | P3 | PLANNED | A → D/H: external evidence and provenance |
| 21 | REAL AI EXECUTION GRAPH | P3 | PLANNED | A → D/H: external evidence and provenance |
| 22 | REAL PROVIDER VALIDATION | P3 | PLANNED | A → D/H: external evidence and provenance |
| 23 | TRACE REPLAY | P3 | PLANNED | A → D/H: external evidence and provenance |
| 24 | DATASET RELEASE | P3 | PLANNED | A → D/H: external evidence and provenance |
| 25 | MULTI-OBJECTIVE EVALUATION | P2 | PLANNED | A → B/C: exploratory validity map |
| 26 | V2 — ADAPTIVE COMPUTATION | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 27 | UNCERTAINTY AS A CORE STATE VARIABLE | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 28 | EPISTEMIC VS ALEATORIC UNCERTAINTY | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 29 | VALUE OF INFORMATION | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 30 | STOP AS A REAL ACTION | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 31 | HARD POLICY CONSTRAINTS | P4 | PLANNED | A complete + demonstrated implementation need |
| 32 | POLICY ENGINE | P4 | PLANNED | A complete + demonstrated implementation need |
| 33 | FAULT CONTAINMENT | P4 | PLANNED | A complete + demonstrated implementation need |
| 34 | CASCADING FAILURES | P4 | PLANNED | A complete + demonstrated implementation need |
| 35 | ADVERSARIAL ROBUSTNESS | P2 | PLANNED | A → B/C: exploratory validity map |
| 36 | THEORETICAL PROGRAM | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 37 | BEGIN WITH A SIMPLIFIED THEORETICAL MODEL | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 38 | SAMPLE COMPLEXITY | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 39 | CONSISTENCY AND FAILURE CONDITIONS | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 40 | HEAVY-TAILED ENVIRONMENTS | P2 | PLANNED | A → B/C: exploratory validity map |
| 41 | SLO-AWARE ROUTING | P4 | PLANNED | A complete + demonstrated implementation need |
| 42 | CONTEXTUAL ROUTING | P2 | PLANNED | A → B/C: exploratory validity map |
| 43 | CONTEXT-DEPENDENT SHOCKS | P2 | PLANNED | A → B/C: exploratory validity map |
| 44 | GRAPH DISCOVERY | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 45 | DYNAMIC TOPOLOGY | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 46 | META-LEARNING / LEARNING TO ADAPT | P2 | PLANNED | A → B/C: exploratory validity map |
| 47 | MEMORY CONSOLIDATION | P2 | PLANNED | A → B/C: exploratory validity map |
| 48 | CONTINUAL LEARNING METRICS | P2 | PLANNED | A → B/C: exploratory validity map |
| 49 | CAUSAL HIERARCHY | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 50 | INTERVENTIONS | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 51 | ACTIVE FAULT LOCALIZATION | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 52 | REPRODUCIBILITY METADATA | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 53 | ONE-COMMAND PAPER REPRODUCTION | P3 | PLANNED | A → D/H: external evidence and provenance |
| 54 | ARTIFACT EVALUATION | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 55 | SCIENTIFIC CI | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 56 | PROPERTY-BASED TESTING | P0 | PLANNED | A: integrity and pre-outcome commitments |
| 57 | MUTATION TESTING | P0 | PLANNED | A: integrity and pre-outcome commitments |
| 58 | CONFIG FUZZING | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 59 | PERFORMANCE ENGINEERING | P4 | PLANNED | A complete + demonstrated implementation need |
| 60 | ARCHITECTURAL MODULARIZATION | P4 | PLANNED | A complete + demonstrated implementation need |
| 61 | SIMPLE SDK | P4 | PLANNED | A complete + demonstrated implementation need |
| 62 | OBSERVABILITY | P4 | PLANNED | A complete + demonstrated implementation need |
| 63 | DECISION PROVENANCE | P4 | PLANNED | A complete + demonstrated implementation need |
| 64 | DASHBOARD | P4 | PLANNED | A complete + demonstrated implementation need |
| 65 | PAPER FIGURES | P1 | PLANNED | A → B or bounded theory |
| 66 | PREREGISTRATION | P0 | PLANNED | A: integrity and pre-outcome commitments |
| 67 | RELEASES AND DOI | P3 | PLANNED | A → D/H: external evidence and provenance |
| 68 | CITATION | P3 | PLANNED | A → D/H: external evidence and provenance |
| 69 | PAPER | P1 | PLANNED | A → B or bounded theory |
| 70 | RELATED WORK | P1 | PLANNED | A → B or bounded theory |
| 71 | NOVELTY MAP | P1 | PLANNED | A → B or bounded theory |
| 72 | FAILURE MODES | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 73 | SCIENTIFIC RED TEAM | P1 | PLANNED | A → B or bounded theory |
| 74 | EXTERNAL REPRODUCTION | P3 | PLANNED | A → D/H: external evidence and provenance |
| 75 | COLLABORATION | P3 | PLANNED | A → D/H: external evidence and provenance |
| 76 | MYCELIALBENCH CHALLENGE | P2 | PLANNED | A → B/C: exploratory validity map |
| 77 | MAP WHERE MYCELIAL LOSES | P1 | PLANNED | A → B or bounded theory |
| 78 | BIOLOGICAL METAPHOR DISCIPLINE | P1 | ACTIVE / PARTIAL | A → B or bounded theory |
| 79 | LONG-TERM SCIENTIFIC IDENTITY | P1 | ACTIVE / PARTIAL | A → B or bounded theory |
| 80 | LONG-TERM SYSTEM VISION | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 81 | ADDITIONAL FRONTIER DIRECTION — STRUCTURAL UNCERTAINTY | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 82 | ADDITIONAL FRONTIER DIRECTION — COUNTERFACTUAL ROUTING | P2 | PLANNED | A → B/C: exploratory validity map |
| 83 | ADDITIONAL FRONTIER DIRECTION — CALIBRATION | P2 | PLANNED | A → B/C: exploratory validity map |
| 84 | ADDITIONAL FRONTIER DIRECTION — DISTRIBUTION SHIFT | P2 | PLANNED | A → B/C: exploratory validity map |
| 85 | ADDITIONAL FRONTIER DIRECTION — IDENTIFIABILITY | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 86 | ADDITIONAL FRONTIER DIRECTION — CALIBRATED ABSTENTION | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 87 | ADDITIONAL FRONTIER DIRECTION — ADAPTATION DEBT | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 88 | ADDITIONAL FRONTIER DIRECTION — BELIEF PROPAGATION BUDGET | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 89 | ADDITIONAL FRONTIER DIRECTION — FEDERATED / DECENTRALIZED ADAPTATION | P5 | PLANNED | A complete + separate falsifiable research protocol |
| 90 | ADDITIONAL FRONTIER DIRECTION — MECHANISM INTERPRETABILITY | P2 | PLANNED | A → B/C: exploratory validity map |
| 91 | ADDITIONAL FRONTIER DIRECTION — MINIMUM SUFFICIENT COMPLEXITY | P1 | PLANNED | A → B or bounded theory |
| 92 | ADDITIONAL FRONTIER DIRECTION — COMPUTE BUDGET FOR RESEARCH ITSELF | P2 | PLANNED | A → B/C: exploratory validity map |
| 93 | ADDITIONAL FRONTIER DIRECTION — CLAIM REGISTRY | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 94 | ADDITIONAL FRONTIER DIRECTION — RESULT IMMUTABILITY | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 95 | ADDITIONAL FRONTIER DIRECTION — EXPERIMENT LEDGER | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 96 | ADDITIONAL FRONTIER DIRECTION — RESEARCH DEBT REGISTER | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 97 | ADDITIONAL FRONTIER DIRECTION — ENGINEERING DEBT REGISTER | P4 | ACTIVE / PARTIAL | A complete + demonstrated implementation need |
| 98 | ADDITIONAL FRONTIER DIRECTION — DOCUMENT EVIDENCE LEVELS | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 99 | PROJECT EXECUTION ORDER | P1 | ACTIVE / PARTIAL | A → B or bounded theory |
| 100 | EACH IMPLEMENTATION ITERATION MUST FOLLOW THIS LOOP | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 101 | BEFORE MAKING A CHANGE, CLASSIFY IT | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 102 | REQUIRED RESPONSE FORMAT FOR EACH DEVELOPMENT CYCLE | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 103 | CODE QUALITY STANDARD | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 104 | EXPERIMENT QUALITY STANDARD | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 105 | DOCUMENTATION STANDARD | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 106 | CLAIM LANGUAGE | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 107 | DO NOT OVER-ENGINEER | P4 | ACTIVE / PARTIAL | A complete + demonstrated implementation need |
| 108 | DO NOT TURN EVERYTHING INTO AN LLM AGENT | P4 | ACTIVE / PARTIAL | A complete + demonstrated implementation need |
| 109 | SUCCESS CRITERIA FOR “GLOBAL-LEVEL” | P1 | PLANNED | A → B or bounded theory |
| 110 | DEFINITION OF DONE FOR THE CURRENT PROGRAM | P1 | PLANNED | A → B or bounded theory |
| 111 | FINAL RESEARCH NORTH STAR | P1 | PLANNED | A → B or bounded theory |
| 112 | IMMEDIATE EXECUTION INSTRUCTION | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 113 | REQUIRED PRIORITY LABELS | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 114 | REQUIRED EVIDENCE MATRIX | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 115 | REQUIRED “DO NOT CLAIM YET” SECTION | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 116 | QUALITY BAR | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
| 117 | FINAL INSTRUCTION | P0 | ACTIVE / PARTIAL | A: integrity and pre-outcome commitments |
