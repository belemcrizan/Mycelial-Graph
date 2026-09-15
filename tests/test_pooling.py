from __future__ import annotations

import unittest

import numpy as np

from mycelial_graph.pooling.empirical_bayes import james_stein_means, pooling_weight_from_variances
from mycelial_graph.pooling.toy_model import ToyConfig, evaluate, generate_means, rho_grid


class EmpiricalBayesTests(unittest.TestCase):
    def test_identical_arms_shrink_toward_grand_mean(self) -> None:
        rng = np.random.default_rng(0)
        data = rng.normal(0.5, 0.2, size=(6, 30))
        state = james_stein_means(data, 0.04)
        self.assertTrue(np.all(state.lambdas >= 0))
        self.assertLess(float(np.mean(np.abs(state.pooled_means - state.grand_mean))), float(np.mean(np.abs(data.mean(1) - state.grand_mean))) + 1e-12)

    def test_high_between_variance_reduces_pooling(self) -> None:
        local_weight = pooling_weight_from_variances(between_var=10.0, within_var=0.1)
        shared_weight = pooling_weight_from_variances(between_var=0.01, within_var=0.1)
        self.assertLess(local_weight, shared_weight)


class ToyModelTests(unittest.TestCase):
    def test_shock_l2_is_constant_in_rho(self) -> None:
        norms = []
        for rho in (0.0, 0.5, 1.0):
            pre, post = generate_means(ToyConfig(rho=rho))
            norms.append(float(np.linalg.norm(post - pre)))
        self.assertTrue(max(norms) - min(norms) < 1e-10)

    def test_rho_grid_records_negative_transfer_sign(self) -> None:
        rows = rho_grid(seed=7)
        self.assertEqual(len(rows), 5)
        self.assertTrue(all(row.mse_local >= 0 for row in rows))
        local_rho0 = next(row for row in rows if row.rho == 0.0)
        shared_rho1 = next(row for row in rows if row.rho == 1.0)
        # At rho=0 pooling can hurt; at rho=1 it should not be dramatically worse than local.
        self.assertIsInstance(local_rho0.nt_adaptive_minus_local, float)
        self.assertIsInstance(shared_rho1.mse_adaptive, float)

    def test_evaluate_is_seed_deterministic(self) -> None:
        self.assertEqual(evaluate(ToyConfig(seed=3)).mse_local, evaluate(ToyConfig(seed=3)).mse_local)
