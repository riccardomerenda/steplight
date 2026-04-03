from __future__ import annotations

from steplight.adapters.common import compact_text, parse_dt
from steplight.core.models import Step, StepType, Trace


EVENT_MAP = {
    "tool_call": StepType.TOOL_CALL,
    "tool_result": StepType.TOOL_RESULT,
    "tool_error": StepType.ERROR,
    "session_start": StepType.CHAIN_START,
    "session_end": StepType.CHAIN_END,
    "retry": StepType.RETRY,
}


def parse_mcp_trace(payload: dict) -> Trace:
    events = payload.get("events") or payload.get("entries") or []
    steps: list[Step] = []

    for index, event in enumerate(events):
        event_type = event.get("type") or event.get("event") or "tool_call"
        step_type = EVENT_MAP.get(event_type, StepType.TOOL_CALL)
        steps.append(
            Step(
                id=str(event.get("id") or f"{payload.get('id', 'mcp')}:event:{index}"),
                type=step_type,
                name=event.get("tool_name") or event.get("name") or event_type,
                timestamp=parse_dt(event.get("timestamp") or event.get("created_at")),
                duration_ms=float(event["duration_ms"]) if event.get("duration_ms") is not None else None,
                input=compact_text(event.get("input") or event.get("arguments")),
                output=compact_text(event.get("output") if "output" in event else event.get("result"), keep_empty=True),
                error=compact_text(event.get("error")),
                metadata={"raw": event},
            )
        )

    started_at = parse_dt(payload.get("started_at") or (steps[0].timestamp if steps else None))
    ended_at = parse_dt(payload.get("ended_at")) if payload.get("ended_at") else _infer_ended_at(steps)

    return Trace(
        id=str(payload.get("id") or "mcp-trace"),
        name=payload.get("name"),
        started_at=started_at,
        ended_at=ended_at,
        steps=steps,
        total_cost_usd=payload.get("total_cost_usd"),
        source="mcp",
        status=payload.get("status"),
        metadata={"raw": payload},
    )


def _infer_ended_at(steps: list[Step]):
    if not steps:
        return None
    latest = max(steps, key=lambda item: item.timestamp)
    return latest.timestamp
