# ADR 0001 — Event Envelope Structure

Status: Accepted
Date: 2026-03-29

## Context

Every event on the bus must be independently verifiable and auditable.
We need to know who emitted it, from which model, in which session, and whether it was tampered with.

## Decision

Use a fixed 10-field envelope for every event. All fields mandatory. No optional fields at envelope level.

Fields:
- id: uuid-v4, globally unique
- timestamp: ISO-8601 UTC, immutable
- actor_type: agent | human | system
- actor_id: named actor string
- model_id: model that produced the event, or "none" for system events
- session_id: session context, or "none" for scripts
- event_type: dot-namespaced string (e.g. transcript.indexed)
- payload_hash: sha256 of payload_json, for integrity
- signature: hmac-sha256 of canonical string, for authenticity
- payload_json: event-specific data

## Consequences

Positive:
- Any event can be verified in isolation
- Full provenance chain from event_type back to session and model
- Schema evolution is additive in payload_json only; envelope is stable

Negative:
- Every publisher must compute hash and signature — no raw inserts
- model_id and session_id are required even for non-AI events (use "none")

Migration note:
Envelope schema is versioned implicitly by ADR. Any breaking change requires new ADR and migration plan.
