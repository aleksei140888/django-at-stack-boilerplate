# django-at-stack

> Django + Alpine.js + Tailwind CSS + DaisyUI — a boilerplate for server-rendered
> web apps, set up so that a person or a coding agent can start building on
> day one.

```bash
git clone https://github.com/aleksei140888/django-at-stack-boilerplate my-project
cd my-project
make demo-up          # a running site with demo data on :8000 — no Docker, no keys
```

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 6 + Django REST Framework |
| Frontend | Alpine.js 3 |
| Styling | Tailwind CSS 4 + DaisyUI 5 |
| Build | Vite 6 |
| Database | PostgreSQL 17 (SQLite for tests and the demo environment) |
| Cache / queue | Redis + Celery |
| Static files | WhiteNoise; media optionally on S3 |
| Auth | Custom `User` model (email login) + django-allauth |
| Packaging | uv (`pyproject.toml` + committed `uv.lock`) |
| Infra | Docker + docker compose, GitHub Actions |

Exact versions live in `pyproject.toml` and `package.json`.

## Why this stack

- **Server-rendered.** Good SEO by default, no hydration, no API layer to keep in
  sync with a client.
- **Alpine.js for interactivity.** Small enough that a page's behaviour reads next
  to its markup; no component framework to learn.
- **Tailwind 4 + DaisyUI 5.** Accessible components with light and dark themes,
  and a bundle that only contains classes actually used.
- **uv.** Dependency resolution measured in milliseconds and a lockfile that is
  actually committed.

## What is in the box

**Application**
- Custom `User` model — email login, roles, GDPR consent, avatar
- Full auth flow: register, log in, password reset and change, profile, account
  deactivation
- Content pages, contact form, error pages (403/404/500), cookie consent banner
- SEO: sitemap.xml, robots.txt, canonical URLs, Open Graph, Twitter Card,
  schema.org

**Operations**
- `/api/v1/health/` with a pluggable check registry, and `/health/` as a live
  dashboard
- Request-id correlation across logs, response headers and Sentry
- Structured JSON logging in production
- `/metrics` for Prometheus, behind a token
- Security headers and a CSP assembled from settings

**Development**
- Four settings layers: `dev`, `test`, `demo`, `prod`
- A demo environment with seeded data in one command, no infrastructure
- Tests in parallel (pytest-xdist), factories, query budgets, JS unit tests via
  `node --test`
- A browser smoke walk that fails on console errors and on horizontal overflow at
  phone widths
- CI: lint, missing-migration check, tests, frontend build, collectstatic, and an
  end-to-end run of the seeder
- Version consistency enforced across `pyproject.toml`, `package.json` and
  `package-lock.json`

**For coding agents**
- `CLAUDE.md` / `AGENTS.md` — conventions and a routing table into `docs/`
- `docs/agents.md` — project memory: decisions and edge cases that already cost
  somebody time
- Playbooks for the repetitive tasks (add an app, a seeder, a health check)
- A `SessionStart` hook that installs dependencies and seeds a demo database, so
  a cloud session starts with a runnable app

## Getting started

### Just look at it

```bash
make demo-up
```

SQLite, seeded data, built assets, server on http://localhost:8000. No `.env`, no
Docker, no API keys. Log in as `user@demo.local` / `demo12345` (also
`admin@demo.local` and `moderator@demo.local`).

### Develop on it

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) and
Node.js 22+.

```bash
make install-dev      # Python deps + pre-commit hooks
make npm-install      # Node deps
make env-copy         # .env from .env.example — set SECRET_KEY and DATABASE_URL
make migrate
make create-admin EMAIL=you@example.com PASSWORD=...

# two terminals
make npm-dev          # Vite on :5173
uv run python manage.py runserver
```

### With Docker

```bash
make env-copy
make up               # Postgres, Redis, Django, Vite, Celery
```

## Everyday commands

`make help` lists all of them.

| Command | Does |
|---|---|
| `make demo-up` | demo environment: assets, migrations, seed data, server |
| `make test` | Python tests in parallel + JS unit tests |
| `make ci` | format + lint + version check + tests |
| `make demo-smoke` | walk the demo site in Chromium, screenshots in `var/` |
| `make lock-upgrade` | upgrade every Python package |
| `make build-prod` | build the production image |

## Making it your own

1. Rename the project: `name` in `pyproject.toml` and `package.json`, the app
   name in `config/celery.py`, `SITE_NAME` in `.env`.
2. Reset the version to something like `2026.1.0` in all three files
   (`make version-check` verifies them).
3. Replace the placeholder artwork in `static/img/`.
4. Rewrite the content pages in `templates/pages/` — privacy, terms, cookies are
   scaffolding, not legal advice.
5. Rewrite `CLAUDE.md`'s first paragraph for your product, and empty
   `docs/agents.md` down to its index.
6. Add your first app: [`docs/playbooks/add-app.md`](docs/playbooks/add-app.md).

## Documentation

| Document | Covers |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Conventions and routing — the working manual |
| [`docs/architecture.md`](docs/architecture.md) | Where code belongs and how apps stay decoupled |
| [`docs/conventions.md`](docs/conventions.md) | Style, commits, versioning, gates |
| [`docs/testing.md`](docs/testing.md) | Test mechanics and the parallel-run rules |
| [`docs/test-environment.md`](docs/test-environment.md) | The demo environment and the smoke walk |
| [`docs/observability.md`](docs/observability.md) | Logs, health, metrics, incident steps |
| [`docs/deployment.md`](docs/deployment.md) | Images, static files, environment, checklists |
| [`docs/README.md`](docs/README.md) | Full catalogue |

## License

MIT
