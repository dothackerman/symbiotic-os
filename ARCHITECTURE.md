# Symbiotic OS — Architecture

_Version: v0. Living document. Updated after each vertical slice._

---

## The Six Layers

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 6 — Sil                                              │
│  The AI being. Inhabits the stack. Not a layer — a tenant.  │
├─────────────────────────────────────────────────────────────┤
│  Layer 5 — Interfaces                                       │
│  Silicato (voice) · Telegram (text) · Canvas (visual)       │
├─────────────────────────────────────────────────────────────┤
│  Layer 4 — Policy Kernel                          [future]  │
│  Trust rules · data flow · domain allowlists                │
├─────────────────────────────────────────────────────────────┤
│  Layer 3 — Memory Plane                                     │
│  Git-backed · scoped · versioned · YYYY-MM-DD.md files      │
├─────────────────────────────────────────────────────────────┤
│  Layer 2 — Event Bus                              [v0 HERE] │
│  SQLite append-only · HMAC-SHA256 signed · local only       │
├─────────────────────────────────────────────────────────────┤
│  Layer 1 — Inference                              [future]  │
│  SGLang / Ollama · local GPU · model router                 │
├─────────────────────────────────────────────────────────────┤
│  Layer 0 — Hardware                               [future]  │
│  Local GPU · Podman rootless · kill switches                │
└─────────────────────────────────────────────────────────────┘
```

---

## V0 Scope

V0 builds only Layer 2 — one thin, working vertical slice:

```
yt-transcriber
    │
    │  publishes: transcript.indexed
    ▼
┌─────────────────────────────┐
│  Event Bus (SQLite)         │
│  append-only · signed       │
└──────────┬──────────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
WEEK.md    heartbeat-state.json
updater    audit logger
```

One publisher. Two subscribers. One working trace.

---

## Event Envelope Schema

Every event written to the bus must include all fields. No exceptions.

```json
{
  "id": "uuid-v4",
  "timestamp": "ISO-8601 UTC",
  "actor_type": "agent | human | system",
  "actor_id": "sil | og | yt-transcriber | ...",
  "model_id": "claude-sonnet-4-6 | local/llama-32b | none",
  "session_id": "openclaw session id or script run id",
  "event_type": "transcript.indexed | session.ended | memory.updated | ...",
  "payload_hash": "sha256 hex of payload_json",
  "signature": "hmac-sha256 hex of canonical fields",
  "payload_json": "{...event-specific data...}"
}
```

Canonical signing string (ordered, pipe-separated):
```
{id}|{timestamp}|{actor_type}|{actor_id}|{event_type}|{payload_hash}
```

---

## SQLite Schema

```sql
CREATE TABLE events (
    id          TEXT PRIMARY KEY,
    timestamp   TEXT NOT NULL,
    actor_type  TEXT NOT NULL,
    actor_id    TEXT NOT NULL,
    model_id    TEXT NOT NULL DEFAULT 'none',
    session_id  TEXT NOT NULL DEFAULT 'none',
    event_type  TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    signature   TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- No UPDATE. No DELETE. Append only enforced in application layer.
-- Trigger to enforce append-only:
CREATE TRIGGER prevent_update BEFORE UPDATE ON events
BEGIN
    SELECT RAISE(ABORT, 'events table is append-only');
END;

CREATE TRIGGER prevent_delete BEFORE DELETE ON events
BEGIN
    SELECT RAISE(ABORT, 'events table is append-only');
END;
```

---

## Trust Boundaries

```
TRUSTED (local process, known actor)
  └── yt-transcriber, Sil session, heartbeat

SEMI-TRUSTED (local file system output)
  └── WEEK.md, heartbeat-state.json subscribers

UNTRUSTED (never touches bus directly)
  └── web fetch content, external APIs, user-pasted URLs
      → must go through isolated sub-agent → review → then may emit event
```

---

## Redis Migration Path

SQLite is sufficient for single-machine use with low event volume.

Migrate to Redis Streams when any of these triggers are met:
- Events per minute exceeds 100 sustained
- More than 3 subscriber services running concurrently
- Multi-machine setup (farm sensors, secondary node)
- Consumer lag becomes observable

Migration contract:
- Event envelope schema is identical (Redis just replaces SQLite storage)
- Publishers use same interface (client library abstraction)
- Subscribers use same consumer group pattern
- All existing events remain in SQLite as cold archive

---

## Podman Service Topology (v0)

```
pod: symbiosis-bus
  container: bus-db    (SQLite file volume, read/write)

pod: symbiosis-workers
  container: subscriber-week     (read bus, write WEEK.md)
  container: subscriber-audit    (read bus, write heartbeat-state.json)

external publisher: yt-transcriber (runs in OpenClaw workspace, publishes via bus client)
```

---

## Signing Strategy Summary

- v0: HMAC-SHA256 with local secret in `secrets/bus.key` (never committed)
- v1: Ed25519 keypairs per actor when multi-node trust boundaries emerge
- Secret rotation: documented in SECURITY.md, quarterly minimum

---

_Last updated: 2026-03-29 | v0 vertical slice_
