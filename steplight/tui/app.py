from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Footer, Header, Static

from steplight.core.models import Diagnostic, Trace
from steplight.core.stats import compute_trace_stats
from steplight.tui.detail_panel import DetailPanel
from steplight.tui.diagnostics import DiagnosticsPanel
from steplight.tui.timeline import StepListItem, TimelineList


class SteplightApp(App[None]):
    CSS = """
    Screen {
        background: #f3efe8;
        color: #1f1c19;
    }

    #main {
        height: 1fr;
    }

    #timeline {
        width: 42%;
        border: round #c76d3a;
        padding: 1;
        background: #fff9f3;
    }

    #detail {
        width: 58%;
        border: round #b89d82;
        padding: 1;
        background: #fffdf8;
    }

    #diagnostics {
        height: 10;
        border: round #7a6756;
        padding: 1;
        margin-top: 1;
        background: #fffdf8;
    }

    #summary {
        height: auto;
        padding: 0 1;
    }
    """

    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, trace: Trace, diagnostics: list[Diagnostic]) -> None:
        super().__init__()
        self.trace = trace
        self.trace_diagnostics = diagnostics

    def compose(self) -> ComposeResult:
        stats = compute_trace_stats(self.trace)
        yield Header(show_clock=True)
        yield Static(
            (
                f"{self.trace.name or self.trace.id} | source={self.trace.source or 'unknown'} | "
                f"{stats.step_count} steps | {stats.duration_ms / 1000:.2f}s"
            ),
            id="summary",
        )
        with Horizontal(id="main"):
            yield TimelineList(id="timeline")
            with Vertical(id="detail"):
                yield DetailPanel()
        yield DiagnosticsPanel(id="diagnostics")
        yield Footer()

    def on_mount(self) -> None:
        timeline = self.query_one(TimelineList)
        timeline.load_trace(self.trace)
        if self.trace.steps:
            timeline.index = 0
            self._show_step(self.trace.steps[0])
        self.query_one(DiagnosticsPanel).show_diagnostics(self.trace_diagnostics)

    def on_list_view_highlighted(self, event: TimelineList.Highlighted) -> None:
        if isinstance(event.item, StepListItem):
            self._show_step(event.item.step)

    def _show_step(self, step) -> None:
        self.query_one(DetailPanel).show_step(step)


def run_trace_app(trace: Trace, diagnostics: list[Diagnostic]) -> None:
    app = SteplightApp(trace, diagnostics)
    app.run()
