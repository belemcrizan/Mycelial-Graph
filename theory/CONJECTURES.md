# Conjectures

Nothing in this file is a theorem.

## C-RATE hierarchical recovery rate

**CONJECTURE (target form, not proved).** In a suitable layered semi-bandit with $L$ effective layers, $K_{\mathrm{node}}$ shared factors, $K_{\mathrm{edge}}$ local factors, horizon $T$, and shared-shock fraction $\rho$, hierarchical pooling might achieve a recovery/regret rate conceptually similar to

$$
\tilde O\Big(
\sqrt{L K_{\mathrm{node}} T}
+
\sqrt{L K_{\mathrm{edge}} T(1-\rho)}
\Big)
$$

instead of an edge-only dependence closer to

$$
\tilde O\big(\sqrt{L K_{\mathrm{edge}} T}\big).
$$

The actual rate may differ. Constants, logs, and the precise estimand (regret versus restricted recovery time) are unspecified.

**OPEN_PROBLEM.** Prove, refute, or replace this form under stated assumptions. Document impossibility when assumptions fail (for example unknown $g$, heavy tails, or adversarial $\epsilon$).

## C-RHO crossover

**CONJECTURE.** There exists a critical $\rho^*$ such that, for a fixed local-versus-shared comparison and a fixed estimand $M$ (lower better),

$$
\rho < \rho^* \Rightarrow \mathbb E[M_{\mathrm{shared}}] > \mathbb E[M_{\mathrm{local}}]
$$

$$
\rho > \rho^* \Rightarrow \mathbb E[M_{\mathrm{shared}}] < \mathbb E[M_{\mathrm{local}}].
$$

$\rho^*$ is a function of $K,\sigma,L,\Delta,T$, topology, and prior. Fitting $\rho^*$ after seeing a confirmatory sweep and presenting it as a prediction is forbidden.

## C-ADAPTIVE

**EMPIRICAL_HYPOTHESIS (new protocol only).** Adaptive pooling that estimates between-edge variance can dominate fixed hierarchical Mycelial on some $(\rho,K,\sigma)$ regions.

If this occurs, it is scientific information, not a result to hide.

## C-MODELSEL

**OPEN_PROBLEM.** Whether CORRAL / regret balancing / EXP4 over {local, pooled, hierarchical} removes the need to preselect aggregation level.
