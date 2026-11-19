from __future__ import annotations

import numpy as np

from ...agents.base import stable_softmax
from ...environment.graph import LayeredDAG
from ..biology import (
    TOKEN_SCALE,
    assert_budget_conserved,
    budget_l1_shift,
    estimate_token_voc,
    prune_score,
    routing_utility,
    should_spend,
    translocate,
    update_conductance,
    update_prune_evidence,
)
from ..environment.roles import alternative_index, edge_role
from ..graph_model import ComputationalGraph, HealthSignals
from ..ledger import ResourceObservation
from ..types import V2ExperimentConfig
from .base import ResourceAgent, ResourceDecision

COST_SCALE = 2.5
LATENCY_SCALE = 1000.0


def _pareto_nondominated_indices(vectors: np.ndarray) -> list[int]:
    """Return indices of rows in ``vectors`` (all maximize) not dominated by any other row."""
    keep: list[int] = []
    n = len(vectors)
    for i in range(n):
        dominated = False
        for j in range(n):
            if i == j:
                continue
            if np.all(vectors[j] >= vectors[i] - 1e-12) and np.any(vectors[j] > vectors[i] + 1e-12):
                dominated = True
                break
        if not dominated:
            keep.append(i)
    return keep or list(range(n))


class MycelialResourceController(ResourceAgent):
    """Adaptive resource-aware Mycelial V2 routing controller over G = (V, E, S, B, H)."""

    name = "v2_mycelial"

    def __init__(
        self,
        config: V2ExperimentConfig,
        edge_count: int,
        rng: np.random.Generator,
        *,
        pruning: bool = True,
        transfer: bool = True,
        cord: bool = True,
        cost_aware: bool = True,
        branching: bool = True,
        anastomosis: bool = True,
        uncertainty: bool = True,
        shock_memory: bool = True,
        dynamic_topology: bool = True,
        objective_mode: str = "scalarized",
    ) -> None:
        super().__init__(rng)
        if objective_mode not in {"scalarized", "constrained", "pareto"}:
            raise ValueError(f"Unsupported objective_mode: {objective_mode}")
        self.config = config
        self.pruning_enabled = bool(pruning and dynamic_topology)
        self.dynamic_topology = bool(dynamic_topology)
        self.transfer_enabled = bool(transfer)
        self.cord_enabled = bool(cord)
        self.cost_aware = bool(cost_aware)
        self.branching_enabled = bool(branching)
        self.anastomosis_enabled = bool(anastomosis)
        self.uncertainty_enabled = bool(uncertainty)
        self.shock_memory_enabled = bool(shock_memory)
        self.objective_mode = objective_mode

        c = config.controller
        self.conductance = np.full(edge_count, c.initial_conductance, dtype=float)
        self.budget = np.zeros(edge_count, dtype=float)
        self._budget_initialized = False
        self._comp_graph: ComputationalGraph | None = None
        self.health: HealthSignals | None = None

        self.prune_evidence = np.zeros(edge_count, dtype=int)
        self.pruned = np.zeros(edge_count, dtype=bool)
        self.dual_price = float(config.utility.lambda_tokens)
        self.last_path: tuple[int, ...] | None = None
        self.last_switch_step = -10_000
        self.last_prune_count = 0
        self.last_transfer_l1 = 0.0
        self.last_mvc = 0.0
        self.last_anastomosis_gate = 0.0

    def _ensure_graph_state(self, graph: LayeredDAG, step_cap: float) -> tuple[ComputationalGraph, HealthSignals]:
        if self._comp_graph is None or self._comp_graph.edge_count != len(graph.edges):
            self._comp_graph = ComputationalGraph.from_layered_dag(graph)
            self.health = HealthSignals(
                edge_count=self._comp_graph.edge_count,
                node_count=self._comp_graph.node_count,
            )
        assert self.health is not None
        if not self._budget_initialized or abs(float(self.budget.sum()) - step_cap) > 1e-4 * max(1.0, step_cap):
            if not self._budget_initialized:
                self.budget = np.full(len(graph.edges), step_cap / max(len(graph.edges), 1), dtype=float)
                self._budget_initialized = True
            else:
                self.budget = translocate(
                    self.budget,
                    np.maximum(self.conductance, self.config.controller.minimum_conductance),
                    step_cap,
                    self.config.controller,
                    self.transfer_enabled,
                )
            assert_budget_conserved(self.budget, step_cap, atol=1e-5)
        return self._comp_graph, self.health

    def _step_budget_envelope(self, step: int, budget_cap: float) -> float:
        steps_left = max(self.config.horizon.total_steps - step, 1)
        if budget_cap > 2500.0:
            return float(max(15.0, budget_cap / float(steps_left)))
        return float(max(15.0, budget_cap))

    def _effective_estimates(
        self,
        comp_graph: ComputationalGraph,
        health: HealthSignals,
        edge_id: int,
    ) -> tuple[float, float, float, float, float, float, float]:
        """Return (quality, token_norm, cost_norm, lat_norm, fail_prob, unc, gate) with optional anastomosis."""
        target = comp_graph.dag.edges[edge_id].target
        q_e = float(health.quality_hat[edge_id])
        c_e = float(health.cost_hat[edge_id])
        f_e = float(health.fail_hat[edge_id])
        gate = 0.0
        if self.anastomosis_enabled and target not in {comp_graph.source, comp_graph.sink}:
            incoming = comp_graph.incoming.get(target, ())
            gate = health.anastomosis_gate(target, incoming, max_mix=0.45)
            if gate > 0.0:
                q_e = (1.0 - gate) * q_e + gate * float(health.node_quality_hat[target])
                c_e = (1.0 - gate) * c_e + gate * float(health.node_cost_hat[target])
                f_e = (1.0 - gate) * f_e + gate * float(health.node_fail_hat[target])
        t_norm = float(health.token_hat[edge_id] / TOKEN_SCALE)
        c_norm = float(c_e / COST_SCALE)
        l_norm = float(health.latency_hat[edge_id] / LATENCY_SCALE)
        unc = health.uncertainty(edge_id) if self.uncertainty_enabled else 0.0
        return q_e, t_norm, c_norm, l_norm, f_e, unc, gate

    def _edge_score(
        self,
        comp_graph: ComputationalGraph,
        health: HealthSignals,
        edge_id: int,
        step: int,
        *,
        skip_bonus: float = 0.0,
    ) -> tuple[float, float, float]:
        c = self.config.controller
        u = self.config.utility
        q_eff, t_norm, c_norm, l_norm, f_eff, unc, gate = self._effective_estimates(
            comp_graph, health, edge_id
        )
        risk_term = min(1.0, f_eff + 0.35 * unc)
        state_norm = float(comp_graph.edge_count * self.config.resources.state_overhead_tokens) / TOKEN_SCALE

        if self.objective_mode == "constrained":
            util = (
                q_eff
                - (self.dual_price if self.cost_aware else 0.0) * t_norm
                - (u.lambda_cost * c_norm if self.cost_aware else 0.0)
                - (u.lambda_latency * l_norm if self.cost_aware else 0.0)
                - u.lambda_risk * risk_term
                - u.lambda_failure * f_eff
            )
        else:
            util = routing_utility(
                q_eff,
                t_norm,
                c_norm,
                l_norm,
                risk_term,
                f_eff,
                state_norm,
                u,
                self.cost_aware,
            )

        base = 0.45 * float(self.conductance[edge_id]) + 0.55 * float(util) + skip_bonus
        if self.transfer_enabled and self.cost_aware:
            # Active translocation bias: favor corridors whose allocated budget comfortably covers demand.
            corridor_share = float(self.budget[edge_id])
            expected_tok = max(float(health.token_hat[edge_id]), 10.0)
            ratio = float(np.clip((corridor_share * 3.5) / expected_tok, 0.25, 2.5))
            base += 0.08 * float(np.log(ratio))

        if self.branching_enabled and self.uncertainty_enabled:
            # Controlled VoI exploration bonus: explore uncertain edges only when token cost is justified.
            voi_bonus = max(0.0, 0.22 * unc - 0.12 * u.lambda_tokens * t_norm)
            base += voi_bonus

        if self.last_path is not None:
            last_edges = set(comp_graph.dag.path_edges(self.last_path))
            if edge_id in last_edges:
                base += c.hysteresis
            elif step - self.last_switch_step < u.switch_cooldown:
                base -= u.switching_penalty

        return float(base), float(util), float(gate)

    def _verification_policy_at_node(
        self,
        comp_graph: ComputationalGraph,
        health: HealthSignals,
        candidates: tuple[int, ...],
        upstream_quality_est: float,
        upstream_risk_est: float,
    ) -> tuple[list[int], dict[int, float], str | None]:
        """Enforce hard verification/guardrail constraints at ANY model->verification transition."""
        dag = comp_graph.dag
        skip = min(candidates, key=lambda e: alternative_index(dag, dag.edges[e].target))
        spend = max(candidates, key=lambda e: alternative_index(dag, dag.edges[e].target))
        q_skip, _, _, _, f_skip, _, _ = self._effective_estimates(comp_graph, health, skip)
        q_spend, _, _, _, _, _, _ = self._effective_estimates(comp_graph, health, spend)
        dq = max(0.0, q_spend - q_skip)
        dt = max(float(health.token_hat[spend] - health.token_hat[skip]), 1.0)
        voc = estimate_token_voc(dq, dt, self.config.utility.lambda_tokens)
        self.last_mvc = voc.ratio

        combined_q_if_skip = 0.5 * upstream_quality_est + 0.5 * q_skip
        combined_risk_if_skip = max(upstream_risk_est, f_skip)
        must_verify = (
            self.config.constraints.mandatory_verification
            or combined_q_if_skip < self.config.constraints.minimum_quality
            or combined_risk_if_skip > self.config.constraints.max_risk
        )
        if must_verify:
            non_skip = [e for e in candidates if e != skip]
            if non_skip:
                return non_skip, {}, "mandatory_verification_enforced"
        spend_ok = should_spend(
            voc.difference,
            self.config.utility.mvc_threshold,
            combined_q_if_skip,
            combined_risk_if_skip,
            self.config.constraints,
        )
        bonuses: dict[int, float] = {}
        if not spend_ok:
            bonuses[skip] = 0.14
        return list(candidates), bonuses, None

    def choose(self, graph: LayeredDAG, step: int, budget_cap: float) -> ResourceDecision:
        step_cap = self._step_budget_envelope(step, float(budget_cap))
        comp_graph, health = self._ensure_graph_state(graph, step_cap)
        c = self.config.controller

        node = graph.source
        path = [node]
        selected_edges: list[int] = []
        selected_scores: list[float] = []
        evaluated_candidates = 0
        exploratory = 0
        fallback_reason: str | None = None
        decision_mode = "exploitation"
        est_utilities: list[float] = []
        est_tokens = 0.0
        est_cost = 0.0
        uncertainties: list[float] = []
        gates: list[float] = []
        comp_health_trace: list[float] = []

        while node != graph.sink:
            raw_candidates = graph.outgoing[node]
            if len(raw_candidates) == 1:
                chosen = raw_candidates[0]
                evaluated_candidates += 1
                s_val, u_val, g_val = self._edge_score(comp_graph, health, chosen, step)
                selected_edges.append(chosen)
                selected_scores.append(s_val)
                est_utilities.append(u_val)
                est_tokens += float(health.token_hat[chosen])
                est_cost += float(health.cost_hat[chosen])
                uncertainties.append(health.uncertainty(chosen) if self.uncertainty_enabled else 0.0)
                gates.append(g_val)
                node = graph.edges[chosen].target
                comp_health_trace.append(float(health.node_quality_hat[node]))
                path.append(node)
                continue

            # 1. Cytoplasmic retraction filter (saves router candidate evaluations; keeps fallback probe).
            rehab_probe = bool(
                self.pruning_enabled
                and any(self.pruned[e] for e in raw_candidates)
                and self.rng.random() < 0.03
            )
            if self.pruning_enabled and not rehab_probe:
                active = [e for e in raw_candidates if not self.pruned[e]]
                if not active:
                    active = [min(raw_candidates, key=lambda e: int(self.prune_evidence[e]))]
            else:
                active = list(raw_candidates)

            # 2. Hard safety & verification guardrails BEFORE soft routing.
            bonuses: dict[int, float] = {}
            if edge_role(graph, raw_candidates[0]) == "verification":
                up_q = float(np.mean(est_utilities)) if est_utilities else 0.65
                up_r = max(( float(health.fail_hat[e]) for e in selected_edges ), default=0.05)
                allowed_ver, bonuses, ver_reason = self._verification_policy_at_node(
                    comp_graph, health, tuple(active), up_q, up_r
                )
                active = allowed_ver
                if ver_reason:
                    fallback_reason = fallback_reason or ver_reason

            safe = [e for e in active if float(health.fail_hat[e]) <= self.config.constraints.max_risk]
            if safe:
                active = safe
            elif len(active) > 1:
                fallback_reason = fallback_reason or "max_risk_guardrail"
                decision_mode = "safety_fallback"
                active = [min(active, key=lambda e: float(health.fail_hat[e]))]

            # 3. Hard step token budget feasibility filter (enforces RESOURCE_SCARCITY & budget curves).
            rem_layers = max(1, (len(graph.layers) - 2) - len(selected_edges))
            downstream_reserve = 12.0 * (rem_layers - 1)
            affordable = [
                e
                for e in active
                if est_tokens + float(health.token_hat[e]) + downstream_reserve <= step_cap
            ]
            if affordable:
                if len(affordable) < len(active):
                    fallback_reason = fallback_reason or "budget_cap_downgrade"
                active = affordable
            else:
                fallback_reason = fallback_reason or "budget_exhausted_minimal_fallback"
                decision_mode = "budget_downgrade"
                active = [min(active, key=lambda e: float(health.token_hat[e]))]

            # 4. Pareto candidate filtering when objective_mode == "pareto".
            if self.objective_mode == "pareto" and len(active) > 1:
                vecs = []
                for e in active:
                    q_e, t_n, c_n, l_n, f_e, _, _ = self._effective_estimates(comp_graph, health, e)
                    vecs.append([q_e - f_e, -t_n, -c_n, -l_n])
                nd_idx = _pareto_nondominated_indices(np.array(vecs, dtype=float))
                active = [active[idx] for idx in nd_idx]

            evaluated_candidates += len(active)
            scored_triples = [
                self._edge_score(comp_graph, health, e, step, skip_bonus=bonuses.get(e, 0.0))
                for e in active
            ]
            cand_scores = np.array([item[0] for item in scored_triples], dtype=float)

            # 5. Controlled hyphal branching vs exploitation.
            is_explore = len(active) > 1 and self.rng.random() < c.exploration_probability
            if len(active) == 1:
                chosen_idx = 0
            elif is_explore:
                exploratory += 1
                if self.branching_enabled:
                    # VoI-weighted branching toward uncertain, affordable alternatives.
                    voi_scores = np.array(
                        [
                            (health.uncertainty(e) if self.uncertainty_enabled else 0.1)
                            - 0.25 * self.config.utility.lambda_tokens * (float(health.token_hat[e]) / TOKEN_SCALE)
                            for e in active
                        ],
                        dtype=float,
                    )
                    probs = stable_softmax(voi_scores, max(0.08, c.temperature * 0.5))
                    chosen_idx = int(self.rng.choice(len(active), p=probs))
                    if decision_mode == "exploitation":
                        decision_mode = "branching_exploration"
                else:
                    chosen_idx = int(self.rng.integers(0, len(active)))
                    if decision_mode == "exploitation":
                        decision_mode = "uniform_exploration"
            else:
                probs = stable_softmax(cand_scores, c.temperature)
                chosen_idx = int(self.rng.choice(len(active), p=probs))

            chosen = active[chosen_idx]
            s_val, u_val, g_val = scored_triples[chosen_idx]
            selected_edges.append(chosen)
            selected_scores.append(s_val)
            est_utilities.append(u_val)
            est_tokens += float(health.token_hat[chosen])
            est_cost += float(health.cost_hat[chosen])
            uncertainties.append(health.uncertainty(chosen) if self.uncertainty_enabled else 0.0)
            gates.append(g_val)
            node = graph.edges[chosen].target
            comp_health_trace.append(float(health.node_quality_hat[node]))
            path.append(node)

        path_tuple = tuple(path)
        if self.last_path is not None and path_tuple != self.last_path:
            self.last_switch_step = step
        self.last_path = path_tuple
        self.last_anastomosis_gate = float(np.mean(gates)) if gates else 0.0

        return ResourceDecision(
            path_tuple,
            tuple(selected_edges),
            exploratory,
            tuple(selected_scores),
            evaluated_candidates,
            float(self.last_mvc),
            int(self.last_prune_count),
            float(self.last_transfer_l1),
            estimated_utility=float(np.mean(est_utilities)) if est_utilities else 0.0,
            estimated_tokens=est_tokens,
            estimated_cost=est_cost,
            uncertainty=float(np.mean(uncertainties)) if uncertainties else 0.0,
            decision_mode=decision_mode,
            fallback_reason=fallback_reason,
            objective_mode=self.objective_mode,
            candidate_paths_available=len(graph.all_paths()),
            anastomosis_gate=self.last_anastomosis_gate,
            component_health=tuple(round(v, 5) for v in comp_health_trace),
        )

    def update(
        self,
        graph: LayeredDAG,
        decision: ResourceDecision,
        observations: list[ResourceObservation],
        step: int,
        budget_cap: float,
    ) -> None:
        step_cap = self._step_budget_envelope(step, float(budget_cap))
        comp_graph, health = self._ensure_graph_state(graph, step_cap)
        u = self.config.utility

        targets: list[float] = []
        waste = np.zeros(len(self.conductance), dtype=float)
        reliable_cord = np.zeros(len(self.conductance), dtype=float)
        used_tokens = 0.0

        for obs in observations:
            e = obs.edge_id
            target_node = graph.edges[e].target
            shock_fired = health.observe(
                obs, target_node, shock_memory_enabled=self.shock_memory_enabled
            )
            if shock_fired and self.shock_memory_enabled:
                # Dampen stale cord inertia on shocked edge so recovery is immediate.
                self.conductance[e] = 0.5 * self.conductance[e] + 0.5 * self.config.controller.minimum_conductance

            tokens = float(obs.token_usage.path_tokens)
            used_tokens += tokens
            token_norm = tokens / TOKEN_SCALE
            cost_norm = obs.monetary_cost / COST_SCALE
            lat_norm = obs.latency_ms / LATENCY_SCALE
            fail = 0.0 if obs.success else 1.0
            unc = health.uncertainty(e) if self.uncertainty_enabled else 0.0
            risk_term = min(1.0, fail + 0.35 * unc)
            state_norm = float(comp_graph.edge_count * self.config.resources.state_overhead_tokens) / TOKEN_SCALE

            util = routing_utility(
                obs.quality,
                token_norm,
                cost_norm,
                lat_norm,
                risk_term,
                fail,
                state_norm,
                u,
                self.cost_aware,
            )
            targets.append(util)
            resource_burden = u.lambda_tokens * token_norm + u.lambda_cost * cost_norm + u.lambda_latency * lat_norm
            waste[e] = max(0.0, resource_burden - obs.quality * (1.0 - fail))
            # Cord reinforcement ONLY when task succeeded and delivered positive net utility above prior!
            if obs.success and util > self.config.controller.initial_conductance:
                reliability = max(0.0, 1.0 - float(health.fail_hat[e]))
                reliable_cord[e] = reliability * (util - self.config.controller.initial_conductance)

        self.conductance = update_conductance(
            self.conductance,
            decision.edge_ids,
            np.array(targets, dtype=float),
            reliable_cord,
            waste,
            self.config.controller,
            self.cord_enabled,
        )

        # Update online dual variable for constrained objective mode.
        if self.objective_mode == "constrained":
            target_spend = 0.85 * step_cap
            self.dual_price = float(np.clip(self.dual_price + 0.0012 * (used_tokens - target_spend), 0.02, 4.0))

        # Observation-gated, price- & latency-aware cytoplasmic retraction with connectivity guard.
        scores = np.zeros(len(self.conductance), dtype=float)
        for edge_id in range(len(self.conductance)):
            q_e, t_n, c_n, l_n, f_e, _, _ = self._effective_estimates(comp_graph, health, edge_id)
            source = graph.edges[edge_id].source
            siblings = graph.outgoing.get(source, ())
            redundancy = 0.0
            if siblings:
                best_sib_u = max(
                    float(health.quality_hat[sib])
                    - (u.lambda_tokens * float(health.token_hat[sib]) / TOKEN_SCALE if self.cost_aware else 0.0)
                    - (u.lambda_cost * float(health.cost_hat[sib]) / COST_SCALE if self.cost_aware else 0.0)
                    for sib in siblings
                )
                own_u = (
                    q_e
                    - (u.lambda_tokens * t_n if self.cost_aware else 0.0)
                    - (u.lambda_cost * c_n if self.cost_aware else 0.0)
                )
                redundancy = max(0.0, best_sib_u - own_u)
            burden = (u.lambda_tokens * t_n + u.lambda_cost * c_n + u.lambda_latency * l_n) if self.cost_aware else 0.0
            scores[edge_id] = prune_score(
                burden,
                redundancy,
                f_e,
                q_e - burden,
            )

        self.prune_evidence, self.pruned = update_prune_evidence(
            self.prune_evidence,
            health.edge_counts,
            scores,
            self.config.controller,
            self.pruning_enabled,
            observed_edges=decision.edge_ids,
            outgoing_map=graph.outgoing,
        )
        if self.pruning_enabled:
            self.conductance[self.pruned] = np.minimum(
                self.conductance[self.pruned],
                self.config.controller.minimum_conductance * 1.5,
            )
        self.last_prune_count = int(np.count_nonzero(self.pruned))

        # Single conservation-checked translocation update per step weighted by efficiency.
        before = self.budget.copy()
        efficiency_weights = self.conductance * np.maximum(
            health.quality_hat - (u.lambda_cost * health.cost_hat / COST_SCALE if self.cost_aware else 0.0),
            0.05,
        )
        efficiency_weights[self.pruned] = self.config.controller.minimum_conductance
        self.budget = translocate(
            self.budget,
            efficiency_weights,
            step_cap,
            self.config.controller,
            self.transfer_enabled,
        )
        self.last_transfer_l1 = budget_l1_shift(before, self.budget)
        assert_budget_conserved(self.budget, step_cap, atol=1e-5)
