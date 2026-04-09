from pathlib import Path

from steplight.core.analyzer import analyze_trace
from steplight.core.parser import parse_trace_file


ROOT = Path(__file__).resolve().parents[1]


def test_failing_run_emits_retry_and_silent_error() -> None:
    trace = parse_trace_file(ROOT / "sample_traces" / "failing_run.json")
    messages = [diagnostic.rule for diagnostic in analyze_trace(trace)]
    assert "retry_loop" in messages
    assert "silent_error" in messages
    assert "slow_tool" in messages


def test_expensive_run_emits_cost_and_context_growth() -> None:
    trace = parse_trace_file(ROOT / "sample_traces" / "expensive_run.json")
    messages = [diagnostic.rule for diagnostic in analyze_trace(trace)]
    assert "high_cost" in messages
    assert "context_growth" in messages
    assert "tool_abuse" in messages
    assert "empty_output" in messages


def test_tool_concentration_fires_when_one_tool_dominates() -> None:
    """agent_with_tools has web_search at ~89% of total tool runtime."""
    trace = parse_trace_file(ROOT / "sample_traces" / "agent_with_tools.json")
    diagnostics = analyze_trace(trace)
    rules = [d.rule for d in diagnostics]
    assert "tool_concentration" in rules
    concentration = next(d for d in diagnostics if d.rule == "tool_concentration")
    assert concentration.metadata["tool"] == "web_search"
    assert concentration.metadata["share"] > 0.7


def test_tool_concentration_skipped_with_single_tool() -> None:
    """Rule needs at least 2 distinct tools to make a 'concentration' claim meaningful."""
    from datetime import datetime, timezone

    from steplight.core.analyzer import AnalyzerConfig, ToolConcentrationRule
    from steplight.core.models import Step, StepType, Trace

    base = datetime(2025, 1, 1, tzinfo=timezone.utc)
    trace = Trace(
        id="t",
        started_at=base,
        steps=[
            Step(id="1", type=StepType.TOOL_CALL, name="only_tool", timestamp=base, duration_ms=1000),
            Step(id="2", type=StepType.TOOL_CALL, name="only_tool", timestamp=base, duration_ms=1000),
        ],
    )
    assert ToolConcentrationRule().evaluate(trace, AnalyzerConfig()) == []
