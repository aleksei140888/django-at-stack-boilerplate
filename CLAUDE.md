# CLAUDE.md

This file provides guidance to Claude Code when working in this repository.

## Project overview

Django AT Stack — production-ready boilerplate for SSR web apps.

**Stack:** Django 5.1 + DRF · Alpine.js 3 · Tailwind CSS 4 · DaisyUI 4 · Vite 6 · PostgreSQL 17 · Redis · Celery · Docker

## Development setup

```bash
cp .env.example .env          # edit DATABASE_URL, SECRET_KEY
make install-dev               # uv sync --extra dev + pre-commit install
make npm-install               # Node deps
make migrate                   # run migrations
make superuser                 # create admin user
make npm-dev                   # start Vite (port 5173)
uv run python manage.py runserver  # start Django (port 8000)
```

Or with Docker:

```bash
docker-compose up --build
```

## Package management — uv

Dependencies live in `pyproject.toml`. The lockfile `uv.lock` is committed.

| Command | Description |
|---|---|
| `uv sync --extra dev` | Install all deps including dev extras |
| `uv sync --extra prod` | Install base + Sentry (production) |
| `uv lock` | Regenerate `uv.lock` after editing `pyproject.toml` |
| `uv lock --upgrade` | Upgrade all packages |
| `uv add <pkg>` | Add a new dependency |
| `uv add --optional dev <pkg>` | Add a dev dependency |
| `uv run <cmd>` | Run a command inside the managed venv |

**Do not** create or edit `requirements/*.txt` — the project uses `pyproject.toml` exclusively.

## Common commands

| Command | Description |
|---|---|
| `make up` | Start Docker services |
| `make migrate` | Run migrations |
| `make makemigrations` | Create new migrations |
| `make test` | Run pytest |
| `make format` | black + isort |
| `make lint` | flake8 |
| `make check` | format + lint |
| `make npm-dev` | Vite dev server |
| `make npm-build` | Build frontend for prod |
| `make shell` | Django shell |
| `make lock` | Regenerate uv.lock |
| `make lock-upgrade` | Upgrade all packages |

## Project structure

```
apps/
  accounts/   — custom User model, full auth (register/login/password reset/profile)
  core/       — sitemap, robots.txt, security middleware, context processors, API health
  pages/      — home, contact, privacy, terms, cookies
config/
  settings/
    base.py   — shared settings
    dev.py    — development overrides
    prod.py   — production overrides (Sentry, security headers)
  urls.py
  celery.py
templates/
  base.html              — root layout with dark/light theme
  core/
    health.html          — system health dashboard (Alpine.js, auto-refresh 60 s)
  partials/
    _meta_seo.html       — SEO meta tags, OG, Twitter Card, canonical
    _schema_org.html     — schema.org JSON-LD
    _navbar.html
    _footer.html
    _messages.html       — flash messages (Alpine auto-dismiss)
    _cookie_consent.html — GDPR cookie banner
  accounts/              — all auth templates
  pages/                 — content page templates
  errors/                — 404, 403, 500
  email/                 — transactional email templates
static/src/
  js/main.js   — Alpine.js components (themeManager, cookieConsent, searchDemo,
                 modal, toast, healthDashboard)
  css/main.css — Tailwind CSS 4 + DaisyUI
pyproject.toml — all Python dependencies + tool configs (black, isort, pytest)
uv.lock        — committed lockfile
```

## Key conventions

### Python

- Line length: **100** (black + flake8)
- Imports sorted with **isort** (profile=black)
- All new apps go under `apps/`
- Settings split into `base` / `dev` / `prod` — never hardcode secrets
- Use `env("VAR")` from `django-environ` for all env variables

### Django

- Custom user model: `apps.accounts.User` (email as USERNAME_FIELD, no username)
- Always use `get_user_model()` when referencing the User model
- URL namespaces: `accounts:`, `pages:`, `api:`
- Views pass `page_title` and `meta_description` to context for SEO
- All forms include `{% csrf_token %}` — never skip it

### Templates

- Extend `base.html` for all pages
- Set `{% block title %}`, `{% block meta_description %}`, `{% block canonical %}` per page
- Use `{% trans %}` / `{% blocktrans %}` for all user-facing strings
- One `<h1>` per page — required for SEO
- Breadcrumb nav on inner pages (DaisyUI `breadcrumbs`)

### Frontend (Alpine.js)

- Register all Alpine components in `static/src/js/main.js` before `Alpine.start()`
- Use `apiFetch(url, options)` from `main.js` for API calls — it handles CSRF automatically
- Theme is controlled via `data-theme` on `<html>` — do not override inline
- Form inputs automatically get DaisyUI styles via base CSS layer rules

### Health checks

- Add new checks in any app with `@HealthCheck.register("name")` from `apps.core.health`
- Check functions return `{"status": "ok"|"degraded"|"error", ...extra_fields}`
- Raising any exception automatically marks the check as `"error"`

### SEO checklist for new pages

- [ ] Set `page_title` and `meta_description` in view context
- [ ] One `<h1>` in the template
- [ ] Pass `schema_type` if relevant (e.g., `"Article"`, `"Product"`)
- [ ] Add URL to `StaticViewSitemap.items()` in `apps/core/sitemaps.py`
- [ ] Set `noindex=True` in context for pages that should not be indexed

## Running tests

```bash
make test          # all tests
make test-cov      # with coverage report (htmlcov/)
uv run pytest apps/accounts/tests.py  # single file
uv run pytest -k "login"              # by name pattern
```

Tests use SQLite in memory by default (no Docker needed). Fixtures are in `conftest.py`.

## Adding a new app

```bash
uv run python manage.py startapp myapp apps/myapp
```

Then:
1. Add `"apps.myapp"` to `LOCAL_APPS` in `config/settings/base.py`
2. Create `apps/myapp/urls.py` with `app_name`
3. Include in `config/urls.py`
4. Add to `apps/core/sitemaps.py` if it has public pages

## Adding a Python dependency

```bash
uv add <package>                    # production dep
uv add --optional dev <package>     # dev-only dep
uv add --optional prod <package>    # production extras (e.g. sentry)
# uv.lock is updated automatically — commit both files
```

## Environment variables

All variables are documented in `.env.example`. Required for local dev:

```
SECRET_KEY=...
DATABASE_URL=postgres://...
DJANGO_SETTINGS_MODULE=config.settings.dev
```

For production additionally set:
```
SENTRY_DSN=...
REDIS_URL=...
AWS_STORAGE_BUCKET_NAME=...  (optional, enables S3 for media)
```

## Deployment

```bash
make deploy          # npm build + collectstatic
docker-compose -f docker-compose.prod.yml up -d
```

Production uses Gunicorn (4 workers) behind Nginx with SSL termination.
Static files served by WhiteNoise (Django) and Nginx directly.
uv manages the production venv inside the Docker image via `uv sync --frozen --extra prod`.
