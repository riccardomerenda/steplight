from __future__ import annotations

from rich.text import Text
from textual.widgets import Static

from steplight.core.models import Diagnostic, Severity

_SEVERITY_STYLES: dict[Severity, str] = {
    Severity.INFO: "bold dodger_blue2",
    Severity.WARNING: "bold dark_orange",
    Severity.ERROR: "bold red",
}


class DiagnosticsPanel(Static):
    def show_diagnostics(self, diagnostics: list[Diagnostic]) -> None:
        if not diagnostics:
            self.update("Diagnostics\n\nNo diagnostics fired for this trace.")
            return

        output = Text()
        output.append("Diagnostics\n\n", style="bold")
        for i, diagnostic in enumerate(diagnostics):
            style = _SEVERITY_STYLES.get(diagnostic.severity, "")
            output.append(f"  {diagnostic.severity.value:<8}", style=style)
            output.append(f" {diagnostic.message}", style="#1f1c19")
            if i < len(diagnostics) - 1:
                output.append("\n")
        self.update(output)
