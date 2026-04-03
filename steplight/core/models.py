from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class StepType(str, Enum):
    PROMPT = "prompt"
    COMPLETION = "completion"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    RETRY = "retry"
    ERROR = "error"
    CHAIN_START = "chain_start"
    CHAIN_END = "chain_end"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Step(BaseModel):
    id: str
    type: StepType
    timestamp: datetime
    name: str | None = None
    duration_ms: float | None = None
    input: str | None = None
    output: str | None = None
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Trace(BaseModel):
    id: str
    started_at: datetime
    steps: list[Step]
    name: str | None = None
    ended_at: datetime | None = None
    total_tokens: int | None = None
    total_cost_usd: float | None = None
    source: str | None = None
    status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Diagnostic(BaseModel):
    rule: str
    message: str
    severity: Severity = Severity.WARNING
    step_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TraceStats(BaseModel):
    duration_ms: float
    step_count: int
    tool_calls: int
    retries: int
    tokens_in: int
    tokens_out: int
    total_cost_usd: float | None = None
