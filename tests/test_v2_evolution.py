from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from mycelial_graph.agents.base import stable_softmax
from mycelial_graph.cli import main
from mycelial_graph.environment.graph import Edge, LayeredDAG
from mycelial_graph.v2 import (
    AdapterRequest,
    ComputationalGraph,
    DeterministicMockProvider,
    HealthSignals,
    ProviderAdapter,
)
from mycelial_graph.v2.analysis import analyze_v2_results
from mycelial_graph.v2.audit import audit_resource_traces
from mycelial_graph.v2.biology import (
    assert_budget_conserved,
    translocate,
    update_conductance,
    update_prune_evidence,
)
from mycelial_graph.v2.config import load_v2_config
from mycelial_graph.v2.environment import generate_resource_scenario
from mycelial_graph.v2.environment.roles import alternative_index, edge_role
from mycelial_graph.v2.evaluation import budget_response_curve
from mycelial_graph.v2.evaluation.waste import decompose_waste, waste_identity_ok
from mycelial_graph.v2.ledger import ResourceObservation, TokenUsage
from mycelial_graph.v2.policies import create_resource_agent
from mycelial_graph.v2.real.hypothesize import _empty_guard_source, _shifted_return_source
from mycelial_graph.v2.reporting import generate_v2_report
from mycelial_graph.v2.resources import BudgetReservation, ReservationError
from mycelial_graph.v2.runner import run_v2_experiment
from mycelial_graph.v2.seeding import create_rng
from mycelial_graph.v2.viz import render_topology_svg, render_trace_dashboard

ROOT = Path(__file__).resolve().parents[1]
V2_DEV = ROOT / "experiments" / "v2" / "config.development.yaml"


class ComputationalGraphTests(unittest.TestCase):
    def test_layered_and_heterogeneous_graphs_preserve_invariants(self) -> None:
        for layers, width in ((2, 2), (3, 3), (4, 4), (5, 3)):
            dag = LayeredDAG.complete_layered(layers, width)
            cg = ComputationalGraph.from_layered_dag(dag)
            self.assertTrue(cg.has_feasible_path())
            self.assertEqual(cg.source, dag.source)
            self.assertEqual(cg.sink, dag.sink)

        het = ComputationalGraph.heterogeneous_pipeline((2, 4, 3, 2))
        self.assertTrue(het.has_feasible_path())
        self.assertEqual(het.node_count, 1 + 2 + 4 + 3 + 2 + 1)

    def test_cycle_is_rejected(self) -> None:
        dag = LayeredDAG(
            layers=((0,), (1, 2), (3,)),
            edges=(
                Edge(0, 0, 1),
                Edge(1, 1, 2),
                Edge(2, 2, 1),
                Edge(3, 2, 3),
            ),
            outgoing={0: (0,), 1: (1,), 2: (2, 3), 3: ()},
            edge_lookup={(0, 1): 0, (1, 2): 1, (2, 1): 2, (2, 3): 3},
        )
        with self.assertRaises(ValueError):
            ComputationalGraph.from_layered_dag(dag)


class PropertyBasedBiologyTests(unittest.TestCase):
    @settings(max_examples=60, deadline=None)
    @given(
        weights=st.lists(
            st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
            min_size=2,
            max_size=20,
        ),
        cap=st.floats(min_value=20.0, max_value=5000.0, allow_nan=False, allow_infinity=False),
    )
    def test_translocation_conserves_budget_and_floor(self, weights: list[float], cap: float) -> None:
        config = load_v2_config(V2_DEV)
        n = len(weights)
        initial = np.full(n, cap / n, dtype=float)
        updated = translocate(initial, np.array(weights, dtype=float), cap, config.controller, True)
        assert_budget_conserved(updated, cap, atol=1e-5)
        floor = (cap / n) * config.controller.minimum_conductance
        self.assertTrue(np.all(updated >= floor - 1e-7))

    @settings(max_examples=50, deadline=None)
    @given(
        scores=st.lists(
            st.floats(min_value=-2.0, max_value=5.0, allow_nan=False, allow_infinity=False),
            min_size=24,
            max_size=24,
        )
    )
    def test_pruning_never_disconnects_source_to_sink(self, scores: list[float]) -> None:
        config = load_v2_config(V2_DEV)
        dag = LayeredDAG.complete_layered(3, 3)
        cg = ComputationalGraph.from_layered_dag(dag)
        evidence = np.zeros(len(dag.edges), dtype=int)
        counts = np.full(len(dag.edges), 25, dtype=int)
        arr_scores = np.array(scores, dtype=float)
        all_edges = tuple(range(len(dag.edges)))
        for _ in range(config.controller.prune_persistence + 3):
            evidence, pruned = update_prune_evidence(
                evidence,
                counts,
                arr_scores,
                config.controller,
                True,
                observed_edges=all_edges,
                outgoing_map=dag.outgoing,
            )
        self.assertTrue(cg.has_feasible_path(~pruned))

    @settings(max_examples=50, deadline=None)
    @given(
        logits=st.lists(
            st.floats(min_value=-500.0, max_value=500.0, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=12,
        ),
        temp=st.floats(min_value=0.02, max_value=5.0, allow_nan=False, allow_infinity=False),
    )
    def test_stable_softmax_normalizes(self, logits: list[float], temp: float) -> None:
        probs = stable_softmax(np.array(logits, dtype=float), temp)
        self.assertAlmostEqual(float(probs.sum()), 1.0, places=9)
        self.assertTrue(np.all(probs >= 0.0))

    def test_conductance_decays_toward_prior_and_respects_bounds(self) -> None:
        config = load_v2_config(V2_DEV)
        c = config.controller
        high = np.full(4, c.maximum_conductance, dtype=float)
        low = np.full(4, c.minimum_conductance, dtype=float)
        for _ in range(200):
            high = update_conductance(high, (), np.array([]), np.zeros(4), np.zeros(4), c, True)
            low = update_conductance(low, (), np.array([]), np.zeros(4), np.zeros(4), c, True)
        self.assertLess(float(high[0]), c.maximum_conductance)
        self.assertGreater(float(low[0]), c.minimum_conductance)
        self.assertAlmostEqual(float(high[0]), c.initial_conductance, delta=0.05)
        self.assertAlmostEqual(float(low[0]), c.initial_conductance, delta=0.05)


class GuardrailAndSafetyTests(unittest.TestCase):
    def test_mandatory_verification_blocks_skip_across_all_model_nodes(self) -> None:
        base = load_v2_config(V2_DEV)
        cfg = replace(
            base,
            constraints=replace(base.constraints, mandatory_verification=True),
            controller=replace(base.controller, exploration_probability=1.0),
        )
        scenario = generate_resource_scenario(cfg, 7103, "STATIC")
        agent = create_resource_agent("v2_mycelial", cfg, scenario.graph, create_rng(7103, "test:mv"))
        for step in range(40):
            decision = agent.choose(scenario.graph, step, float(scenario.budget_pre))
            ver_edges = [e for e in decision.edge_ids if edge_role(scenario.graph, e) == "verification"]
            self.assertEqual(len(ver_edges), 1)
            target_alt = alternative_index(scenario.graph, scenario.graph.edges[ver_edges[0]].target)
            self.assertNotEqual(target_alt, 0, "Skip verification node (tier 0) must never be selected.")

    def test_budget_reservation_rejects_invalid_inputs_and_shapes_curve(self) -> None:
        wallet = BudgetReservation(cap=100.0)
        for bad in (float("nan"), float("inf"), -1.0, True):
            with self.assertRaises((ReservationError, TypeError, ValueError)):
                wallet.reserve(bad)  # type: ignore[arg-type]

        cfg = load_v2_config(V2_DEV)
        with tempfile.TemporaryDirectory() as tmp:
            curve = budget_response_curve(
                cfg,
                "v2_mycelial",
                (7103,),
                budgets=(2000, 32000),
                output_directory=Path(tmp),
                project_root=ROOT,
            )
            points = curve["points"]
            self.assertLess(points[0]["tokens_mean"], points[1]["tokens_mean"])


class BioinspiredMechanismTests(unittest.TestCase):
    def test_anastomosis_gate_shares_correlated_shock_and_blocks_discordant_shock(self) -> None:
        dag = LayeredDAG.complete_layered(3, 3)
        cg = ComputationalGraph.from_layered_dag(dag)
        target_model = dag.layers[2][2]
        incoming = cg.incoming[target_model]
        self.assertGreaterEqual(len(incoming), 2)

        h_corr = HealthSignals(edge_count=cg.edge_count, node_count=cg.node_count)
        for eid in incoming[:2]:
            for _ in range(4):
                obs = ResourceObservation(
                    edge_id=eid,
                    token_usage=TokenUsage(input_tokens=150),
                    latency_ms=200.0,
                    monetary_cost=0.2,
                    success=False,
                    quality=0.12,
                    uncertainty=0.05,
                )
                h_corr.observe(obs, target_model)
        gate_corr = h_corr.anastomosis_gate(target_model, incoming)

        h_local = HealthSignals(edge_count=cg.edge_count, node_count=cg.node_count)
        for _ in range(4):
            h_local.observe(
                ResourceObservation(
                    edge_id=incoming[0],
                    token_usage=TokenUsage(input_tokens=150),
                    latency_ms=200.0,
                    monetary_cost=0.2,
                    success=False,
                    quality=0.08,
                    uncertainty=0.05,
                ),
                target_model,
            )
            h_local.observe(
                ResourceObservation(
                    edge_id=incoming[1],
                    token_usage=TokenUsage(input_tokens=150),
                    latency_ms=120.0,
                    monetary_cost=0.1,
                    success=True,
                    quality=0.90,
                    uncertainty=0.05,
                ),
                target_model,
            )
        gate_local = h_local.anastomosis_gate(target_model, incoming)
        self.assertGreater(gate_corr, 0.30)
        self.assertLess(gate_local, 0.02)

    def test_unobserved_edges_do_not_accumulate_prune_evidence(self) -> None:
        cfg = load_v2_config(V2_DEV)
        evidence = np.zeros(4, dtype=int)
        counts = np.array([10, 10, 10, 10])
        scores = np.array([0.95, 0.95, 0.95, 0.10])
        for _ in range(cfg.controller.prune_persistence + 2):
            evidence, pruned = update_prune_evidence(
                evidence,
                counts,
                scores,
                cfg.controller,
                True,
                observed_edges=(3,),
                outgoing_map={0: (0, 1, 2, 3)},
            )
        self.assertEqual(int(evidence[0]), 0)
        self.assertFalse(bool(np.any(pruned)))


class IsolationDeterminismAndAuditTests(unittest.TestCase):
    def test_scenario_arrays_are_immutable_and_mock_provider_conforms(self) -> None:
        cfg = load_v2_config(V2_DEV)
        scenario = generate_resource_scenario(cfg, 7103, "LOCAL_OUTAGE")
        self.assertFalse(scenario.quality_means_pre.flags.writeable)
        self.assertFalse(scenario.quality_means_post.flags.writeable)
        with self.assertRaises(ValueError):
            scenario.quality_means_post[0] = 0.99

        provider = DeterministicMockProvider(seed=42, tokens_per_call=100)
        self.assertIsInstance(provider, ProviderAdapter)
        req = AdapterRequest("t-1", "model_2_1", "model", 60, "solve task")
        resp1 = provider.invoke(req)
        resp2 = DeterministicMockProvider(seed=42, tokens_per_call=100).invoke(req)
        self.assertEqual(resp1, resp2)
        self.assertLessEqual(resp1.token_usage.total_tokens, 60)

    def test_trace_gzip_is_byte_identical_and_end_to_end_pipeline_audits_cleanly(self) -> None:
        base = load_v2_config(V2_DEV)
        cfg = replace(
            base,
            environment=replace(base.environment, regimes=("PRICE_SHOCK", "LOCAL_OUTAGE")),
            methods=(
                "always_high_compute",
                "always_low_compute",
                "random_feasible",
                "v1_edge_only",
                "v1_node_only",
                "v1_hierarchical",
                "resource_heuristic",
                "structured_sw_ucb",
                "v2_mycelial",
                "v2_constrained",
                "v2_pareto",
            ),
        )
        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            out1, out2 = Path(d1), Path(d2)
            run_v2_experiment(cfg, out1, workers=1)
            run_v2_experiment(cfg, out2, workers=1)
            t1 = sorted((out1 / "traces").glob("*.jsonl.gz"))
            t2 = sorted((out2 / "traces").glob("*.jsonl.gz"))
            self.assertEqual(len(t1), len(t2))
            for f1, f2 in zip(t1, t2):
                self.assertEqual(
                    hashlib.sha256(f1.read_bytes()).hexdigest(),
                    hashlib.sha256(f2.read_bytes()).hexdigest(),
                )

            analyze_v2_results(cfg, out1)
            report_path = generate_v2_report(cfg, out1)
            self.assertTrue(report_path.exists())
            audit = audit_resource_traces(out1)
            self.assertTrue(audit["ok"], audit)

            for raw_file in (out1 / "raw").rglob("*.json"):
                payload = json.loads(raw_file.read_text(encoding="utf-8"))["scientific_payload"]
                for row in payload["results"]:
                    bd = decompose_waste(
                        row["ledger"],
                        success=row["success_rate"] >= 0.5,
                        retrieval_used=True,
                    )
                    self.assertTrue(waste_identity_ok(bd, row["ledger"]["total_tokens"]))

            self.assertEqual(main(["v2-viz", "--config", str(V2_DEV), "--output", str(out1)]), 0)
            self.assertTrue((out1 / "figures" / "v2_topology.svg").exists())
            self.assertTrue((out1 / "figures" / "v2_trace_dashboard.png").exists())

            cg = ComputationalGraph.from_layered_dag(
                LayeredDAG.complete_layered(cfg.graph.internal_layers, cfg.graph.alternatives_per_layer)
            )
            svg = render_topology_svg(cg, active_edges=(0, 3))
            self.assertIn("<svg", svg)
            import gzip

            with gzip.open(t1[0], "rt", encoding="utf-8") as handle:
                recs = [json.loads(line) for line in handle if line.strip()]
            png = render_trace_dashboard(recs, out1 / "figures" / "dash.png", shock_step=24)
            self.assertTrue(png.exists())

    def test_ast_repair_preserves_multi_arg_and_multiline_bodies_and_cli_exit_codes(self) -> None:
        src = "def pick(items, default=0):\n    x = len(items)\n    return items[0] + default + x\n"
        guarded = _empty_guard_source(src)
        self.assertIsNotNone(guarded)
        assert guarded is not None
        compile(guarded, "guarded.py", "exec")
        self.assertIn("default=0", guarded)

        shifted = _shifted_return_source("def count(items, offset=1):\n    return len(items) + offset\n", -1)
        self.assertIsNotNone(shifted)
        assert shifted is not None
        self.assertIn("offset=1", shifted)

        with tempfile.TemporaryDirectory() as tmp:
            bad_yaml = Path(tmp) / "bad.yaml"
            bad_yaml.write_text("not: [valid: yaml\n", encoding="utf-8")
            self.assertEqual(main(["validate", "--config", str(bad_yaml)]), 2)
            self.assertEqual(main(["v2-validate", "--config", str(bad_yaml)]), 2)


if __name__ == "__main__":
    unittest.main()
