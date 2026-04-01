COMPOSE_FILE      = podman-compose.yml
DB_PATH           = state/bus.db
KEY_PATH          = secrets/bus.key

help:
	@echo "symbiotic-os build targets"
	@echo ""
	@echo "  key-gen          Generate a new secrets/bus.key (first-time setup)"
	@echo "  up               Start subscriber workers via podman-compose"
	@echo "  down             Stop all subscriber services"
	@echo "  test             Run all tests (pytest)"
	@echo "  reset            Remove state/bus.db and cursor files (keeps code)"
	@echo ""
# ---------------------------------------------------------------------------
# Key generation (first-time setup)
# ---------------------------------------------------------------------------
key-gen:
	@mkdir -p secrets state
	@if [ -f $(KEY_PATH) ]; then \
		echo "WARNING: $(KEY_PATH) already exists. Delete it first to regenerate."; \
	else \
		python3 -c "import secrets; print(secrets.token_hex(32))" > $(KEY_PATH); \
		echo "Generated $(KEY_PATH)"; \
		echo "Also writing BUS_KEY to secrets/.env for podman-compose..."; \
		echo "BUS_KEY=$$(cat $(KEY_PATH))" > secrets/.env; \
	fi

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
up: _check-key
down:
# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------
test:
	@test -f .venv/bin/pytest || (python3 -m venv .venv && .venv/bin/pip install pytest python-dotenv -q)
	.venv/bin/pytest tests/ -v

# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------
reset:
	rm -f $(DB_PATH)
	rm -f state/week_updater_cursor.txt
	rm -f state/audit_logger_cursor.txt
	@echo "State cleared. Code and key intact."

# ---------------------------------------------------------------------------
# Internal guards
# ---------------------------------------------------------------------------
_check-key:
	@test -f $(KEY_PATH) || (echo "ERROR: $(KEY_PATH) not found. Run 'make key-gen' first." && exit 1)
