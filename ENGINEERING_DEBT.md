# Engineering debt

| ID | Priority | Issue | Current handling / next step |
|---|---|---|---|
| E01 | P0 | Analysis previously scanned arbitrary raw files and silently dropped incomplete pairs | Fixed: verify the expected seed × rho × method population and all hashes before analysis/power/report |
| E02 | P0 | Checkpoint resume could bless modified/missing traces and overwrite the final manifest | Fixed: checkpoint integrity records, source identity, single-writer directory lock and immutable completed manifests |
| E03 | P0 | Confirmatory lock was just a missing seed file | Fixed: committed freeze record binds code/config/protocol/addendum/pool/seeds and reviewed, sealed pilot evidence |
| E04 | P0 | Dataclass freezing did not protect arrays or topology dictionaries | Fixed: immutable byte-backed arrays and read-only mappings; existing numerical outputs preserved |
| E05 | P0 | Failures disappeared when execution raised | Contained: persistent diagnostics with prior completed methods; block silent retries and inferential output. Complete failure-inclusive estimand awaits R03 |
| E06 | P0 | `python -m mycelial_graph` returned zero after failed CLI commands | Fixed: module propagates CLI exit status |
| E07 | P0 | Non-finite/invalid numeric settings, duplicate methods and rho filename collisions | Fixed: defensive validation and regression cases |
| E08 | P1 | Historical Windows artifact hashes do not verify against current checked-in bytes | Preserve original outputs untouched, mark the limitation, generate new artifacts with portable paths and deterministic gzip headers |
| E09 | P4 | SW-UCB refits a dense inverse; graph paths enumerate exponentially | Measure before changing; no scalability claim, no speculative performance rewrite |
| E10 | P4 | Wheel does not bundle default repository configs; `demo` assumes a checkout | Editable checkout documented; package data before standalone SDK release |
| E11 | P3 | Dependency versions are ranges rather than a maintained cross-platform lock | Runtime versions captured; portable lock/container remain PLANNED |
| E12 | P4 | Abrupt process termination may leave a directory lock or a checkpoint without an integrity record | Preserve files; inspect and document infrastructure recovery, use a new versioned output if uncertain. No automatic force-unlock |
| E13 | P4 | Raw failure diagnostics do not yet contain partial per-step trace for the failing method | Track explicitly; no invented metrics or automatic exclusion |

A hash proves byte identity against its recorded anchor, not authenticity against a malicious actor who replaces all anchors. Git history and separately retained seal hashes remain part of provenance.
