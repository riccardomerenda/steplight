from __future__ import annotations

from rich.panel import Panel
from rich.table import Table
from textual.widgets import Static

from steplight.core.models import Step


class DetailPanel(Static):
    def show_step(self, step: Step | None) -> None:
        if step is None:
            self.update("No step selected.")
            return

        table = Table.grid(padding=(0, 1))
        table.add_column(style="bold")
        table.add_column()
        table.add_row("Type", step.type.value)
        table.add_row("Name", step.name or "-")
        table.add_row("Timestamp", step.timestamp.isoformat())
        table.add_row("Duration", f"{step.duration_ms:.0f}ms" if step.duration_ms is not None else "-")
        table.add_row("Model", step.model or "-")
        table.add_row("Tokens", f"{step.tokens_in or 0} in / {step.tokens_out or 0} out")
        table.add_row("Input", step.input or "-")
        table.add_row("Output", step.output or "-")
        table.add_row("Error", step.error or "-")
        self.update(Panel(table, title="Step Details"))
