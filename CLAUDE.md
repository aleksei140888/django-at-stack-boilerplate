# CLAUDE.md

Guidance for coding agents working in this repository. Humans: `README.md` is the
front door, this file is the working manual.

**Django AT Stack** — a boilerplate for server-rendered web apps: Django + DRF on
the back, Alpine.js + Tailwind + DaisyUI on the front, Vite for the build. The
exact stack is in `pyproject.toml` and `package.json`; nothing here restates
version numbers, because a restated version number goes stale.

## Before you start a task

1. Skim the index at the top of [`docs/agents.md`](docs/agents.md) — the project's
   memory of decisions and edge cases. Open **only** the sections the index points
   at; do not read it end to end.
2. Use the routing table below to find the one document that covers your task. If
   nothing matches, the full catalogue is in [`docs/README.md`](docs/README.md).

| What you are deciding | What to read |
|---|---|
| Where a piece of code belongs, how apps talk to each other | [`architecture.md`](docs/architecture.md) |
| Naming, commits, versioning, style, opt-in gates | [`conventions.md`](docs/conventions.md) |
| Anything visual — colour, type, spacing, motion, components | [`design.md`](docs/design.md), specified in [`DESIGN.md`](DESIGN.md) |
| Writing tests — factories, parallel runs, budgets | [`testing.md`](docs/testing.md) |
| Getting a running site with data to click through | [`test-environment.md`](docs/test-environment.md) |
| Logs, metrics, health checks, an incident in production | [`observability.md`](docs/observability.md) |
| Shipping it — Docker, static files, environment variables | [`deployment.md`](docs/deployment.md) |
| Adding a new app | [`playbooks/add-app.md`](docs/playbooks/add-app.md) |
| Adding demo data for a domain | [`playbooks/add-seeder.md`](docs/playbooks/add-seeder.md) |
| Adding a health check for a dependency | [`playbooks/add-health-check.md`](docs/playbooks/add-health-check.md) |

## Conventions

**Python.** Apps live under `apps/`. Secrets come from `env("VAR")` and every
variable is listed in `.env.example`. Line length 100, black + isort + flake8.

**Layers.** `selectors.py` holds every SELECT (filters, search, read aggregation);
`services.py` holds everything that writes (create/update/delete plus side
effects such as sending mail). Views call those — they do not build querysets
inline. The payoff arrives the third time a filter is needed.

**Settings.** Four layers, none of them imported directly: `dev`, `test`, `demo`,
`prod` (see the module docstring in `config/settings/base.py`). `test` and `demo`
provide their own `SECRET_KEY`, so a fresh clone runs `make test` and
`make demo-up` with no `.env` at all.

**Django.**
- Custom user `apps.accounts.User`, email as `USERNAME_FIELD`
- URL namespaces: `accounts:`, `pages:`, `api:`
- Views put `page_title` and `meta_description` in the context
- One `<h1>` per page; add public pages to `apps/core/sitemaps.py`

**Templates.**
- `{% trans %}` for every user-facing string
- **`{# … #}` is single-line only.** A multi-line one leaks its own text into the
  page and can swallow the tag that follows it. Use `{% comment %}` blocks.
- **Do not override `{% block canonical %}` with a full `<link>` tag** —
  `canonical_url` comes from a context processor and is already inside `href=""`.
  Django passes an overridden block through `{% include %}` as a string.
- Anything visible by default behind an `x-show` needs `x-cloak`, or it flashes
  before Alpine initialises.

**Mobile-first is the default for all frontend work,** admin screens included.
Base classes target a narrow screen; `sm:`/`lg:` *add* width rather than rescue
it. Typical markers of desktop-first markup: a row of controls with no
`flex-wrap`, fixed widths without an `sm:` prefix, `grid-flow-col` for a list that
has to wrap. Check before committing anything visible: at 360 and 390px,
`document.documentElement.scrollWidth == clientWidth`. `make demo-smoke` asserts
exactly that on every page it walks.

**Frontend.** Alpine components are registered in `main.js` before
`Alpine.start()`; requests go through `apiFetch(url, options)`, which attaches the
CSRF token. Tailwind finds class names through the `@source` lines in `main.css` —
a new template directory outside `templates/` and `apps/` needs a line there, or
its classes are silently dropped from the bundle.

**Design.** The visual system is [`DESIGN.md`](DESIGN.md); how it maps onto the
code is [`docs/design.md`](docs/design.md). Templates use semantic classes
(`bg-base-200`, `text-primary`) and the component classes (`.btn-tribal`,
`.card-tribal`, `.field-label`) — never raw hex, so retheming stays one block of
CSS. The theme is dark-only and fixed on `<html>`; there is no switcher. No emoji
in the UI (inline SVG icons instead), no `h-screen` (use `min-h-[100dvh]`), and
`apps/core/tests/test_design.py` enforces the rules that are checkable.

**Version.** `YYYY.M.PATCH`, identical in `pyproject.toml`, `package.json` and
`package-lock.json`. The same commit that changes code bumps it, otherwise
`auto-tag.yml` creates no tag. `make version-check` (also a pre-commit hook)
catches the drift.

## Architecture in one paragraph

Apps depend on each other only through contracts — base classes, registries,
signals — never by importing another app's internals. Wiring happens by
autodiscovery on module name (`seeding.py`), extension by decorator
(`@register_seeder`, `@HealthCheck.register`). Adding an app requires no change
in `apps/core`. Details and the reasoning: [`docs/architecture.md`](docs/architecture.md).

## Commands

`make help` lists everything. The ones that matter day to day:

| Command | What it does |
|---|---|
| `make demo-up` | SQLite + demo data + server, no Docker, no API keys |
| `make test` | Python tests in parallel + JS unit tests |
| `make ci` | format + lint + version check + tests |
| `make demo-smoke` | walks the demo site in Chromium, screenshots in `var/` |

## Working rhythm

**TDD is required** for business logic, services, models, API and views. Tests are
**not** required for text and template typos, config and constants without logic,
documentation, or cosmetic CSS/JS. Mechanics: [`docs/testing.md`](docs/testing.md).

**After every change:** `make ci`, or step by step with `make beautify` /
`make lint` / `make version-check` / `make test`. Use `# noqa` only with a reason
worth reading.

**Update documentation in the same commit:** architecture or domain model →
the matching file in `docs/`; project structure, stack or setup → `README.md`;
conventions → this file. Decisions and edge cases → the
[`memory`](.claude/skills/memory/SKILL.md) skill (`docs/agents.md`).

**Noticed something outside the scope of your task** — undocumented behaviour in a
dependency, technical debt, a strange shape in real data — write one line into
`docs/agents.md` → "Incidental observations" straight away, without waiting for a
better moment.

Commits: `<type>(<scope>): <short description>`, body after a blank line when it
earns its place. Explain *why*, not *what* — the diff already says what.
