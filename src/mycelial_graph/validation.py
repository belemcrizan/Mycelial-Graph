from __future__ import annotations

import math
import re
from numbers import Real
from pathlib import Path
from typing import Any

from .types import ExperimentConfig


SUPPORTED_METHODS = {
    "edge_only",
    "node_only",
    "hierarchical",
    "structured_sw_ucb",
}


def validate_config_semantics(config: ExperimentConfig) -> list[str]:
    """Finite numbers, protocol fields, and seed-file parseability. No freeze gate."""
    errors: list[str] = []
    def numeric_fields(value: Any, name: str = "config") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                numeric_fields(item, f"{name}.{key}")
        elif isinstance(value, (list, tuple)):
            for item in value:
                numeric_fields(item, name)
        elif isinstance(value, Real) and (isinstance(value, bool) or not math.isfinite(value)):
            errors.append(f"{name} must contain finite numeric values, not booleans.")
    numeric_fields(config.to_dict())
    if errors:
        return errors
    g, h, e, m, a = (
        config.graph,
        config.horizon,
        config.environment,
        config.mycelial,
        config.analysis,
    )
    for name, value in {
        "internal_layers": g.internal_layers, "alternatives_per_layer": g.alternatives_per_layer,
        "pre_shock_steps": h.pre_shock_steps, "post_shock_steps": h.post_shock_steps,
        "recovery_trailing_window": h.recovery_trailing_window,
        "recovery_confirmation_window": h.recovery_confirmation_window,
        "max_generation_attempts": e.max_generation_attempts,
        "bootstrap_samples": a.bootstrap_samples,
        "window_size": config.structured_sw_ucb.window_size,
    }.items():
        if type(value) is not int or value < 1:
            errors.append(f"{name} must be a positive integer.")
    if errors:
        return errors
    if config.protocol_version != "MG-EXP-V1":
        errors.append("V1 configuration requires protocol_version MG-EXP-V1.")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", config.experiment_id):
        errors.append("experiment_id must be a safe path component.")
    if e.optimum_margin <= 0:
        errors.append("optimum_margin must be positive.")
    if config.structured_sw_ucb.ridge <= 0 or config.structured_sw_ucb.uncertainty_bonus < 0:
        errors.append("UCB ridge must be positive and uncertainty_bonus non-negative.")
    if m.minimum_conductance <= 0:
        errors.append("minimum_conductance must be positive.")
    for name in ("learning_rate", "node_learning_rate", "interaction_learning_rate", "exploration_reinforcement", "shrinkage"):
        if getattr(m, name) < 0:
            errors.append(f"mycelial.{name} must be non-negative.")
    if not 0 <= m.temporal_decay <= 1:
        errors.append("temporal_decay must be in [0, 1].")
    if not math.isclose(a.confidence_level, 1 - a.superiority_alpha, abs_tol=1e-12):
        errors.append("confidence_level must equal 1 - superiority_alpha for the one-sided gate.")
    if g.internal_layers < 2:
        errors.append("graph.internal_layers must be at least 2.")
    if config.run_kind not in {"development", "pilot", "confirmatory"}:
        errors.append("run_kind must be development, pilot, or confirmatory.")
    if g.alternatives_per_layer < 2:
        errors.append("graph.alternatives_per_layer must be at least 2.")
    if h.pre_shock_steps < 1 or h.post_shock_steps < 1:
        errors.append("Both horizons must be positive.")
    if h.recovery_trailing_window + h.recovery_confirmation_window > h.post_shock_steps:
        errors.append("Recovery windows do not fit inside the post-shock horizon.")
    if not 0 < h.recovery_utility_fraction <= 1:
        errors.append("recovery_utility_fraction must be in (0, 1].")
    if not e.rho_values:
        errors.append("At least one rho value is required.")
    if any(rho < 0 or rho > 1 for rho in e.rho_values):
        errors.append("Every rho value must be in [0, 1].")
    if len(set(e.rho_values)) != len(e.rho_values):
        errors.append("rho_values must not contain duplicates.")
    if len({f"{rho:.2f}" for rho in e.rho_values}) != len(e.rho_values):
        errors.append("rho_values collide in V1's two-decimal scenario identifiers.")
    if a.primary_rho not in e.rho_values:
        errors.append("analysis.primary_rho must be present in environment.rho_values.")
    if e.shock_magnitude <= 0 or e.reward_noise_std < 0:
        errors.append("Shock magnitude must be positive and noise must be non-negative.")
    if not 0 < a.confidence_level < 1 or not 0 < a.superiority_alpha < 1:
        errors.append("Confidence level and alpha must be in (0, 1).")
    if not 0 <= a.engineering_gain_gate < 1:
        errors.append("engineering_gain_gate must be in [0, 1).")
    if not 0 <= a.noninferiority_margin < 1:
        errors.append("noninferiority_margin must be in [0, 1).")
    if not set(config.methods).issubset(SUPPORTED_METHODS):
        errors.append(f"Unsupported methods: {sorted(set(config.methods) - SUPPORTED_METHODS)}")
    if len(set(config.methods)) != len(config.methods):
        errors.append("methods must not contain duplicates.")
    if not {"edge_only", "hierarchical"}.issubset(config.methods):
        errors.append("edge_only and hierarchical are required for the primary contrast.")
    if not (m.minimum_conductance < m.initial_conductance < m.maximum_conductance):
        errors.append("Conductance bounds must contain initial_conductance.")
    if m.temperature <= 0:
        errors.append("mycelial.temperature must be positive.")
    if not 0 <= m.exploration_probability <= 1:
        errors.append("exploration_probability must be in [0, 1].")
    seeds_path = (config.source_path.parent / config.seeds_file).resolve()
    if not seeds_path.exists():
        errors.append(f"Seeds file does not exist: {seeds_path}")
    else:
        try:
            seeds = load_seeds(seeds_path)
            if not seeds:
                errors.append("Seeds file is empty.")
        except ValueError as exc:
            errors.append(str(exc))
    return errors


def validate_config(config: ExperimentConfig) -> list[str]:
    """Semantic configuration plus seed-population isolation.

    This does **not** authorize confirmatory execution. A confirmatory YAML that
    passes ``validate_config`` is scientifically well-formed, not unlocked.
    New confirmatory runs must call ``validate_confirmatory_execution_authorization``.
    Historical reproduction must call ``verify_historical_confirmatory_evidence``.
    """
    from .protocol import validate_phase_seeds

    errors = validate_config_semantics(config)
    if errors:
        return errors
    errors.extend(validate_phase_seeds(config))
    return errors


def load_seeds(path: str | Path) -> list[int]:
    values: list[int] = []
    for line_number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        try:
            value = int(stripped)
        except ValueError as exc:
            raise ValueError(f"Invalid seed on line {line_number}: {stripped!r}") from exc
        if value < 0:
            raise ValueError(f"Seed on line {line_number} must be non-negative.")
        values.append(value)
    if len(values) != len(set(values)):
        raise ValueError(f"Seeds file contains duplicates: {path}")
    return values


def require_valid_config(config: ExperimentConfig) -> None:
    errors = validate_config(config)
    if errors:
        joined = "\n - ".join(errors)
        raise ValueError(f"Invalid experiment configuration:\n - {joined}")


def validate_result_payload(payload: dict[str, Any], config: ExperimentConfig) -> None:
    if set(payload) != {"scientific_payload", "provenance"}:
        raise ValueError("Result payload must contain scientific_payload and provenance only.")
    scientific = payload["scientific_payload"]
    required = {
        "scenario_hash",
        "scenario_id",
        "rho",
        "seed",
        "shock_l2_norm",
        "shock_node",
        "interaction_edge",
        "optimal_pre_path",
        "optimal_post_path",
        "results",
    }
    missing = required - set(scientific)
    if missing:
        raise ValueError(f"Scientific payload is missing fields: {sorted(missing)}")
    if not re.fullmatch(r"[a-f0-9]{64}", scientific["scenario_hash"]):
        raise ValueError("scenario_hash must be a SHA-256 hex digest.")
    if not 0 <= float(scientific["rho"]) <= 1:
        raise ValueError("Result rho must be in [0, 1].")
    results = scientific["results"]
    if len(results) != len(config.methods) or {result["method"] for result in results} != set(config.methods):
        raise ValueError("Paired result does not contain exactly the configured methods.")
    if {result["scenario_id"] for result in results} != {scientific["scenario_id"]}:
        raise ValueError("All methods must share the enclosing scenario_id.")
    from .artifacts import config_digest
    if not math.isclose(scientific["shock_l2_norm"], config.environment.shock_magnitude, rel_tol=0, abs_tol=1e-10):
        raise ValueError("Shock magnitude differs from the frozen configuration.")
    if scientific["optimal_pre_path"] == scientific["optimal_post_path"]:
        raise ValueError("Pre/post optimal paths must differ.")
    for result in results:
        for key, expected in {
            "config_hash": config_digest(config), "protocol_version": config.protocol_version,
            "seed": scientific["seed"], "rho": scientific["rho"],
            "pre_shock_steps": config.horizon.pre_shock_steps,
            "post_shock_steps": config.horizon.post_shock_steps,
            "trial_id": f"{scientific['scenario_id']}-{result['method']}",
        }.items():
            if result[key] != expected:
                raise ValueError(f"Paired result {key} mismatch.")
        if result["method_status"] not in {"completed", "method_failure", "timeout"}:
            raise ValueError("Unknown method_status.")
        for key in ("dynamic_regret", "final_expected_utility", "decision_cpu_seconds"):
            value = result[key]
            if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{key} must be finite and non-negative.")
        if result["final_expected_utility"] > 1:
            raise ValueError("final_expected_utility must not exceed one.")
        recovered = result["recovered"]
        censored = result["censored"]
        if type(recovered) is not bool or type(censored) is not bool:
            raise ValueError("Censoring indicators must be booleans.")
        recovery_time = result["recovery_time"]
        restricted = result["restricted_recovery_time"]
        if type(restricted) is not int or not 1 <= restricted <= config.horizon.post_shock_steps:
            raise ValueError("RRT must be an integer inside the post-shock horizon.")
        if recovery_time is not None and (type(recovery_time) is not int or not 1 <= recovery_time <= config.horizon.post_shock_steps):
            raise ValueError("Recovery time must be null or an integer inside the horizon.")
        if recovered == censored:
            raise ValueError("recovered and censored must be logical opposites.")
        if recovered and recovery_time is None:
            raise ValueError("Recovered trials require recovery_time.")
        if not recovered and recovery_time is not None:
            raise ValueError("Censored trials require null recovery_time.")
        if not recovered and restricted != config.horizon.post_shock_steps:
            raise ValueError("Censored RRT must equal the post-shock horizon.")
        if recovered and restricted != recovery_time:
            raise ValueError("Recovered RRT must equal recovery_time.")
