# Development tuning note

## Purpose and claim boundary

The final V0 Mycelial settings were selected on five development seeds: `17, 29, 43, 59, 71`. These do not appear in the generated 12-seed demonstration report. This separation reduces direct result chasing, but the V0 demonstration seeds are not represented as a publication-grade untouched holdout.

## Frozen combined-shock scenario

The tuning rehearsal used the checked-in graph, 240 steps, shock at step 100, the same common utility, and the final combined shock against `model_balanced`. The pre/post oracle certification had to pass before routing.

## Search space

| Parameter | Values |
| --- | --- |
| Temporal decay | `0.002, 0.005, 0.01, 0.02` |
| Plasticity | `0.30, 0.45, 0.80, 1.20` |
| Temperature | `0.05, 0.10, 0.20, 0.35` |
| Explicit exploration | `0.04, 0.08, 0.15, 0.25` |

All 256 combinations used the same five frozen development trials. Selection was lexicographic: higher recovery probability, higher post-shock utility, lower recovered-only SRC, then lower SER.

## Selected V0 values

| Parameter | Value |
| --- | ---: |
| Temporal decay | `0.002` |
| Plasticity | `0.80` |
| Temperature | `0.35` |
| Explicit exploration | `0.15` |

Other frozen conductance bounds and exploration reinforcement remain in `configs/v0_demo.yaml`.

## Limitation

Five development seeds and one combined shock are enough to rehearse a tuning boundary, not to establish robustness. Scientific V1 must pre-register a broader development matrix, freeze it before final evaluation, and report sensitivity rather than publishing only the selected point.
