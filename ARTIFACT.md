# V1 artifact evaluation

This revision adds an evidence-integrity layer around the frozen MG-EXP-V1 implementation. It is not the completed global research program. See research/V1_AUDIT.md and research/CYCLE_001.md.

## What an evaluator can check

1. Install the editable checkout with Python >=3.11: `python -m pip install -e .`.
2. Run `python -m unittest discover -s tests -v`.
3. Run `python scripts/reproduce_v1.py --output outputs/reproduced-v1 --workers 2`.
4. Run `python -m mycelial_graph validate-artifacts --config experiments/v1/config.development.yaml --output outputs/reproduced-v1`.
5. Run `python -m mycelial_graph verify-seal --output outputs/reproduced-v1`.

The output contains per-scenario raw records, deterministic compressed decision traces, checkpoint integrity records, source/protocol/config/seed identity, processed statistics, a Markdown report, figures and a seal of all files. The sealed directory cannot be overwritten by run/analyze/report commands. A repeated reproduction command reports verification of an existing artifact, not a new execution.

## Scientific boundary

Development verifies machinery; pilot supports planning; only a valid frozen confirmatory population can support the primary claim. Product promotion additionally requires a specified operational budget. No external reproduction is claimed by internal testing.

Historical `outputs/demo` is retained unchanged. Its Windows-style manifest paths can be read, but some tracked file bytes do not match the recorded hashes. Do not use it as verified evidence or silently repair its manifest.

See REPRODUCIBILITY.md for provenance limitations and experiments/v1/FREEZE_CONTRACT.md for the confirmatory gate.
