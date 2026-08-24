from __future__ import annotations

import random
import unittest
from pathlib import Path

from mycelial_graph.config import load_config
from mycelial_graph.graph import HardPolicy, LayeredGraph
from mycelial_graph.routing import MycelialRouter
from mycelial_graph.trial import FrozenTrial


ROOT = Path(__file__).resolve().parents[1]


class RouterInvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(ROOT / "configs" / "v0_demo.yaml").copy()
        self.graph = LayeredGraph.from_config(self.config["graph"])
        self.policy = HardPolicy.from_config(self.config["policy"])
        self.trial = FrozenTrial.generate(self.graph, self.config, 101)

    def test_feedback_updates_only_traversed_edges(self) -> None:
        router = MycelialRouter(self.graph, self.policy, self.config)
        decision = router.select(0, random.Random(7))
        before_feedback = dict(router.conductance)
        observations = self.trial.observations_for(0, decision.edge_ids)
        router.observe(0, decision, observations)
        for edge_id in set(self.graph.edges) - set(decision.edge_ids):
            self.assertEqual(router.conductance[edge_id], before_feedback[edge_id])
        self.assertTrue(
            any(router.conductance[edge_id] != before_feedback[edge_id] for edge_id in decision.edge_ids)
        )

    def test_conductance_stays_bounded(self) -> None:
        router = MycelialRouter(self.graph, self.policy, self.config)
        rng = random.Random(9)
        for step in range(50):
            decision = router.select(step, rng)
            router.observe(step, decision, self.trial.observations_for(step, decision.edge_ids))
        self.assertTrue(all(router.minimum <= value <= router.maximum for value in router.conductance.values()))

    def test_single_edge_fallback_is_explicit(self) -> None:
        router = MycelialRouter(self.graph, self.policy, self.config)
        decision = router.select(0, random.Random(3))
        self.assertEqual(decision.choices[-1].mode, "single-edge-fallback")

    def test_timestamps_are_separate(self) -> None:
        router = MycelialRouter(self.graph, self.policy, self.config)
        decision = router.select(3, random.Random(4))
        edge_id = decision.edge_ids[0]
        self.assertEqual(router.last_use[edge_id], 3)
        self.assertIsNone(router.last_feedback[edge_id])
        router.observe(3, decision, self.trial.observations_for(3, decision.edge_ids))
        self.assertEqual(router.last_feedback[edge_id], 3)


if __name__ == "__main__":
    unittest.main()

