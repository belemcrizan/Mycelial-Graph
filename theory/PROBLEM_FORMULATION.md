# Problem formulation

**CLASSIFICATION: DEFINITION** unless marked otherwise.

## Research identity

Learn the appropriate amount of information sharing under correlated non-stationarity.

Let $\lambda_t \in [0,1]$ be a pooling weight (1 = fully local, 0 = fully shared, or an equivalent orientation documented at use). The long-term object is

$$
\lambda_t^*
=
f(
\text{shared variation},
\text{idiosyncratic variation},
\text{uncertainty},
\text{topology},
\text{history},
\text{context},
\text{cost}
).
$$

This $f$ is **not derived** in this document.

## Minimal observation model

Index edges (actions) by $e \in \{1,\ldots,K\}$ and discrete time by $t=1,\ldots,T$.

$$
R_e(t)
=
\mu_e
+
S_{g(e)}(t)
+
L_e(t)
+
\epsilon_e(t).
$$

| Symbol | Meaning |
|---|---|
| $\mu_e$ | stationary edge component |
| $S_{g(e)}(t)$ | variation shared by structurally related actions in group $g(e)$ |
| $L_e(t)$ | idiosyncratic / local variation |
| $\epsilon_e(t)$ | observation noise |

**DEFINITION (variation budget).** For a window $\mathcal T$,

$$
V_{\mathrm{shared}}(\mathcal T)
=
\sum_{g}\sum_{t\in\mathcal T}\|S_g(t)\|^2,
\qquad
V_{\mathrm{idio}}(\mathcal T)
=
\sum_e\sum_{t\in\mathcal T}\|L_e(t)\|^2.
$$

$$
V = V_{\mathrm{shared}} + V_{\mathrm{idio}}
$$

is a convenient accounting identity, **not** an identification result.

**ASSUMPTION (non-identifiability).** Without restrictions on $S$, $L$, $\epsilon$, and $g$, the decomposition is not identifiable from observed rewards alone.

## Minimal solvable setting (start here)

```text
one shared parent
K child edges
single change point τ
Gaussian or bounded rewards
shared shock and/or idiosyncratic shock
known structure g
finite horizon T
```

Action space: choose one edge (or one path that includes one child) per round.

Feedback: semi-bandit / local reward on the chosen edge.

Topology: star with known parent.

Stationarity: piecewise constant with one change at $\tau$.

Noise: $\epsilon_e(t)\sim\mathcal N(0,\sigma^2)$ independent, or bounded in $[0,1]$ as in V1 (V1 is a different protocol).

Horizon: $T = T_{\mathrm{pre}} + T_{\mathrm{post}}$.

Number of actions: $K$.

Shared group structure: all $K$ children share parent $g$.

Known versus unknown topology: **known** in the minimal model.

Known versus unknown correlation: $\rho$ may be treated as known for derivation and unknown for learning $\lambda_t$.

## Learners to compare in this model

```text
local-only
fixed pooled
adaptive pooled (empirical Bayes / James–Stein)
oracle (knows post-change means)
```

Increase DAG complexity only after this model is characterized.

## Execution DAG versus causal DAG

**DEFINITION.** The V1 layered execution graph is an action/feasibility graph.

$$
\text{Execution DAG} \neq \text{Causal DAG}.
$$

Causal claims require an explicit SCM. None is assumed here.
