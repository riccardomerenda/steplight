from pathlib import Path

from typer.testing import CliRunner

from steplight.core.diff import Delta, compare_traces
from steplight.core.parser import parse_trace_file
from steplight.cli.main import app

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "sample_traces"


def test_delta_positive_change() -> None:
    d = Delta(100.0, 150.0)
    assert d.absolute == 50.0
    assert d.percent == 50.0


def test_delta_negative_change() -> None:
    d = Delta(200.0, 100.0)
    assert d.absolute == -100.0
    assert d.percent == -50.0


def test_delta_zero_base() -> None:
    d = Delta(0.0, 10.0)
    assert d.absolute == 10.0
    assert d.percent is None


def test_compare_same_trace() -> None:
    trace = parse_trace_file(SAMPLE / "agent_with_tools.json")
    result = compare_traces(trace, trace)
    assert result.duration.absolute == 0
    assert result.step_count.absolute == 0
    assert result.tokens_in.absolute == 0
    assert result.step_type_deltas == []
    assert result.base_only_steps == []
    assert result.head_only_steps == []


def test_compare_different_traces() -> None:
    base = parse_trace_file(SAMPLE / "agent_with_tools.json")
    head = parse_trace_file(SAMPLE / "expensive_run.json")
    result = compare_traces(base, head)
    assert result.duration.absolute > 0
    assert result.step_count.new > result.step_count.old
    assert len(result.base_only_steps) > 0
    assert len(result.head_only_steps) > 0


def test_compare_traces_cost_delta() -> None:
    base = parse_trace_file(SAMPLE / "agent_with_tools.json")
    head = parse_trace_file(SAMPLE / "expensive_run.json")
    result = compare_traces(base, head)
    assert result.cost is not None
    assert result.cost.new > result.cost.old


def test_diff_cli_command() -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["diff", str(SAMPLE / "agent_with_tools.json"), str(SAMPLE / "expensive_run.json")],
    )
    assert result.exit_code == 0
    assert "Comparing" in result.output
    assert "Duration" in result.output
    assert "Steps" in result.output


def test_diff_cli_same_file() -> None:
    runner = CliRunner()
    f = str(SAMPLE / "agent_with_tools.json")
    result = runner.invoke(app, ["diff", f, f])
    assert result.exit_code == 0
    assert "Comparing" in result.output
