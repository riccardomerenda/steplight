from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from steplight.adapters.generic import load_mapping, parse_generic_trace
from steplight.adapters.langchain import parse_langchain_trace
from steplight.adapters.mcp import parse_mcp_trace
from steplight.adapters.openai import parse_openai_trace
from steplight.core.models import Trace


SUPPORTED_SOURCES = {"openai", "langchain", "mcp", "generic"}


def parse_trace_file(path: Path, source: str | None = None, config_path: Path | None = None) -> Trace:
    payload = load_payload(path)
    selected_source = source or detect_source(payload, config_path=config_path)

    if selected_source == "openai":
        return parse_openai_trace(payload)
    if selected_source == "langchain":
        return parse_langchain_trace(payload)
    if selected_source == "mcp":
        return parse_mcp_trace(payload)
    if selected_source == "generic":
        mapping = load_mapping(config_path)
        return parse_generic_trace(payload, mapping)

    raise ValueError(f"Unsupported source '{selected_source}'. Expected one of: {', '.join(sorted(SUPPORTED_SOURCES))}.")


def load_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        payload = yaml.safe_load(text)
    else:
        payload = json.loads(text)

    if not isinstance(payload, dict):
        raise ValueError("Trace file must contain a JSON or YAML object.")
    return payload


def detect_source(payload: dict[str, Any], config_path: Path | None = None) -> str:
    if config_path:
        return "generic"

    steps = payload.get("steps")
    if isinstance(steps, list) and steps:
        step_types = {str(step.get("type", "")).lower() for step in steps if isinstance(step, dict)}
        if "message_creation" in step_types or "tool_calls" in step_types:
            return "openai"

    events = payload.get("events")
    if isinstance(events, list) and events:
        event_names = {
            str(event.get("event") or event.get("type") or "").lower()
            for event in events
            if isinstance(event, dict)
        }
        if any(name.startswith("on_") for name in event_names):
            return "langchain"
        if {"tool_call", "tool_result"} & event_names:
            return "mcp"

    if payload.get("entries"):
        return "mcp"

    if steps or events:
        return "generic"

    raise ValueError("Could not detect trace source. Pass --source explicitly or provide a steplight.yaml mapping.")
