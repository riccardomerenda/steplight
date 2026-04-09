from __future__ import annotations

import json as json_mod
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from steplight.cli.config import RuntimeConfig, discover_generic_config
from steplight.core.analyzer import AnalyzerConfig, analyze_trace
from steplight.core.diff import Delta, TraceDiff, compare_traces
from steplight.core.models import Severity
from steplight.core.parser import SUPPORTED_SOURCES, parse_trace_file
from steplight.core.stats import compute_tool_breakdown, compute_trace_stats, find_bottleneck
from steplight.export.html import export_trace_html


class OutputFormat(str, Enum):
    RICH = "rich"
    JSON = "json"

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
    format: Annotated[OutputFormat, typer.Option("--format", "-f", help="Output format: rich (default) or json.")] = OutputFormat.RICH,
    fail_on: Annotated[str | None, typer.Option(help="Exit with code 1 if any diagnostic meets or exceeds this severity (info, warning, error).")] = None,
) -> None:
    """Print a non-interactive summary."""

    if fail_on is not None:
        try:
            fail_severity = Severity(fail_on.lower())
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid severity '{fail_on}'. Use: info, warning, or error.")
            raise typer.Exit(code=2)

    runtime_config = _runtime_config(file, source, config, high_cost_threshold_usd)
    trace = _load_trace(file, runtime_config)
    stats = compute_trace_stats(trace)
    diagnostics = analyze_trace(trace, _diagnostics_config(runtime_config))
    bottleneck = find_bottleneck(trace)
    tool_breakdown = compute_tool_breakdown(trace)

    if format == OutputFormat.JSON:
        _print_summary_json(trace, stats, diagnostics, bottleneck, tool_breakdown)
    else:
        _print_summary_rich(trace, stats, diagnostics, bottleneck, tool_breakdown)

    if fail_on is not None:
        _severity_rank = {Severity.INFO: 0, Severity.WARNING: 1, Severity.ERROR: 2}
        threshold = _severity_rank[fail_severity]
        if any(_severity_rank[d.severity] >= threshold for d in diagnostics):
            raise typer.Exit(code=1)


def _print_summary_rich(trace, stats, diagnostics, bottleneck, tool_breakdown) -> None:
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

    if tool_breakdown:
        from rich.table import Table

        console.print()
        table = Table(title="Tool breakdown", expand=False, show_edge=False, pad_edge=False)
        table.add_column("Tool", style="bold")
        table.add_column("Calls", justify="right")
        table.add_column("Total", justify="right")
        table.add_column("Avg", justify="right")
        table.add_column("% runtime", justify="right")
        for tool in tool_breakdown:
            table.add_row(
                tool.name,
                str(tool.count),
                f"{tool.total_duration_ms / 1000:.2f}s",
                f"{tool.avg_duration_ms / 1000:.2f}s",
                f"{tool.pct_of_runtime:.1f}%",
            )
        console.print(table)

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


def _print_summary_json(trace, stats, diagnostics, bottleneck, tool_breakdown) -> None:
    data: dict = {
        "trace_id": trace.id,
        "name": trace.name,
        "source": trace.source or "unknown",
        "stats": {
            "duration_s": round(stats.duration_ms / 1000, 3),
            "step_count": stats.step_count,
            "tool_calls": stats.tool_calls,
            "retries": stats.retries,
            "tokens_in": stats.tokens_in,
            "tokens_out": stats.tokens_out,
            "cost_usd": stats.total_cost_usd,
        },
        "diagnostics": [
            {
                "rule": d.rule,
                "severity": d.severity.value,
                "message": d.message,
                "step_id": d.step_id,
            }
            for d in diagnostics
        ],
        "tool_breakdown": [
            {
                "name": t.name,
                "count": t.count,
                "total_duration_ms": round(t.total_duration_ms, 1),
                "avg_duration_ms": round(t.avg_duration_ms, 1),
                "pct_of_runtime": round(t.pct_of_runtime, 1),
            }
            for t in tool_breakdown
        ],
    }
    if bottleneck and bottleneck.percentage > 0.5:
        data["bottleneck"] = {
            "step_id": bottleneck.step_id,
            "name": bottleneck.name,
            "percentage": round(bottleneck.percentage * 100, 1),
        }
    print(json_mod.dumps(data, indent=2))


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


@app.command()
def diff(
    base: Annotated[Path, typer.Argument(exists=True, readable=True, resolve_path=True, help="Base (before) trace file.")],
    head: Annotated[Path, typer.Argument(exists=True, readable=True, resolve_path=True, help="Head (after) trace file.")],
    source: Annotated[str | None, typer.Option(help="Force a parser source.")] = None,
    config: Annotated[Path | None, typer.Option(help="Optional steplight.yaml mapping file.")] = None,
) -> None:
    """Compare two traces side-by-side."""

    base_rc = _runtime_config(base, source, config, 0.10)
    head_rc = _runtime_config(head, source, config, 0.10)
    base_trace = _load_trace(base, base_rc)
    head_trace = _load_trace(head, head_rc)
    result = compare_traces(base_trace, head_trace)
    _print_diff(result)


def _print_diff(d: TraceDiff) -> None:
    from rich.table import Table

    console.print()
    console.print(f"[bold]Comparing:[/bold] {d.base_name}  [dim]->[/dim]  {d.head_name}")
    console.print()

    table = Table(title="Stats", expand=False, show_edge=False, pad_edge=False)
    table.add_column("Metric", style="bold")
    table.add_column("Base", justify="right")
    table.add_column("Head", justify="right")
    table.add_column("Change", justify="right")

    _WORSE_IF_HIGHER = {"Retries", "Cost", "Tokens in", "Tokens out", "Duration"}

    def _add_row(label: str, delta: Delta, fmt: str = ".0f", suffix: str = "", prefix: str = "") -> None:
        change_val = delta.absolute
        pct = delta.percent
        if change_val == 0:
            style = "dim"
            sign = ""
        elif change_val > 0:
            style = "red" if label in _WORSE_IF_HIGHER else "green"
            sign = "+"
        else:
            style = "green" if label in _WORSE_IF_HIGHER else "red"
            sign = ""
        pct_str = f" ({sign}{pct:.1f}%)" if pct is not None else ""
        table.add_row(
            label,
            f"{prefix}{delta.old:{fmt}}{suffix}",
            f"{prefix}{delta.new:{fmt}}{suffix}",
            Text(f"{sign}{prefix}{abs(change_val):{fmt}}{suffix}{pct_str}" if change_val != 0 else "0", style=style),
        )

    _add_row("Duration", Delta(d.duration.old / 1000, d.duration.new / 1000), ".2f", suffix="s")
    _add_row("Steps", d.step_count, ".0f")
    _add_row("Tool calls", d.tool_calls, ".0f")
    _add_row("Retries", d.retries, ".0f")
    _add_row("Tokens in", d.tokens_in, ",.0f")
    _add_row("Tokens out", d.tokens_out, ",.0f")
    if d.cost is not None:
        _add_row("Cost", d.cost, ".4f", prefix="$")

    console.print(table)

    if d.step_type_deltas:
        console.print()
        console.print("[bold]Step type changes[/bold]")
        for st in d.step_type_deltas:
            diff_val = st.new_count - st.old_count
            sign = "+" if diff_val > 0 else ""
            style = "green" if diff_val > 0 else "red"
            console.print(f"  {st.step_type.value:<14} {st.old_count} -> {st.new_count}  [{style}]{sign}{diff_val}[/{style}]")

    if d.base_only_steps or d.head_only_steps:
        console.print()
        if d.base_only_steps:
            console.print("[bold]Steps only in base:[/bold]")
            for name in d.base_only_steps:
                console.print(f"  [red]- {name}[/red]")
        if d.head_only_steps:
            console.print("[bold]Steps only in head:[/bold]")
            for name in d.head_only_steps:
                console.print(f"  [green]+ {name}[/green]")

    console.print()


def _format_cost(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"${value:.4f}"


if __name__ == "__main__":
    app()
