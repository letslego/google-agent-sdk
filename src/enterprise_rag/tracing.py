from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json
import uuid


TRACE_LOG_PATH = Path("logs/traces.jsonl")


def append_trace(entry: dict) -> dict:
    TRACE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "trace_id": str(uuid.uuid4()),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        **entry,
    }
    with TRACE_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload) + "\n")
    return payload


def read_traces(limit: int = 200) -> list[dict]:
    if not TRACE_LOG_PATH.exists():
        return []

    lines = TRACE_LOG_PATH.read_text(encoding="utf-8").strip().splitlines()
    if not lines:
        return []

    records = [json.loads(line) for line in lines if line.strip()]
    return list(reversed(records[-limit:]))

