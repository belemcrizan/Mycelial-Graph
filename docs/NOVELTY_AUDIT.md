# Novelty audit

**Date:** 2026-08-31  
**Rule:** renaming is not novelty. `conductance` ≠ new bandit. `metabolism` ≠ new budget. `anastomosis` ≠ new shared memory.

| Candidate contribution | Closest prior work | Substantive difference? | Experimental evidence? | Claim allowed? |
|---|---|---|---|---|
| Local conductance adaptation | V0/V1 of this repo; online learning | Historical lineage, not new in V2.1 | V1 development only | “V1 tests recovery-representation” |
| Resource ledger including router | FinOps / usage APIs | Scientific identity constraint, not a product dashboard | Unit tests | “accounted tokens include router” |
| MVC/VOC on a DAG | Russell & Wefald 1991; CALM | Multi-action (retrieve/verify/route) + shocks | V2.1 voc-bench synthetic | “synthetic VOC calibration”, not “knows when to think” |
| Iso-model allocation | Implicit in TTC papers that fix the model | Explicit firewall vs RouteLLM | Protocol + generator flag | Track definition only until results exist |
| Fungal-inspired prune/transfer | Bebber et al. 2007 transport remodeling; bandit pruning | Combination + recovery metrics | Alpha ablations (real flags only) | “inspired by”, not “biologically validated” |
| Dynamic branching / compatibility fusion | Harris branching; Fischer & Glass fusion | **Not implemented** | None | Not a contribution |
| Real coding efficiency | SWE-bench agents; token studies | **Not measured** | Fixtures only | NOT_SUPPORTED |
| Beating strong contextual bandits | TS, linear cost-sensitive, SW-UCB | Must be shown | Baselines now exist; **no confirmatory** | Not allowed as a result |

**Novelty threat (primary):** a well-tuned cost-sensitive bandit or Lagrangian allocator on the same graph explains alpha “wins”. V2.1 exists to surface that threat early.

**Novelty threat (secondary):** iso-model null result → remaining story is model routing, i.e. RouteLLM territory with fungal names. That would refute the broader architectural claim, not the entire repo (V1 recovery question remains).
