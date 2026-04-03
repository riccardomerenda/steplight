from __future__ import annotations

from steplight.adapters.common import compact_text, parse_dt
from steplight.core.models import Step, StepType, Trace


EVENT_MAP = {
    "on_chain_start": StepType.CHAIN_START,
    "on_chain_end": StepType.CHAIN_END,
    "on_chain_error": StepType.ERROR,
    "on_chat_model_start": StepType.PROMPT,
    "on_llm_start": StepType.PROMPT,
    "on_llm_end": StepType.COMPLETION,
    "on_tool_start": StepType.TOOL_CALL,
    "on_tool_end": StepType.TOOL_RESULT,
    "on_retry": StepType.RETRY,
}


def parse_langchain_trace(payload: dict) -> Trace:
    raw_events = payload.get("events") or payload.get("steps") or []
    steps: list[Step] = []

    for index, event in enumerate(raw_events):
        event_name = event.get("event") or event.get("type") or "event"
        step_type = EVENT_MAP.get(event_name, StepType.ERROR if "error" in event_name else StepType.CHAIN_START)
        data = event.get("data") or {}
        step = Step(
            id=str(event.get("id") or f"{payload.get('id', 'langchain')}:event:{index}"),
            type=step_type,
            name=event.get("name") or data.get("name") or event_name,
            timestamp=parse_dt(event.get("time") or event.get("created_at") or event.get("timestamp")),
            duration_ms=_duration_ms(event),
            input=compact_text(data.get("input") or data.get("messages") or event.get("input")),
            output=compact_text(
                data.get("output") if "output" in data else data.get("response") or event.get("output"),
                keep_empty=True,
            ),
            model=data.get("model") or event.get("model"),
            tokens_in=_extract_token(data, "prompt_tokens"),
            tokens_out=_extract_token(data, "completion_tokens"),
            error=compact_text(data.get("error") or event.get("error")),
            metadata={"raw": event},
        )
        steps.append(step)

    started_at = parse_dt(payload.get("started_at") or (steps[0].timestamp if steps else None))
    ended_at = parse_dt(payload.get("ended_at")) if payload.get("ended_at") else _infer_ended_at(steps)

    return Trace(
        id=str(payload.get("id") or payload.get("run_id") or "langchain-trace"),
        name=payload.get("name"),
        started_at=started_at,
        ended_at=ended_at,
        steps=steps,
        total_tokens=payload.get("total_tokens"),
        total_cost_usd=payload.get("total_cost_usd") or payload.get("cost_usd"),
        source="langchain",
        status=payload.get("status"),
        metadata={"raw": payload},
    )


def _duration_ms(event: dict) -> float | None:
    if event.get("duration_ms") is not None:
        return float(event["duration_ms"])
    if event.get("start_time") and event.get("end_time"):
        start = parse_dt(event["start_time"])
        end = parse_dt(event["end_time"])
        return max((end - start).total_seconds() * 1000, 0.0)
    return None


def _extract_token(data: dict, key: str) -> int | None:
    usage = data.get("usage") or data.get("token_usage") or {}
    value = usage.get(key) or data.get(key)
    return int(value) if value is not None else None


def _infer_ended_at(steps: list[Step]):
    if not steps:
        return None
    latest = max(steps, key=lambda item: item.timestamp)
    return latest.timestamp
