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
