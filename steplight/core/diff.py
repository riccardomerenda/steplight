"""Compare two traces and produce a structured diff."""

from __future__ import annotations

from dataclasses import dataclass, field

from steplight.core.models import StepType, Trace, TraceStats
from steplight.core.stats import compute_trace_stats


@dataclass(slots=True)
class Delta:
    """A numeric change between two values."""

    old: float
    new: float

    @property
    def absolute(self) -> float:
        return self.new - self.old

    @property
    def percent(self) -> float | None:
        if self.old == 0:
            return None
        return (self.new - self.old) / self.old * 100


@dataclass(slots=True)
class StepTypeDelta:
    step_type: StepType
    old_count: int
    new_count: int


@dataclass(slots=True)
class TraceDiff:
    """Structured comparison between two traces."""

    base_name: str
    head_name: str
    duration: Delta
    step_count: Delta
    tool_calls: Delta
    retries: Delta
    tokens_in: Delta
    tokens_out: Delta
    cost: Delta | None
    step_type_deltas: list[StepTypeDelta] = field(default_factory=list)
    base_only_steps: list[str] = field(default_factory=list)
    head_only_steps: list[str] = field(default_factory=list)


def _step_type_counts(trace: Trace) -> dict[StepType, int]:
    counts: dict[StepType, int] = {}
    for step in trace.steps:
        counts[step.type] = counts.get(step.type, 0) + 1
    return counts


def _step_names(trace: Trace) -> set[str]:
    return {step.name for step in trace.steps if step.name}


def compare_traces(base: Trace, head: Trace) -> TraceDiff:
    """Compare *base* (old/before) against *head* (new/after)."""

    base_stats = compute_trace_stats(base)
    head_stats = compute_trace_stats(head)

    cost: Delta | None = None
    if base_stats.total_cost_usd is not None and head_stats.total_cost_usd is not None:
        cost = Delta(base_stats.total_cost_usd, head_stats.total_cost_usd)

    # Step-type breakdown
    base_type_counts = _step_type_counts(base)
    head_type_counts = _step_type_counts(head)
    all_types = sorted(set(base_type_counts) | set(head_type_counts), key=lambda t: t.value)
    step_type_deltas = [
        StepTypeDelta(t, base_type_counts.get(t, 0), head_type_counts.get(t, 0))
        for t in all_types
        if base_type_counts.get(t, 0) != head_type_counts.get(t, 0)
    ]

    # Named steps that appear in only one trace
    base_names = _step_names(base)
    head_names = _step_names(head)

    return TraceDiff(
        base_name=base.name or base.id,
        head_name=head.name or head.id,
        duration=Delta(base_stats.duration_ms, head_stats.duration_ms),
        step_count=Delta(base_stats.step_count, head_stats.step_count),
        tool_calls=Delta(base_stats.tool_calls, head_stats.tool_calls),
        retries=Delta(base_stats.retries, head_stats.retries),
        tokens_in=Delta(base_stats.tokens_in, head_stats.tokens_in),
        tokens_out=Delta(base_stats.tokens_out, head_stats.tokens_out),
        cost=cost,
        step_type_deltas=step_type_deltas,
        base_only_steps=sorted(base_names - head_names),
        head_only_steps=sorted(head_names - base_names),
    )
