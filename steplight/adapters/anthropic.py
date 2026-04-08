"""Adapter for Anthropic Messages API conversation traces.

Parses traces produced by `anthropic.messages.create()` and similar SDK calls.
The expected payload shape is a conversation history:

    {
      "id": "conv_01",
      "name": "...",
      "model": "claude-opus-4-5",
      "created_at": "...",
      "completed_at": "...",
      "messages": [
        {"role": "user", "content": "..."},
        {
          "role": "assistant",
          "id": "msg_01",
          "model": "claude-opus-4-5",
          "created_at": "...",
          "duration_ms": 1200,
          "content": [
            {"type": "text", "text": "..."},
            {"type": "tool_use", "id": "toolu_01", "name": "calculator",
             "input": {"a": 1}}
          ],
          "stop_reason": "tool_use",
          "usage": {"input_tokens": 100, "output_tokens": 50}
        },
        {
          "role": "user",
          "content": [
            {"type": "tool_result", "tool_use_id": "toolu_01",
             "content": "42", "is_error": false}
          ]
        }
      ]
    }
"""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from steplight.adapters.common import compact_text, parse_dt
from steplight.core.models import Step, StepType, Trace


def parse_anthropic_trace(payload: dict[str, Any]) -> Trace:
    raw_messages = payload.get("messages") or []
    trace_id = str(payload.get("id") or "anthropic-trace")
    default_model = payload.get("model")
    steps: list[Step] = []

    for index, message in enumerate(raw_messages):
        if not isinstance(message, dict):
            continue
        role = (message.get("role") or "").lower()
        timestamp = parse_dt(message.get("created_at") or message.get("timestamp") or payload.get("created_at"))
        message_id = str(message.get("id") or f"{trace_id}:msg:{index}")
        duration_ms = _extract_duration_ms(message)
        usage = message.get("usage") or {}
        tokens_in = usage.get("input_tokens")
        tokens_out = usage.get("output_tokens")
        model = message.get("model") or default_model
        stop_reason = message.get("stop_reason")
        error = compact_text(message.get("error"))

        content = message.get("content")
        text_blocks, tool_use_blocks, tool_result_blocks = _split_content(content)

        if role == "user":
            if tool_result_blocks:
                for tr_index, block in enumerate(tool_result_blocks, start=1):
                    is_error = bool(block.get("is_error"))
                    steps.append(
                        Step(
                            id=f"{message_id}:tool_result:{tr_index}",
                            type=StepType.TOOL_RESULT,
                            name=block.get("tool_use_id") or "tool_result",
                            timestamp=timestamp,
                            output=compact_text(_block_text(block.get("content"))),
                            error=compact_text(_block_text(block.get("content"))) if is_error else None,
                            metadata={
                                "raw": block,
                                "tool_use_id": block.get("tool_use_id"),
                                "is_error": is_error,
                            },
                        )
                    )
            else:
                steps.append(
                    Step(
                        id=message_id,
                        type=StepType.PROMPT,
                        name=message.get("name") or "user",
                        timestamp=timestamp,
                        input=compact_text(_block_text(content)),
                        metadata={"raw": message},
                    )
                )
            continue

        if role == "assistant":
            if text_blocks:
                steps.append(
                    Step(
                        id=message_id,
                        type=StepType.ERROR if error else StepType.COMPLETION,
                        name=message.get("name") or "assistant",
                        timestamp=timestamp,
                        duration_ms=duration_ms,
                        output=compact_text("\n".join(text_blocks), keep_empty=True),
                        model=model,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        error=error,
                        metadata={
                            "raw": message,
                            "stop_reason": stop_reason,
                        },
                    )
                )
            elif not tool_use_blocks and not error:
                steps.append(
                    Step(
                        id=message_id,
                        type=StepType.COMPLETION,
                        name=message.get("name") or "assistant",
                        timestamp=timestamp,
                        duration_ms=duration_ms,
                        output=compact_text(_block_text(content), keep_empty=True),
                        model=model,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        metadata={"raw": message, "stop_reason": stop_reason},
                    )
                )

            for tu_index, block in enumerate(tool_use_blocks, start=1):
                steps.append(
                    Step(
                        id=f"{message_id}:tool_use:{tu_index}",
                        type=StepType.TOOL_CALL,
                        name=block.get("name") or "tool_use",
                        timestamp=timestamp,
                        input=compact_text(block.get("input")),
                        model=model,
                        metadata={
                            "raw": block,
                            "tool_use_id": block.get("id"),
                        },
                    )
                )

            if error and not text_blocks:
                steps.append(
                    Step(
                        id=f"{message_id}:error",
                        type=StepType.ERROR,
                        name=message.get("name") or "assistant_error",
                        timestamp=timestamp,
                        duration_ms=duration_ms,
                        error=error,
                        model=model,
                        metadata={"raw": message},
                    )
                )

    started_at = parse_dt(payload.get("created_at") or (steps[0].timestamp if steps else None))
    if payload.get("completed_at"):
        ended_at = parse_dt(payload["completed_at"])
    else:
        ended_at = _infer_ended_at(steps)

    total_tokens = payload.get("total_tokens")
    if total_tokens is None:
        total_in = sum(s.tokens_in or 0 for s in steps)
        total_out = sum(s.tokens_out or 0 for s in steps)
        total_tokens = (total_in + total_out) or None

    return Trace(
        id=trace_id,
        name=payload.get("name"),
        started_at=started_at,
        ended_at=ended_at,
        steps=steps,
        total_tokens=total_tokens,
        total_cost_usd=payload.get("total_cost_usd") or payload.get("cost_usd"),
        source="anthropic",
        status=payload.get("status"),
        metadata={"raw": payload},
    )


def _split_content(content: Any) -> tuple[list[str], list[dict], list[dict]]:
    """Split Anthropic content into text strings, tool_use blocks, tool_result blocks."""
    text_blocks: list[str] = []
    tool_use_blocks: list[dict] = []
    tool_result_blocks: list[dict] = []

    if content is None:
        return text_blocks, tool_use_blocks, tool_result_blocks
    if isinstance(content, str):
        text_blocks.append(content)
        return text_blocks, tool_use_blocks, tool_result_blocks
    if not isinstance(content, list):
        return text_blocks, tool_use_blocks, tool_result_blocks

    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == "text":
            text = block.get("text")
            if text:
                text_blocks.append(text)
        elif block_type == "tool_use":
            tool_use_blocks.append(block)
        elif block_type == "tool_result":
            tool_result_blocks.append(block)

    return text_blocks, tool_use_blocks, tool_result_blocks


def _block_text(content: Any) -> str | None:
    """Extract a flat text representation from a content block or value."""
    if content is None:
        return None
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and item.get("text"):
                    parts.append(item["text"])
                elif "text" in item and item["text"]:
                    parts.append(str(item["text"]))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts) if parts else None
    return str(content)


def _extract_duration_ms(message: dict[str, Any]) -> float | None:
    if message.get("duration_ms") is not None:
        return float(message["duration_ms"])
    if message.get("latency_ms") is not None:
        return float(message["latency_ms"])
    if message.get("started_at") and message.get("ended_at"):
        start = parse_dt(message["started_at"])
        end = parse_dt(message["ended_at"])
        return max((end - start).total_seconds() * 1000, 0.0)
    return None


def _infer_ended_at(steps: list[Step]):
    if not steps:
        return None
    latest = max(steps, key=lambda item: item.timestamp)
    if latest.duration_ms:
        return latest.timestamp + timedelta(milliseconds=latest.duration_ms)
    return latest.timestamp
