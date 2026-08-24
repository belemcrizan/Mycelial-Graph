"""Immutable execution-graph scenarios."""

from .graph import LayeredDAG
from .scenario import Scenario, generate_scenario, generate_scenario_family

__all__ = ["LayeredDAG", "Scenario", "generate_scenario", "generate_scenario_family"]
