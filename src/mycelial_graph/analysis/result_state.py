"""Frozen result-state taxonomy for MG-EXP-V1.

The state is a deterministic function of quantities the protocol already froze: the paired
bootstrap one-sided upper bound, the two-sided interval, the point estimate, the engineering
threshold, the non-inferiority margin, and the integrity counters. It introduces no new
statistic, no new hypothesis, and no new threshold.

Mapping (pre-specified in ``experiments/v1/AMENDMENT_002.md``, before any confirmatory
outcome was observed; see ``experiments/v1/HYPOTHESIS_MATRIX.md``):

``PROTOCOL_INVALID``
    Integrity failure: non-administrative censoring, a method-level failure inside a primary
    or safety contrast, or fewer executed pairs than the frozen sample size.
``SUPPORTED``
    Protocol §8.2 requirements 1-3 all hold.
``CONDITIONAL``
    Statistical superiority holds, but the engineering threshold or the safety gate fails.
``REFUTED``
    Superiority fails and the pre-specified relevant benefit is excluded by the interval.
``INCONCLUSIVE``
    Superiority fails and the interval still contains the pre-specified relevant benefit.
"""

from __future__ import annotations

from typing import Any

RESULT_STATES = (
    "SUPPORTED",
    "CONDITIONAL",
    "INCONCLUSIVE",
    "REFUTED",
    "PROTOCOL_INVALID",
)


def classify_result_state(
    primary: dict[str, Any],
    noninferiority: dict[str, Any] | None,
    integrity: dict[str, Any],
    engineering_gain_gate: float,
    noninferiority_margin: float,
    expected_pairs: int | None,
) -> dict[str, Any]:
    """Classify a V1 analysis into exactly one frozen result state."""
    reasons: list[str] = []

    if integrity["non_administrative_censoring"]:
        reasons.append(
            f"{integrity['non_administrative_censoring']} trial(s) censored without reaching tau"
        )
    if integrity["method_failures_in_frozen_contrasts"]:
        reasons.append(
            f"{integrity['method_failures_in_frozen_contrasts']} method failure(s) inside a frozen contrast"
        )
    if expected_pairs is not None and integrity["primary_pairs"] < expected_pairs:
        reasons.append(
            f"primary contrast has {integrity['primary_pairs']} pairs, frozen sample size is {expected_pairs}"
        )
    if reasons:
        return {
            "state": "PROTOCOL_INVALID",
            "reasons": reasons,
            "safety_gate_state": "NOT_EVALUABLE",
        }

    superiority = primary["one_sided_upper_bound"] < 0.0
    engineering = primary["estimate"] <= -engineering_gain_gate
    relevant_benefit_excluded = primary["confidence_low"] > -engineering_gain_gate

    if noninferiority is None:
        safety_state = "NOT_EVALUABLE"
        safety_ok = False
        reasons.append("no rho=0 contrast is present, so the safety gate cannot be evaluated")
    elif noninferiority["one_sided_upper_bound"] < noninferiority_margin:
        safety_state = "NON_INFERIOR"
        safety_ok = True
    else:
        safety_state = "NEGATIVE_TRANSFER_NOT_EXCLUDED"
        safety_ok = False

    if superiority and engineering and safety_ok:
        state = "SUPPORTED"
        reasons.append("all three frozen promotion requirements hold")
    elif superiority:
        state = "CONDITIONAL"
        if not engineering:
            reasons.append(
                f"point estimate {primary['estimate']:+.4f} does not reach the frozen "
                f"engineering threshold {-engineering_gain_gate:+.2f}"
            )
        if not safety_ok:
            reasons.append(f"safety gate at rho=0 is {safety_state}")
    elif relevant_benefit_excluded:
        state = "REFUTED"
        reasons.append(
            f"one-sided upper bound {primary['one_sided_upper_bound']:+.4f} is not below zero and the "
            f"interval lower bound {primary['confidence_low']:+.4f} excludes the pre-specified "
            f"relevant benefit {-engineering_gain_gate:+.2f}"
        )
    else:
        state = "INCONCLUSIVE"
        reasons.append(
            f"one-sided upper bound {primary['one_sided_upper_bound']:+.4f} is not below zero and the "
            f"interval [{primary['confidence_low']:+.4f}, {primary['confidence_high']:+.4f}] still "
            f"contains the pre-specified relevant benefit {-engineering_gain_gate:+.2f}"
        )

    return {"state": state, "reasons": reasons, "safety_gate_state": safety_state}
