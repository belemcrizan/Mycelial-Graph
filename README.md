# Mycelial Graph V1 Research Edition

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

## Quick start - Windows PowerShell

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& .\.venv\Scripts\Activate.ps1
python -m pip install -e .
mycelial-graph validate --config experiments/v1/config.development.yaml
mycelial-graph demo
```

If you prefer not to activate the environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\mycelial-graph.exe demo
```

The demo writes raw paired trials, processed statistics, figures, a manifest, and `REPORT.md` under `outputs/demo/`. It is explicitly development-only evidence.

## Scientific workflow

```text
development seeds -> implementation checks
pilot seeds       -> variance and sample-size calculation
addendum          -> fixes N and selects first N seeds mechanically
confirmatory run  -> frozen execution with no tuning
report            -> pass, conditional result, inconclusive, or refuted
```

The confirmatory configuration deliberately points to a missing `seeds.confirmatory.txt`. This is an execution lock, not a packaging error. Follow [`experiments/v1/SAMPLE_SIZE_ADDENDUM.md`](experiments/v1/SAMPLE_SIZE_ADDENDUM.md) after the pilot.

## V2.0-alpha (additive)

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
```

## Read next

- [Getting Started](docs/GETTING_STARTED.md) - step-by-step instructions for non-specialists.
- [Architecture](docs/ARCHITECTURE.md) - system boundaries and data flow.
- [Frozen Experiment Protocol](experiments/v1/EXPERIMENT_PROTOCOL_V1.md) - hypotheses and immutable rules.
- [Analysis Plan](experiments/v1/ANALYSIS_PLAN.md) - estimands, bootstrap, gates, and interpretation.
- [Roadmap](docs/ROADMAP.md) - evidence-gated growth toward real providers and cloud tests.
- [V2 implementation plan](docs/V2_IMPLEMENTATION_PLAN.md) - additive resource-allocation layer.
- [Sustainability](docs/SUSTAINABILITY.md) - technical, financial, scientific, and environmental sustainability.
- [Migration from V0](docs/MIGRATION_FROM_V0.md) - how to integrate the three prototypes without a blind code merge.

## Honest status

- The development demonstrator is executable.
- The pilot and confirmatory machinery are present.
- No confirmatory run is included.
- No cloud-provider superiority, convergence theorem, or production-readiness claim is made.
- A positive development result is not evidence for publication.
- V2.0-alpha is a simulated resource-allocation layer with its own locked confirmatory protocol.
- MG-EXP-V2.1 (Evidence Bridge) is additive instrumentation: iso-model, VOC bench, strong baselines, local executable smoke. It is not confirmatory and is not SWE-bench.
- MG-EXP-V2.1-A replaces known-fix injection with a local autonomous repair loop on isolated fixtures. It still does not support a real coding-agent token-reduction claim.

## License

Apache-2.0. See [LICENSE](LICENSE).
