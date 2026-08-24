from __future__ import annotations

from pathlib import Path
from typing import Any

from .types import ExperimentConfig


SUPPORTED_METHODS = {
    "edge_only",
    "node_only",
    "hierarchical",
    "structured_sw_ucb",
}


def validate_config(config: ExperimentConfig) -> list[str]:
    errors: list[str] = []
    g, h, e, m, a = (
        config.graph,
        config.horizon,
        config.environment,
        config.mycelial,
        config.analysis,
    )
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
    if len(scientific["scenario_hash"]) != 64:
        raise ValueError("scenario_hash must be a SHA-256 hex digest.")
    if not 0 <= float(scientific["rho"]) <= 1:
        raise ValueError("Result rho must be in [0, 1].")
    results = scientific["results"]
    if {result["method"] for result in results} != set(config.methods):
        raise ValueError("Paired result does not contain exactly the configured methods.")
    if {result["scenario_id"] for result in results} != {scientific["scenario_id"]}:
        raise ValueError("All methods must share the enclosing scenario_id.")
    for result in results:
        recovered = bool(result["recovered"])
        censored = bool(result["censored"])
        recovery_time = result["recovery_time"]
        restricted = int(result["restricted_recovery_time"])
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
