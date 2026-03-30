# devcontainer — for humans

## What this is

This devcontainer is the ONLY environment where Codex may run in `--yolo` mode.
It enforces isolation structurally, not by discipline.

## Security guarantees

| Control | Value | Why |
|---|---|---|
| `--network=none` | No external calls | Prevents data exfiltration |
| `--cap-drop=ALL` | No privilege escalation | Minimal attack surface |
| `--no-new-privileges` | Processes stay limited | Defence in depth |
| Single workspace mount | Codex sees only this repo | Scope enforcement |
| Non-root user | Runs as `vscode` | No host privilege |

## How to use (human)

### Option A: IDE integration (VS Code, Cursor, DevPod)

Docker required for native devcontainer tooling support.

```bash
# Open repo in IDE → "Reopen in Container"
```

### Option B: Manual with Podman (preferred for sovereignty)

```bash
make build-container          # build the image
make shell-container          # open a shell inside
# then inside the container:
acpx codex exec --yolo -s symbiotic-os-builder "$(cat CODEX_BRIEF.md)"
```

### Option C: Manual with Docker (fallback)

```bash
CONTAINER_RUNTIME=docker make build-container
CONTAINER_RUNTIME=docker make shell-container
```

## Invariant

Codex `--yolo` outside this container = policy violation (see CODEX_POLICY.md).
Codex `--full-auto` outside this container = permitted.

## What Codex sees inside

Codex reads these files on startup:
- `AGENTS.md` — role, rules, project context
- `codex.toml` — approval policy, instructions
- `CODEX_BRIEF.md` — current task
- `CODEX_POLICY.md` — governance rules
