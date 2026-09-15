from __future__ import annotations

from ..environment.scenario import ResourceScenario


def allocation_regret(scenario: ResourceScenario, step: int, edge_ids: tuple[int, ...]) -> float:
    """Evaluation-only gap to the quality oracle path.

    The oracle observes expected path quality from frozen means. It must never
    be passed into a treatment policy's action selection.
    """
    return float(scenario.oracle_quality(step) - scenario.expected_path_quality(edge_ids, step))
