"""Event envelope schema, builder, and HMAC-SHA256 signing."""

from __future__ import annotations

import hashlib
import hmac
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Key loading
# ---------------------------------------------------------------------------

def _load_key() -> bytes:
    """Load HMAC key from secrets/bus.key relative to project root.

    Falls back to BUS_KEY env var for testing convenience.
    """
    import os

    env_key = os.environ.get("BUS_KEY")
    if env_key:
        return env_key.encode()

    # Walk up from this file to find secrets/bus.key
    here = Path(__file__).resolve().parent
    project_root = here.parent
    key_path = project_root / "secrets" / "bus.key"
    if not key_path.exists():
        raise FileNotFoundError(
            f"Bus key not found at {key_path}. "
            "Generate with: python3 -c \"import secrets; print(secrets.token_hex(32))\" > secrets/bus.key"
        )
    return key_path.read_text().strip().encode()


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class Event:
    """Fully validated event envelope."""

    id: str
    timestamp: str           # ISO-8601 UTC
    actor_type: str          # agent | human | system
    actor_id: str
    model_id: str
    session_id: str
    event_type: str
    payload_hash: str        # sha256 hex of payload_json
    signature: str           # hmac-sha256 hex of canonical fields
    payload_json: str        # JSON string of payload dict

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "actor_type": self.actor_type,
            "actor_id": self.actor_id,
            "model_id": self.model_id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "payload_hash": self.payload_hash,
            "signature": self.signature,
            "payload_json": self.payload_json,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "Event":
        """Reconstruct from a DB row (column order matches CREATE TABLE)."""
        (
            id_, timestamp, actor_type, actor_id, model_id, session_id,
            event_type, payload_hash, signature, payload_json, _created_at
        ) = row
        return cls(
            id=id_,
            timestamp=timestamp,
            actor_type=actor_type,
            actor_id=actor_id,
            model_id=model_id,
            session_id=session_id,
            event_type=event_type,
            payload_hash=payload_hash,
            signature=signature,
            payload_json=payload_json,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _canonical_string(event_id: str, timestamp: str, actor_type: str,
                       actor_id: str, event_type: str, payload_hash: str) -> str:
    """Pipe-separated canonical signing string (order is spec)."""
    return "|".join([event_id, timestamp, actor_type, actor_id, event_type, payload_hash])


def _sign(canonical: str, key: bytes) -> str:
    return hmac.new(key, canonical.encode(), hashlib.sha256).hexdigest()


def _payload_hash(payload_json: str) -> str:
    return hashlib.sha256(payload_json.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_event(
    event_type: str,
    payload: dict[str, Any],
    actor_type: str = "system",
    actor_id: str = "yt-transcriber",
    model_id: str = "none",
    session_id: str = "none",
    key: bytes | None = None,
) -> Event:
    """Build and sign a new event envelope."""
    if key is None:
        key = _load_key()

    event_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    phash = _payload_hash(payload_json)
    canonical = _canonical_string(event_id, timestamp, actor_type, actor_id, event_type, phash)
    sig = _sign(canonical, key)

    return Event(
        id=event_id,
        timestamp=timestamp,
        actor_type=actor_type,
        actor_id=actor_id,
        model_id=model_id,
        session_id=session_id,
        event_type=event_type,
        payload_hash=phash,
        signature=sig,
        payload_json=payload_json,
    )


def verify_event(event: Event, key: bytes | None = None) -> bool:
    """Return True iff the event signature is valid."""
    if key is None:
        key = _load_key()

    canonical = _canonical_string(
        event.id, event.timestamp, event.actor_type,
        event.actor_id, event.event_type, event.payload_hash,
    )
    expected = _sign(canonical, key)
    return hmac.compare_digest(expected, event.signature)
