from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


class RuntimeConfig(BaseModel):
    """Runtime configuration used by CLI commands."""

    source: str | None = None
    generic_config: Path | None = None
    high_cost_threshold_usd: float = Field(default=0.10, ge=0.0)


def discover_generic_config(trace_path: Path, explicit: Path | None = None) -> Path | None:
    """Find a steplight.yaml config near the trace unless a path was provided."""

    if explicit:
        return explicit

    candidates = [
        trace_path.parent / "steplight.yaml",
        Path.cwd() / "steplight.yaml",
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None
