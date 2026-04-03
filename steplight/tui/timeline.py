from __future__ import annotations

from rich.text import Text
from textual.widgets import Label, ListItem, ListView

from steplight.core.models import Step, StepType, Trace

_STEP_COLORS: dict[StepType, str] = {
    StepType.COMPLETION: "green",
    StepType.PROMPT: "bright_blue",
    StepType.TOOL_CALL: "cyan",
    StepType.TOOL_RESULT: "dark_cyan",
    StepType.RETRY: "yellow",
    StepType.ERROR: "red",
    StepType.CHAIN_START: "magenta",
    StepType.CHAIN_END: "magenta",
}


def _step_line(step: Step, indent: int = 0) -> Text:
    color = _STEP_COLORS.get(step.type, "white")
    duration = f" | {step.duration_ms:.0f}ms" if step.duration_ms is not None else ""
    name = step.name or step.type.value
    prefix = "  " * indent
    line = Text()
    line.append(f"{prefix}{step.type.value:<12} ", style=f"bold {color}")
    line.append(f"{name}{duration}", style="#1f1c19")
    return line


class StepListItem(ListItem):
    def __init__(self, step: Step, index: int, indent: int = 0) -> None:
        self.step = step
        self.step_index = index
        super().__init__(Label(_step_line(step, indent)))


def _compute_indents(steps: list[Step]) -> list[int]:
    """Compute indent level for each step based on chain_start/chain_end nesting."""
    indents: list[int] = []
    depth = 0
    for step in steps:
        if step.type == StepType.CHAIN_END:
            depth = max(depth - 1, 0)
        indents.append(depth)
        if step.type == StepType.CHAIN_START:
            depth += 1
    return indents


class TimelineList(ListView):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._trace: Trace | None = None

    def load_trace(self, trace: Trace) -> None:
        self._trace = trace
        self._populate(trace.steps)

    def filter_by_type(self, step_type: StepType | None) -> None:
        if self._trace is None:
            return
        if step_type is None:
            steps = self._trace.steps
        else:
            steps = [s for s in self._trace.steps if s.type == step_type]
        self._populate(steps)

    def _populate(self, steps: list[Step]) -> None:
        self.clear()
        indents = _compute_indents(steps)
        for index, step in enumerate(steps):
            self.append(StepListItem(step, index, indents[index]))
