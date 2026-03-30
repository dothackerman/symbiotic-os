#!/usr/bin/env python3
"""Subscriber: polls bus for all events → appends to heartbeat-state.json.

Each event becomes one entry in the `bus_events` array:
    {
        "timestamp": "<ISO-8601>",
        "event_id": "<uuid>",
        "event_type": "<str>",
        "actor_id": "<str>"
    }

heartbeat-state.json target path defaults to:
    ~/.openclaw/workspace/memory/heartbeat-state.json
Override with env var HEARTBEAT_STATE_PATH.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bus import BusClient  # noqa: E402

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "2"))
_STATE_DIR = Path(__file__).resolve().parent.parent / "state"


def _heartbeat_state_path() -> Path:
    return Path(
        os.environ.get(
            "HEARTBEAT_STATE_PATH",
            Path.home() / ".openclaw" / "workspace" / "memory" / "heartbeat-state.json",
        )
    )


def _cursor_file() -> Path:
    return _STATE_DIR / "audit_logger_cursor.txt"


def _load_cursor() -> str | None:
    f = _cursor_file()
    if f.exists():
        return f.read_text().strip() or None
    return None


def _save_cursor(event_id: str) -> None:
    f = _cursor_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(event_id)


def append_to_heartbeat_state(event) -> None:
    """Append one entry to the bus_events array in heartbeat-state.json."""
    HEARTBEAT_STATE_PATH = _heartbeat_state_path()
    # Load existing state (or start fresh)
    if HEARTBEAT_STATE_PATH.exists():
        try:
            state = json.loads(HEARTBEAT_STATE_PATH.read_text())
        except json.JSONDecodeError:
            state = {}
    else:
        state = {}

    if "bus_events" not in state:
        state["bus_events"] = []

    entry = {
        "timestamp": event.timestamp,
        "event_id": event.id,
        "event_type": event.event_type,
        "actor_id": event.actor_id,
    }
    state["bus_events"].append(entry)

    HEARTBEAT_STATE_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    )
    print(f"[audit_logger] appended to heartbeat-state.json: event_id={event.id[:8]}... type={event.event_type}")


def run(run_once: bool = False, db_path: Path | None = None) -> None:
    client = BusClient(db_path=db_path)
    cursor = _load_cursor()
    print(f"[audit_logger] starting (cursor={cursor}, run_once={run_once})")

    while True:
        events = client.consume(after_id=cursor)
        for event in events:
            append_to_heartbeat_state(event)
            cursor = event.id
            _save_cursor(cursor)

        if run_once:
            break
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-once", action="store_true")
    args = parser.parse_args()
    run(run_once=args.run_once)
