# Derivations

All results below are either textbook or sketches. None is a Mycelial recovery-time theorem.

## D1 James–Stein positive-part shrinkage

**PROPOSITION (classical, not original).** For $K\ge 3$ independent Gaussian means with known observation variance $\sigma^2/n$, the positive-part James–Stein estimator dominates the MLE of the mean vector under SSE.

This justifies an **adaptive pooling competitor**, not V1 hierarchical conductance.

## D2 MSE of local versus grand-mean pooling after one shock

Consider post-change samples $n$ per arm, noise variance $\sigma^2$, true means $\theta_e = \mu + s + \ell_e$.

**DEFINITION.** Local estimator $\hat\theta_e^{\mathrm{loc}} = \bar X_e$, pooled estimator $\hat\theta_e^{\mathrm{pool}} = \bar X_{\cdot}$.

$$
\mathrm{MSE}_{\mathrm{loc}}
=
\frac{\sigma^2}{n},
\qquad
\mathrm{MSE}_{\mathrm{pool}}
=
\Big(\theta_e - \bar\theta\Big)^2
+
\frac{\sigma^2}{nK}.
$$

Pooling reduces variance by $K$ and pays bias $\|\theta - \bar\theta 1\|^2 / K$ per coordinate.

When $\ell=0$ and $s$ is common, bias is zero and pooling wins for every $n,K$.

When $s=0$ and $\ell$ is sparse, bias is first-order in the idiosyncratic mass and pooling can lose.

## D3 Why the target regret form is not proved here

A non-stationary combinatorial semi-bandit with sliding-window UCB already has variation-budget analyses in the literature. Mapping those bounds onto V1's restricted recovery time, layered path constraints, and conductance updates is **not** a routine corollary.

**OPEN_PROBLEM.** Reduce V1 RRT to a standard dynamic-regret estimand under A1–A4, or prove they are inequivalent.
