# Demo environment

A working site with realistic data, in one command, with no Docker, no Redis and
no API keys.

```bash
make demo-up      # build assets if needed, migrate, seed, run on :8000
```

Log in with any of the demo accounts — the password for all of them is
`demo12345`:

| Email | Role |
|---|---|
| `admin@demo.local` | superuser, reaches `/admin/` |
| `moderator@demo.local` | staff |
| `user@demo.local` | ordinary user |

## What it is

`config.settings.demo` — a development layer with everything expensive swapped
for a local equivalent: SQLite instead of Postgres, inline Celery instead of a
broker, console email instead of SMTP, local disk instead of S3. It sets its own
`SECRET_KEY`, so it works on a clone with no `.env`.

Assets come from the built bundle in `static/dist`, not from the Vite dev server
— this is "one command and a site", and nobody is running `npm run dev` next to
it. `make demo-assets` builds it once if it is missing.

Do not use it to measure query performance: SQLite and Postgres choose different
plans, and a query that is slow in production can look fast here.

## Commands

| Command | Does |
|---|---|
| `make demo-up` | everything: assets, migrate, seed, serve |
| `make demo-run` | just the server, against the existing database |
| `make demo-seed PROFILE=medium` | add more data |
| `make demo-reseed` | delete demo data and seed again |
| `make demo-clear` | delete demo data, keep the schema |
| `make demo-reset` | drop the database file and rebuild from scratch |
| `make demo-seeders` | list the registered seeders |
| `make demo-shell` | Django shell against the demo database |
| `make demo-smoke` | walk the site in Chromium |

## Volume profiles

| Profile | For |
|---|---|
| `tiny` | smoke tests — seeds in about a second |
| `small` | default: every scenario covered, data still readable |
| `medium` | pagination, filters, list-page load |
| `large` | query profiling and N+1 hunting at realistic volumes |

A seeder never hardcodes counts; it asks `ctx.count("users")` and the profile
scales it. Adding a domain means adding keys to `_BASE_COUNTS` in
`apps/core/seeding/profiles.py`.

## The demo marker

Everything a seeder creates has to be findable by a marker — for accounts, the
`@demo.local` email domain. That is what makes `--fresh` and `--clear` safe to run
against a database that also holds real records, and it is checked by a test.

`seed_demo` refuses to run when `DEBUG=False` unless you pass `--force`: seeding
a production database is not something you undo.

Adding demo data for your own domain:
[`playbooks/add-seeder.md`](playbooks/add-seeder.md).

## The smoke walk

```bash
make demo-smoke                                  # starts its own server
uv run python scripts/demo_smoke.py --base-url http://localhost:8000
uv run python scripts/demo_smoke.py --headed     # watch it happen
```

It drives Chromium through every listed page, logging in where a page needs it,
and fails on:

- a non-200 response,
- an error in the browser console,
- missing expected text,
- **horizontal overflow at 360px or 390px** — the mobile-first rule from
  `CLAUDE.md`, checked rather than remembered.

Screenshots for every page (and for every overflow failure) land in
`var/demo-smoke/`, which is where to look first when it fails.

This is the layer that catches what pytest cannot: a bundle that built empty, an
Alpine component that never initialised, a template comment that leaked into the
page. All three of those were real defects found this way.

Playwright's browsers are not installed by default:

```bash
uv run playwright install chromium
```

In a container that already ships one, `PLAYWRIGHT_BROWSERS_PATH` is picked up
automatically.
