# ADR 0002 — Signing Strategy

Status: Accepted
Date: 2026-03-29

## Context

Events must be tamper-evident. We need confidence that an event written by yt-transcriber was not modified before a subscriber reads it.

Single machine for now. Multiple nodes (farm sensors, secondary compute) are a future state.

## Decision

v0: HMAC-SHA256 with a shared local secret.

Secret stored in `secrets/bus.key` — never committed to repo.
Canonical signing string: `{id}|{timestamp}|{actor_type}|{actor_id}|{event_type}|{payload_hash}`

v1 (multi-node): Ed25519 keypairs per actor.
Each actor (yt-transcriber, sil, heartbeat-worker) has its own keypair.
Public keys registered in `config/trusted-actors.json`.
Signature verification uses per-actor public key.

## Why HMAC-SHA256 now

- Zero dependency beyond Python stdlib (hmac, hashlib)
- Single machine: shared secret is not a trust problem
- Fast to implement correctly
- Migration to Ed25519 is mechanical: same canonical string, different algorithm

## Why Ed25519 later

- Multi-node: different machines cannot safely share a single secret
- Ed25519: small keys, fast, well-audited (libsodium / PyNaCl)
- Per-actor identity: you can revoke one actor without rotating all secrets

## Migration trigger

Migrate when: first non-local publisher appears (farm sensor, secondary node, external script).

## Consequences

Positive:
- v0 is secure on single machine with zero new dependencies
- v1 migration is low-risk and mechanical

Negative:
- Shared secret means any compromised local process can forge events — acceptable on single sovereign machine
- Must not forget to rotate `secrets/bus.key` quarterly
