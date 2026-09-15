# Changelog

## Unreleased

### Paper A submission package

- Wrote the V1 TMLR manuscript (`paper/tmlr/paper.tex`) reporting the frozen `REFUTED` result without narrative rescue.
- Canonical scientific state is `research/state.json`; runtime metrics are `research/runtime.json`. Sealed-run decision CPU is **0.122 CPU-hours** (437.59375 CPU-s), not a second conflicting figure.
- Headline and Honest Status now name the frozen hierarchical routing update, record EQ-B, and list representation-only attribution as unsupported.
- Moratorium exit condition is Paper A submission, not confirmatory completion.
- Added `python reproduce_confirmatory.py`, dependency pins, Linux-first quickstart, reserved disjoint seed namespaces, anonymized supplementary builder, and TMLR policy notes. OpenReview submission remains a human boundary.

### V1 confirmatory result — REFUTED

- Executed the frozen MG-EXP-V1 confirmatory experiment at commit `5f314d2` on the 97 pre-selected paired scenarios (485 paired scenarios across the ρ grid, 1940 trials), with no post-pilot tuning and no inspection-driven change to seeds, N, hyperparameters, methods, censoring, estimands, or thresholds.
- **Primary hypothesis `REFUTED`.** At ρ=0.50, mean restricted recovery time was 42.1% *higher* for hierarchical node-edge pooling than for edge-only adaptation (95% bootstrap CI +11.9% to +79.1%; one-sided upper bound +72.1%). The pre-specified relevant benefit of −20% falls outside the interval.
- **Safety gate failed.** At ρ=0 the one-sided upper bound was +16.3% against the frozen +10% non-inferiority margin, so negative transfer cannot be excluded.
- Integrity: 97/97 primary pairs, administrative censoring only, zero method failures inside the frozen contrasts.
- Sealed evidence in `experiments/v1/artifacts/confirmatory/`, appended to `research/ledger/ledger.jsonl`, claim `C01` downgraded to `CONFIRMATORY_REFUTED`, and the moratorium exit condition recorded as satisfied.
- The refutation is bounded by the tested graph, observation contract, shock construction, and parameter range. It establishes nothing about other ρ values, a crossover, real providers, or production behaviour.

### V1 confirmatory convergence cycle

- Declared a repository-wide [V1 confirmatory moratorium](V1_CONFIRMATORY_MORATORIUM.md): V2.0-alpha, V2.1, V2.1-A, `theory/`, `external/`, and the pooling/real tracks are frozen (preserved, not deleted) until V1 reaches a legitimate terminal state.
- Resolved the `seeds.confirmatory.txt` contradiction. The file exists with 97 unique seeds equal to the unfiltered pool prefix and the hash bound in the freeze; `docs/GETTING_STARTED.md` and `docs/V2_IMPLEMENTATION_PLAN.md` no longer describe it as intentionally missing.
- Rewrote the README to expose the primary contrast (`rho=0.50`, hierarchical vs edge-only) and the `+0.10` non-inferiority safety gate at `rho=0`, and to separate completed infrastructure, verified evidence, confirmatory evidence, external evidence, theory, and explicitly unsupported claims.
- Added `experiments/v1/HYPOTHESIS_MATRIX.md`: every contrast that can appear in a report, its role, its error control, and the claim it permits.
- Added `scripts/audit_v1_readiness.py` and the generated `CONFIRMATORY_READINESS_REPORT.md`/`.json`, which mechanically verify seed selection, the N=97 chain, freeze bindings, multiplicity, reproducibility, environment drift, and claim invariants, then emit GO / STOP / PROTOCOL_INVALID.
- Added `AMENDMENT_002.md`, a pre-confirmatory-outcome clarification: a result-state taxonomy (`SUPPORTED` / `CONDITIONAL` / `INCONCLUSIVE` / `REFUTED` / `PROTOCOL_INVALID`) derived from the frozen interpretation matrix, disclosure that the automated gate covers protocol §8.2 requirements 1-3 only, role labels, integrity counters, and an additive freeze hash supplement. No hypothesis, estimand, threshold, sample size, seed, or method changed.
- Added report-level claim containment (`science/claim_guard.py`): V1 report generation now fails on assertive crossover, all-rho, production-readiness, external-validity, causal, theoretical, or independent-reproduction language, while documented limitations stay sayable.
- Extended `mycelial-graph claim-audit` with machine-verifiable V1 readiness invariants declared in `docs/claim_evidence_matrix.yaml`.
- Added `CONFIRMATORY_RUNBOOK.md` as the single canonical execution path, plus `scripts/seal_v1_confirmatory.py` for evidence sealing.

### Earlier in this cycle

- Added isolated theory, external-validation, and adaptive-pooling tracks without changing MG-EXP-V1 methods, configs, or confirmatory meaning.
- Added license-gated adapters, dry-run collector, IPS support diagnostics, scientific ledger helpers, and MG-EXP-REAL-001 / MG-EXP-POOLING-001 protocols.
- Did not add a V1 confirmatory result.

## 0.2.2 - 2026-08-31

- Replaced the V2.1 coding smoke known-fix shortcut (`apply_fix=True`) with an autonomous local agent loop: read, search, retrieve, reason, test, inspect, edit, verify, escalate, stop.
- Quality is now the executable grader on an isolated workspace copy. Oracle patches are evaluation metadata only and are never injected into the agent path.
- Action traces carry `action_id` and `context_id` hashes. This is still not a live coding-agent or SWE-bench result.

## 0.2.1 - 2026-08-31

- Added MG-EXP-V2.1 Evidence Bridge as an additive layer (VOC difference+ratio, counterfactual VOC bench, iso-model generator flag, budget curves, waste proxies, strong allocation baselines, local executable smoke tasks, claim audit).
- Left MG-EXP-V1 and MG-EXP-V2 (V2.0-alpha) protocols, confirmatory locks, and CLI meaning unchanged.
- Documented unimplemented alpha ablation aliases and a verified literature snapshot.

## 0.2.0 - 2026-08-31

- Added Mycelial Graph V2.0-alpha as an additive scientific layer (resource ledger, synthetic environment, resource controller, Pareto and quality non-inferiority reporting).
- Left MG-EXP-V1 configs, CLI, agents, and confirmatory lock unchanged.
- Added `mycelial-graph v2-*` commands and `experiments/v2/` with a separate confirmatory lock.
- Fixed git provenance decoding on Windows paths that are not cp1252-encodable (scientific payloads unchanged).

## 0.1.0 - 2026-08-24

- Reframed the core experiment as a non-stationary graph semi-bandit benchmark.
- Added immutable paired scenarios and indexed potential outcomes.
- Added node-only and hierarchical node-edge representations.
- Added structured sliding-window UCB with the same feature family.
- Added controlled shared-shock fraction with constant L2 magnitude.
- Added restricted recovery time, dynamic regret, paired bootstrap, and decision gates.
- Added atomic results, compressed traces, manifests, static figures, and reports.
- Added development, pilot, and confirmatory workflow with an execution lock.
- Added English documentation for technical and non-technical readers.

