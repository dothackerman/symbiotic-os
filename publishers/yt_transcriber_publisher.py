#!/usr/bin/env python3
"""Publisher: yt-transcriber → transcript.indexed.

Emits one signed event to the local SQLite bus. Run directly or import
publish_transcript() from other code.

Usage:
    python publishers/yt_transcriber_publisher.py [--youtube-id ID] [--segments N]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow running from project root without installing
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bus import BusClient  # noqa: E402


def publish_transcript(
    youtube_id: str = "MssPse4Fxa0",
    segment_count: int = 700,
    session_id: str = "none",
) -> None:
    """Publish a transcript.indexed event to the bus."""
    client = BusClient()
    event = client.publish(
        event_type="transcript.indexed",
        payload={
            "youtube_id": youtube_id,
            "segment_count": segment_count,
        },
        actor_type="system",
        actor_id="yt-transcriber",
        session_id=session_id,
    )
    print(f"[publisher] emitted event {event.id}")
    print(f"[publisher] event_type={event.event_type}")
    print(f"[publisher] payload={event.payload_json}")
    print(f"[publisher] signature={event.signature[:16]}...")
    return event


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Emit a transcript.indexed event")
    parser.add_argument("--youtube-id", default="MssPse4Fxa0", help="YouTube video ID")
    parser.add_argument("--segments", type=int, default=700, help="Segment count")
    parser.add_argument("--session-id", default="none", help="OpenClaw session ID")
    args = parser.parse_args()

    publish_transcript(
        youtube_id=args.youtube_id,
        segment_count=args.segments,
        session_id=args.session_id,
    )
