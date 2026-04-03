from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from steplight.cli.config import RuntimeConfig, discover_generic_config
from steplight.core.analyzer import AnalyzerConfig, analyze_trace
from steplight.core.parser import SUPPORTED_SOURCES, parse_trace_file
from steplight.core.stats import compute_trace_stats, find_bottleneck
from steplight.export.html import export_trace_html

app = typer.Typer(
    help="Local-first trace inspector for LLM agents and tool-driven workflows.",
    pretty_exceptions_enable=False,
)
console = Console()


def _runtime_config(
    file: Path,
    source: str | None,
    config_path: Path | None,
    high_cost_threshold_usd: float,
) -> RuntimeConfig:
    return RuntimeConfig(
        source=source,
        generic_config=discover_generic_config(file, config_path),
        high_cost_threshold_usd=high_cost_threshold_usd,
    )


def _load_trace(file: Path, runtime_config: RuntimeConfig):
    try:
        return parse_trace_file(file, source=runtime_config.source, config_path=runtime_config.generic_config)
    except (FileNotFoundError, OSError, ValueError, TypeError, KeyError, ValidationError) as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc


def _diagnostics_config(runtime_config: RuntimeConfig) -> AnalyzerConfig:
    return AnalyzerConfig(high_cost_threshold_usd=runtime_config.high_cost_threshold_usd)


@app.command()
def inspect(
    file: Annotated[Path, typer.Argument(exists=True, readable=True, resolve_path=True)],
    source: Annotated[str | None, typer.Option(help="Force a parser source.")] = None,
    config: Annotated[Path | None, typer.Option(help="Optional steplight.yaml mapping file.")] = None,
    high_cost_threshold_usd: Annotated[float, typer.Option(help="High-cost diagnostic threshold in USD.")] = 0.10,
) -> None:
    """Open the interactive TUI inspector."""

    runtime_config = _runtime_config(file, source, config, high_cost_threshold_usd)
    trace = _load_trace(file, runtime_config)
    diagnostics = analyze_trace(trace, _diagnostics_config(runtime_config))

    try:
        from steplight.tui.app import run_trace_app
    except ModuleNotFoundError as exc:
        if exc.name == "textual":
            console.print(
                "`slt inspect` requires the optional `textual` dependency. "
                "Install project dependencies to use the TUI."
            )
            raise typer.Exit(code=1) from exc
        raise

    run_trace_app(trace, diagnostics)


@app.command()
def summary(
    file: Annotated[Path, typer.Argument(exists=True, readable=True, resolve_path=True)],
    source: Annotated[str | None, typer.Option(help="Force a parser source.")] = None,
    config: Annotated[Path | None, typer.Option(help="Optional steplight.yaml mapping file.")] = None,
    high_cost_threshold_usd: Annotated[float, typer.Option(help="High-cost diagnostic threshold in USD.")] = 0.10,
) -> None:
    """Print a non-interactive summary."""

    runtime_config = _runtime_config(file, source, config, high_cost_threshold_usd)
    trace = _load_trace(file, runtime_config)
    stats = compute_trace_stats(trace)
    diagnostics = analyze_trace(trace, _diagnostics_config(runtime_config))
    bottleneck = find_bottleneck(trace)

    lines = [
        f"[bold]Run:[/bold] {trace.name or trace.id}",
        f"[bold]Source:[/bold] {trace.source or 'unknown'}",
        (
            "[bold]Overview:[/bold] "
            f"Duration: {stats.duration_ms / 1000:.1f}s | Steps: {stats.step_count} | "
            f"Tool calls: {stats.tool_calls} | Retries: {stats.retries}"
        ),
        (
            "[bold]Tokens:[/bold] "
            f"{stats.tokens_in:,} in / {stats.tokens_out:,} out | Est. cost: {_format_cost(stats.total_cost_usd)}"
        ),
    ]
    console.print(Panel("\n".join(lines), title="Steplight Summary", expand=False))

    highlights: list[str] = []
    if bottleneck and bottleneck.percentage > 0.5:
        highlights.append(f"Bottleneck: {bottleneck.name} ({bottleneck.percentage * 100:.1f}% of total runtime)")
    if diagnostics:
        console.print()
        console.print("[bold]Diagnostics[/bold]")
        for diagnostic in diagnostics:
            severity_style = {
                "ERROR": "red",
                "WARNING": "yellow",
                "INFO": "cyan",
            }[diagnostic.severity.value.upper()]
            label = Text(diagnostic.severity.value.upper(), style=severity_style)
            console.print(Text.assemble("- ", label, ": ", diagnostic.message))
    else:
        console.print("No diagnostics fired.")

    for line in highlights:
        console.print(line)


@app.command()
def export(
    file: Annotated[Path, typer.Argument(exists=True, readable=True, resolve_path=True)],
    output: Annotated[Path, typer.Option("--output", "-o", help="Path to the HTML report.", resolve_path=True)],
    source: Annotated[str | None, typer.Option(help="Force a parser source.")] = None,
    config: Annotated[Path | None, typer.Option(help="Optional steplight.yaml mapping file.")] = None,
    high_cost_threshold_usd: Annotated[float, typer.Option(help="High-cost diagnostic threshold in USD.")] = 0.10,
) -> None:
    """Export a static HTML report."""

    runtime_config = _runtime_config(file, source, config, high_cost_threshold_usd)
    trace = _load_trace(file, runtime_config)
    report_path = export_trace_html(trace, output, analyzer_config=_diagnostics_config(runtime_config))
    console.print(f"Exported report to {report_path}")


@app.command()
def validate(
    file: Annotated[Path, typer.Argument(exists=True, readable=True, resolve_path=True)],
    source: Annotated[str | None, typer.Option(help=f"Optional source override: {', '.join(sorted(SUPPORTED_SOURCES))}.")] = None,
    config: Annotated[Path | None, typer.Option(help="Optional steplight.yaml mapping file.")] = None,
) -> None:
    """Validate that a trace is parseable."""

    runtime_config = _runtime_config(file, source, config, 0.10)
    trace = _load_trace(file, runtime_config)
    console.print(
        f"Valid trace: {trace.id} ({len(trace.steps)} steps, source={trace.source or runtime_config.source or 'unknown'})"
    )


def _format_cost(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"${value:.4f}"


if __name__ == "__main__":
    app()
