from __future__ import annotations

import copy
import unittest
from pathlib import Path

from mycelial_graph.config import ConfigError, load_config, validate_config
from mycelial_graph.graph import HardPolicy, LayeredGraph, NoFeasiblePathError


ROOT = Path(__file__).resolve().parents[1]


class ConfigAndGraphTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(ROOT / "configs" / "v0_demo.yaml").copy()

    def test_frozen_config_is_valid(self) -> None:
        validate_config(self.config)

    def test_reward_weights_must_sum_to_one(self) -> None:
        invalid = copy.deepcopy(self.config)
        invalid["reward"]["quality"] = 0.20
        with self.assertRaises(ConfigError):
            validate_config(invalid)

    def test_graph_has_expected_shape_and_path_count(self) -> None:
        graph = LayeredGraph.from_config(self.config["graph"])
        policy = HardPolicy.from_config(self.config["policy"])
        self.assertEqual(graph.path_count, 48)
        self.assertEqual(len(graph.all_paths(policy)), 48)
        self.assertEqual(len(graph.edges), 24)

    def test_hard_policy_filters_before_routing(self) -> None:
        graph = LayeredGraph.from_config(self.config["graph"])
        policy = HardPolicy(frozenset({"model_balanced", "model_premium"}), 0.020)
        incoming = graph.outgoing("retriever_hybrid", policy)
        self.assertEqual([edge.target for edge in incoming], ["model_economy"])

    def test_hard_policy_can_fail_closed(self) -> None:
        graph = LayeredGraph.from_config(self.config["graph"])
        blocked = frozenset(graph.layer_order[0])
        policy = HardPolicy(blocked, 0.020)
        with self.assertRaises(NoFeasiblePathError):
            graph.outgoing("source", policy)


if __name__ == "__main__":
    unittest.main()

