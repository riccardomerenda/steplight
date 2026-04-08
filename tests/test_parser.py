from pathlib import Path

from steplight.core.parser import parse_trace_file


ROOT = Path(__file__).resolve().parents[1]


def test_parse_openai_trace() -> None:
    trace = parse_trace_file(ROOT / "sample_traces" / "agent_with_tools.json")
    assert trace.source == "openai"
    assert len(trace.steps) == 4
    assert trace.steps[1].type.value == "tool_call"
    assert trace.steps[1].name == "web_search"


def test_parse_anthropic_trace() -> None:
    trace = parse_trace_file(ROOT / "sample_traces" / "anthropic_agent.json")
    assert trace.source == "anthropic"
    # 1 user prompt + 3 assistant completions + 2 tool_use + 2 tool_result
    assert len(trace.steps) == 8

    types = [s.type.value for s in trace.steps]
    assert types.count("prompt") == 1
    assert types.count("completion") == 3
    assert types.count("tool_call") == 2
    assert types.count("tool_result") == 2

    tool_calls = [s for s in trace.steps if s.type.value == "tool_call"]
    assert tool_calls[0].name == "github_list_workflow_runs"
    assert tool_calls[1].name == "github_get_run_logs"

    completions = [s for s in trace.steps if s.type.value == "completion"]
    assert completions[0].tokens_in == 920
    assert completions[0].tokens_out == 140
    assert completions[0].model == "claude-sonnet-4-5"


def test_anthropic_detection_via_claude_model() -> None:
    """A messages payload with a Claude model should be detected even without content blocks."""
    from steplight.core.parser import detect_source

    payload = {
        "model": "claude-opus-4-6",
        "messages": [{"role": "user", "content": "hello"}],
    }
    assert detect_source(payload) == "anthropic"


def test_anthropic_detection_via_content_blocks() -> None:
    """A payload with tool_use content blocks should be detected as Anthropic."""
    from steplight.core.parser import detect_source

    payload = {
        "messages": [
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "t1", "name": "x", "input": {}},
                ],
            }
        ]
    }
    assert detect_source(payload) == "anthropic"


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
