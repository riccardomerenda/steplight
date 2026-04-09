from __future__ import annotations

from dataclasses import dataclass

from steplight.core.models import StepType, Trace, TraceStats


MODEL_PRICING_PER_MILLION = {
    "gpt-4.1": (2.00, 8.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "o4-mini": (1.10, 4.40),
    "claude-opus-4-5": (15.00, 75.00),
    "claude-opus-4-6": (15.00, 75.00),
    "claude-sonnet-4-5": (3.00, 15.00),
    "claude-sonnet-4-6": (3.00, 15.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-3-5-sonnet": (3.00, 15.00),
    "claude-3-5-haiku": (0.80, 4.00),
    "claude-3-opus": (15.00, 75.00),
    "claude-3-sonnet": (3.00, 15.00),
    "claude-3-haiku": (0.25, 1.25),
}


@dataclass(slots=True)
class StepShare:
    step_id: str
    name: str
    percentage: float


@dataclass(slots=True)
class ToolStats:
    name: str
    count: int
    total_duration_ms: float
    avg_duration_ms: float
    pct_of_runtime: float


def compute_trace_stats(trace: Trace) -> TraceStats:
    tokens_in = sum(step.tokens_in or 0 for step in trace.steps)
    tokens_out = sum(step.tokens_out or 0 for step in trace.steps)
    total_cost = trace.total_cost_usd if trace.total_cost_usd is not None else estimate_trace_cost(trace)
    return TraceStats(
        duration_ms=trace_duration_ms(trace),
        step_count=len(trace.steps),
        tool_calls=sum(1 for step in trace.steps if step.type == StepType.TOOL_CALL),
        retries=sum(1 for step in trace.steps if step.type == StepType.RETRY),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        total_cost_usd=total_cost,
    )


def trace_duration_ms(trace: Trace) -> float:
    if trace.ended_at:
        return max((trace.ended_at - trace.started_at).total_seconds() * 1000, 0.0)

    if not trace.steps:
        return 0.0

    last_timestamp = max(step.timestamp for step in trace.steps)
    return max((last_timestamp - trace.started_at).total_seconds() * 1000, 0.0)


def estimate_trace_cost(trace: Trace) -> float | None:
    if trace.total_cost_usd is not None:
        return trace.total_cost_usd

    explicit_costs = [
        float(step.metadata["cost_usd"])
        for step in trace.steps
        if "cost_usd" in step.metadata and step.metadata["cost_usd"] is not None
    ]
    if explicit_costs:
        return round(sum(explicit_costs), 6)

    total = 0.0
    priced_steps = 0
    for step in trace.steps:
        if not step.model:
            continue
        pricing = MODEL_PRICING_PER_MILLION.get(step.model)
        if not pricing:
            continue
        input_price, output_price = pricing
        total += ((step.tokens_in or 0) / 1_000_000) * input_price
        total += ((step.tokens_out or 0) / 1_000_000) * output_price
        priced_steps += 1

    if not priced_steps:
        return None
    return round(total, 6)


def compute_tool_breakdown(trace: Trace) -> list[ToolStats]:
    """Aggregate per-tool counts and durations across all tool_call steps.

    Returned entries are sorted by total_duration_ms descending so the
    most expensive tools surface first. pct_of_runtime is computed against
    the trace's total wall-clock duration.
    """
    total_runtime_ms = trace_duration_ms(trace)

    counts: dict[str, int] = {}
    durations: dict[str, float] = {}

    for step in trace.steps:
        if step.type != StepType.TOOL_CALL:
            continue
        name = step.name or "tool"
        counts[name] = counts.get(name, 0) + 1
        durations[name] = durations.get(name, 0.0) + (step.duration_ms or 0.0)

    breakdown: list[ToolStats] = []
    for name, count in counts.items():
        total_dur = durations[name]
        pct = (total_dur / total_runtime_ms * 100) if total_runtime_ms > 0 else 0.0
        breakdown.append(
            ToolStats(
                name=name,
                count=count,
                total_duration_ms=total_dur,
                avg_duration_ms=total_dur / count if count else 0.0,
                pct_of_runtime=pct,
            )
        )

    breakdown.sort(key=lambda t: t.total_duration_ms, reverse=True)
    return breakdown


def find_bottleneck(trace: Trace) -> StepShare | None:
    total_duration = trace_duration_ms(trace)
    if total_duration <= 0:
        return None

    candidate = max(
        (step for step in trace.steps if step.duration_ms),
        key=lambda step: step.duration_ms or 0,
        default=None,
    )
    if candidate is None or not candidate.duration_ms:
        return None

    percentage = candidate.duration_ms / total_duration
    return StepShare(
        step_id=candidate.id,
        name=candidate.name or candidate.type.value,
        percentage=percentage,
    )
