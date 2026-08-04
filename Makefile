.DEFAULT_GOAL := help
.PHONY: help install install-dev lock lock-upgrade npm-install env-copy \
        up up-logs down build build-prod logs logs-web ps restart \
        shell shell-docker db-shell migrate migrate-docker makemigrations \
        makemigrations-docker superuser superuser-docker create-user create-admin \
        collectstatic flush reset-db \
        demo-setup demo-assets demo-up demo-run demo-seed demo-reseed demo-clear \
        demo-reset demo-shell demo-seeders demo-smoke \
        npm-dev npm-build beautify lint check ci version-check check-docker \
        test test-js test-seq test-cov test-docker celery celery-docker deploy

PYTHON        := uv run python
MANAGE        := uv run python manage.py
DC            := docker compose
DC_EXEC       := $(DC) exec web
SETTINGS      := config.settings.dev
DEMO_SETTINGS := config.settings.demo
DEMO_DB       := db.demo.sqlite3
PROFILE       ?= small
# Everything the formatter and linter own — kept in one place so the Makefile,
# pre-commit and CI cannot drift apart.
PY_PATHS      := apps/ config/ scripts/ conftest.py manage.py

# ============================================================
# Help
# ============================================================
help: ## Show this help message
	@echo ""
	@echo "Django AT Stack — available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ============================================================
# Setup
# ============================================================
install: ## Install runtime dependencies only (no dev tools)
	uv sync --no-dev

install-dev: ## Install all dependencies + pre-commit hooks
	uv sync
	uv run pre-commit install

lock: ## Regenerate uv.lock from pyproject.toml
	uv lock

lock-upgrade: ## Upgrade every package and regenerate uv.lock
	uv lock --upgrade

npm-install: ## Install Node.js dependencies
	npm install

env-copy: ## Copy .env.example to .env
	cp .env.example .env
	@echo ".env created — edit it before starting."

# ============================================================
# Docker
# ============================================================
up: ## Start all services (detached)
	$(DC) up -d

up-logs: ## Start all services with logs
	$(DC) up

down: ## Stop all services
	$(DC) down

build: ## Build Docker images
	$(DC) build

build-prod: ## Build the production Docker image
	docker build --target prod -t django-at-stack:prod .

logs: ## Follow logs from all services
	$(DC) logs -f

logs-web: ## Follow web service logs
	$(DC) logs -f web

ps: ## Show running containers
	$(DC) ps

restart: ## Restart the web service
	$(DC) restart web

# ============================================================
# Django management
# ============================================================
shell: ## Open the Django shell
	$(MANAGE) shell --settings=$(SETTINGS)

shell-docker: ## Open the Django shell in Docker
	$(DC_EXEC) python manage.py shell

db-shell: ## Connect to PostgreSQL
	$(DC) exec db psql -U postgres django_at_stack

migrate: ## Run database migrations
	$(MANAGE) migrate --settings=$(SETTINGS)

migrate-docker: ## Run migrations in Docker
	$(DC_EXEC) python manage.py migrate

makemigrations: ## Create new migrations
	$(MANAGE) makemigrations --settings=$(SETTINGS)

makemigrations-docker: ## Create migrations in Docker
	$(DC_EXEC) python manage.py makemigrations

superuser: ## Create a superuser (interactive)
	$(MANAGE) createsuperuser --settings=$(SETTINGS)

superuser-docker: ## Create a superuser in Docker (interactive)
	$(DC_EXEC) python manage.py createsuperuser

# Usage: make create-user EMAIL=user@example.com PASSWORD=pass123 [FIRST_NAME=Jane] [LAST_NAME=Doe]
create-user: ## Create a regular user — EMAIL= PASSWORD= [FIRST_NAME=] [LAST_NAME=]
	$(MANAGE) create_user --email=$(EMAIL) --password=$(PASSWORD) \
		$(if $(FIRST_NAME),--first-name=$(FIRST_NAME)) \
		$(if $(LAST_NAME),--last-name=$(LAST_NAME)) \
		--settings=$(SETTINGS)

# Usage: make create-admin EMAIL=admin@example.com PASSWORD=pass123
create-admin: ## Create an admin superuser — EMAIL= PASSWORD= [FIRST_NAME=] [LAST_NAME=]
	$(MANAGE) create_admin --email=$(EMAIL) --password=$(PASSWORD) \
		$(if $(FIRST_NAME),--first-name=$(FIRST_NAME)) \
		$(if $(LAST_NAME),--last-name=$(LAST_NAME)) \
		--settings=$(SETTINGS)

collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput --settings=$(SETTINGS)

flush: ## Flush the database (WARNING: destroys all data)
	$(MANAGE) flush --no-input --settings=$(SETTINGS)

reset-db: ## Drop and recreate the database (WARNING: destructive!)
	$(DC) exec db psql -U postgres -c "DROP DATABASE IF EXISTS django_at_stack;"
	$(DC) exec db psql -U postgres -c "CREATE DATABASE django_at_stack;"
	$(MAKE) migrate-docker

# ============================================================
# Demo environment (config.settings.demo — SQLite, no Docker)
# ============================================================
demo-setup: demo-assets ## Build the demo environment from scratch (PROFILE=small)
	$(MANAGE) migrate --settings=$(DEMO_SETTINGS)
	$(MANAGE) seed_demo --settings=$(DEMO_SETTINGS) --profile=$(PROFILE)

demo-assets: ## Build the frontend bundle if it is missing
	@if [ ! -f static/dist/main.js ]; then \
		echo "Building the frontend (one-off)…"; \
		npm install --no-audit --no-fund && npm run build; \
	else \
		echo "Frontend already built (static/dist) — skipping."; \
	fi

demo-up: demo-setup demo-run ## Build the demo environment and start the server

demo-run: ## Run the server against the demo database (http://localhost:8000)
	$(MANAGE) runserver 0.0.0.0:8000 --settings=$(DEMO_SETTINGS)

demo-seed: ## Add demo data — PROFILE=tiny|small|medium|large
	$(MANAGE) seed_demo --settings=$(DEMO_SETTINGS) --profile=$(PROFILE)

demo-reseed: ## Delete demo data and seed it again
	$(MANAGE) seed_demo --settings=$(DEMO_SETTINGS) --profile=$(PROFILE) --fresh

demo-clear: ## Delete demo data, keeping the schema and any real records
	$(MANAGE) seed_demo --settings=$(DEMO_SETTINGS) --clear

demo-reset: ## Drop the demo database entirely and rebuild it
	rm -f $(DEMO_DB) $(DEMO_DB)-wal $(DEMO_DB)-shm
	$(MAKE) demo-setup PROFILE=$(PROFILE)

demo-shell: ## Django shell against the demo database
	$(MANAGE) shell --settings=$(DEMO_SETTINGS)

demo-seeders: ## List the registered seeders
	$(MANAGE) seed_demo --settings=$(DEMO_SETTINGS) --list

demo-smoke: ## Walk the demo environment in a real browser (screenshots in var/demo-smoke/)
	$(PYTHON) scripts/demo_smoke.py

# ============================================================
# Frontend
# ============================================================
npm-dev: ## Start the Vite dev server
	npm run dev

npm-build: ## Build frontend assets for production
	npm run build

# ============================================================
# Code quality
# ============================================================
beautify: ## Format code with black and isort
	uv run black $(PY_PATHS)
	uv run isort $(PY_PATHS)

lint: ## Run the flake8 linter
	uv run flake8 $(PY_PATHS)

check: beautify lint ## Format and lint

version-check: ## Verify the version matches across pyproject/package.json/package-lock
	$(PYTHON) scripts/check_version_sync.py

ci: beautify lint version-check test ## Full pre-commit checklist: format + lint + versions + tests

check-docker: ## Run the linters inside Docker
	$(DC_EXEC) black --check apps/ config/
	$(DC_EXEC) isort --check-only apps/ config/
	$(DC_EXEC) flake8 apps/ config/

# ============================================================
# Tests
# ============================================================
test: test-js ## Run all tests (Python in parallel + JS unit tests)
	uv run pytest

test-js: ## Run JS unit tests (node --test, no bundler)
	npm test --silent

test-seq: ## Run tests sequentially (for debugging one failure)
	uv run pytest --override-ini="addopts=-v"

test-cov: ## Run tests with a coverage report
	uv run pytest --cov=apps --cov-report=html --cov-report=term-missing

test-docker: ## Run tests in Docker
	$(DC) exec -e DJANGO_SETTINGS_MODULE=config.settings.test web pytest

# ============================================================
# Celery
# ============================================================
celery: ## Start a Celery worker
	uv run celery -A config.celery worker -l info

celery-docker: ## Start a Celery worker in Docker
	$(DC_EXEC) celery -A config.celery worker -l info

# ============================================================
# Production helpers
# ============================================================
deploy: npm-build collectstatic ## Build assets and collect static (pre-deploy step)
