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
