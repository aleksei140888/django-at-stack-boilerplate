# Playbook: add an app

For a new domain in `apps/`. Nothing in `apps/core` needs to change.

## 1. Create it

```bash
mkdir apps/myapp
uv run python manage.py startapp myapp apps/myapp
```

Fix the app label in `apps/myapp/apps.py` — `startapp` writes the bare name and
Django will not find it:

```python
class MyappConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.myapp"          # not "myapp"
    verbose_name = "My app"
```

Register it in `LOCAL_APPS` in `config/settings/base.py`.

## 2. Give it the layers

Create the files the conventions expect, even if some start nearly empty
([`../architecture.md`](../architecture.md) explains why):

```
apps/myapp/
  models.py       schema
  selectors.py    every SELECT
  services.py     every write and its side effects
  views.py        HTTP only — calls selectors/services
  urls.py         app_name = "myapp"
  factories.py    test factories
  seeding.py      demo data (optional)
  tests/          __init__.py + test_*.py
```

Wire the URLs in `config/urls.py`:

```python
path("myapp/", include("apps.myapp.urls")),
```

## 3. Models and migrations

```bash
make makemigrations
make migrate
```

CI fails on a model change without its migration
(`makemigrations --check --dry-run`), which is the cheapest way to catch the
mistake that otherwise surfaces during a deploy.

## 4. Tests

Write them first for anything with logic. Minimum shape and the parallel-run
rules: [`../testing.md`](../testing.md).

Factories go in `apps/myapp/factories.py`, sequences for every unique field.
`apps/core/tests/test_factories.py` picks them up with no registration.

## 5. Public pages

- Views put `page_title` and `meta_description` in the context
- One `<h1>` per page
- Add public URLs to `StaticViewSitemap.items()` in `apps/core/sitemaps.py` —
  there is a test asserting every listed name resolves
- Set `noindex=True` in the context for anything that should stay out of search

## 6. Demo data

Add a seeder so the app has something to show in `make demo-up`:
[`add-seeder.md`](add-seeder.md).

## 7. Before committing

```bash
make ci
```

If the app has visible pages, add them to `CHECKS` in `scripts/demo_smoke.py` and
run `make demo-smoke` — that is what verifies they render in a browser and fit a
360px screen.
