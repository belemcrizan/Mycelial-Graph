# Implementation report — Evidence Bridge (MG-EXP-V2.1)

## What changed and why

V2.0-alpha could not falsify the threat that Mycelial is an elegant graph whose gains vanish against a strong allocator, or that gains are only cheaper-model routing. V2.1 adds **measurement instruments** and **adversaries** without deleting V0/V1/V2-alpha or unlocking confirmatory execution.

## Equations

```text
VOC_diff = E[ΔQ] − λ E[ΔR]
MVC      = E[ΔQ] / max(E[ΔR], ε)
ΔQ NI    : lower_CI(Q_M − Q_H) > −ε
Saving   : lower_CI(1 − T_M/T_H) > MMRR
Regret   : U_oracle(B) − U_policy(B)   (evaluation-only)
```

## Files (additive)

- `src/mycelial_graph/v2/biology/voc.py`
- `src/mycelial_graph/v2/evaluation/*`
- `src/mycelial_graph/v2/policies/baselines_strong.py`, `oracle.py`
- `src/mycelial_graph/v2/resources/reservation.py`
- `src/mycelial_graph/v2/real/*`
- `experiments/v2_1/`
- docs listed in the PR
- `research/references.yaml`

V1 modules were not rewritten. V2 analysis JSON schema for alpha runs is unchanged.

## New tests

`tests/test_v2_1.py`: VOC stability, reservation, iso-model collapse, oracle regret sign, strong baseline factory, waste identity, voc-bench smoke, executable real grader, autonomous agent (no gold injection), claim audit, CLI.

## New benchmarks

- Synthetic VOC bench (`mycelial-graph voc-bench`)  
- Iso-model development config  
- Budget curves (`mycelial-graph budget-curve`)  
- Waste audit  
- Local real-smoke (2 tasks, autonomous repair loop, no gold-patch injection)

## Results

UNKNOWN / development-only. This report does not contain fabricated scores.

## Failures (pre-registered)

Expected: TS or Lagrangian matches Mycelial; iso-model null; false-stop on hard verify; real-smoke is too small to generalize.

## Limitations

No SWE-bench; no live models; no dynamic branching; stub alpha ablation names remain aliases (now labeled); literature first pass only.

## Deferred

Milestone 2+ in the research prompt (true branching, fusion gating, E6–E9, confirmatory).

## Claim status

See `docs/CLAIM_EVIDENCE_MATRIX.md`. C03 remains NOT_SUPPORTED.

## Reproducibility

```powershell
python -m pip install -e .
python -m unittest discover -s tests -v
mycelial-graph validate --config experiments/v1/config.development.yaml
mycelial-graph v2-validate --config experiments/v2/config.development.yaml
mycelial-graph v2-validate --config experiments/v2_1/config.development.yaml
mycelial-graph voc-bench --config experiments/v2_1/config.development.yaml
mycelial-graph real-smoke
mycelial-graph claim-audit --matrix docs/claim_evidence_matrix.yaml
mycelial-graph evidence-audit
```

Do not present these commands’ stdout as confirmatory science.
