from __future__ import annotations

from datetime import timedelta
from typing import Any

from steplight.adapters.common import compact_text, parse_dt
from steplight.core.models import Step, StepType, Trace


TYPE_MAP = {
    "message_creation": StepType.COMPLETION,
    "message": StepType.COMPLETION,
    "tool_calls": StepType.TOOL_CALL,
    "tool_call": StepType.TOOL_CALL,
    "tool_result": StepType.TOOL_RESULT,
    "response.error": StepType.ERROR,
    "response.created": StepType.CHAIN_START,
    "response.completed": StepType.CHAIN_END,
}


def parse_openai_trace(payload: dict[str, Any]) -> Trace:
    raw_steps = payload.get("steps", [])
    steps: list[Step] = []

    for index, raw_step in enumerate(raw_steps):
        step_type = TYPE_MAP.get(raw_step.get("type"), StepType.COMPLETION)
        timestamp = parse_dt(raw_step.get("created_at") or raw_step.get("timestamp") or payload.get("created_at"))

        if step_type == StepType.TOOL_CALL and raw_step.get("tool_calls"):
            for tool_index, tool_call in enumerate(raw_step["tool_calls"], start=1):
                function = tool_call.get("function", {})
                steps.append(
                    Step(
                        id=f"{payload.get('id', 'trace')}:tool:{index}:{tool_index}",
                        type=StepType.TOOL_CALL,
                        name=function.get("name") or tool_call.get("name") or "tool_call",
                        timestamp=timestamp,
                        input=compact_text(function.get("arguments") or tool_call.get("arguments")),
                        duration_ms=_extract_duration_ms(tool_call) or _extract_duration_ms(raw_step),
                        metadata={"raw": tool_call},
                    )
                )
            continue

        usage = raw_step.get("usage", {})
        output = raw_step.get("output")
        if output is None and raw_step.get("message"):
            output = raw_step["message"].get("content")

        step = Step(
            id=str(raw_step.get("id") or f"{payload.get('id', 'trace')}:step:{index}"),
            type=step_type,
            name=raw_step.get("name") or raw_step.get("type"),
            timestamp=timestamp,
            duration_ms=_extract_duration_ms(raw_step),
            input=compact_text(raw_step.get("input")),
            output=compact_text(output, keep_empty=True),
            model=raw_step.get("model") or payload.get("model"),
            tokens_in=usage.get("prompt_tokens") or raw_step.get("prompt_tokens"),
            tokens_out=usage.get("completion_tokens") or raw_step.get("completion_tokens"),
            error=compact_text(raw_step.get("error")),
            metadata={"raw": raw_step},
        )
        steps.append(step)

    started_at = parse_dt(payload.get("created_at") or (steps[0].timestamp if steps else None))
    ended_at = parse_dt(payload.get("completed_at")) if payload.get("completed_at") else _infer_ended_at(steps)

    return Trace(
        id=str(payload.get("id") or "openai-trace"),
        name=payload.get("name"),
        started_at=started_at,
        ended_at=ended_at,
        steps=steps,
        total_tokens=payload.get("usage", {}).get("total_tokens"),
        total_cost_usd=payload.get("cost_usd"),
        source="openai",
        status=payload.get("status"),
        metadata={"raw": payload},
    )


def _extract_duration_ms(raw_step: dict[str, Any]) -> float | None:
    if "duration_ms" in raw_step and raw_step["duration_ms"] is not None:
        return float(raw_step["duration_ms"])
    if "latency_ms" in raw_step and raw_step["latency_ms"] is not None:
        return float(raw_step["latency_ms"])
    if raw_step.get("started_at") and raw_step.get("ended_at"):
        start = parse_dt(raw_step["started_at"])
        end = parse_dt(raw_step["ended_at"])
        return max((end - start).total_seconds() * 1000, 0.0)
    return None


def _infer_ended_at(steps: list[Step]):
    if not steps:
        return None
    latest = max(steps, key=lambda item: item.timestamp)
    if latest.duration_ms:
        return latest.timestamp + timedelta(milliseconds=latest.duration_ms)
    return latest.timestamp
