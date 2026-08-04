# Architecture

What goes where, and why the boundaries sit where they do.

## The shape

```
config/          settings layers, root URLconf, WSGI/ASGI, Celery app
apps/
  accounts/      custom User, auth flow, selectors/services/factories/seeding
  core/          cross-cutting: middleware, health, metrics, seeding framework, sitemaps
  pages/         static content pages and the contact form
templates/       project-level templates; app templates may live in the app
static/
  src/           Vite build root — sources only, never collected into STATIC_ROOT
  dist/          build output (gitignored)
  img/           finished assets served as-is
scripts/         standalone scripts: version sync, smoke walk, opt-in gates
docs/            this folder
```

## Layers inside an app

| File | Holds | Rule |
|---|---|---|
| `models.py` | schema, `__str__`, properties derived from own fields | no queries against other models |
| `selectors.py` | every SELECT — filters, search, read aggregation | no writes, no side effects |
| `services.py` | every write plus its side effects (mail, tasks, cache invalidation) | returns objects, not HTTP responses |
| `forms.py` | validation and widgets | no persistence — `save()` overrides belong in services |
| `views.py` | HTTP: parse the request, call selectors/services, choose a template | no inline querysets |
| `factories.py` | test factories | imported by other apps' tests |
| `seeding.py` | demo data | registers itself, imports nothing from other apps |

The split earns its keep the third time a filter is needed: it exists once, is
tested once, and an N+1 fix lands everywhere at once. It also gives management
commands and API endpoints a path that is not "call the view".

Two things follow that are easy to get wrong:

- **A service takes explicit keyword arguments, not `request` or `cleaned_data`.**
  Passing a form's `cleaned_data` straight into `setattr` is how `is_staff`
  becomes user-editable; `services.update_profile` whitelists fields for exactly
  that reason, and there is a test holding the line.
- **A selector returns a queryset, not a list.** The caller decides whether to
  slice, count or iterate.

## How apps stay decoupled

Apps depend on each other only through contracts — a base class, a registry, a
signal. No app imports another app's internals.

Wiring is by autodiscovery on module name, extension by decorator:

```python
# apps/myapp/seeding.py — core never learns this app exists
from apps.core.seeding import register_seeder

@register_seeder("myapp", order=40, clear=clear_demo_myapp)
def seed_myapp(ctx): ...
```

```python
# health check for a dependency, registered from anywhere
from apps.core.health import HealthCheck

@HealthCheck.register("stripe")
def check_stripe(): ...
```

Registries here are plain dicts with a decorator, not a framework. Seeders
exchange objects through `ctx.store` rather than importing each other, so
deleting an app does not break the seeding chain of the ones that remain.

Adding an app requires no change inside `apps/core`.

## The request path

```
nginx / gunicorn
  → SecurityMiddleware
  → RequestIDMiddleware        mints or reuses X-Request-ID, binds it to logs + Sentry
  → HTTPMetricsMiddleware      per-request Prometheus counters (no-op without the package)
  → WhiteNoise                 static files
  → session / CSRF / auth / messages
  → SecurityHeadersMiddleware  CSP and the headers Django does not set
  → view
```

`RequestIDMiddleware` sits near the top on purpose: the id has to exist before
the first log line of the request is emitted.

## Settings layers

```
base.py   everything shared. Never used directly.
  dev.py    DEBUG, debug toolbar, LocMem cache, Vite dev server
    demo.py   SQLite file + seeded data, external services off  (make demo-up)
  test.py   in-memory SQLite, eager Celery, locmem email, fast hasher
  prod.py   HSTS, secure cookies, JSON logs, optional Sentry
```

`test` extends `base`, not `dev`: tests should not depend on the debug toolbar
being installed, and `DEBUG=False` is closer to how the code runs in production.
`demo` extends `dev` because it is a development environment with data.

`test` and `demo` set their own `SECRET_KEY` before importing `base`, so neither
needs a `.env` file. That is what makes a fresh clone runnable in one command.

## Frontend

One entry point, `static/src/js/main.js`, which imports the stylesheet so Vite
emits both `dist/main.js` and `dist/main.css`. Entry filenames are stable;
cache busting is Django's job through `ManifestStaticFilesStorage`.

Alpine components are registered before `Alpine.start()` — one registered
afterwards is silently inert. Anything talking to the API goes through
`apiFetch`, which attaches the CSRF token and leaves `FormData` bodies alone.

Tailwind v4 discovers class names by scanning the directories listed with
`@source` in `main.css`. The default scan root is the CSS file's own directory,
which contains no templates — so those lines are load-bearing, and a template
directory that is not covered by them loses its classes from the bundle with no
warning anywhere.

## Adding a second language

The template ships single-language for simplicity. To serve several:

1. Add `django.middleware.locale.LocaleMiddleware` after `SessionMiddleware`.
2. Set `LANGUAGES` in `base.py` and keep `LANGUAGE_CODE` as the fallback.
3. Wrap the URLs you want prefixed in `i18n_patterns()`.
4. `django-admin makemessages -l <code>`, translate, `compilemessages`.
5. Add the autouse fixture from `conftest.py` to any new test module that hits
   the client with a non-default `Accept-Language` — `LocaleMiddleware` activates
   a language per request and never deactivates it, so it leaks across tests on
   the same worker.
