# Codex Execution Policy

## Hard rules

1. Codex `--yolo` mode: ONLY inside the devcontainer (`.devcontainer/`)
2. Outside devcontainer: `--full-auto` maximum
3. No exceptions without explicit human approval

## How Sil delegates to Codex

```bash
# One-shot task (preferred for discrete builds)
acpx codex exec -s symbiotic-os-builder "$(cat CODEX_BRIEF.md)"

# Persistent session (for iterative work)
acpx codex sessions new --name symbiotic-os-builder
acpx codex -s symbiotic-os-builder "$(cat CODEX_BRIEF.md)"
```

## Devcontainer for yolo mode

Start the devcontainer with Podman (preferred):

```bash
podman run --rm -it \
  --network=none \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  -v $(pwd):/workspace:z \
  -w /workspace \
  symbiotic-os-builder bash

# Then inside the container:
acpx codex exec --yolo -s symbiotic-os-builder "$(cat CODEX_BRIEF.md)"
```

## Why this structure

- Network=none: prevents data exfiltration and external calls
- Cap-drop=ALL: prevents privilege escalation
- Single mount: Codex can only touch this repo
- Policy enforced by container, not by discipline

## Architecture inputs

Before any Codex build task:
1. Opus produces architecture decisions and CODEX_BRIEF.md
2. Sil reviews and approves
3. Sil submits via acpx to Codex
4. Codex builds inside devcontainer (yolo) or outside (full-auto)
5. Codex reports back via acpx structured output
6. Sil reviews output before committing

## Session verification (future sessions)

Before running Codex, verify container is active:
```bash
podman ps | grep symbiotic-os-builder  # must show running
```
If not running, start container first. Never run yolo outside container.
