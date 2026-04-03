from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.widgets import RichLog

from steplight.core.models import Step, StepType

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


class DetailPanel(RichLog):
    def __init__(self, **kwargs) -> None:
        super().__init__(wrap=True, markup=False, **kwargs)

    def show_step(self, step: Step | None) -> None:
        self.clear()
        if step is None:
            self.write("No step selected.")
            return

        color = _STEP_COLORS.get(step.type, "white")

        table = Table.grid(padding=(0, 1))
        table.add_column(style="bold #4a3f35")
        table.add_column(style="#1f1c19")
        table.add_row("Type", Text(step.type.value, style=f"bold {color}"))
        table.add_row("Name", step.name or "-")
        table.add_row("Timestamp", step.timestamp.isoformat())
        table.add_row("Duration", f"{step.duration_ms:.0f}ms" if step.duration_ms is not None else "-")
        table.add_row("Model", step.model or "-")
        table.add_row("Tokens", f"{step.tokens_in or 0} in / {step.tokens_out or 0} out")
        if step.metadata.get("cost_usd") is not None:
            table.add_row("Cost", f"${step.metadata['cost_usd']:.6f}")
        table.add_row("Input", step.input or "-")
        table.add_row("Output", step.output or "-")
        if step.error:
            table.add_row("Error", Text(step.error, style="bold red"))
        self.write(Panel(table, title="Step Details"))
