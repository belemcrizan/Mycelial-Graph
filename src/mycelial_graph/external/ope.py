"""Off-policy evaluation with explicit support diagnostics. Not a ground-truth oracle."""

from __future__ import annotations

from dataclasses import dataclass
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

    def to_dict(self) -> dict[str, Any]:
        return {
            "n": self.n,
            "estimator": self.estimator,
            "estimate": self.estimate,
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
        if p_mu <= near_zero:
            near_zero_count += 1
            support_violations += 1
            continue
        action = str(row["action"])
        p_pi = 1.0 if target_propensity is None else float(target_propensity.get(action, 0.0))
        if p_pi <= near_zero:
            support_violations += 1
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
    if not values:
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
        )
    arr_w = np.array(weights, dtype=float)
    arr_v = np.array(values, dtype=float)
    ess = float((arr_w.sum() ** 2) / np.square(arr_w).sum()) if arr_w.size else 0.0
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
    )
