# Assumptions

Label every modeling choice. Do not treat these as theorems.

## A1 known structure

**ASSUMPTION.** The grouping map $g$ is known. Unknown $g$ is deferred (`P(G\mid\mathrm{data})` is an OPEN_PROBLEM).

## A2 one change point

**ASSUMPTION.** There is a single change time $\tau$ in the minimal model. Multiple change points are a later protocol.

## A3 Gaussian or bounded noise

**ASSUMPTION.** Either $\epsilon_e(t)$ is i.i.d. Gaussian with known or consistently estimated variance, or rewards are bounded in a known interval.

## A4 variation orthogonality (identifying restriction)

**ASSUMPTION (optional, for matching V1's L2 construction).** Shared and idiosyncratic shock patterns are disjoint in a known inner-product sense so that

$$
\|d(\rho)\|_2 = m \quad \forall \rho\in[0,1].
$$

Without this, $\rho$ is a correlational shorthand, not a calibrated budget coordinate.

## A5 known versus estimated $\rho$

**ASSUMPTION (derivation).** Closed-form $\rho^*$ sketches treat $\rho$, $K$, $\sigma$, and sample size as known.

**ASSUMPTION (learning).** Online $\lambda_t$ does **not** observe $\rho$ directly.

## A6 no causal fault

**ASSUMPTION.** Observing correlated degradation is not a $do(\cdot)$ intervention. Status-page incidents, if used later, are annotations, not causal labels.

## A7 V1 isolation

**ASSUMPTION (governance).** Insights written after V1 freeze do not modify MG-EXP-V1. They spawn new protocols.
