# Validation evidence — cycle 001

Pre-pilot checks in the provided Python 3.12 environment:

- Untouched base revision: 32 tests passed.
- Integrity revision: 54 tests passed, including four-method serial/parallel compressed-trace equality and artifact sealing/report reproduction.
- Canonical scientific payload for development seed 1103, rho=.50: identical to base 4966daf for all four methods, excluding only volatile provenance according to the existing canonical function. See baseline_comparison.json. This is a scoped regression result, not a proof for every possible input.
- All nine original frozen V1 protocol/schema/config/seed files are byte-identical to base; see frozen_v1_hashes.json.
- Historical checked-in demo fails byte/hash verification and is retained unchanged.
- Confirmatory seeds and freeze remain absent. No confirmatory run has been executed.

The source will be committed before the independent pilot. Actual pilot outcome and artifact identity are added after execution in a separate commit. No pilot outcome has informed these implementation changes.
