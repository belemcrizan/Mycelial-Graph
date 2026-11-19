"""Off-policy evaluation with explicit support diagnostics. Not a ground-truth oracle."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import numpy as np

from .schemas import SchemaError, validate_logged_bandit


@dataclass(frozen=True)
class OPEReport:
    n: int
    estimator: str
    estimate: float | None
    variance: float | None
    effective_sample_size: float | None
    clipping: float | None
    support_violations: int
    near_zero_propensity: int
    weight_mean: float | None
    weight_max: float | None
    notes: tuple[str, ...]
    snips_estimate: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "estimator": self.estimator,
            "estimate": self.estimate,
            "snips_estimate": self.snips_estimate,
            "variance": self.variance,
            "effective_sample_size": self.effective_sample_size,
            "clipping": self.clipping,
            "support_violations": self.support_violations,
            "near_zero_propensity": self.near_zero_propensity,
            "weight_mean": self.weight_mean,
            "weight_max": self.weight_max,
            "notes": list(self.notes),
        }


def ips_estimate(
    records: list[dict[str, Any]],
    target_propensity: dict[str, float] | None = None,
    *,
    clip: float | None = 20.0,
    near_zero: float = 1e-8,
) -> OPEReport:
    notes: list[str] = []
    if target_propensity is not None:
        for act, prob in target_propensity.items():
            if isinstance(prob, bool) or not math.isfinite(float(prob)) or not (0.0 <= float(prob) <= 1.0):
                raise ValueError(f"target_propensity[{act!r}] must be a finite probability in [0, 1].")
    else:
        notes.append("target_propensity omitted; evaluated logging policy on-policy mean (p_pi = p_mu).")
    weights: list[float] = []
    values: list[float] = []
    support_violations = 0
    near_zero_count = 0
    malformed = 0
    for row in records:
        try:
            validate_logged_bandit(row)
        except SchemaError as exc:
            malformed += 1
            notes.append(f"malformed:{exc}")
            continue
        p_mu = float(row["propensity"])
        action = str(row["action"])
        p_pi = p_mu if target_propensity is None else float(target_propensity.get(action, 0.0))
        if p_mu <= near_zero:
            near_zero_count += 1
            if p_pi > 0.0:
                support_violations += 1
                continue
            weights.append(0.0)
            values.append(0.0)
            continue
        if p_pi <= 0.0:
            # Zero target probability is NOT a positivity violation; w_i = 0 must remain in denominator n.
            weights.append(0.0)
            values.append(0.0)
            continue
        weight = p_pi / p_mu
        if clip is not None:
            weight = min(weight, clip)
        weights.append(weight)
        values.append(weight * float(row["reward"]))
    if malformed:
        notes.append("Malformed records were retained as errors and excluded from the point estimate.")
    if support_violations:
        notes.append("Do not report a reliable counterfactual in unsupported regions.")
    if not values or (support_violations > 0 and all(w == 0.0 for w in weights)):
        return OPEReport(
            n=len(records),
            estimator="ips",
            estimate=None,
            variance=None,
            effective_sample_size=None,
            clipping=clip,
            support_violations=support_violations,
            near_zero_propensity=near_zero_count,
            weight_mean=None,
            weight_max=None,
            notes=tuple(notes or ("no supported records",)),
            snips_estimate=None,
        )
    arr_w = np.array(weights, dtype=float)
    arr_v = np.array(values, dtype=float)
    w_sum = float(arr_w.sum())
    w_sq_sum = float(np.square(arr_w).sum())
    ess = float((w_sum ** 2) / w_sq_sum) if w_sq_sum > 0.0 else 0.0
    snips = float(arr_v.sum() / w_sum) if w_sum > 0.0 else None
    return OPEReport(
        n=len(records),
        estimator="ips",
        estimate=float(arr_v.mean()),
        variance=float(arr_v.var(ddof=1)) if arr_v.size > 1 else 0.0,
        effective_sample_size=ess,
        clipping=clip,
        support_violations=support_violations,
        near_zero_propensity=near_zero_count,
        weight_mean=float(arr_w.mean()),
        weight_max=float(arr_w.max()),
        notes=tuple(notes),
        snips_estimate=snips,
    )
