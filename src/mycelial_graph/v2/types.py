from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


REGIMES = (
    "STATIC",
    "DRIFT",
    "PRICE_SHOCK",
    "QUALITY_SHOCK",
    "LATENCY_SHOCK",
    "OUTAGE",
    "MIXED_SHOCK",
    "RESOURCE_SCARCITY",
    "BURST_LOAD",
    "ADVERSARIAL_COST",
    "CORRELATED_PROVIDER_FAILURE",
    "TASK_DIFFICULTY_SHIFT",
)

DIFFICULTIES = ("easy", "medium", "hard", "very_hard", "unknown")


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
    regimes: tuple[str, ...]
    primary_regime: str
    shock_magnitude: float
    quality_noise_std: float
    token_noise_std: float
    latency_noise_std: float
    max_generation_attempts: int


@dataclass(frozen=True)
class ResourceConfig:
    global_budget_tokens: int
    scarce_budget_tokens: int
    router_tokens_per_candidate: int
    state_overhead_tokens: int


@dataclass(frozen=True)
class UtilityConfig:
    lambda_tokens: float
    lambda_cost: float
    lambda_latency: float
    lambda_risk: float
    lambda_failure: float
    lambda_state: float
    mvc_threshold: float
    switching_penalty: float
    switch_cooldown: int


@dataclass(frozen=True)
class ControllerConfig:
    initial_conductance: float
    minimum_conductance: float
    maximum_conductance: float
    learning_rate: float
    temporal_decay: float
    exploration_probability: float
    temperature: float
    transfer_mix: float
    prune_threshold: float
    prune_persistence: int
    min_prune_observations: int
    hysteresis: float
    floor_budget_fraction: float


@dataclass(frozen=True)
class ConstraintConfig:
    minimum_quality: float
    max_risk: float
    mandatory_verification: bool


@dataclass(frozen=True)
class AnalysisConfig:
    bootstrap_samples: int
    confidence_level: float
    quality_noninferiority_margin: float
    engineering_token_gate: float


@dataclass(frozen=True)
class V2ExperimentConfig:
    protocol_version: str
    experiment_id: str
    run_kind: str
    graph: GraphConfig
    horizon: HorizonConfig
    environment: EnvironmentConfig
    resources: ResourceConfig
    utility: UtilityConfig
    controller: ControllerConfig
    constraints: ConstraintConfig
    analysis: AnalysisConfig
    methods: tuple[str, ...]
    seeds_file: str
    source_path: Path = field(compare=False, repr=False)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("source_path", None)
        return payload
