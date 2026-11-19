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
    if not isinstance(mapping, dict):
        raise ValueError(f"Expected mapping for '{context}'.")
    if key not in mapping:
        raise ValueError(f"Missing required field '{context}.{key}'.")
    return mapping[key]


def load_v2_config(path: str | Path) -> V2ExperimentConfig:
    source = Path(path).resolve()
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("The V2 experiment configuration must be a YAML object.")
    environment_raw = _require(raw, "environment", "config")
    analysis_raw = _require(raw, "analysis", "config")
    if not isinstance(environment_raw, dict) or not isinstance(analysis_raw, dict):
        raise ValueError("environment and analysis sections must be YAML mappings.")
    regimes_raw = _require(environment_raw, "regimes", "environment")
    methods_raw = _require(raw, "methods", "config")
    if not isinstance(regimes_raw, list) or not isinstance(methods_raw, list):
        raise ValueError("environment.regimes and methods must be YAML lists.")
    return V2ExperimentConfig(
        protocol_version=str(_require(raw, "protocol_version", "config")),
        experiment_id=str(_require(raw, "experiment_id", "config")),
        run_kind=str(_require(raw, "run_kind", "config")),
        graph=GraphConfig(**_require(raw, "graph", "config")),
        horizon=HorizonConfig(**_require(raw, "horizon", "config")),
        environment=EnvironmentConfig(
            regimes=tuple(regimes_raw),
            primary_regime=str(_require(environment_raw, "primary_regime", "environment")),
            shock_magnitude=float(_require(environment_raw, "shock_magnitude", "environment")),
            quality_noise_std=float(_require(environment_raw, "quality_noise_std", "environment")),
            token_noise_std=float(_require(environment_raw, "token_noise_std", "environment")),
            latency_noise_std=float(_require(environment_raw, "latency_noise_std", "environment")),
            max_generation_attempts=int(_require(environment_raw, "max_generation_attempts", "environment")),
            iso_model=bool(environment_raw.get("iso_model", False)),
        ),
        resources=ResourceConfig(**_require(raw, "resources", "config")),
        utility=UtilityConfig(**_require(raw, "utility", "config")),
        controller=ControllerConfig(**_require(raw, "controller", "config")),
        constraints=ConstraintConfig(**_require(raw, "constraints", "config")),
        analysis=AnalysisConfig(
            bootstrap_samples=int(_require(analysis_raw, "bootstrap_samples", "analysis")),
            confidence_level=float(_require(analysis_raw, "confidence_level", "analysis")),
            quality_noninferiority_margin=float(_require(analysis_raw, "quality_noninferiority_margin", "analysis")),
            engineering_token_gate=float(_require(analysis_raw, "engineering_token_gate", "analysis")),
            mmrr=float(analysis_raw.get("mmrr", 0.05)),
        ),
        methods=tuple(methods_raw),
        seeds_file=str(_require(raw, "seeds_file", "config")),
        source_path=source,
    )
