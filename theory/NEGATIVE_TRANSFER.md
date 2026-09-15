# Negative transfer

Negative transfer is a first-class theoretical object, not only a V1 safety gate.

## Definition

Let $M$ be a lower-better performance functional (MSE of post-change means in the toy model; RRT in V1 — **do not mix protocols**).

**DEFINITION.**

$$
\mathrm{NT}(\rho)
=
M_{\mathrm{shared}}(\rho)
-
M_{\mathrm{local}}(\rho).
$$

$\mathrm{NT}>0$ means sharing hurt.

## What to characterize

| Aspect | Question |
|---|---|
| Magnitude | How large is $\mathrm{NT}(\rho)$? |
| Duration | How long does the bias persist after the shock? |
| Recovery | Does sharing shorten or lengthen RRT? |
| Topology | Does a misspecified $g$ inflate NT? |
| Shock | Sparse idiosyncratic versus dense shared |
| Uncertainty | Does NT grow when $\sigma$ is large enough that $\rho$ cannot be estimated? |

## Bias–variance trade-off

**PROPOSITION (sketch, Gaussian toy).** For grand-mean pooling,

$$
\mathbb E[\mathrm{NT}]
\approx
\mathbb E\|\theta-\bar\theta 1\|^2_{\mathrm{avg}}
-
\sigma^2\Big(\frac{1}{n}-\frac{1}{nK}\Big).
$$

Variance reduction is $O(\sigma^2(1-1/K)/n)$. Bias is the idiosyncratic mean spread.

Adaptive pooling aims to estimate that spread ($\tau^2$ in $\theta_e\sim\mathcal N(\theta_{\mathrm{node}},\tau^2)$) and move $\lambda$ toward local when $\tau^2$ is large.

## V1 connection (non-amending)

V1 already uses $\rho=0$ as a non-inferiority gate on RRT. That gate is a **protocol-specific empirical NT control**, not a derivation of $\mathrm{NT}(\rho)$.
