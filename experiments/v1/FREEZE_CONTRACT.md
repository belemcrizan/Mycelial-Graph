# Confirmatory freeze contract

Status: **LOCKED** until a scientifically justified sample size is reviewed and committed. This is a repository record, not an interactive permission request.

`CONFIRMATORY_FREEZE.json` must be committed before outcomes. Validation rejects a missing/incomplete record, changed source/config/protocol, a pending addendum, uncommitted inputs, a modified pilot seal, an ineligible power estimate or reordered/overlapping seeds.

Required JSON fields for a **new** confirmatory execution authorization record
placed at `experiments/v1/CONFIRMATORY_FREEZE.json` (next to the confirmatory YAML):

| Field | Meaning |
|---|---|
| `schema_version` | Integer 1 |
| `status` | `frozen` |
| `required_confirmatory_pairs` | Reviewed integer N, 2–500, at least the eligible planning estimate; exceeding pool needs amendment |
| `config_hash` | Canonical `config_digest` of original confirmatory config |
| `source_tree_sha256` | Fresh `source_digest` of the code used for the pilot and confirmatory execution |
| `files` | SHA-256 map for the original protocol, analysis plan, result schema, every numbered amendment, completed sample-size addendum, ordered pool and selected seeds |
| `pilot_artifact_path` | Repository-relative directory containing the sealed, complete original 20-seed pilot |
| `pilot_artifact_seal_sha256` | SHA-256 of that pilot's `artifact_seal.json` |
| `power_review_path` | Repository-relative, committed methodology review including bounded/censored outcome and bootstrap-test assumptions |
| `power_review_sha256` | SHA-256 of that review |

Use `mycelial_graph.artifacts.file_hash`, `config_digest` and `source_digest` to compute actual values; no placeholder/template is treated as a freeze. The pilot seal and review must already be committed, and the pilot and confirmatory scientific configuration sections must agree.

The normal approximation in `sample-size` remains a planning estimate. Validation checks its eligibility and provenance; it cannot certify the scientific quality of a written review. A degenerate pilot, unsupported power assumption or unspecified failure policy is a research problem, not a reason to hand-edit a smaller N. The schema is intentionally not auto-created by the pilot script.

After completing these commitments in version control, use the original confirmatory config and a fresh output directory. Report positive, negative, inconclusive or protocol-invalid outcomes without tuning or substituting seeds. Do not create a new confirmatory cohort to replace an unfavorable one.

## Historical freeze versus execution authorization

The executed V1 confirmatory record is `experiments/v1/artifacts/CONFIRMATORY_FREEZE.json`.
It is a pre-execution schema (`status: SAMPLE_SIZE_RECORDED_SEEDS_SELECTED_CONFIRMATORY_NOT_EXECUTED`,
`confirmatory_executed: false`). It does **not** use `schema_version=1` / `status=frozen`.
Do not move it, duplicate it as the execution gate, or rewrite it into the modern schema.

Historical reproduction verifies that freeze plus sealed `CONFIRMATORY_EVIDENCE.json`.
A new confirmatory execution still requires the modern authorization record above.
Passing historical reproduction does not unlock a new confirmatory run.
