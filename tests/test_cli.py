import json
from pathlib import Path

from typer.testing import CliRunner

from steplight.cli.main import app


ROOT = Path(__file__).resolve().parents[1]
runner = CliRunner()


def test_summary_command() -> None:
    result = runner.invoke(app, ["summary", str(ROOT / "sample_traces" / "agent_with_tools.json")])
    assert result.exit_code == 0
    assert "Steplight Summary" in result.stdout
    assert "Find compliance gaps in policy" in result.stdout


def test_validate_command() -> None:
    result = runner.invoke(app, ["validate", str(ROOT / "sample_traces" / "simple_qa.json")])
    assert result.exit_code == 0
    assert "Valid trace" in result.stdout


def test_export_command() -> None:
    output = ROOT / "report-test.html"
    result = runner.invoke(app, ["export", str(ROOT / "sample_traces" / "expensive_run.json"), "--output", str(output)])
    assert result.exit_code == 0
    assert output.exists()
    output.unlink(missing_ok=True)


def test_export_command_creates_parent_directories() -> None:
    output = ROOT / "artifacts" / "nested" / "report-test.html"
    result = runner.invoke(app, ["export", str(ROOT / "sample_traces" / "expensive_run.json"), "--output", str(output)])
    assert result.exit_code == 0
    assert output.exists()
    output.unlink(missing_ok=True)
    output.parent.rmdir()
    output.parent.parent.rmdir()


def test_validate_command_reports_parse_errors_cleanly() -> None:
    invalid_trace = ROOT / "invalid-trace.json"
    invalid_trace.write_text("{bad json", encoding="utf-8")
    try:
        result = runner.invoke(app, ["validate", str(invalid_trace)])
        assert result.exit_code == 1
        assert "Error:" in result.stdout
    finally:
        invalid_trace.unlink(missing_ok=True)


# --format json tests


def test_summary_format_json() -> None:
    result = runner.invoke(
        app, ["summary", str(ROOT / "sample_traces" / "agent_with_tools.json"), "--format", "json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "trace_id" in data
    assert "stats" in data
    assert data["stats"]["step_count"] > 0
    assert isinstance(data["diagnostics"], list)
    assert isinstance(data["tool_breakdown"], list)
    assert len(data["tool_breakdown"]) == 2
    # Sorted by total_duration_ms descending
    assert data["tool_breakdown"][0]["name"] == "web_search"
    assert data["tool_breakdown"][0]["count"] == 1
    assert data["tool_breakdown"][0]["pct_of_runtime"] > 50


def test_summary_format_json_includes_cost() -> None:
    result = runner.invoke(
        app, ["summary", str(ROOT / "sample_traces" / "expensive_run.json"), "--format", "json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["stats"]["cost_usd"] is not None


def test_summary_format_json_includes_bottleneck() -> None:
    result = runner.invoke(
        app, ["summary", str(ROOT / "sample_traces" / "agent_with_tools.json"), "--format", "json"],
    )
    assert result.exit_code == 0
    data = json.loads(result.output)
    # This trace has a bottleneck (web_search > 50%)
    if "bottleneck" in data:
        assert "name" in data["bottleneck"]
        assert "percentage" in data["bottleneck"]


# --fail-on tests


def test_summary_fail_on_warning_exits_nonzero() -> None:
    """The expensive_run trace triggers high-cost warning, so --fail-on warning should exit 1."""
    result = runner.invoke(
        app, ["summary", str(ROOT / "sample_traces" / "expensive_run.json"), "--fail-on", "warning"],
    )
    assert result.exit_code == 1


def test_summary_fail_on_error_exits_zero_when_no_errors() -> None:
    """agent_with_tools has warnings but no errors, so --fail-on error should exit 0."""
    result = runner.invoke(
        app, ["summary", str(ROOT / "sample_traces" / "agent_with_tools.json"), "--fail-on", "error"],
    )
    assert result.exit_code == 0


def test_summary_fail_on_invalid_severity() -> None:
    result = runner.invoke(
        app, ["summary", str(ROOT / "sample_traces" / "agent_with_tools.json"), "--fail-on", "critical"],
    )
    assert result.exit_code == 2


def test_summary_fail_on_with_json_format() -> None:
    """--fail-on and --format json work together."""
    result = runner.invoke(
        app, [
            "summary", str(ROOT / "sample_traces" / "expensive_run.json"),
            "--format", "json", "--fail-on", "warning",
        ],
    )
    assert result.exit_code == 1
    # JSON output should still be valid even when exit code is non-zero
    data = json.loads(result.output)
    assert len(data["diagnostics"]) > 0
