"""Minimum solvable model: one shared parent, K child arms, one change point."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .empirical_bayes import james_stein_means, pooling_weight_from_variances


@dataclass(frozen=True)
class ToyConfig:
    k: int = 6
    pre_n: int = 40
    post_n: int = 40
    noise_std: float = 0.2
    shock_magnitude: float = 0.8
    rho: float = 0.5
    seed: int = 0


@dataclass(frozen=True)
class ToyResult:
    rho: float
    mse_local: float
    mse_pooled: float
    mse_adaptive: float
    nt_adaptive_minus_local: float
    pooling_weight: float


def generate_means(config: ToyConfig) -> tuple[np.ndarray, np.ndarray]:
    """Shared + idiosyncratic decomposition with constant L2 shock budget.

    R_e = mu + S + L_e + eps
    After the change point, S = -m sqrt(rho) on all arms and L applies an
    additional disjoint idiosyncratic pattern with L2 mass m sqrt(1-rho).
    """
    mu = np.full(config.k, 0.6)
    shared_dir = np.ones(config.k)
    shared_dir /= np.linalg.norm(shared_dir)
    shared = -config.shock_magnitude * np.sqrt(config.rho) * shared_dir
    direction = np.zeros(config.k)
    direction[0] = 1.0
    direction -= direction.mean()
    norm = float(np.linalg.norm(direction))
    if norm > 0:
        direction /= norm
    idio = -config.shock_magnitude * np.sqrt(1.0 - config.rho) * direction
    post = mu + shared + idio
    return mu, post


def evaluate(config: ToyConfig) -> ToyResult:
    rng = np.random.default_rng(config.seed)
    pre_mean, post_mean = generate_means(config)
    post = rng.normal(post_mean[:, None], config.noise_std, size=(config.k, config.post_n))
    local = post.mean(axis=1)
    pooled = np.full(config.k, float(post.mean()))
    shrink = james_stein_means(post, config.noise_std**2)
    mse_local = float(np.mean((local - post_mean) ** 2))
    mse_pooled = float(np.mean((pooled - post_mean) ** 2))
    mse_adaptive = float(np.mean((shrink.pooled_means - post_mean) ** 2))
    weight = pooling_weight_from_variances(shrink.between_var, max(shrink.within_var, 1e-12))
    return ToyResult(
        rho=config.rho,
        mse_local=mse_local,
        mse_pooled=mse_pooled,
        mse_adaptive=mse_adaptive,
        nt_adaptive_minus_local=mse_adaptive - mse_local,
        pooling_weight=weight,
    )


def rho_grid(seed: int = 0) -> list[ToyResult]:
    rhos = (0.0, 0.25, 0.5, 0.75, 1.0)
    return [evaluate(ToyConfig(rho=rho, seed=seed + i)) for i, rho in enumerate(rhos)]
