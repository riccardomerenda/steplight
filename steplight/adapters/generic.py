from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from steplight.adapters.common import compact_text, parse_dt
from steplight.core.models import Step, StepType, Trace


DEFAULT_MAPPING = {
    "steps_path": "$.steps",
    "timestamp_field": "timestamp",
    "type_field": "type",
    "name_field": "name",
    "duration_field": "duration_ms",
    "input_field": "input",
    "output_field": "output",
    "model_field": "model",
    "tokens_in_field": "tokens_in",
    "tokens_out_field": "tokens_out",
    "error_field": "error",
    "metadata_field": "metadata",
    "type_values": {},
}


def load_mapping(config_path: Path | None) -> dict[str, Any]:
    mapping = dict(DEFAULT_MAPPING)
    if not config_path or not config_path.exists():
        return mapping

    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    mapping.update(payload.get("mapping") or {})
    return mapping


def parse_generic_trace(payload: dict[str, Any], mapping: dict[str, Any] | None = None) -> Trace:
    active_mapping = dict(DEFAULT_MAPPING)
    if mapping:
        active_mapping.update(mapping)

    raw_steps = _extract_path(payload, active_mapping["steps_path"])
    if not isinstance(raw_steps, list):
        raise ValueError("Generic mapping did not resolve to a list of steps.")

    steps: list[Step] = []
    type_values = active_mapping.get("type_values") or {}

    for index, raw_step in enumerate(raw_steps):
        if not isinstance(raw_step, dict):
            raise ValueError(f"Generic step at index {index} is not an object.")
        raw_type = _get_field(raw_step, active_mapping["type_field"])
        normalized_type = _normalize_type(raw_type, type_values)
        metadata = _get_field(raw_step, active_mapping["metadata_field"]) or {}
        steps.append(
            Step(
                id=str(raw_step.get("id") or f"{payload.get('id', 'generic')}:step:{index}"),
                type=normalized_type,
                name=_get_field(raw_step, active_mapping["name_field"]),
                timestamp=parse_dt(_get_field(raw_step, active_mapping["timestamp_field"])),
                duration_ms=_maybe_float(_get_field(raw_step, active_mapping["duration_field"])),
                input=compact_text(_get_field(raw_step, active_mapping["input_field"])),
                output=compact_text(_get_field(raw_step, active_mapping["output_field"]), keep_empty=True),
                model=_get_field(raw_step, active_mapping["model_field"]),
                tokens_in=_maybe_int(_get_field(raw_step, active_mapping["tokens_in_field"])),
                tokens_out=_maybe_int(_get_field(raw_step, active_mapping["tokens_out_field"])),
                error=compact_text(_get_field(raw_step, active_mapping["error_field"])),
                metadata=metadata if isinstance(metadata, dict) else {"value": metadata},
            )
        )

    started_at = parse_dt(payload.get("started_at") or (steps[0].timestamp if steps else None))
    ended_at = parse_dt(payload.get("ended_at")) if payload.get("ended_at") else _infer_ended_at(steps)

    return Trace(
        id=str(payload.get("id") or "generic-trace"),
        name=payload.get("name"),
        started_at=started_at,
        ended_at=ended_at,
        steps=steps,
        total_tokens=_maybe_int(payload.get("total_tokens")),
        total_cost_usd=_maybe_float(payload.get("total_cost_usd") or payload.get("cost_usd")),
        source="generic",
        status=payload.get("status"),
        metadata={"raw": payload, "mapping": active_mapping},
    )


def _extract_path(payload: dict[str, Any], json_path: str) -> Any:
    current: Any = payload
    path = json_path.strip()
    if path in {"$", ""}:
        return current
    if path.startswith("$."):
        path = path[2:]
    for part in path.split("."):
        if not part:
            continue
        if "[" in part and part.endswith("]"):
            key, index_text = part[:-1].split("[", maxsplit=1)
            if key:
                current = current[key]
            current = current[int(index_text)]
        else:
            current = current[part]
    return current


def _get_field(item: dict[str, Any], field_name: str | None) -> Any:
    if not field_name:
        return None
    current: Any = item
    for part in str(field_name).split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _normalize_type(raw_type: Any, type_values: dict[str, str]) -> StepType:
    value = str(raw_type or "").strip().lower()
    for normalized, external in type_values.items():
        if value == str(external).strip().lower():
            return StepType(normalized)
    if value in {member.value for member in StepType}:
        return StepType(value)
    if "tool" in value and "result" in value:
        return StepType.TOOL_RESULT
    if "tool" in value:
        return StepType.TOOL_CALL
    if "retry" in value:
        return StepType.RETRY
    if "error" in value:
        return StepType.ERROR
    if "start" in value:
        return StepType.CHAIN_START
    if "end" in value:
        return StepType.CHAIN_END
    return StepType.COMPLETION


def _maybe_int(value: Any) -> int | None:
    return int(value) if value is not None else None


def _maybe_float(value: Any) -> float | None:
    return float(value) if value is not None else None


def _infer_ended_at(steps: list[Step]):
    if not steps:
        return None
    latest = max(steps, key=lambda item: item.timestamp)
    return latest.timestamp
