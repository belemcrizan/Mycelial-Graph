# MG-EXP-POOLING-001 — Adaptive pooling on the minimal shared/idiosyncratic model

**Status:** Protocol + toy estimator implemented. Not a V1 result.  
**Frozen-protocol impact on V1:** NONE.

## Question

On the star with $K$ children and one change point, when does James–Stein / empirical-Bayes pooling beat local means and beat naive grand-mean pooling, as a function of $\rho$?

## Estimand

Post-change mean-squared error versus true post means. Lower is better.

$$
\mathrm{NT}(\rho)=\mathrm{MSE}_{\mathrm{adaptive}}(\rho)-\mathrm{MSE}_{\mathrm{local}}(\rho).
$$

## Methods

- local-only sample means
- fixed pooled grand mean
- adaptive pooled (positive-part James–Stein)
- oracle (true means; zero MSE by construction, diagnostic only)

## What this cannot answer

V1 restricted recovery time, path constraints, conductance, or confirmatory hierarchical advantage.

## Command

```text
mycelial-graph pooling-toy --seed 0
```

Toy outputs are development diagnostics for the competitor, not confirmatory science.
