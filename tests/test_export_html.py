from datetime import datetime, timezone
from pathlib import Path

from steplight.core.models import Step, StepType, Trace
from steplight.export.html import export_trace_html


ROOT = Path(__file__).resolve().parents[1]


def test_zero_duration_steps_are_visible_in_export() -> None:
    timestamp = datetime(2025, 1, 1, tzinfo=timezone.utc)
    trace = Trace(
        id="zero-duration",
        started_at=timestamp,
        ended_at=timestamp,
        source="generic",
        steps=[
            Step(
                id="s1",
                type=StepType.TOOL_CALL,
                name="instant_tool",
                timestamp=timestamp,
                duration_ms=0.0,
            )
        ],
    )

    output = ROOT / "zero-duration-test.html"
    export_trace_html(trace, output)
    html = output.read_text(encoding="utf-8")

    assert "Duration Waterfall" in html
    assert "0ms" in html
    assert "instant_tool" in html
    output.unlink(missing_ok=True)


def test_empty_outputs_are_rendered_explicitly() -> None:
    timestamp = datetime(2025, 1, 1, tzinfo=timezone.utc)
    trace = Trace(
        id="empty-output",
        started_at=timestamp,
        ended_at=timestamp,
        source="generic",
        steps=[
            Step(
                id="s1",
                type=StepType.COMPLETION,
                name="empty_completion",
                timestamp=timestamp,
                output="",
            )
        ],
    )

    output = ROOT / "empty-output-test.html"
    export_trace_html(trace, output)
    html = output.read_text(encoding="utf-8")

    assert "Output" in html
    assert "(empty output)" in html
    output.unlink(missing_ok=True)
