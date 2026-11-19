"""Counterfactual Value of Computation (VOC) for Mycelial-Graph V2.1.

Separates difference-form VOC from ratio-form MVC. Ratio form is unstable when
ΔR → 0; difference form is the canonical allocation criterion.
"""

from __future__ import annotations

from dataclasses import dataclass

EPSILON_RESOURCE = 1e-6
TOKEN_SCALE = 1000.0


@dataclass(frozen=True)
class VOCEstimate:
    delta_quality: float
    delta_resource: float
    lambda_resource: float
    difference: float
    ratio: float
    ratio_stable: bool


def voc_difference(expected_quality_gain: float, extra_resource: float, lambda_resource: float) -> float:
    """Difference-form VOC: E[ΔQ] - λ E[ΔR] on normalized resource units."""
    return float(expected_quality_gain - lambda_resource * max(0.0, extra_resource))


def voc_ratio(expected_quality_gain: float, extra_resource: float) -> float:
    """Ratio-form MVC retained as a diagnostic. Guarded near zero resource."""
    denom = max(float(extra_resource), EPSILON_RESOURCE)
    return float(expected_quality_gain / denom)


def estimate_voc(
    expected_quality_gain: float,
    extra_resource: float,
    lambda_resource: float,
    *,
    min_stable_resource: float = 1e-3,
) -> VOCEstimate:
    stable = float(extra_resource) >= min_stable_resource
    return VOCEstimate(
        delta_quality=float(expected_quality_gain),
        delta_resource=float(extra_resource),
        lambda_resource=float(lambda_resource),
        difference=voc_difference(expected_quality_gain, extra_resource, lambda_resource),
        ratio=voc_ratio(expected_quality_gain, extra_resource),
        ratio_stable=stable,
    )


def estimate_token_voc(
    expected_quality_gain: float,
    extra_tokens: float,
    lambda_tokens: float,
) -> VOCEstimate:
    """Estimate VOC with raw token delta normalized by ``TOKEN_SCALE`` (per 1k tokens)."""
    norm_tokens = max(0.0, float(extra_tokens)) / TOKEN_SCALE
    return estimate_voc(
        expected_quality_gain,
        norm_tokens,
        lambda_tokens,
        min_stable_resource=1.0 / TOKEN_SCALE,
    )


def should_allocate(
    voc: VOCEstimate,
    threshold: float,
    *,
    use_difference: bool = True,
) -> bool:
    if use_difference:
        return voc.difference > threshold
    if not voc.ratio_stable:
        return voc.difference > 0.0
    return voc.ratio > threshold
