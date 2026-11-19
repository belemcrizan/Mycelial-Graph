from __future__ import annotations

import math
from typing import Any

from mycelial_graph.validation import load_seeds

from .types import REGIMES, V2ExperimentConfig

SUPPORTED_METHODS = {
    "always_high_compute",
    "always_low_compute",
    "fixed_budget",
    "random_router",
    "random_feasible",
    "epsilon_greedy",
    "v1_edge_only",
    "v1_node_only",
    "v1_hierarchical",
    "resource_heuristic",
    "v2_mycelial",
    "v2_constrained",
    "v2_pareto",
    "v2_no_pruning",
    "v2_no_transfer",
    "v2_no_cord",
    "v2_no_cost_awareness",
    "v2_no_branching",
    "v2_no_anastomosis",
    "v2_no_uncertainty",
    "v2_static_topology",
    "v2_no_shock_memory",
    "thompson_sampling",
    "cost_sensitive_bandit",
    "structured_sw_ucb",
    "uncertainty_threshold",
    "adaptive_early_stop",
    "lagrangian_budget",
    "static_cascade",
}


def _is_real_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_finite_num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_v2_config(config: V2ExperimentConfig) -> list[str]:
    errors: list[str] = []
    if config.protocol_version not in {"MG-EXP-V2", "MG-EXP-V2.1", "MG-EXP-V2.2"}:
        errors.append("protocol_version must be MG-EXP-V2, MG-EXP-V2.1, or MG-EXP-V2.2.")
    if config.run_kind not in {"development", "pilot", "validation", "confirmatory"}:
        errors.append("run_kind must be development, pilot, validation, or confirmatory.")
    if not _is_real_int(config.graph.internal_layers) or not (2 <= config.graph.internal_layers <= 6):
        errors.append("internal_layers must be an integer between 2 and 6.")
    if config.protocol_version == "MG-EXP-V2" and config.graph.internal_layers != 3:
        errors.append("MG-EXP-V2 requires internal_layers=3 (retriever/model/verify).")
    if not _is_real_int(config.graph.alternatives_per_layer) or config.graph.alternatives_per_layer < 2:
        errors.append("alternatives_per_layer must be an integer >= 2.")

    h = config.horizon
    if not _is_real_int(h.pre_shock_steps) or not _is_real_int(h.post_shock_steps):
        errors.append("Horizon step counts must be integers.")
    elif h.pre_shock_steps < 1 or h.post_shock_steps < 1:
        errors.append("Both horizons must be positive.")
    if h.recovery_trailing_window < 1 or h.recovery_confirmation_window < 1:
        errors.append("Recovery trailing and confirmation windows must be >= 1.")
    if h.recovery_trailing_window + h.recovery_confirmation_window > h.post_shock_steps:
        errors.append("Recovery windows do not fit inside the post-shock horizon.")
    if not _is_finite_num(h.recovery_utility_fraction) or not (0.0 < h.recovery_utility_fraction <= 1.0):
        errors.append("recovery_utility_fraction must be in (0, 1].")

    env = config.environment
    if not env.regimes:
        errors.append("At least one regime is required.")
    unknown = [regime for regime in env.regimes if regime not in REGIMES]
    if unknown:
        errors.append(f"Unknown regimes: {unknown}")
    if env.primary_regime not in env.regimes:
        errors.append("primary_regime must be listed in environment.regimes.")
    for field_name in ("shock_magnitude", "quality_noise_std", "token_noise_std", "latency_noise_std"):
        val = getattr(env, field_name)
        if not _is_finite_num(val) or float(val) < 0.0:
            errors.append(f"environment.{field_name} must be finite and >= 0.")
    if not _is_real_int(env.max_generation_attempts) or env.max_generation_attempts < 1:
        errors.append("environment.max_generation_attempts must be an integer >= 1.")

    res = config.resources
    if not _is_real_int(res.global_budget_tokens) or res.global_budget_tokens <= 0:
        errors.append("resources.global_budget_tokens must be a positive integer.")
    if not _is_real_int(res.scarce_budget_tokens) or res.scarce_budget_tokens <= 0:
        errors.append("resources.scarce_budget_tokens must be a positive integer.")
    if res.router_tokens_per_candidate < 0 or res.state_overhead_tokens < 0:
        errors.append("router_tokens_per_candidate and state_overhead_tokens must be >= 0.")

    c = config.controller
    for field_name in (
        "initial_conductance",
        "minimum_conductance",
        "maximum_conductance",
        "learning_rate",
        "temporal_decay",
        "exploration_probability",
        "temperature",
        "transfer_mix",
        "prune_threshold",
        "hysteresis",
        "floor_budget_fraction",
    ):
        if not _is_finite_num(getattr(c, field_name)):
            errors.append(f"controller.{field_name} must be finite.")
    if not (0.0 < c.minimum_conductance < c.initial_conductance < c.maximum_conductance):
        errors.append("Conductance bounds must be positive and contain initial_conductance.")
    if c.temperature <= 0.0:
        errors.append("controller.temperature must be > 0.")
    if not (0.0 <= c.exploration_probability <= 1.0):
        errors.append("controller.exploration_probability must be in [0, 1].")
    if not (0.0 <= c.temporal_decay <= 1.0):
        errors.append("controller.temporal_decay must be in [0, 1].")
    if not (0.0 <= c.transfer_mix <= 1.0):
        errors.append("controller.transfer_mix must be in [0, 1].")
    if not (0.0 <= c.floor_budget_fraction < 1.0):
        errors.append("controller.floor_budget_fraction must be in [0, 1).")
    if c.prune_persistence < 1 or c.min_prune_observations < 1:
        errors.append("prune_persistence and min_prune_observations must be >= 1.")

    con = config.constraints
    if not _is_finite_num(con.minimum_quality) or not (0.0 <= con.minimum_quality <= 1.0):
        errors.append("constraints.minimum_quality must be in [0, 1].")
    if not _is_finite_num(con.max_risk) or not (0.0 <= con.max_risk <= 1.0):
        errors.append("constraints.max_risk must be in [0, 1].")

    ana = config.analysis
    if not _is_real_int(ana.bootstrap_samples) or ana.bootstrap_samples < 10:
        errors.append("analysis.bootstrap_samples must be an integer >= 10.")
    if not _is_finite_num(ana.confidence_level) or not (0.50 <= ana.confidence_level < 1.0):
        errors.append("analysis.confidence_level must be in [0.50, 1.0).")
    if not _is_finite_num(ana.quality_noninferiority_margin) or ana.quality_noninferiority_margin < 0.0:
        errors.append("analysis.quality_noninferiority_margin must be >= 0.")
    if not _is_finite_num(ana.engineering_token_gate) or ana.engineering_token_gate < 0.0:
        errors.append("analysis.engineering_token_gate must be >= 0.")

    if not set(config.methods).issubset(SUPPORTED_METHODS):
        errors.append(f"Unsupported methods: {sorted(set(config.methods) - SUPPORTED_METHODS)}")
    if len(set(config.methods)) != len(config.methods):
        errors.append("methods must not contain duplicates.")
    if "always_high_compute" not in config.methods or "v2_mycelial" not in config.methods:
        errors.append("always_high_compute and v2_mycelial are required for the primary contrast.")

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
