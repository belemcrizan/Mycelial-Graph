from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class GraphConfig:
    internal_layers: int
    alternatives_per_layer: int


@dataclass(frozen=True)
class HorizonConfig:
    pre_shock_steps: int
    post_shock_steps: int
    recovery_trailing_window: int
    recovery_confirmation_window: int
    recovery_utility_fraction: float

    @property
    def total_steps(self) -> int:
        return self.pre_shock_steps + self.post_shock_steps


@dataclass(frozen=True)
class EnvironmentConfig:
    rho_values: tuple[float, ...]
    shock_magnitude: float
    reward_noise_std: float
    optimum_margin: float
    max_generation_attempts: int


@dataclass(frozen=True)
class MycelialConfig:
    initial_conductance: float
    minimum_conductance: float
    maximum_conductance: float
    learning_rate: float
    node_learning_rate: float
    interaction_learning_rate: float
    temporal_decay: float
    exploration_probability: float
    exploration_reinforcement: float
    temperature: float
    shrinkage: float


@dataclass(frozen=True)
class UCBConfig:
    window_size: int
    ridge: float
    uncertainty_bonus: float


@dataclass(frozen=True)
class AnalysisConfig:
    bootstrap_samples: int
    confidence_level: float
    superiority_alpha: float
    engineering_gain_gate: float
    noninferiority_margin: float
    primary_rho: float


@dataclass(frozen=True)
class ExperimentConfig:
    protocol_version: str
    experiment_id: str
    run_kind: str
    graph: GraphConfig
    horizon: HorizonConfig
    environment: EnvironmentConfig
    mycelial: MycelialConfig
    structured_sw_ucb: UCBConfig
    analysis: AnalysisConfig
    methods: tuple[str, ...]
    seeds_file: str
    source_path: Path = field(compare=False, repr=False)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("source_path", None)
        return payload


@dataclass(frozen=True)
class DecisionRecord:
    step: int
    path: tuple[int, ...]
    edge_ids: tuple[int, ...]
    expected_utility: float
    realized_utility: float
    oracle_expected_utility: float
    exploratory_edges: int
    selected_edge_scores: tuple[float, ...]


@dataclass(frozen=True)
class TrialResult:
    trial_id: str
    scenario_id: str
    protocol_version: str
    config_hash: str
    code_commit: str
    rho: float
    seed: int
    method: str
    method_status: str
    recovery_time: int | None
    restricted_recovery_time: int
    recovered: bool
    censored: bool
    dynamic_regret: float
    final_expected_utility: float
    pre_shock_steps: int
    post_shock_steps: int
    decision_cpu_seconds: float
    trace_ref: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _require(mapping: dict[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise ValueError(f"Missing required field '{context}.{key}'.")
    return mapping[key]


def load_config(path: str | Path) -> ExperimentConfig:
    source = Path(path).resolve()
    raw = yaml.safe_load(source.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("The experiment configuration must be a YAML object.")

    graph = GraphConfig(**_require(raw, "graph", "config"))
    horizon = HorizonConfig(**_require(raw, "horizon", "config"))
    environment_raw = _require(raw, "environment", "config")
    environment = EnvironmentConfig(
        rho_values=tuple(environment_raw["rho_values"]),
        shock_magnitude=environment_raw["shock_magnitude"],
        reward_noise_std=environment_raw["reward_noise_std"],
        optimum_margin=environment_raw["optimum_margin"],
        max_generation_attempts=environment_raw["max_generation_attempts"],
    )
    return ExperimentConfig(
        protocol_version=_require(raw, "protocol_version", "config"),
        experiment_id=_require(raw, "experiment_id", "config"),
        run_kind=_require(raw, "run_kind", "config"),
        graph=graph,
        horizon=horizon,
        environment=environment,
        mycelial=MycelialConfig(**_require(raw, "mycelial", "config")),
        structured_sw_ucb=UCBConfig(**_require(raw, "structured_sw_ucb", "config")),
        analysis=AnalysisConfig(**_require(raw, "analysis", "config")),
        methods=tuple(_require(raw, "methods", "config")),
        seeds_file=_require(raw, "seeds_file", "config"),
        source_path=source,
    )
