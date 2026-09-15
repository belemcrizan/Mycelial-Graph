# Rho crossover

## Target

**CONJECTURE.** A threshold $\rho^*$ exists for a specified $(M,K,\sigma,n,\text{topology})$.

Ideal workflow:

```text
theory -> predicted rho* -> pre-registration -> frozen experiment -> observed rho* -> prediction error
```

Never fit $\rho^*$ after seeing the evaluation sweep and call it a prediction.

## Sketch in the Gaussian toy (not V1)

From D2, pooling wins when average squared idiosyncratic deviation is smaller than the variance gap:

$$
\frac{1}{K}\sum_e(\theta_e-\bar\theta)^2
<
\sigma^2\Big(\frac{1}{n}-\frac{1}{nK}\Big).
$$

Under the constant-L2 construction $\|\mathrm{shared}\|_2^2 = m^2\rho$ and $\|\mathrm{idio}\|_2^2 = m^2(1-\rho)$, the left side scales with $m^2(1-\rho)$ (up to a geometry factor $c_{\mathrm{top}}$). Then a crossover of the form

$$
\rho^*
=
1
-
\frac{\sigma^2(1-1/K)}{c_{\mathrm{top}} m^2 n}
$$

is a **candidate**, valid only under A4, Gaussian MSE, and grand-mean pooling.

**This formula is not a V1 prediction.** V1 uses RRT on paths with conductance updates. Using this $\rho^*$ as a confirmatory forecast for MG-EXP-V1 would be invalid.

## V1.5 protocol

A future **MG-EXP-V1.5-RHO** may pre-register a predicted curve $G(\rho)$ after a derivation that actually uses RRT, not MSE. Until then $\rho^*$ remains OPEN_PROBLEM for the scientific identity of Mycelial.

## Falsification

An observation that would falsify a specific predicted $\rho^*_{\mathrm{theory}}$ is

$$
|\hat\rho^*_{\mathrm{obs}}-\rho^*_{\mathrm{theory}}|
$$

exceeding a pre-registered tolerance after the independent sweep.
