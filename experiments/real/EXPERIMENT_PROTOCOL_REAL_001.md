# MG-EXP-REAL-001 — Real-World Routing Replay Under Structured Non-Stationarity

**Protocol version:** MG-EXP-REAL-001  
**Status:** Designed, not executed. No real-trace or live result exists.  
**Frozen-protocol impact on V1:** NONE. This is a new protocol.

## Question

How should a router adapt when the identity of a better route changes over time on data **not designed around Mycelial**?

This is not the V1 RRT question.

## Evidence layer

Layer B (replay). Layer C (bounded live) is out of scope until a dry-run collector is authorized for spend.

## Data (candidate, not ingested)

Subject to license gates in `external/LICENSES.md`:

- Arena / LMSYS preference tables for quality signals;
- RouteLLM / RouterArena public artifacts for router comparison;
- optional UTC incident annotations joined only as observational labels.

If a chosen corpus has no timestamps, the run must be labeled **UNORDERED_STATIC_BATTLE** and must not claim recovery analysis.

## Methods (inclusion with justification)

| Method | Include? | Justification |
|---|---|---|
| Static | yes | non-adaptive floor |
| SW-UCB | yes | standard non-stationary bandit |
| Discounted UCB | yes | standard alternative |
| Change-point + reset | yes | detect-then-reset competitor |
| Adaptive pooling (EB) | yes | mandatory strong competitor |
| Mycelial edge-only | yes | V1 control family, new data |
| Mycelial hierarchical | yes | V1 treatment family, new data |
| Model-selection master | yes if $\ge$3 learners | answers “why preselect aggregation?” |
| Oracle | yes, offline only | not a deployed competitor |
| Random / greedy / UCB1 / TS / EXP3 | optional | include when action set is a simple MAB |
| LinUCB | only if context $x_t$ exists |
| CORRAL | deferred to a later amendment if compute allows |

Do not insert these methods into MG-EXP-V1.

## Metrics (pre-specified; primary frozen before first evaluation)

Primary (if timestamps and a post-change window exist):

- DynamicRegret

Secondary:

- Quality (preference or benchmark accuracy)
- Cost (versioned prices only)
- p95Latency (only if collected)
- FailureRate
- NegativeTransfer (defined on a pre-registered unaffected subset)
- RestrictedRecoveryTime (only if a recovery event is defined)
- AdaptationDebt (definition must be frozen before use; currently unspecified — do not report)

If the corpus is static battles without time, primary becomes pairwise quality versus cost Pareto, and RRT is **inapplicable**.

## Logging for OPE

When logging a policy, store $x_t,a_t,r_t,p_t(a_t\mid x_t)$ plus cost, latency, timestamp, model, policy_version. Report ESS, propensity support, clipping, variance, and unsupported regions. Do not present unstable IPS as truth.

## Contamination

Record benchmark date, model date, possible training contamination, whether outputs are precomputed, and judge exposure.

## Execution status

Not run. No paid calls. No downloaded restricted data.
