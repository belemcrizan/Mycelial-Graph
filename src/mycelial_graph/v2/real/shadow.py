from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .tasks import RealCodingTask


@dataclass(frozen=True)
class ShadowDecision:
    recommended_policy: str
    recommended_budget_tokens: int
    stop: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def shadow_recommend(task: RealCodingTask, observed_tokens: int, passed: bool) -> ShadowDecision:
    """Observe a baseline trajectory and record what Mycelial would have done.

    This does not intervene. Counterfactual quality of the recommendation is
    UNKNOWN unless a paired execution is later collected.
    """
    if passed and observed_tokens > 120:
        return ShadowDecision("always_low_compute", 80, True, "SATURATION")
    if not passed:
        return ShadowDecision("always_high_compute", 200, False, "QUALITY_INSUFFICIENT")
    return ShadowDecision("v2_mycelial", observed_tokens, True, "QUALITY_SUFFICIENT")
