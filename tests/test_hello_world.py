"""Test: hello-world vertical slice.

Publishes one transcript.indexed event, verifies:
- DB contains the event
- Signature verifies
- week_updater reacts (WEEK.md updated)
- audit_logger reacts (heartbeat-state.json updated)
- Append-only triggers fire on UPDATE/DELETE
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
import threading
import time
from pathlib import Path

import pytest

# Ensure project root is importable
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bus import BusClient
from bus.schema import build_event, verify_event
import bus.db as bus_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp_dir(tmp_path):
    """A temp directory scoped to one test."""
    return tmp_path


@pytest.fixture()
def bus_key(tmp_dir) -> bytes:
    """Generate a fresh key for each test; inject via env."""
    import secrets as _secrets
    key = _secrets.token_hex(32)
    key_path = tmp_dir / "bus.key"
    key_path.write_text(key)
    os.environ["BUS_KEY"] = key
    yield key.encode()
    del os.environ["BUS_KEY"]


@pytest.fixture()
def db_path(tmp_dir) -> Path:
    return tmp_dir / "bus.db"


@pytest.fixture()
def client(db_path, bus_key) -> BusClient:
    return BusClient(db_path=db_path, key=bus_key)


@pytest.fixture()
def week_md(tmp_dir) -> Path:
    path = tmp_dir / "WEEK.md"
    path.write_text("# WEEK.md — Test\n\n## Indexed transcripts\n- existing item\n")
    os.environ["WEEK_MD_PATH"] = str(path)
    yield path
    del os.environ["WEEK_MD_PATH"]


@pytest.fixture()
def heartbeat_state(tmp_dir) -> Path:
    path = tmp_dir / "heartbeat-state.json"
    path.write_text('{"lastRun": "2026-03-30T00:00:00+00:00"}\n')
    os.environ["HEARTBEAT_STATE_PATH"] = str(path)
    yield path
    del os.environ["HEARTBEAT_STATE_PATH"]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEventSchema:
    def test_build_and_verify(self, bus_key):
        event = build_event(
            event_type="transcript.indexed",
            payload={"youtube_id": "test123", "segment_count": 42},
            key=bus_key,
        )
        assert event.event_type == "transcript.indexed"
        assert verify_event(event, key=bus_key) is True

    def test_tampered_signature_fails(self, bus_key):
        import secrets as _secrets
        event = build_event(
            event_type="transcript.indexed",
            payload={"youtube_id": "test123"},
            key=bus_key,
        )
        # Corrupt the signature
        bad_event = event.__class__(
            **{**event.to_dict(), "signature": _secrets.token_hex(32)}
        )
        assert verify_event(bad_event, key=bus_key) is False

    def test_wrong_key_fails(self, bus_key):
        event = build_event(
            event_type="transcript.indexed",
            payload={"youtube_id": "test123"},
            key=bus_key,
        )
        wrong_key = b"wrong-key-that-is-definitely-not-the-right-one"
        assert verify_event(event, key=wrong_key) is False


class TestBusClient:
    def test_publish_and_consume(self, client):
        event = client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "abc123", "segment_count": 700},
        )
        assert event.id is not None
        assert event.event_type == "transcript.indexed"

        events = client.consume(event_type="transcript.indexed")
        assert len(events) == 1
        assert events[0].id == event.id

    def test_verify_all_stored(self, client):
        client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "abc123"},
        )
        events = client.consume()
        for e in events:
            assert client.verify(e) is True

    def test_consume_after_id(self, client):
        e1 = client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "first"},
        )
        e2 = client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "second"},
        )
        events = client.consume(after_id=e1.id)
        assert len(events) == 1
        assert events[0].id == e2.id


class TestAppendOnly:
    def test_update_raises(self, client):
        event = client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "abc123"},
        )
        # SQLite RAISE(ABORT, ...) raises IntegrityError (not OperationalError)
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="append-only"):
            client._conn.execute(
                "UPDATE events SET event_type = 'tampered' WHERE id = ?",
                (event.id,),
            )

    def test_delete_raises(self, client):
        event = client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "abc123"},
        )
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError), match="append-only"):
            client._conn.execute("DELETE FROM events WHERE id = ?", (event.id,))


class TestWeekUpdater:
    def test_appends_to_week_md(self, client, week_md):
        from subscribers.week_updater import append_to_week_md

        event = client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "MssPse4Fxa0", "segment_count": 700},
        )
        append_to_week_md(youtube_id="MssPse4Fxa0", timestamp=event.timestamp)

        content = week_md.read_text()
        assert "transcript.indexed" in content
        assert "youtube_id: MssPse4Fxa0" in content
        assert "## Bus Events" in content

    def test_run_once_processes_event(self, client, db_path, week_md):
        from subscribers import week_updater

        # Clear any leftover cursor
        cursor_file = Path(__file__).resolve().parent.parent / "state" / "week_updater_cursor.txt"
        cursor_file.unlink(missing_ok=True)

        client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "RunOnceTest", "segment_count": 1},
        )
        week_updater.run(run_once=True, db_path=db_path)

        content = week_md.read_text()
        assert "RunOnceTest" in content


class TestAuditLogger:
    def test_appends_to_heartbeat_state(self, client, heartbeat_state):
        from subscribers.audit_logger import append_to_heartbeat_state

        event = client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "audit_test"},
        )
        append_to_heartbeat_state(event)

        state = json.loads(heartbeat_state.read_text())
        assert "bus_events" in state
        assert len(state["bus_events"]) == 1
        entry = state["bus_events"][0]
        assert entry["event_id"] == event.id
        assert entry["event_type"] == "transcript.indexed"
        assert entry["actor_id"] == "yt-transcriber"

    def test_run_once_processes_event(self, client, db_path, heartbeat_state):
        from subscribers import audit_logger

        # Clear any leftover cursor
        cursor_file = Path(__file__).resolve().parent.parent / "state" / "audit_logger_cursor.txt"
        cursor_file.unlink(missing_ok=True)

        client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "AuditRunOnce"},
        )
        audit_logger.run(run_once=True, db_path=db_path)

        state = json.loads(heartbeat_state.read_text())
        assert "bus_events" in state
        assert len(state["bus_events"]) >= 1

    def test_creates_bus_events_array_if_missing(self, client, heartbeat_state):
        from subscribers.audit_logger import append_to_heartbeat_state

        # Start with state that has no bus_events key
        heartbeat_state.write_text('{"lastRun": "2026-01-01T00:00:00+00:00"}\n')

        event = client.publish(
            event_type="session.ended",
            payload={"reason": "test"},
        )
        append_to_heartbeat_state(event)

        state = json.loads(heartbeat_state.read_text())
        assert "bus_events" in state
        assert isinstance(state["bus_events"], list)


class TestHelloWorldSlice:
    """Full vertical slice: publish one event, verify both subscribers fire."""

    def test_full_slice(self, client, db_path, week_md, heartbeat_state):
        from subscribers import week_updater, audit_logger

        # Clear cursors
        for name in ["week_updater_cursor.txt", "audit_logger_cursor.txt"]:
            f = Path(__file__).resolve().parent.parent / "state" / name
            f.unlink(missing_ok=True)

        # Publish
        event = client.publish(
            event_type="transcript.indexed",
            payload={"youtube_id": "HELLO_WORLD_001", "segment_count": 1},
        )

        # Both subscribers react
        week_updater.run(run_once=True, db_path=db_path)
        audit_logger.run(run_once=True, db_path=db_path)

        # 1. WEEK.md updated
        week_content = week_md.read_text()
        assert "HELLO_WORLD_001" in week_content

        # 2. heartbeat-state.json updated
        state = json.loads(heartbeat_state.read_text())
        assert "bus_events" in state
        assert any(e["event_id"] == event.id for e in state["bus_events"])

        # 3. Signature verified
        events = client.consume()
        for e in events:
            assert client.verify(e) is True

        # 4. event_type is correct in DB
        rows = client._conn.execute(
            "SELECT event_type FROM events WHERE id = ?", (event.id,)
        ).fetchall()
        assert len(rows) == 1
        assert rows[0][0] == "transcript.indexed"

        print(f"\n✅ Hello World vertical slice passed — event_id={event.id}")
