from __future__ import annotations

from mycelial_graph.validation import load_seeds

from .types import REGIMES, V2ExperimentConfig

SUPPORTED_METHODS = {
    "always_high_compute",
    "always_low_compute",
    "fixed_budget",
    "random_router",
    "epsilon_greedy",
    "v1_edge_only",
    "v2_mycelial",
    "v2_no_pruning",
    "v2_no_transfer",
    "v2_no_cord",
    "v2_no_cost_awareness",
    "v2_no_branching",
    "v2_no_anastomosis",
    "v2_no_uncertainty",
    "v2_static_topology",
    "v2_no_shock_memory",
}


def validate_v2_config(config: V2ExperimentConfig) -> list[str]:
    errors: list[str] = []
    if config.protocol_version != "MG-EXP-V2":
        errors.append("protocol_version must be MG-EXP-V2.")
    if config.run_kind not in {"development", "pilot", "confirmatory"}:
        errors.append("run_kind must be development, pilot, or confirmatory.")
    if config.graph.internal_layers != 3:
        errors.append("V2.0-alpha requires internal_layers=3 (retriever/model/verify).")
    if config.graph.alternatives_per_layer < 2:
        errors.append("alternatives_per_layer must be at least 2.")
    h = config.horizon
    if h.pre_shock_steps < 1 or h.post_shock_steps < 1:
        errors.append("Both horizons must be positive.")
    if h.recovery_trailing_window + h.recovery_confirmation_window > h.post_shock_steps:
        errors.append("Recovery windows do not fit inside the post-shock horizon.")
    env = config.environment
    if not env.regimes:
        errors.append("At least one regime is required.")
    unknown = [regime for regime in env.regimes if regime not in REGIMES]
    if unknown:
        errors.append(f"Unknown regimes: {unknown}")
    if env.primary_regime not in env.regimes:
        errors.append("primary_regime must be listed in environment.regimes.")
    if not set(config.methods).issubset(SUPPORTED_METHODS):
        errors.append(f"Unsupported methods: {sorted(set(config.methods) - SUPPORTED_METHODS)}")
    if len(set(config.methods)) != len(config.methods):
        errors.append("methods must not contain duplicates.")
    if "always_high_compute" not in config.methods or "v2_mycelial" not in config.methods:
        errors.append("always_high_compute and v2_mycelial are required for the primary contrast.")
    if not (
        config.controller.minimum_conductance
        < config.controller.initial_conductance
        < config.controller.maximum_conductance
    ):
        errors.append("Conductance bounds must contain initial_conductance.")
    seeds_path = (config.source_path.parent / config.seeds_file).resolve()
    if not seeds_path.exists():
        errors.append(f"Seeds file does not exist: {seeds_path}")
    else:
        try:
            if not load_seeds(seeds_path):
                errors.append("Seeds file is empty.")
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def require_valid_v2_config(config: V2ExperimentConfig) -> None:
    errors = validate_v2_config(config)
    if errors:
        joined = "\n - ".join(errors)
        raise ValueError(f"Invalid V2 experiment configuration:\n - {joined}")
