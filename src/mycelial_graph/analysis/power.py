from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from scipy.stats import norm

from ..runner.checkpoint import atomic_write_json
from ..artifacts import ensure_unsealed, load_validated_trials
from ..types import ExperimentConfig
from .aggregate import _paired_arrays


def estimate_confirmatory_sample_size(
    config: ExperimentConfig,
    output_directory: str | Path,
    target_power: float = 0.80,
) -> Path:
    if config.run_kind != "pilot":
        raise ValueError("Sample-size estimation must use the independent pilot configuration.")
    if not 0 < target_power < 1:
        raise ValueError("target_power must be in (0, 1).")
    output = Path(output_directory).resolve()
    ensure_unsealed(output)
    trials, provenance = load_validated_trials(config, output)
    treatment, control = _paired_arrays(
        trials,
        config.analysis.primary_rho,
        "hierarchical",
        "edge_only",
    )
    differences = treatment - control
    paired_sd = float(np.std(differences, ddof=1))
    control_mean = float(np.mean(control))
    absolute_design_effect = config.analysis.engineering_gain_gate * control_mean
    estimable = math.isfinite(paired_sd) and paired_sd > 0 and absolute_design_effect > 0
    z_alpha = float(norm.ppf(1.0 - config.analysis.superiority_alpha))
    z_power = float(norm.ppf(target_power))
    required = int(
        max(2, math.ceil(((z_alpha + z_power) * paired_sd / absolute_design_effect) ** 2))
    ) if estimable else None
    payload = {
        "status": "planning_estimate" if estimable else "unestimable",
        "confirmatory_ready": False,
        "lock_reason": ("Review bounded/censored sampling and bootstrap-test power before freezing N." if estimable else "Pilot paired variance is zero or non-finite; no defensible N is produced."),
        "pool_exhausted": required is not None and required > 500,
        "provenance": provenance,
        "method": "normal approximation for paired mean difference",
        "pilot_pairs": len(differences),
        "primary_rho": config.analysis.primary_rho,
        "one_sided_alpha": config.analysis.superiority_alpha,
        "target_power": target_power,
        "relative_design_effect": -config.analysis.engineering_gain_gate,
        "control_mean_rrt": control_mean,
        "absolute_design_effect": absolute_design_effect,
        "paired_difference_sd": paired_sd,
        "required_confirmatory_pairs": required,
        "caveat": "Review approximation assumptions and supplement with simulation-based power before locking N.",
    }
    destination = output / "processed" / "sample_size.json"
    atomic_write_json(destination, payload)
    return destination
