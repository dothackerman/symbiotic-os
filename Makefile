.PHONY: help build-container shell-container build test up down reset codex-check

CONTAINER_NAME = symbiotic-os-builder
CONTAINER_RUNTIME ?= podman

help:
	@echo "symbiotic-os build targets"
	@echo ""
	@echo "  build-container  Build the devcontainer image"
	@echo "  shell-container  Open a shell inside the devcontainer (for yolo Codex)"
	@echo "  codex-check      Verify container is running before yolo mode"
	@echo "  test             Run tests (outside container, no yolo)"
	@echo "  up               Start bus and subscribers (future)"
	@echo "  down             Stop all services"
	@echo "  reset            Remove state/bus.db (keeps code)"

build-container:
	$(CONTAINER_RUNTIME) build \
		-f .devcontainer/Dockerfile.devcontainer \
		-t $(CONTAINER_NAME) \
		.devcontainer/

shell-container:
	$(CONTAINER_RUNTIME) run --rm -it \
		--network=none \
		--cap-drop=ALL \
		--security-opt=no-new-privileges \
		-v $$(pwd):/workspace:z \
		-w /workspace \
		$(CONTAINER_NAME) bash

codex-check:
	@echo "Checking if devcontainer is available..."
	@$(CONTAINER_RUNTIME) image inspect $(CONTAINER_NAME) > /dev/null 2>&1 \
		|| (echo "ERROR: Container image not built. Run 'make build-container' first." && exit 1)
	@echo "Container image ready. Safe to run Codex yolo inside container."

test:
	python3 -m pytest tests/ -v

up:
	@echo "Event bus startup not yet implemented (v0 pending Codex build)"

down:
	@echo "No running services to stop"

reset:
	rm -f state/bus.db
	@echo "State cleared. Code intact."
