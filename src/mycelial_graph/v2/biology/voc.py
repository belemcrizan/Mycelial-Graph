from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VOCEstimate:
    """Difference and ratio formulations of value of computation.

    Ratio form is diagnostic only. It is undefined/unstable near zero extra
    resource and must not be the sole scientific estimand.
    """

    expected_quality_gain: float
    expected_resource: float
    lambda_resource: float
    difference: float
    ratio: float
    ratio_stable: bool


def voc_difference(
    expected_quality_gain: float,
    expected_resource: float,
    lambda_resource: float,
) -> float:
    return float(expected_quality_gain) - float(lambda_resource) * float(expected_resource)


def voc_ratio(expected_quality_gain: float, expected_resource: float, epsilon: float = 1e-6) -> float:
    return float(expected_quality_gain) / max(float(expected_resource), epsilon)


def estimate_voc(
    expected_quality_gain: float,
    expected_resource: float,
    lambda_resource: float,
    stability_floor: float = 1.0,
) -> VOCEstimate:
    extra = float(expected_resource)
    return VOCEstimate(
        expected_quality_gain=float(expected_quality_gain),
        expected_resource=extra,
        lambda_resource=float(lambda_resource),
        difference=voc_difference(expected_quality_gain, extra, lambda_resource),
        ratio=voc_ratio(expected_quality_gain, extra),
        ratio_stable=extra >= stability_floor,
    )


def should_allocate(
    estimate: VOCEstimate,
    threshold: float,
    *,
    use_difference: bool = True,
) -> bool:
    if use_difference:
        return estimate.difference > threshold
    if not estimate.ratio_stable:
        return False
    return estimate.ratio > threshold
