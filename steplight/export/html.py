from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from steplight.core.analyzer import AnalyzerConfig, analyze_trace
from steplight.core.models import Trace
from steplight.core.stats import compute_trace_stats


def export_trace_html(trace: Trace, output_path: Path, *, analyzer_config: AnalyzerConfig | None = None) -> Path:
    diagnostics = analyze_trace(trace, analyzer_config)
    stats = compute_trace_stats(trace)
    template_dir = Path(__file__).parent / "templates"
    environment = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = environment.get_template("report.html.jinja")
    html = template.render(trace=trace, diagnostics=diagnostics, stats=stats)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
