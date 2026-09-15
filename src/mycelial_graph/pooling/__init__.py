"""MG-EXP-POOLING-001 utilities. Isolated from MG-EXP-V1."""

from .empirical_bayes import james_stein_means
from .toy_model import ToyConfig, evaluate, rho_grid

__all__ = ["james_stein_means", "ToyConfig", "evaluate", "rho_grid"]
