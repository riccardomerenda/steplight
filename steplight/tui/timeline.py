from __future__ import annotations

from textual.widgets import Label, ListItem, ListView

from steplight.core.models import Step, Trace


def _step_line(step: Step) -> str:
    duration = f" | {step.duration_ms:.0f}ms" if step.duration_ms is not None else ""
    name = step.name or step.type.value
    return f"{step.type.value:<12} {name}{duration}"


class StepListItem(ListItem):
    def __init__(self, step: Step, index: int) -> None:
        self.step = step
        self.step_index = index
        super().__init__(Label(_step_line(step)))


class TimelineList(ListView):
    def load_trace(self, trace: Trace) -> None:
        self.clear()
        for index, step in enumerate(trace.steps):
            self.append(StepListItem(step, index))
