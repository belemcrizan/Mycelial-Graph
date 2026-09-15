# Mycelial Graph V1 Research Edition

> **Headline result (2026-09-15).** The frozen V1 confirmatory experiment has been run. Its
> primary hypothesis is **`REFUTED`**: at ρ=0.50 hierarchical node-edge pooling recovered
> **42.1% slower** than edge-only adaptation (95% CI +11.9% to +79.1%, n=97 paired scenarios), and
> the ρ=0 negative-transfer safety gate also failed. Details and claim boundary in
> [Honest status](#honest-status). A refutation is a legitimate scientific outcome and is reported
> here without reframing.

**Paper A.** A TMLR-formatted manuscript of this frozen result is in
[`paper/tmlr/paper.tex`](paper/tmlr/paper.tex). Current TMLR policy was verified 2026-09-15
(double-blind, mandatory stylefile, anonymized supplementary ZIP, preprints allowed if not
linked from the submission). The paper is **not yet submitted**; OpenReview login is a human
boundary. See [`paper/SUBMISSION.md`](paper/SUBMISSION.md). A post-confirmatory equalization
triage classified the comparison as **EQ-B** (material effective-policy mismatch, result still
interpretable): disclose prominently, do not overwrite `REFUTED`. Until Paper A is submitted,
V1.5 / routing-product work remains out of scope.

V2.0-alpha is an **additive** scientific layer. It does not replace V1. The V1 question, protocol, CLI, and confirmatory lock remain in force. See [V2 implementation plan](docs/V2_IMPLEMENTATION_PLAN.md) and `mycelial-graph v2-demo`.

Mycelial Graph studies a practical question: **can an AI execution system recover from a local disruption without relearning everything?**

Modern AI work rarely uses one model in isolation. A task may cross a prompt strategy, retriever, model, tool, guardrail, parser, cloud region, and fallback. Mycelial Graph represents these choices as a directed graph. Like an adaptive transport network, frequently useful connections become easier to select, degraded connections weaken, and unaffected structure can retain what it already learned.

This repository is a reproducible research implementation by **Crizan Belem Ribeiro, Independent Researcher**. It is not a production router and it does not claim that the hierarchical method is superior. Its purpose is to test that claim fairly.

## What changed from V0

V0 demonstrated local edge conductance. V1 preserves that mechanism and adds the scientific controls needed to determine *why* a method wins:

- immutable scenarios with identical potential outcomes for every method;
- isolated random-number streams for environment and agents;
- edge-only, node-only, hierarchical node-edge, and structured SW-UCB conditions;
- controlled shared-shock fraction `rho` with constant total shock magnitude;
- pre/post optimum certification;
- censoring-aware restricted recovery time;
- paired bootstrap analysis and explicit decision gates;
- atomic checkpoints, manifests, trace hashes, and automatic reports;
- a locked confirmatory configuration that cannot run before sample size is recorded.

## The idea in one picture

```text
Task -> Prompt -> Retriever -> Model -> Guardrail -> Output
          \          \          \
           alternative nodes and edges at each stage

Local observations -> adaptive state -> next route
                              |
                 edge-only / node-only / hierarchical
```

The critical comparison is not “adaptive versus nothing.” It asks whether sharing state through nodes accelerates recovery when a disruption is genuinely shared, without causing unacceptable negative transfer when it is edge-specific.

## Quick start (Linux / macOS first)

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
python -m pip install -e .
python reproduce_confirmatory.py
```

Windows PowerShell:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.lock.txt
python -m pip install -e .
python reproduce_confirmatory.py
```

`python reproduce_confirmatory.py` verifies sealed hashes and, if local raw trials exist, recomputes the frozen primary contrast. Full re-execution: `python reproduce_confirmatory.py --full`. Measured decision CPU of the sealed confirmatory run: **0.122 CPU-hours**.

The demo remains a development-only path:

```bash
mycelial-graph demo
```

## Scientific workflow

```text
development seeds -> implementation checks
pilot seeds       -> variance and sample-size calculation
addendum          -> fixes N and selects first N seeds mechanically
confirmatory run  -> frozen execution with no tuning
report            -> pass, conditional result, inconclusive, or refuted
```

### Current state of the confirmatory lock

There is exactly one description of this state, and it is mechanically checked by
`python scripts/audit_v1_readiness.py`:

- `experiments/v1/seeds.confirmatory.txt` **exists**. It was created after the pilot, from
  the first `N=97` entries of the precommitted pool `seeds.confirmatory.pool.txt`, unfiltered
  and unreordered (seeds `700000`–`700096`).
- Its SHA-256 is `8ef4c6b0dc481fea70054b6d7cbc9ecc2663f63b4523f3f55bb374a0339ee00c`, which is
  the value bound in [`CONFIRMATORY_FREEZE.json`](experiments/v1/artifacts/CONFIRMATORY_FREEZE.json).
- It has zero overlap with the pilot (20 seeds) or development (5 seeds) populations.
- `N=97` comes from the pre-specified normal-approximation formula applied to pilot
  variability, recorded in [`SAMPLE_SIZE_ADDENDUM.md`](experiments/v1/SAMPLE_SIZE_ADDENDUM.md).
- Before the addendum existed, this file was deliberately absent and
  `mycelial-graph validate --config experiments/v1/config.confirmatory.yaml` failed by design.
  That lock is now **released**; validation passes.

The confirmatory experiment has since been executed on exactly these 97 seeds. Its outcome is
`REFUTED`; see [Confirmatory evidence](#confirmatory-evidence-produced-by-the-frozen-v1-protocol)
below. Do not treat the pilot as confirmatory.

## The V1 confirmatory question

Frozen on 2026-08-24 in [`EXPERIMENT_PROTOCOL_V1.md`](experiments/v1/EXPERIMENT_PROTOCOL_V1.md)
(sections 7.3, 8.1, 8.3) and [`ANALYSIS_PLAN.md`](experiments/v1/ANALYSIS_PLAN.md) (sections 2–5),
before the pilot was run and before any confirmatory outcome was observed.

**Primary confirmatory contrast.** Hierarchical node-edge pooling versus edge-only adaptation
at a shared-shock fraction of `rho = 0.50`, on the frozen primary estimand

```text
delta_RRT = (mean RRT_hierarchical - mean RRT_edge_only) / mean RRT_edge_only
```

where `RRT` is restricted recovery time (`min(recovery_time, tau)`, `tau = 300` post-shock
steps, administrative censoring only). `H0: delta_RRT >= 0` against `H1: delta_RRT < 0`,
paired bootstrap over frozen scenarios, frozen one-sided 95% upper bound.

**Safety / negative-transfer gate.** The same paired contrast at `rho = 0`, where the shock is
purely edge-specific, against the pre-specified non-inferiority margin `Delta_NI = +0.10`:
`H0: delta_RRT >= +0.10` against `H1: delta_RRT < +0.10`. This gate asks whether hierarchical
sharing spreads a wrong conclusion when nothing is actually shared.

`N = 97` paired scenarios are powered for the **primary contrast only** (one-sided alpha 0.05,
power 0.80, design target `delta_RRT = -0.20`). See
[`HYPOTHESIS_MATRIX.md`](experiments/v1/HYPOTHESIS_MATRIX.md) for every contrast that can appear
in a report, its role, and the claim it is permitted to support.

### What V1 can test

- the pre-specified hierarchical-versus-edge-only primary contrast at `rho = 0.50`;
- the pre-specified negative-transfer non-inferiority condition at `rho = 0`.

### What V1 cannot establish

V1 is not designed or powered for any of the following, and no V1 result may be worded as if
it were:

- existence of a crossover `rho*`;
- the location of `rho*`;
- the shape of the `rho -> effect` curve;
- universal superiority of hierarchical pooling;
- universal superiority of Mycelial Graph;
- production superiority or production readiness;
- generalisation to real providers;
- causal fault localisation;
- theoretical sample-complexity improvements;
- general contextual-routing superiority.

Everything reported at `rho` values other than `0` and `0.50`, and every contrast other than
hierarchical-versus-edge-only, is **exploratory or diagnostic** under the frozen analysis plan.

## Development moratorium

A [V1 confirmatory moratorium](V1_CONFIRMATORY_MORATORIUM.md) is in force. V2.0-alpha, V2.1,
V2.1-A, `theory/`, `external/`, and the pooling/real protocol tracks are frozen — preserved,
not deleted — until V1 reaches a legitimate terminal state.

## V2.0-alpha (additive, frozen)

V2 asks a second question without unfreezing V1: can an adaptive graph spend extra inference resources only where they are worth it, while keeping quality non-inferior and counting **all** tokens, including the router? See [V2 research questions](docs/V2_RESEARCH_QUESTIONS.md) and [MG-EXP-V2](experiments/v2/EXPERIMENT_PROTOCOL_V2.md). Physarum is not a fungus. This layer is not production-ready.

```powershell
mycelial-graph v2-validate --config experiments/v2/config.development.yaml
mycelial-graph v2-demo
```

## Commands

```powershell
mycelial-graph validate --config experiments/v1/config.pilot.yaml
mycelial-graph experiment --config experiments/v1/config.pilot.yaml --output outputs/pilot --workers 4
mycelial-graph analyze --config experiments/v1/config.pilot.yaml --output outputs/pilot
mycelial-graph report --config experiments/v1/config.pilot.yaml --output outputs/pilot
mycelial-graph sample-size --config experiments/v1/config.pilot.yaml --output outputs/pilot
mycelial-graph v2-experiment --config experiments/v2/config.development.yaml --output outputs/v2-dev
mycelial-graph v2-analyze --config experiments/v2/config.development.yaml --output outputs/v2-dev
mycelial-graph v2-report --config experiments/v2/config.development.yaml --output outputs/v2-dev
mycelial-graph v2-resource-audit --output outputs/v2-dev
mycelial-graph voc-bench --config experiments/v2_1/config.development.yaml
mycelial-graph real-smoke
mycelial-graph claim-audit --matrix docs/claim_evidence_matrix.yaml
python scripts/audit_v1_readiness.py
```

## Read next

- [Paper A manuscript](paper/tmlr/paper.tex) - TMLR-formatted report of the frozen V1 result (not yet submitted).
- [Getting Started](docs/GETTING_STARTED.md) - step-by-step instructions for non-specialists.
- [Architecture](docs/ARCHITECTURE.md) - system boundaries and data flow.
- [Frozen Experiment Protocol](experiments/v1/EXPERIMENT_PROTOCOL_V1.md) - hypotheses and immutable rules.
- [Analysis Plan](experiments/v1/ANALYSIS_PLAN.md) - estimands, bootstrap, gates, and interpretation.
- [Hypothesis Matrix](experiments/v1/HYPOTHESIS_MATRIX.md) - every contrast, its role, and the claim it permits.
- [Confirmatory Readiness Report](CONFIRMATORY_READINESS_REPORT.md) - integrity audit and GO/STOP decision.
- [Confirmatory Runbook](CONFIRMATORY_RUNBOOK.md) - the single canonical execution path.
- [V1 Confirmatory Moratorium](V1_CONFIRMATORY_MORATORIUM.md) - what is frozen and how the freeze ends.
- [Roadmap](docs/ROADMAP.md) - evidence-gated growth toward real providers and cloud tests.
- [V2 implementation plan](docs/V2_IMPLEMENTATION_PLAN.md) - additive resource-allocation layer.
- [Sustainability](docs/SUSTAINABILITY.md) - technical, financial, scientific, and environmental sustainability.
- [Migration from V0](docs/MIGRATION_FROM_V0.md) - how to integrate the three prototypes without a blind code merge.

## Honest status

Read this section instead of inferring status from the number of files, tests, or modules.
Infrastructure is not evidence.

### Completed infrastructure (exists and runs)

- V1 simulator, four methods, immutable paired scenarios, isolated RNG streams, atomic
  checkpoints, manifests, trace hashing, static figures, automated reports.
- V1 development demonstrator and the 20-seed pilot pipeline.
- V2.0-alpha resource layer, MG-EXP-V2.1 Evidence Bridge instrumentation, MG-EXP-V2.1-A local
  autonomous repair loop, `external/` adapters and schemas, `theory/` scaffolding,
  claim-evidence audit machinery. All frozen under the moratorium.

### Verified evidence (mechanically checked, non-confirmatory)

- Determinism, paired-scenario identity, serial/parallel payload equivalence, shock-magnitude
  invariance, pre/post optimum certification, and seed-population separation are covered by the
  test suite (`python -m pytest tests`) and by `python scripts/audit_v1_readiness.py`.
- The V1 **pilot** (20 seeds, 5 rho values, 4 methods) completed and is sealed in
  `experiments/v1/artifacts/`. It is variance and sample-size evidence only. Its own numbers
  were unfavourable to the hierarchical method: the primary point estimate was −10.2% with a
  one-sided upper bound above zero, and the `rho=0` non-inferiority gate failed. This is
  recorded, not hidden, and it does not predict the confirmatory outcome.

### Confirmatory evidence (produced by the frozen V1 protocol)

**The V1 confirmatory experiment was executed and the primary hypothesis was `REFUTED`.**

Executed at commit `5f314d2` under
[`CONFIRMATORY_FREEZE.json`](experiments/v1/artifacts/CONFIRMATORY_FREEZE.json), on the 97
pre-selected paired scenarios, with no post-pilot tuning. Sealed evidence:
[`experiments/v1/artifacts/confirmatory/`](experiments/v1/artifacts/confirmatory/).

- **Primary contrast (ρ=0.50, hierarchical vs edge-only).** Mean restricted recovery time was
  **+42.1% higher** for hierarchical pooling, i.e. recovery was *slower*, with a 95% bootstrap
  interval of +11.9% to +79.1% and a one-sided upper bound of +72.1%. The pre-specified relevant
  benefit of −20% lies outside the interval, so the frozen analysis plan classifies this as
  `REFUTED` rather than inconclusive.
- **Safety gate (ρ=0, margin +0.10).** One-sided upper bound +16.3% exceeds the margin, so
  non-inferiority was **not** established: negative transfer at ρ=0 cannot be excluded.
- **Integrity.** 97/97 primary pairs executed, censoring administrative only, zero method
  failures inside the frozen contrasts.

What this means, stated no more strongly than the design permits: in this synthetic layered-DAG
semi-bandit, under this shock construction and this parameter range, hierarchical node-edge
pooling did not accelerate recovery at ρ=0.50 and did not clear its own negative-transfer safety
gate at ρ=0. That is a real negative result for the mechanism this repository was built around, and
it is reported as such. It does not say hierarchical pooling is useless everywhere, and it does not
establish anything about other ρ values, a crossover, or real systems — the design cannot support
those statements in either direction.

The full report, including the frozen decision gate and all exploratory rows, is
[`experiments/v1/artifacts/confirmatory/REPORT.md`](experiments/v1/artifacts/confirmatory/REPORT.md).
Readiness audit: [`CONFIRMATORY_READINESS_REPORT.md`](CONFIRMATORY_READINESS_REPORT.md). Execution
record: `research/ledger/ledger.jsonl`. Claim boundary:
[`HYPOTHESIS_MATRIX.md`](experiments/v1/HYPOTHESIS_MATRIX.md).

### External evidence

- **None.** `external/` contains adapters, schemas, a dry-run collector, and an IPS
  implementation. No third-party raw data was collected and no paid call is authorised.
  External infrastructure is not external evidence; a real-smoke fixture is not real-world
  validation; an adapter is not third-party reproduction; an OPE implementation is not a valid
  OPE result.

### Reproduction

- All reproduction in this repository is **internal / automated**. No independent external
  party has reproduced any result. Another script, machine, branch, agent, model, or CI runner
  does not constitute independent reproduction.

### Theory

- `theory/` contains problem formulation, assumptions, a Gaussian toy-model derivation, a
  negative-transfer analysis, and rho-crossover reasoning. `rho*` and the hierarchical regret
  rate are labelled **CONJECTURE / OPEN_PROBLEM**. No theorem about V1 is claimed, and no
  numerical prediction of `rho*` is treated as a V1 prediction.

### Explicitly unsupported claims

- crossover `rho*` existence or location; any phase-transition or monotone-`rho` claim;
- universal or all-`rho` superiority of hierarchical pooling or of Mycelial Graph;
- production readiness or real-world/production superiority;
- real-provider or cloud-provider generalisation;
- causal fault localisation (the execution DAG is not a causal DAG);
- proved sample-complexity or convergence advantage;
- real coding-agent token reduction (V2.1-A runs on two isolated local fixtures, not SWE-bench);
- independent third-party reproduction.

The machine-readable version of this list is
[`docs/claim_evidence_matrix.yaml`](docs/claim_evidence_matrix.yaml), enforced by
`mycelial-graph claim-audit`.

### Scope boundary for V2.1-A

MG-EXP-V2.1-A (autonomous code repair) is a **different research problem** from the V1 question.
It brings its own literature, baselines, failure modes, and evaluation paradigm. Its evidence
must never be used to strengthen a V1 claim, and it is not evidence that hierarchical
non-stationary routing works. It is preserved and frozen; it may become a separate research
line after V1.

## License

Apache-2.0. See [LICENSE](LICENSE).
