from pathlib import Path

from steplight.core.parser import parse_trace_file


ROOT = Path(__file__).resolve().parents[1]


def test_parse_openai_trace() -> None:
    trace = parse_trace_file(ROOT / "sample_traces" / "agent_with_tools.json")
    assert trace.source == "openai"
    assert len(trace.steps) == 4
    assert trace.steps[1].type.value == "tool_call"
    assert trace.steps[1].name == "web_search"


def test_parse_langchain_trace() -> None:
    trace = parse_trace_file(ROOT / "sample_traces" / "failing_run.json")
    assert trace.source == "langchain"
    assert any(step.type.value == "retry" for step in trace.steps)


def test_parse_generic_trace() -> None:
    trace = parse_trace_file(ROOT / "sample_traces" / "simple_qa.json")
    assert trace.source == "generic"
    assert trace.steps[0].type.value == "prompt"


def test_generic_parser_preserves_explicit_empty_outputs() -> None:
    trace = parse_trace_file(ROOT / "sample_traces" / "expensive_run.json")
    empty_completion = next(step for step in trace.steps if step.id == "g6")
    assert empty_completion.output == ""
