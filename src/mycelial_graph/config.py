"""Configuration loading and frozen V0 schema validation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ConfigError(ValueError):
    """Raised when a configuration violates the frozen V0 contract."""


@dataclass(frozen=True)
class FrozenConfig:
    data: dict[str, Any]
    source: Path

    def copy(self) -> dict[str, Any]:
        return deepcopy(self.data)


REQUIRED_TOP_LEVEL = {
    "project",
    "experiment",
    "mycelial",
    "baselines",
    "reward",
    "policy",
    "shock",
    "graph",
}


def _bounded(name: str, value: float, low: float, high: float, *, inclusive_low: bool = True) -> None:
    valid_low = value >= low if inclusive_low else value > low
    if not valid_low or value > high:
        bracket = "[" if inclusive_low else "("
        raise ConfigError(f"{name} must be in {bracket}{low}, {high}], got {value}")


def validate_config(data: dict[str, Any]) -> None:
    missing = REQUIRED_TOP_LEVEL - set(data)
    if missing:
        raise ConfigError(f"Missing top-level sections: {sorted(missing)}")

    exp = data["experiment"]
    if int(exp["steps"]) <= int(exp["shock_step"]) + int(exp["recovery_window"]):
        raise ConfigError("steps must leave a post-shock recovery horizon")
    if not exp.get("seeds") or len(set(exp["seeds"])) != len(exp["seeds"]):
        raise ConfigError("experiment.seeds must be a non-empty unique list")
    if not exp.get("development_seeds") or len(set(exp["development_seeds"])) != len(exp["development_seeds"]):
        raise ConfigError("experiment.development_seeds must be a non-empty unique list")
    if set(exp["development_seeds"]) & set(exp["seeds"]):
        raise ConfigError("development and demonstration seeds must be disjoint")
    _bounded("quality_threshold", float(exp["quality_threshold"]), 0.0, 1.0)
    _bounded("recovery_tolerance", float(exp["recovery_tolerance"]), 0.0, 1.0)
    _bounded("minimum_oracle_margin", float(exp["minimum_oracle_margin"]), 0.0, 1.0, inclusive_low=False)

    mg = data["mycelial"]
    _bounded("temporal_decay", float(mg["temporal_decay"]), 0.0, 1.0, inclusive_low=False)
    _bounded("explicit_exploration", float(mg["explicit_exploration"]), 0.0, 1.0)
    if float(mg["plasticity"]) <= 0 or float(mg["temperature"]) <= 0:
        raise ConfigError("plasticity and temperature must be positive")
    if not 0 < float(mg["min_conductance"]) <= float(mg["initial_conductance"]) <= float(mg["max_conductance"]):
        raise ConfigError("conductance bounds must satisfy 0 < min <= initial <= max")

    weights = data["reward"]
    if set(weights) != {"quality", "latency", "cost", "failure", "load"}:
        raise ConfigError("reward must contain exactly quality, latency, cost, failure, and load")
    if any(float(value) < 0 for value in weights.values()):
        raise ConfigError("reward weights cannot be negative")
    if abs(sum(float(value) for value in weights.values()) - 1.0) > 1e-9:
        raise ConfigError("reward weights must sum to 1.0")

    layers = data["graph"].get("layers", [])
    if not layers:
        raise ConfigError("graph.layers cannot be empty")
    component_ids: list[str] = []
    for layer in layers:
        if not layer.get("name") or not layer.get("components"):
            raise ConfigError("every layer needs a name and at least one component")
        for component in layer["components"]:
            component_ids.append(component["id"])
            for key in ("quality", "reliability", "load"):
                _bounded(f"{component['id']}.{key}", float(component[key]), 0.0, 1.0)
            if float(component["latency_ms"]) < 0 or float(component["cost_usd"]) < 0:
                raise ConfigError(f"{component['id']} has negative latency or cost")
    if len(component_ids) != len(set(component_ids)):
        raise ConfigError("component ids must be globally unique")
    if data["shock"]["component"] not in component_ids:
        raise ConfigError("shock.component must identify a configured component")
    unknown_blocked = set(data["policy"].get("blocked_components", [])) - set(component_ids)
    if unknown_blocked:
        raise ConfigError(f"policy blocks unknown components: {sorted(unknown_blocked)}")


def load_config(path: str | Path) -> FrozenConfig:
    source = Path(path).resolve()
    with source.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ConfigError("configuration root must be a mapping")
    validate_config(data)
    return FrozenConfig(data=deepcopy(data), source=source)
