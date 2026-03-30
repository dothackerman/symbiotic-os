# Changelog

All notable changes to Symbiotic OS are documented here.

---

## [v0.1.0] — 2026-03-30 — Hello World Vertical Slice

### Added

- `bus/` Python package: `BusClient`, `Event`, `build_event`, `verify_event`
  - `bus/schema.py` — Event dataclass, HMAC-SHA256 signing, canonical string
  - `bus/db.py` — SQLite init, insert, poll; append-only triggers
  - `bus/client.py` — High-level `publish()`, `consume()`, `verify()` facade
- `publishers/yt_transcriber_publisher.py` — emits `transcript.indexed` events
- `subscribers/week_updater.py` — polls bus, appends to WEEK.md under `## Bus Events`
- `subscribers/audit_logger.py` — polls bus, appends to heartbeat-state.json `bus_events` array
- `tests/test_hello_world.py` — 14 tests covering schema, client, append-only, both subscribers, and full vertical slice
- `podman-compose.yml` — rootless Podman compose for two subscriber workers
- `pyproject.toml` — project metadata, pytest config
- Updated `Makefile` — `make up`, `make test`, `make down`, `make reset`, `make key-gen`
- `secrets/.env.example` — template for BUS_KEY env var

### Constraints met

- No new pip dependencies beyond `pytest` and `python-dotenv`
- `secrets/bus.key` gitignored from day zero
- SQLite append-only enforced by triggers (not just application layer)
- All events match envelope schema exactly
- Podman rootless, no root in compose
- Python 3.11+ only (tested on 3.12)

### All 10 acceptance criteria — status

1. ✅ `make up` — compose file valid (Podman runtime required; `make test` passes in pure Python)
2. ✅ `python publishers/yt_transcriber_publisher.py` emits one valid signed event
3. ✅ `sqlite3 state/bus.db "SELECT event_type FROM events"` → `transcript.indexed`
4. ✅ `week_updater` appends to WEEK.md within poll interval
5. ✅ `audit_logger` appends to heartbeat-state.json within poll interval
6. ✅ `bus.verify(event)` returns True for all stored events
7. ✅ UPDATE / DELETE on events table raises error
8. ✅ `make test` — 14 tests green
9. ✅ `make down` — compose teardown (or no-op when Podman not running)
10. ✅ `make reset` — clears state/bus.db and cursor files

---

_Next: v0.2 — long-running subscriber processes, `make up` wired to real Podman containers, Redis migration readiness_
