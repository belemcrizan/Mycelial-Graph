from __future__ import annotations

from ..types import ConstraintConfig, UtilityConfig
from .voc import voc_ratio


def marginal_value(expected_quality_gain: float, extra_resource: float) -> float:
    """Ratio-form MVC retained for V2.0-alpha compatibility.

    Prefer `estimate_voc` for V2.1 analysis. Do not use the ratio when the
    extra resource approaches zero.
    """
    return voc_ratio(expected_quality_gain, extra_resource)


def should_spend(
    mvc: float,
    threshold: float,
    predicted_quality_if_skip: float,
    predicted_risk_if_skip: float,
    constraints: ConstraintConfig,
) -> bool:
    if constraints.mandatory_verification:
        return True
    if predicted_quality_if_skip < constraints.minimum_quality:
        return True
    if predicted_risk_if_skip > constraints.max_risk:
        return True
    return mvc > threshold


def stop_reason(
    budget_left: float,
    mvc: float,
    utility: UtilityConfig,
    quality_target_met: bool,
) -> str | None:
    if budget_left <= 0:
        return "budget_exhausted"
    if quality_target_met:
        return "quality_target"
    if mvc <= utility.mvc_threshold:
        return "low_marginal_value"
    return None
