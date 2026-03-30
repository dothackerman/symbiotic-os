# symbiotic-os devcontainer

## Purpose

This devcontainer is the ONLY environment where Codex may run in yolo mode.

## Security properties

- `--network=none`: no external network calls from inside the container
- `--cap-drop=ALL`: no Linux capability escalation
- `--security-opt=no-new-privileges`: processes cannot gain new privileges
- Single workspace mount: Codex can only touch files in `/workspace`
- Non-root user: runs as `vscode`, not root

## Runtime options

### Podman (preferred — rootless)

```bash
podman build -f Dockerfile.devcontainer -t symbiotic-os-builder .
podman run --rm -it \
  --network=none \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  -v $(pwd):/workspace:z \
  -w /workspace \
  symbiotic-os-builder bash
```

### Docker (fallback)

```bash
docker build -f Dockerfile.devcontainer -t symbiotic-os-builder .
docker run --rm -it \
  --network=none \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  -v $(pwd):/workspace \
  -w /workspace \
  symbiotic-os-builder bash
```

### VS Code / Cursor devcontainer extension

Open the repo, select "Reopen in Container" — uses `devcontainer.json` above.

## Invariant

Codex yolo mode outside this container = policy violation.
Codex in this container = safe by design.
