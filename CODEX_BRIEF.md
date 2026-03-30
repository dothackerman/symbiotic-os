# Codex Brief — Symbiotic OS v0 Vertical Slice

## Definition of Ready

A task is Ready only when ALL are true:

- [ ] Problem statement exists in 3-5 lines
- [ ] In-scope and out-of-scope are explicit
- [ ] Security and privacy constraints are listed
- [ ] Acceptance criteria are testable (pass/fail, not subjective)
- [ ] Target files and module boundaries are known
- [ ] Rollback path is known
- [ ] Unknowns are listed as explicit assumptions

**This brief meets all criteria. Codex may proceed.**

---

## Task: Build Symbiotic OS Event Bus — v0 Vertical Slice

### Problem

The Symbiotic OS has no shared nervous system. When yt-transcriber indexes a transcript, nothing else knows. We need a minimal local event bus so that one event triggers automatic downstream updates.

### In Scope

- `bus/` Python package with:
  - `BusClient` class: `publish()` and `consume()` methods
  - SQLite backend with append-only enforcement
  - HMAC-SHA256 signed event envelopes
- `publishers/yt_transcriber_publisher.py`: emits `transcript.indexed` event
- `subscribers/week_updater.py`: polls bus, appends entry to WEEK.md
- `subscribers/audit_logger.py`: polls bus, appends line to heartbeat-state.json
- `tests/test_hello_world.py`: publishes one event, verifies both subscribers react, verifies trace in log
- `secrets/` directory with `.gitignore` and `bus.key.example`
- `podman-compose.yml`: bus-db volume, two worker containers
- `Makefile`: `make up`, `make test`, `make down`, `make reset`

### Out of Scope

- Redis integration (v1)
- Ed25519 signing (v1)
- Policy kernel enforcement (future)
- Any external network calls
- UI or debug interface
- Integration with live OpenClaw session (stub only)

### Constraints

- Python 3.11+ only
- No new pip dependencies beyond: `pytest`, `python-dotenv`
- SQLite append-only: enforce with triggers (see ARCHITECTURE.md)
- `secrets/bus.key` must never be committed — `.gitignore` from day zero
- All events must match envelope schema exactly (see ARCHITECTURE.md)
- Subscribers poll every 2 seconds — no blocking push required for v0
- Podman rootless — no root in compose file

### Acceptance Criteria (all must pass)

1. `make up` starts cleanly with no errors
2. `python publishers/yt_transcriber_publisher.py` emits one valid signed event
3. `sqlite3 state/bus.db "SELECT event_type FROM events"` returns `transcript.indexed`
4. Within 5 seconds, WEEK.md contains a new line referencing the transcript
5. Within 5 seconds, heartbeat-state.json contains a new audit entry
6. Signature verification passes: `bus.verify(event)` returns True for all stored events
7. Attempting UPDATE or DELETE on events table raises an error
8. `make test` runs all tests green
9. `make down` stops all services cleanly
10. `make reset` removes state but not code

### File Layout

```
symbiotic-os/
├── ARCHITECTURE.md
├── CODEX_BRIEF.md
├── CHANGELOG.md
├── Makefile
├── podman-compose.yml
├── pyproject.toml
├── README.md
├── adr/
│   ├── 0001-event-envelope.md
│   ├── 0002-signing-strategy.md
│   └── 0003-sqlite-first.md
├── bus/
│   ├── __init__.py
│   ├── client.py        ← BusClient: publish(), consume(), verify()
│   ├── schema.py        ← Event dataclass, envelope builder, signer
│   └── db.py            ← SQLite init, insert, poll
├── publishers/
│   └── yt_transcriber_publisher.py
├── subscribers/
│   ├── week_updater.py
│   └── audit_logger.py
├── tests/
│   └── test_hello_world.py
├── secrets/
│   ├── .gitignore       ← ignores bus.key
│   └── bus.key.example  ← placeholder only
└── state/               ← runtime only, gitignored
    └── .gitkeep
```

### Rollback

Delete `state/bus.db`. All events are in one file. Reset is clean.

### Definition of Done

A task is Done only when ALL are true:

- [ ] All 10 acceptance criteria pass
- [ ] `make test` green
- [ ] No secrets committed (verify with `git log --all -- secrets/bus.key`)
- [ ] `state/` is gitignored
- [ ] CHANGELOG.md has entry for v0
- [ ] Handoff note written: what changed, why, risks, next edge
- [ ] Codex has listed any deviations from this brief with reasons

### Codex Pushback Protocol

One ping-pong allowed. If any acceptance criterion is unclear or a constraint conflicts with implementation, Codex stops and asks one specific question. Sil answers. Then Codex proceeds.

Do not silently deviate from this brief.
