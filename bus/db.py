"""SQLite backend — append-only, trigger-enforced."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterator

from .schema import Event

# Default DB path relative to project root
_DEFAULT_DB = Path(__file__).resolve().parent.parent / "state" / "bus.db"


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | None = None) -> sqlite3.Connection:
    """Create tables and triggers if not already present. Returns open connection."""
    db_path = db_path or _DEFAULT_DB
    conn = _connect(db_path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS events (
            id           TEXT PRIMARY KEY,
            timestamp    TEXT NOT NULL,
            actor_type   TEXT NOT NULL,
            actor_id     TEXT NOT NULL,
            model_id     TEXT NOT NULL DEFAULT 'none',
            session_id   TEXT NOT NULL DEFAULT 'none',
            event_type   TEXT NOT NULL,
            payload_hash TEXT NOT NULL,
            signature    TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at   TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TRIGGER IF NOT EXISTS prevent_update
        BEFORE UPDATE ON events
        BEGIN
            SELECT RAISE(ABORT, 'events table is append-only');
        END;

        CREATE TRIGGER IF NOT EXISTS prevent_delete
        BEFORE DELETE ON events
        BEGIN
            SELECT RAISE(ABORT, 'events table is append-only');
        END;
    """)
    conn.commit()
    return conn


def insert_event(event: Event, conn: sqlite3.Connection) -> None:
    """Insert a new event. Raises on duplicate id or trigger violation."""
    conn.execute(
        """
        INSERT INTO events
            (id, timestamp, actor_type, actor_id, model_id, session_id,
             event_type, payload_hash, signature, payload_json)
        VALUES
            (:id, :timestamp, :actor_type, :actor_id, :model_id, :session_id,
             :event_type, :payload_hash, :signature, :payload_json)
        """,
        event.to_dict(),
    )
    conn.commit()


def poll_events(
    conn: sqlite3.Connection,
    after_id: str | None = None,
    event_type: str | None = None,
) -> list[Event]:
    """Return events newer than after_id (or all if None), optionally filtered by event_type.

    Uses rowid ordering so "after" is insertion order, not UUID sort.
    """
    conditions = []
    params: list = []

    if after_id is not None:
        conditions.append(
            "rowid > (SELECT rowid FROM events WHERE id = ?)"
        )
        params.append(after_id)

    if event_type is not None:
        conditions.append("event_type = ?")
        params.append(event_type)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"SELECT * FROM events {where} ORDER BY rowid ASC"
    cursor = conn.execute(sql, params)
    rows = cursor.fetchall()
    return [Event.from_row(tuple(row)) for row in rows]
