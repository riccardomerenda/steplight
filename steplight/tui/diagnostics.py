from __future__ import annotations

from textual.widgets import Static

from steplight.core.models import Diagnostic


class DiagnosticsPanel(Static):
    def show_diagnostics(self, diagnostics: list[Diagnostic]) -> None:
        if not diagnostics:
            self.update("Diagnostics\n\nNo diagnostics fired for this trace.")
            return

        lines = ["Diagnostics", ""]
        for diagnostic in diagnostics:
            lines.append(f"[{diagnostic.severity.value}] {diagnostic.message}")
        self.update("\n".join(lines))
