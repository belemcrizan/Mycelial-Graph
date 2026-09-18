# Independent Replication Package

**Author / maintainer:** Crizan Belem Ribeiro, Independent Researcher
**Serves:** Master Prompt Part II §13 · Kernel gate: **GATE-SAFE** (docs). Minting a DOI / external
release is **GATE-H06** (not performed here).

---

## 0. Goal

A researcher who has never spoken to the author can reproduce the sealed V1 confirmatory result and
detect any divergence, without trusting the author (§25).

## 1. Clean reproduction

```bash
git clone https://github.com/belemcrizan/Mycelial-Graph
cd Mycelial-Graph
python -m pip install --upgrade pip
python -m pip install -r requirements.lock.txt   # pinned dependencies
python -m pip install -e .
python -m pytest                                  # full suite + scientific invariants
python reproduce_confirmatory.py                  # reproduce sealed summaries/hashes
python scripts/reproduce_v1.py --output outputs/repro-v1 --workers 2
python -m mycelial_graph verify-seal --output outputs/repro-v1   # divergence detection
mycelial-graph claim-audit --matrix docs/claim_evidence_matrix.yaml
```

## 2. Determinism & environment

- Pinned deps in `requirements.lock.txt`; editable install via `pyproject.toml`.
- Deterministic seeds: `experiments/v1/seeds.confirmatory.txt` (SHA-256
  `8ef4c6b0dc481fea70054b6d7cbc9ecc2663f63b4523f3f55bb374a0339ee00c`, bound in
  `CONFIRMATORY_FREEZE.json`).
- Platform recorded in `research/runtime.json` (Windows 3.13.3 reference run; CI matrix covers
  Linux 3.11/3.13 and Windows).
- Runtime metric to expect: sealed decision-CPU **0.122 h** (437.59 s over 1940 trials) — do **not**
  confuse with a ~404 s wall-clock replay (`runtime.json` glossary).

## 3. Expected outputs & integrity

- Sealed summaries + hashes under `experiments/v1/artifacts/confirmatory/` and `manifest.json`.
- The 1940 raw trial payloads are **regenerated** by `--full`, not stored in git (by design;
  `research/state.json`).
- `verify-seal` and the integrity tests (`tests/test_v1_reproduction_integrity.py`,
  `tests/test_v1_confirmatory_integrity.py`) detect divergence.

## 4. Result to expect (immutable, INV-01)

Primary ρ=0.50: hierarchical **+42.1%** slower (95% CI +11.9%..+79.1%, N=97). ρ=0 non-inferiority
gate **not** established. Result state **`REFUTED`**. A reproduction that yields anything else
indicates environment divergence, not a new scientific result.

## 5. Release metadata (prepared, not published)

`CITATION.cff` and `paper/zenodo_metadata.json` exist. Publishing / DOI minting is **GATE-H06** and
is not performed.

*Signed, Crizan Belem Ribeiro, Independent Researcher.*
