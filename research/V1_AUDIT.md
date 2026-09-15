# V1 audit — source, protocol and evidence

Audit base: `4966daf3d0f09ba810f6855772145130359eb974` (`main`, PR #2 merge). No AGENTS.md was present. No existing open PR was found when work began.

## Architecture

| Layer | Code | Role / limitation |
|---|---|---|
| V0 legacy | top-level graph/routing/experiment/trial and `config.py` | Historical demonstrator, separate from V1 dataclass config |
| V1 definition | `types.py`, `validation.py`, `experiments/v1/` | Frozen typed design, phase populations, original protocol and analysis |
| Environment | `environment/graph.py`, `environment/scenario.py` | Complete layered DAG; single shock; same indexed outcomes per seed/rho family; enumerated oracle |
| Agents | `agents/` | Edge-only, node-only, hierarchy and structured sliding-window linear UCB |
| Execution | `runner/` | Paired trial jobs, isolated RNG, raw records and traces, process workers |
| Inference | `analysis/` | Restricted recovery, paired bootstrap, NI and normal-approximation power planning |
| Reporting | `reporting/`, CLI | Tables/plots and Markdown; now tied to verified input identity |
| V2 | `v2/`, `experiments/v2/` | Separate synthetic resource-allocation alpha; not V1 evidence |
| New enforcement | `artifacts.py`, `protocol.py` | Population/hash validation, committed freeze, sealing and provenance |

## Frozen boundary

Original V1 files (protocol, analysis plan, schema, three configs, development/pilot/pool seed files and pending addendum) are not edited. The only additional protocol record is amendment 001. Preserve rho's energy-fraction definition; replacing it with an inferred variance ratio would change the experiment.

The primary estimand is relative difference of mean restricted recovery time at rho=.50. The NI margin at rho=0 is +.10; the point engineering threshold is -.20. The percentile bootstrap and its frozen RNG seeds remain unchanged. SW-UCB already supplies a shared node/edge representation baseline independent of the Mycelial update mechanism; it should not be added again under a new name.

## Existing versus missing evidence

| Item at audit start | State | Consequence |
|---|---|---|
| V0 outputs | Historical demonstration | No V1 claim |
| V1 development output | 25 scenario files, 4 methods; original manifest uses Windows separators and at least one raw-byte hash does not verify in current checkout | Preserve unchanged; do not silently rehash as valid evidence |
| Independent pilot | No committed artifact found | Next permissible real experiment after code freeze |
| Sample size | Pending addendum; normal approximation helper only | No justified frozen N |
| Selected confirmatory seeds | Missing intentionally | Confirmatory execution locked |
| Confirmatory artifact | Absent | No primary superiority/NI claim |
| V2 | Code/config/tests only in this audit | Separate synthetic scope |
| Live traces, topology benchmark, external reproduction, theory | No evidence found | PLANNED / NOT YET VALIDATED |

## Tests and statistical risks

The untouched baseline passed **32 tests** in this environment. It covered determinism, censoring, V1/V2 boundaries, serial/parallel execution and resource invariants, but not complete-population validation before inference or content tampering on resume.

The audit found: arbitrary raw-file aggregation; silent deletion of incomplete pairs; no phase/config binding in analysis or report; seed-file-only confirmatory locking; missing failure records; mutable arrays/maps despite frozen dataclasses; gzip timestamps/temporary names; zero-variance planning errors; descriptive promotion without phase or operational-budget gates; module CLI errors returning success; incomplete numeric validation.

The added checks enforce these boundaries without changing the experiment's statistical estimand. Failure-inclusive inference remains explicitly suspended pending its missing contract. The pilot must inspect floor/ceiling effects and review bootstrap-test power before any N is frozen.

## Shortest valid path

1. Commit the integrity changes, amendment, full requirement register and tests.
2. Run the original independent pilot once, without hyperparameter changes; retain all artifacts and failures.
3. Validate and seal it; record its identity in the append-only ledger.
4. Review the planning estimate against the actual bounded/censored distribution. If variance is degenerate or measurement uninformative, publish that finding and keep confirmatory locked.
5. Only with a justified N and completed failure/power decisions: commit addendum, first-N seeds and freeze; execute the unchanged confirmatory protocol and publish its outcome.
6. Advance to robustness/benchmark work through the roadmap gates, without reclassifying exploratory work.
