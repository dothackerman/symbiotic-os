"""BusClient — thin facade over schema + db."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .db import init_db, insert_event, poll_events
from .schema import Event, build_event, verify_event


class BusClient:
    """High-level client for publishing to and consuming from the event bus.

    Usage::

        client = BusClient()
        event = client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "abc123", "segment_count": 42},
            actor_id="yt-transcriber",
        )
        events = client.consume(after_id=None, event_type="transcript.indexed")
        assert client.verify(events[0])
    """

    def __init__(self, db_path: Path | None = None, key: bytes | None = None):
        self._key = key  # None → loaded lazily from secrets/bus.key
        self._conn = init_db(db_path)

    # ------------------------------------------------------------------
    # Write side
    # ------------------------------------------------------------------

    def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
        actor_type: str = "system",
        actor_id: str = "yt-transcriber",
        model_id: str = "none",
        session_id: str = "none",
    ) -> Event:
        """Build, sign, persist, and return a new event."""
        event = build_event(
            event_type=event_type,
            payload=payload,
            actor_type=actor_type,
            actor_id=actor_id,
            model_id=model_id,
            session_id=session_id,
            key=self._key,
        )
        insert_event(event, self._conn)
        return event

    # ------------------------------------------------------------------
    # Read side
    # ------------------------------------------------------------------

    def consume(
        self,
        after_id: str | None = None,
        event_type: str | None = None,
    ) -> list[Event]:
        """Return events from the bus, optionally filtered."""
        return poll_events(self._conn, after_id=after_id, event_type=event_type)

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(self, event: Event) -> bool:
        """Return True iff the event envelope signature is valid."""
        return verify_event(event, key=self._key)
