#!/usr/bin/env python3
"""Subscriber: polls bus for transcript.indexed → appends to WEEK.md.

Runs in a polling loop (every 2 seconds by default). Can also be invoked
once with --run-once for testing.

WEEK.md target path defaults to:
    ~/.openclaw/workspace/WEEK.md
Override with env var WEEK_MD_PATH.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bus import BusClient  # noqa: E402

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

POLL_INTERVAL = float(os.environ.get("POLL_INTERVAL", "2"))
_STATE_DIR = Path(__file__).resolve().parent.parent / "state"


def _week_md_path() -> Path:
    return Path(os.environ.get("WEEK_MD_PATH", Path.home() / ".openclaw" / "workspace" / "WEEK.md"))


def _cursor_file() -> Path:
    return _STATE_DIR / "week_updater_cursor.txt"


def _load_cursor() -> str | None:
    f = _cursor_file()
    if f.exists():
        return f.read_text().strip() or None
    return None


def _save_cursor(event_id: str) -> None:
    f = _cursor_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(event_id)


def _ensure_bus_events_section(content: str) -> str:
    """Ensure WEEK.md has a ## Bus Events section."""
    if "## Bus Events" not in content:
        # Append section at end
        content = content.rstrip() + "\n\n## Bus Events\n"
    return content


def append_to_week_md(youtube_id: str, timestamp: str) -> None:
    """Append one bullet line under ## Bus Events in WEEK.md."""
    week_path = _week_md_path()
    if not week_path.exists():
        print(f"[week_updater] WARNING: WEEK.md not found at {week_path}")
        return

    content = week_path.read_text()
    content = _ensure_bus_events_section(content)

    # Build bullet line
    line = f"- [{timestamp}] transcript.indexed — youtube_id: {youtube_id}\n"

    # Insert after ## Bus Events heading
    lines = content.split("\n")
    insert_at = None
    for i, l in enumerate(lines):
        if l.strip() == "## Bus Events":
            insert_at = i + 1
            break

    if insert_at is None:
        # Fallback: just append
        content += line
    else:
        # Find end of section (next ## heading or EOF)
        end = len(lines)
        for j in range(insert_at, len(lines)):
            if lines[j].startswith("## ") and j > insert_at:
                end = j
                break
        # Insert bullet at end of section
        lines.insert(end, line.rstrip())
        content = "\n".join(lines) + "\n"

    week_path.write_text(content)
    print(f"[week_updater] wrote to WEEK.md: {line.strip()}")


def run(run_once: bool = False, db_path: Path | None = None) -> None:
    client = BusClient(db_path=db_path)
    cursor = _load_cursor()
    print(f"[week_updater] starting (cursor={cursor}, run_once={run_once})")

    while True:
        events = client.consume(after_id=cursor, event_type="transcript.indexed")
        for event in events:
            payload = json.loads(event.payload_json)
            youtube_id = payload.get("youtube_id", "unknown")
            append_to_week_md(youtube_id=youtube_id, timestamp=event.timestamp)
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
