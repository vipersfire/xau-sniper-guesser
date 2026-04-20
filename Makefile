.PHONY: help up down db-init migrate migrate-down migrate-history test test-unit test-cov lint

help:
	@echo "Usage:"
	@echo "  make up               Start PostgreSQL containers"
	@echo "  make down             Stop and remove containers"
	@echo "  make db-init          Initialize DB via Alembic (run all migrations)"
	@echo "  make migrate          Apply pending migrations (alembic upgrade head)"
	@echo "  make migrate-down     Roll back last migration (alembic downgrade -1)"
	@echo "  make migrate-history  Show migration history"
	@echo "  make test             Run all unit tests"
	@echo "  make test-unit        Run unit tests only (no DB required)"
	@echo "  make test-cov         Run tests with coverage report"

# ── Docker ──────────────────────────────────────────────────────────────────

up:
	docker compose up -d
	@echo "Waiting for PostgreSQL to be healthy..."
	@until docker compose exec postgres pg_isready -U postgres -d xauusd_sniper > /dev/null 2>&1; do sleep 1; done
	@echo "PostgreSQL is ready."

down:
	docker compose down

db-init: up
	alembic upgrade head

migrate: up
	alembic upgrade head

migrate-down:
	alembic downgrade -1

migrate-history:
	alembic history --verbose

# ── Tests ────────────────────────────────────────────────────────────────────

test:
	pytest tests/unit/ -m "not integration" -v

test-unit:
	pytest tests/unit/ -v

test-cov:
	pytest tests/unit/ --cov=. --cov-report=term-missing --cov-report=html:htmlcov \
		--cov-omit="tests/*,scripts/*,logs/*,models/artifacts/*"
