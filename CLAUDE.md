# Symbiotic OS — Claude Code Project Instructions

## Project

Symbiotic OS: a local-first sovereign AI operating environment.
Current scope: Layer 2 — event bus (v0 complete, v1 next).

## Your role

Builder. Receive briefs from Sil. Implement. Report back.
Read CODEX_BRIEF.md before touching any code.

## Rules

1. Follow Definition of Ready and Done in CODEX_BRIEF.md
2. One ping-pong allowed for clarification
3. Never touch files outside this repo
4. No external network calls
5. Commit scope: feat(bus)|fix(schema)|feat(subscriber)|test|docs|chore
6. Write CHANGELOG.md entry when done
7. Write HANDOFF.md when done: what changed, why, risks, next edge

## File layout

- Code: bus/, publishers/, subscribers/, tests/
- State (runtime only, gitignored): state/
- Secrets (never committed): secrets/
- Docs: docs/, adr/

## Stack

Python 3.11+, pytest, SQLite, HMAC-SHA256 signing.
See ARCHITECTURE.md for full design.
