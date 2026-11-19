# Reproducibility Guide — V1 Frozen Artifacts & Mycelial V2

## 1. Environment & Installation

All experiments are deterministic, CPU-only, offline-executable, and free of paid external API calls.

- **Tested runtime:** Python `3.13.3` (`>=3.11`), `numpy>=1.26`, `scipy>=1.11`, `PyYAML>=6.0`, `matplotlib>=3.8` (`hypothesis` and `pytest` for verification).
- **Line endings:** Repository text files use LF (`\n`). Historical V1 confirmatory text seals (`8ef4c6b0…` on `experiments/v1/seeds.confirmatory.txt` and `experiments/v1/artifacts/confirmatory/*`) are verified deterministically across LF and CRLF checkouts via `reproduce_confirmatory.py`.

### Setup (Linux / macOS)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python -m pip install -e .
```

### Setup (Windows PowerShell)

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock.txt
python -m pip install -e .
```

---

## 2. Reproducing & Auditing Frozen V1 Confirmatory Evidence

The V1 confirmatory experiment (`N=97` seeds `700000..700096`, `5` $\rho$ levels, `4` methods = `1,940` trials; `REFUTED` at $\rho = 0.50$ with `+42.1%` RRT slowdown; post-confirmatory `EQ-B` classification) is sealed at commit `5f314d2` under `experiments/v1/artifacts/CONFIRMATORY_FREEZE.json`:

```bash
# 1. Verify V1 readiness, seed lineage, freeze hashes, and moratorium state
python scripts/audit_v1_readiness.py

# 2. Verify claim-evidence matrix and README/manuscript scientific-state invariants
mycelial-graph claim-audit --matrix docs/claim_evidence_matrix.yaml

# 3. Fast seal & hash verification of frozen V1 confirmatory artifacts
python reproduce_confirmatory.py

# 4. Full deterministic re-execution of all 1,940 V1 confirmatory trials (~6-7 min on 4 workers)
python reproduce_confirmatory.py --full
```

All reproduction inside this repository is **internal / automated**, not independent third-party reproduction.

---

## 3. Reproducing Mycelial V2 (`MG-EXP-V2.2`) Benchmarks & Audits

### 3.1 Seed Population Isolation

`experiments/v2_2/` enforces strict disjointness across all experimental phases (zero overlap with V1 `1000..700999`, V2.0 `7103..9341`, or V2.1 `9101`):

| Population | File | Count | Seed Range | Permitted Use |
|---|---|---:|---|---|
| Development | `experiments/v2_2/seeds.development.txt` | 10 | `2201001..2201010` | Implementation checks, scaling/noise/budget diagnostics |
| Pilot | `experiments/v2_2/seeds.pilot.txt` | 24 | `2202001..2202024` | Non-confirmatory baseline & biological ablation evaluation |
| Validation | `experiments/v2_2/seeds.validation.txt` | 20 | `2203001..2203020` | Out-of-sample protocol validation prior to freeze |
| Confirmatory Pool | `experiments/v2_2/seeds.confirmatory.pool.txt` | 100 | `2204001..2204100` | Locked pool; `seeds.confirmatory.txt` is **not** materialized until explicit confirmatory authorization |

### 3.2 Determinism Guarantees in V2

1. **SHA-256 namespace RNG derivation (`src/mycelial_graph/v2/seeding.py`):** Scenario latents, outcome realizations, and policy RNGs derive from isolated `SHA-256("mycelial-graph-v2:{seed}:{namespace}")` streams.
2. **Paired ablation variance reduction:** All `v2_*` controller variants share the per-scenario stream `agent:{regime}:v2_mycelial_family` so differences between `v2_mycelial` and `v2_no_*` reflect mechanism toggles rather than Monte Carlo draw divergence.
3. **Immutable scenario tensors:** All `ResourceScenario` numpy arrays are marked `writeable = False` at construction, preventing cross-policy state leakage.
4. **Byte-identical compressed traces:** Step traces (`traces/*.jsonl.gz`) write canonical `sort_keys=True` JSON lines through `gzip.GzipFile(..., mtime=0)` into a temporary file, call `os.fsync`, and atomically `os.replace`, producing identical SHA-256 digests across repeated runs on the same Python/NumPy runtime.

### 3.3 Exact Commands for V2 Reproduction

```bash
# Validate V2 configurations (confirmatory config intentionally returns exit code 2 while locked)
mycelial-graph v2-validate --config experiments/v2_2/config.development.yaml
mycelial-graph v2-validate --config experiments/v2_2/config.pilot.yaml

# Run paired pilot benchmark, analysis, report, resource audit, waste audit, and visualization
mycelial-graph v2-experiment --config experiments/v2_2/config.pilot.yaml --output outputs/v2_2_pilot --workers 1
mycelial-graph v2-analyze --config experiments/v2_2/config.pilot.yaml --output outputs/v2_2_pilot
mycelial-graph v2-report --config experiments/v2_2/config.pilot.yaml --output outputs/v2_2_pilot
mycelial-graph v2-resource-audit --output outputs/v2_2_pilot
mycelial-graph waste-audit --output outputs/v2_2_pilot
mycelial-graph v2-viz --config experiments/v2_2/config.pilot.yaml --output outputs/v2_2_pilot

# Re-run the complete MG-EXP-V2.2 pilot + ablation + scaling + budget + VOC suite
python scripts/run_v2_2_pilot_suite.py

# Execute full unit, regression, integrity, and property-based test suite
python -m pytest -v tests
```
