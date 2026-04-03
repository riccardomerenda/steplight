from __future__ import annotations

from typing import TYPE_CHECKING

from textual.command import Hit, Hits, Provider

from steplight.core.models import StepType

if TYPE_CHECKING:
    from steplight.tui.app import SteplightApp


class StepCommands(Provider):
    """Command provider for navigating and filtering trace steps."""

    @property
    def _app(self) -> SteplightApp:
        from steplight.tui.app import SteplightApp

        assert isinstance(self.app, SteplightApp)
        return self.app

    async def search(self, query: str) -> Hits:
        matcher = self.matcher(query)

        # Jump-to-step commands
        for i, step in enumerate(self._app.trace.steps):
            label = f"Go to: {step.name or step.type.value}"
            score = matcher.match(label)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(label),
                    self._make_jump(i),
                    help=f"Step {i + 1} — {step.type.value}",
                )

        # Filter-by-type commands
        types_present = {s.type for s in self._app.trace.steps}
        for step_type in sorted(types_present, key=lambda t: t.value):
            label = f"Filter: show only {step_type.value}"
            score = matcher.match(label)
            if score > 0:
                yield Hit(
                    score,
                    matcher.highlight(label),
                    self._make_filter(step_type),
                    help="Filter timeline by step type",
                )

        # Show all (reset filter)
        label = "Filter: show all steps"
        score = matcher.match(label)
        if score > 0:
            yield Hit(
                score,
                matcher.highlight(label),
                self._reset_filter,
                help="Remove type filter",
            )

        # Toggle diagnostics
        label = "Toggle diagnostics panel"
        score = matcher.match(label)
        if score > 0:
            yield Hit(
                score,
                matcher.highlight(label),
                self._toggle_diagnostics,
                help="Show or hide the diagnostics panel",
            )

    def _make_jump(self, index: int):
        async def jump() -> None:
            from steplight.tui.timeline import TimelineList

            timeline = self._app.query_one(TimelineList)
            timeline.index = index

        return jump

    def _make_filter(self, step_type: StepType):
        async def do_filter() -> None:
            from steplight.tui.timeline import TimelineList

            timeline = self._app.query_one(TimelineList)
            timeline.filter_by_type(step_type)

        return do_filter

    async def _reset_filter(self) -> None:
        from steplight.tui.timeline import TimelineList

        timeline = self._app.query_one(TimelineList)
        timeline.filter_by_type(None)

    async def _toggle_diagnostics(self) -> None:
        from steplight.tui.diagnostics import DiagnosticsPanel

        panel = self._app.query_one(DiagnosticsPanel)
        panel.display = not panel.display
