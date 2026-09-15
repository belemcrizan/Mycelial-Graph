# Strong baselines plan

New protocols only. **Forbidden** as a silent V1 method list expansion.

## Bandit / routing competitors (use when the action model matches)

Random, static, pre-shock optimal, greedy, $\epsilon$-greedy, UCB1, SW-UCB, discounted UCB, Thompson sampling, discounted TS, EXP3, EXP3.S, change-point+reset, partial reset, BOCPD+UCB, LinUCB (contextual only), cold-reset, oracle, non-Mycelial hierarchical, empirical-Bayes pooling.

## Model selection

CORRAL, regret balancing, EXP4 over learners. Until this class is run, do not claim that preselected hierarchical aggregation is necessary.

## Change detection

Page-Hinkley, CUSUM, BOCPD, PELT, ADWIN if assumptions fit.

Compare: continuous adaptation, full reset, detect→reset, detect→partial reset, detect→hierarchical transfer.

A detector firing is not causal localization.

## Already present (do not confuse)

- V1: edge-only, node-only, hierarchical, structured SW-UCB.
- V2.1: Thompson sampling quality, cost-sensitive bandit, and other allocation baselines inside the resource layer — not V1 recovery competitors.

## Adaptive pooling (mandatory competitor)

Implemented for MG-EXP-POOLING-001 (`james_stein_means`). If it defeats hierarchical Mycelial on a later shared protocol, report it.
