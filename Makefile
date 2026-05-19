COMPOSE := docker compose

.PHONY: dev-build dev-run dev-kill dev-data dev-db-d dev-db-stop dev-backend-local dev-data-local

dev-build:
	$(COMPOSE) build

dev-run:
	$(COMPOSE) up

dev-kill:
	$(COMPOSE) down --remove-orphans

dev-data:
	$(COMPOSE) run --rm backend python -m app.ingest

# --- local-host targets (Postgres in Docker, API/ingest on host) ---

dev-db-d:
	$(COMPOSE) up -d db

dev-db-stop:
	$(COMPOSE) stop db

dev-backend-local:
	set -a && . ./.env && set +a && \
	cd backend && \
	DATABASE_URL=postgresql://$$POSTGRES_USER:$$POSTGRES_PASSWORD@127.0.0.1:5432/$$POSTGRES_DB \
	DATA_DIR=../data \
	.venv/bin/uvicorn app.main:app --reload

dev-data-local:
	set -a && . ./.env && set +a && \
	cd backend && \
	DATABASE_URL=postgresql://$$POSTGRES_USER:$$POSTGRES_PASSWORD@127.0.0.1:5432/$$POSTGRES_DB \
	DATA_DIR=../data \
	.venv/bin/python -m app.ingest
