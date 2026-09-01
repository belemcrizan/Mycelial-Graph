from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .types import (
    AnalysisConfig,
    ConstraintConfig,
    ControllerConfig,
    EnvironmentConfig,
    GraphConfig,
    HorizonConfig,
    ResourceConfig,
    UtilityConfig,
    V2ExperimentConfig,
)


def _require(mapping: dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ValueError(f"Missing required field '{context}.{key}'.")
    return mapping[key]


def load_v2_config(path: str | Path) -> V2ExperimentConfig:
    source = Path(path).resolve()
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("The V2 experiment configuration must be a YAML object.")
    environment_raw = _require(raw, "environment", "config")
    return V2ExperimentConfig(
        protocol_version=_require(raw, "protocol_version", "config"),
        experiment_id=_require(raw, "experiment_id", "config"),
        run_kind=_require(raw, "run_kind", "config"),
        graph=GraphConfig(**_require(raw, "graph", "config")),
        horizon=HorizonConfig(**_require(raw, "horizon", "config")),
        environment=EnvironmentConfig(
            regimes=tuple(environment_raw["regimes"]),
            primary_regime=environment_raw["primary_regime"],
            shock_magnitude=environment_raw["shock_magnitude"],
            quality_noise_std=environment_raw["quality_noise_std"],
            token_noise_std=environment_raw["token_noise_std"],
            latency_noise_std=environment_raw["latency_noise_std"],
            max_generation_attempts=environment_raw["max_generation_attempts"],
            iso_model=bool(environment_raw.get("iso_model", False)),
        ),
        resources=ResourceConfig(**_require(raw, "resources", "config")),
        utility=UtilityConfig(**_require(raw, "utility", "config")),
        controller=ControllerConfig(**_require(raw, "controller", "config")),
        constraints=ConstraintConfig(**_require(raw, "constraints", "config")),
        analysis=AnalysisConfig(
            bootstrap_samples=raw["analysis"]["bootstrap_samples"],
            confidence_level=raw["analysis"]["confidence_level"],
            quality_noninferiority_margin=raw["analysis"]["quality_noninferiority_margin"],
            engineering_token_gate=raw["analysis"]["engineering_token_gate"],
            mmrr=float(raw["analysis"].get("mmrr", 0.05)),
        ),
        methods=tuple(_require(raw, "methods", "config")),
        seeds_file=_require(raw, "seeds_file", "config"),
        source_path=source,
    )
