from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)

    normalized = str(value).replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def compact_text(value: Any, *, limit: int = 240, keep_empty: bool = False) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip()
    else:
        text = str(value).strip()
    if not text:
        return "" if keep_empty else None
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
