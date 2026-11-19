from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0
    estimated_tokens: int = 0
    router_tokens: int = 0
    verification_tokens: int = 0
    tool_tokens: int = 0
    retrieval_tokens: int = 0
    summarization_tokens: int = 0
    memory_tokens: int = 0
    retry_tokens: int = 0
    recovery_overhead_tokens: int = 0
    state_overhead_tokens: int = 0
    provider_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def path_tokens(self) -> int:
        # cached_tokens and estimated_tokens are diagnostic/non-additive and never double-counted.
        return (
            self.input_tokens
            + self.output_tokens
            + self.reasoning_tokens
            + self.verification_tokens
            + self.tool_tokens
            + self.retrieval_tokens
            + self.summarization_tokens
            + self.memory_tokens
            + self.retry_tokens
            + self.recovery_overhead_tokens
        )

    @property
    def total_tokens(self) -> int:
        return self.path_tokens + self.router_tokens + self.state_overhead_tokens

    def merged(self, other: "TokenUsage") -> "TokenUsage":
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cached_tokens=self.cached_tokens + other.cached_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            estimated_tokens=self.estimated_tokens + other.estimated_tokens,
            router_tokens=self.router_tokens + other.router_tokens,
            verification_tokens=self.verification_tokens + other.verification_tokens,
            tool_tokens=self.tool_tokens + other.tool_tokens,
            retrieval_tokens=self.retrieval_tokens + other.retrieval_tokens,
            summarization_tokens=self.summarization_tokens + other.summarization_tokens,
            memory_tokens=self.memory_tokens + other.memory_tokens,
            retry_tokens=self.retry_tokens + other.retry_tokens,
            recovery_overhead_tokens=self.recovery_overhead_tokens + other.recovery_overhead_tokens,
            state_overhead_tokens=self.state_overhead_tokens + other.state_overhead_tokens,
            provider_metadata={**self.provider_metadata, **other.provider_metadata},
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["total_tokens"] = self.total_tokens
        payload["path_tokens"] = self.path_tokens
        return payload


@dataclass(frozen=True)
class ResourceObservation:
    edge_id: int
    token_usage: TokenUsage
    latency_ms: float
    monetary_cost: float
    success: bool
    quality: float
    uncertainty: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "token_usage": self.token_usage.to_dict(),
            "latency_ms": self.latency_ms,
            "monetary_cost": self.monetary_cost,
            "success": self.success,
            "quality": self.quality,
            "uncertainty": self.uncertainty,
        }


@dataclass
class TotalResourceLedger:
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    reasoning_tokens: int = 0
    estimated_tokens: int = 0
    router_tokens: int = 0
    verification_tokens: int = 0
    tool_tokens: int = 0
    retrieval_tokens: int = 0
    summarization_tokens: int = 0
    memory_tokens: int = 0
    retry_tokens: int = 0
    recovery_overhead_tokens: int = 0
    state_overhead_tokens: int = 0
    model_calls: int = 0
    tool_calls: int = 0
    retriever_calls: int = 0
    validator_calls: int = 0
    retry_count: int = 0
    fallback_count: int = 0
    latency_ms: float = 0.0
    monetary_cost: float = 0.0
    policy_cpu_ms: float = 0.0
    quality_sum: float = 0.0
    realized_quality_sum: float = 0.0
    success_sum: float = 0.0
    steps: int = 0
    post_shock_tokens: int = 0
    post_shock_router_tokens: int = 0
    post_shock_cost: float = 0.0
    post_shock_steps: int = 0

    def record_step(
        self,
        path_usage: TokenUsage,
        router_tokens: int,
        state_overhead: int,
        latency_ms: float,
        monetary_cost: float,
        quality: float,
        success: bool,
        model_calls: int,
        tool_calls: int,
        *,
        retriever_calls: int = 0,
        validator_calls: int = 0,
        retry_count: int = 0,
        fallback_count: int = 0,
        policy_cpu_ms: float = 0.0,
        realized_quality: float | None = None,
        is_post_shock: bool = False,
    ) -> None:
        usage = path_usage.merged(
            TokenUsage(router_tokens=router_tokens, state_overhead_tokens=state_overhead)
        )
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        self.cached_tokens += usage.cached_tokens
        self.reasoning_tokens += usage.reasoning_tokens
        self.estimated_tokens += usage.estimated_tokens
        self.router_tokens += usage.router_tokens
        self.verification_tokens += usage.verification_tokens
        self.tool_tokens += usage.tool_tokens
        self.retrieval_tokens += usage.retrieval_tokens
        self.summarization_tokens += usage.summarization_tokens
        self.memory_tokens += usage.memory_tokens
        self.retry_tokens += usage.retry_tokens
        self.recovery_overhead_tokens += usage.recovery_overhead_tokens
        self.state_overhead_tokens += usage.state_overhead_tokens
        self.latency_ms += latency_ms
        self.monetary_cost += monetary_cost
        self.policy_cpu_ms += policy_cpu_ms
        self.quality_sum += quality
        self.realized_quality_sum += quality if realized_quality is None else realized_quality
        self.success_sum += float(success)
        self.model_calls += model_calls
        self.tool_calls += tool_calls
        self.retriever_calls += retriever_calls
        self.validator_calls += validator_calls
        self.retry_count += retry_count
        self.fallback_count += fallback_count
        self.steps += 1
        if is_post_shock:
            self.post_shock_tokens += usage.total_tokens
            self.post_shock_router_tokens += usage.router_tokens
            self.post_shock_cost += monetary_cost
            self.post_shock_steps += 1

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.reasoning_tokens
            + self.router_tokens
            + self.verification_tokens
            + self.tool_tokens
            + self.retrieval_tokens
            + self.summarization_tokens
            + self.memory_tokens
            + self.retry_tokens
            + self.recovery_overhead_tokens
            + self.state_overhead_tokens
        )

    def mean_quality(self) -> float:
        return self.quality_sum / self.steps if self.steps else 0.0

    def mean_realized_quality(self) -> float:
        return self.realized_quality_sum / self.steps if self.steps else 0.0

    def success_rate(self) -> float:
        return self.success_sum / self.steps if self.steps else 0.0

    def tokens_per_successful_task(self) -> float | None:
        return float(self.total_tokens / self.success_sum) if self.success_sum > 0 else None

    def cost_per_successful_task(self) -> float | None:
        return float(self.monetary_cost / self.success_sum) if self.success_sum > 0 else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "ledger_schema_version": "v2.2-resource-1",
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cached_tokens": self.cached_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "estimated_tokens": self.estimated_tokens,
            "router_tokens": self.router_tokens,
            "verification_tokens": self.verification_tokens,
            "tool_tokens": self.tool_tokens,
            "retrieval_tokens": self.retrieval_tokens,
            "summarization_tokens": self.summarization_tokens,
            "memory_tokens": self.memory_tokens,
            "retry_tokens": self.retry_tokens,
            "recovery_overhead_tokens": self.recovery_overhead_tokens,
            "state_overhead_tokens": self.state_overhead_tokens,
            "total_tokens": self.total_tokens,
            "model_calls": self.model_calls,
            "tool_calls": self.tool_calls,
            "retriever_calls": self.retriever_calls,
            "validator_calls": self.validator_calls,
            "retry_count": self.retry_count,
            "fallback_count": self.fallback_count,
            "latency_ms": self.latency_ms,
            "monetary_cost": self.monetary_cost,
            "policy_cpu_ms": self.policy_cpu_ms,
            "mean_quality": self.mean_quality(),
            "mean_realized_quality": self.mean_realized_quality(),
            "success_rate": self.success_rate(),
            "tokens_per_successful_task": self.tokens_per_successful_task(),
            "cost_per_successful_task": self.cost_per_successful_task(),
            "post_shock_tokens": self.post_shock_tokens,
            "post_shock_router_tokens": self.post_shock_router_tokens,
            "post_shock_cost": self.post_shock_cost,
            "post_shock_steps": self.post_shock_steps,
            "steps": self.steps,
        }
