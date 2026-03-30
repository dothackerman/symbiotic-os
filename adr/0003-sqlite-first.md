# ADR 0003 — SQLite First, Redis Later

Status: Accepted
Date: 2026-03-29

## Context

The event bus needs durable, append-only storage. Redis Streams would be ideal at scale. SQLite is simpler and has zero infrastructure dependency.

## Decision

Use SQLite for v0. Abstract the storage behind a `BusClient` interface so the migration to Redis is mechanical.

## Why SQLite now

- Zero infrastructure: no daemon, no port, no container required for v0
- Python stdlib: `sqlite3` built in
- Sufficient for single machine, low event volume
- Append-only enforced with SQLite triggers (no UPDATE, no DELETE)
- File is the bus — backup is `cp`, restore is `cp`

## Why Redis Streams later

- Redis Streams: persistent, replayable, consumer groups, fan-out
- Multi-consumer: multiple subscribers can read at different speeds independently
- Network-accessible: farm sensors and secondary nodes can publish over the wire
- XADD / XREADGROUP maps cleanly to our envelope schema

## Migration trigger criteria (any one sufficient)

- Sustained event rate exceeds 100 per minute
- More than 3 concurrent subscriber services
- First non-local publisher (farm sensor, secondary machine)
- Consumer lag becomes observable and causes stale state

## Migration contract

- BusClient interface is identical in both implementations
- Publishers use `bus.publish(event)` — same call
- Subscribers use `bus.consume(group, consumer, event_types)` — same call
- SQLite file becomes cold archive; Redis starts fresh from migration point
- All existing events remain queryable via SQLite reader

## Consequences

Positive:
- Zero infrastructure overhead for v0
- Fast to build and test
- Migration is low-risk due to abstraction layer

Negative:
- No multi-consumer fan-out in SQLite (subscribers poll, not push)
- Not network-accessible until Redis migration
- Polling interval introduces latency (acceptable for v0)
