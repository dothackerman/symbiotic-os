# HANDOFF — v0 Event Bus Vertical Slice

_2026-03-30 · Built by Sil (subagent)_

---

## What Was Built

A complete v0 event bus — one publisher, two subscribers, one working trace through SQLite.

### Files created/modified

| Path | Role |
|---|---|
| `bus/__init__.py` | Package exports |
| `bus/schema.py` | Event dataclass, HMAC-SHA256 signing, canonical string, verify |
| `bus/db.py` | SQLite init (with append-only triggers), insert, poll |
| `bus/client.py` | `BusClient` facade: `publish()`, `consume()`, `verify()` |
| `publishers/yt_transcriber_publisher.py` | Emits `transcript.indexed` events |
| `subscribers/week_updater.py` | Polls bus → appends to WEEK.md `## Bus Events` section |
| `subscribers/audit_logger.py` | Polls bus → appends to heartbeat-state.json `bus_events` array |
| `tests/test_hello_world.py` | 14 tests: schema, client, append-only, both subscribers, full slice |
| `podman-compose.yml` | Rootless Podman compose for two subscriber workers |
| `pyproject.toml` | Project metadata and pytest config |
| `Makefile` | Updated: `make test`, `make key-gen`, `make up/down/reset` |
| `CHANGELOG.md` | v0.1.0 entry |
| `secrets/.env.example` | Template for BUS_KEY env var in containers |
| `secrets/.gitignore` | Added `.env` to ignore list |

### Live validation performed

- Publisher emitted event → `state/bus.db` has `transcript.indexed`
- `WEEK.md` received: `- [2026-03-30T19:30:51...] transcript.indexed — youtube_id: MssPse4Fxa0`
- `heartbeat-state.json` received: `bus_events` array with one entry
- Signature verification passes for all stored events
- UPDATE and DELETE on events table both blocked by triggers
- 14/14 tests green

---

## Deviations from Brief

1. **SQLite triggers raise `IntegrityError`, not `OperationalError`.** The CODEX_BRIEF says "attempting UPDATE or DELETE raises an error" — it does, but via `sqlite3.IntegrityError` (Python's mapping of `RAISE(ABORT, ...)`). Tests match both exception types for robustness.

2. **Subscribers accept `db_path` parameter.** The brief doesn't mention this, but it was necessary for test isolation (each test gets its own temp SQLite). Production defaults are unchanged.

3. **`.venv/` used for Python 3.12.** The host has Python 3.14 (linuxbrew) without pip, and Python 3.12 (system) without pip. Created a local `.venv` with 3.12 + pytest. `.venv/` is already in `.gitignore`.

4. **`podman-compose.yml` not live-tested.** The compose file is structurally valid but was not run under Podman (Podman daemon availability not confirmed). `make up` requires Podman. All acceptance criteria were validated via direct Python invocation.

5. **Key loaded from env var OR file.** The brief only mentions `secrets/bus.key`. The implementation also checks `BUS_KEY` env var first — needed for container environments and test isolation. File path is the primary mechanism.

---

## Risks

- **Single-writer assumption.** If two processes publish concurrently to the same SQLite file, SQLite's write lock will serialize them but could cause `SQLITE_BUSY` under load. Fine for v0 volumes.
- **Cursor files in `state/`.** Each subscriber tracks its last-seen event ID in a text file. If deleted, subscriber replays all events. This is safe (idempotent writes) but worth knowing.
- **Podman compose not validated.** The bind-mount volumes assume `~/.openclaw/workspace` exists. Container environments may need `OPENCLAW_WORKSPACE` env var.
- **No graceful shutdown.** Subscribers in polling mode (`while True` loop) need SIGINT/SIGTERM handling for clean container stops. Fine for v0.

---

## Next Edge

1. **Wire `make up` to Podman** — validate compose file runs end-to-end with real containers
2. **Graceful shutdown** — signal handling in subscriber loops
3. **yt-transcriber integration** — call `publish_transcript()` from the real yt-transcriber skill after indexing
4. **More event types** — `session.ended`, `memory.updated` per ARCHITECTURE.md
5. **Redis migration** — when event volume or subscriber count crosses thresholds (documented in ARCHITECTURE.md)
