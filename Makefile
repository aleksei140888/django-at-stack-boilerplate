.DEFAULT_GOAL := help
.PHONY: help install install-dev up down build logs shell db-shell migrate makemigrations \
        superuser test lint format check collectstatic npm-install npm-dev npm-build \
        celery flush lock

MANAGE      := uv run python manage.py
DC          := docker-compose
DC_EXEC     := $(DC) exec web
SETTINGS    := config.settings.dev

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
install: ## Install production dependencies (uv sync)
	uv sync --extra prod

install-dev: ## Install all dev dependencies
	uv sync --extra dev
	uv run pre-commit install

lock: ## Regenerate uv.lock from pyproject.toml
	uv lock

lock-upgrade: ## Upgrade all packages and regenerate uv.lock
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

build-prod: ## Build production Docker image
	docker build --target prod -t django-at-stack:prod .

logs: ## Follow logs from all services
	$(DC) logs -f

logs-web: ## Follow web service logs
	$(DC) logs -f web

ps: ## Show running containers
	$(DC) ps

restart: ## Restart web service
	$(DC) restart web

# ============================================================
# Django management
# ============================================================
shell: ## Open Django shell
	$(MANAGE) shell --settings=$(SETTINGS)

shell-docker: ## Open Django shell in Docker
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

superuser: ## Create superuser
	$(MANAGE) createsuperuser --settings=$(SETTINGS)

superuser-docker: ## Create superuser in Docker
	$(DC_EXEC) python manage.py createsuperuser

collectstatic: ## Collect static files
	$(MANAGE) collectstatic --noinput --settings=$(SETTINGS)

flush: ## Flush the database (WARNING: destroys all data)
	$(MANAGE) flush --no-input --settings=$(SETTINGS)

# ============================================================
# Frontend
# ============================================================
npm-dev: ## Start Vite dev server
	npm run dev

npm-build: ## Build frontend assets for production
	npm run build

# ============================================================
# Code quality
# ============================================================
format: ## Format code with black and isort
	uv run black apps/ config/
	uv run isort apps/ config/

lint: ## Run flake8 linter
	uv run flake8 apps/ config/

check: format lint ## Format and lint (run both)

check-docker: ## Run linting inside Docker
	$(DC_EXEC) black --check apps/ config/
	$(DC_EXEC) isort --check-only apps/ config/
	$(DC_EXEC) flake8 apps/ config/

# ============================================================
# Tests
# ============================================================
test: ## Run tests
	uv run pytest

test-cov: ## Run tests with coverage report
	uv run pytest --cov=apps --cov-report=html --cov-report=term-missing

test-docker: ## Run tests in Docker
	$(DC_EXEC) pytest

# ============================================================
# Celery
# ============================================================
celery: ## Start Celery worker
	uv run celery -A config.celery worker -l info

celery-docker: ## Start Celery worker in Docker
	$(DC_EXEC) celery -A config.celery worker -l info

# ============================================================
# Production helpers
# ============================================================
deploy: npm-build collectstatic ## Build assets and collect static (pre-deploy step)
