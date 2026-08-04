# Deployment

The template ships a Docker path. Everything here also applies to a bare
gunicorn-behind-nginx deployment — the images just make the steps explicit.

## Images

`Dockerfile` is multi-stage:

| Stage | What it does |
|---|---|
| `frontend` | `npm ci` + `npm run build` → `static/dist` |
| `base` | Python 3.12 + uv, shared by both app stages |
| `dev` | `uv sync --frozen` (dev group included), runserver |
| `prod` | `uv sync --frozen --extra prod --no-dev`, collectstatic, gunicorn |

Two details worth knowing before you edit it:

- The frontend stage copies `templates/` and `apps/` as well as `static/src`.
  Tailwind scans them for class names (`@source` in `main.css`); build without
  them and the bundle comes out with no utilities and the site renders unstyled.
- The `collectstatic` layer sets a placeholder `SECRET_KEY`. Production settings
  read it from the environment and the build has none, so the layer would fail
  without it. The value never reaches a running container.

```bash
make build-prod                                # build the production image
docker compose -f docker-compose.prod.yml up -d
```

The production stack is gunicorn (4 workers) behind nginx for TLS and static
files, plus Postgres, Redis and a Celery worker.

## Static and media files

Static files are collected into `STATIC_ROOT` and served by WhiteNoise with
`CompressedManifestStaticFilesStorage` — hashed filenames, so a cache header of a
year is safe.

`STATICFILES_DIRS` lists prefixed directories (`dist`, `img`) rather than the
whole `static/` tree. This matters: `static/src` is the Vite build root, and
collecting it would make the manifest storage fail trying to resolve
`@import "tailwindcss"` inside the sources.

Media files go to local disk by default. Setting `AWS_STORAGE_BUCKET_NAME`
switches them to S3 (or any S3-compatible provider via `AWS_S3_ENDPOINT_URL` —
DigitalOcean Spaces, Cloudflare R2, MinIO). `MEDIA_URL` then points at the bucket
or the CDN domain, the storage health check verifies connectivity, and the CDN
origin is added to the CSP automatically.

## Environment

Every variable is documented in `.env.example`. The ones production will not
start correctly without:

| Variable | Why |
|---|---|
| `SECRET_KEY` | no default, by design |
| `ALLOWED_HOSTS` | the real hostnames |
| `DATABASE_URL` | |
| `REDIS_URL` | cache, Celery broker and result backend |
| `SITE_URL` | canonical URLs, Open Graph, the sitemap |
| `CSRF_TRUSTED_ORIGINS` | required once the site is behind HTTPS on a real domain |

`prod.py` sets `SECURE_PROXY_SSL_HEADER`. Behind nginx Django only ever sees
plain HTTP; without that mapping `SECURE_SSL_REDIRECT` treats every request as
insecure and redirects forever.

## Before the first deploy

- [ ] `SECRET_KEY` generated, not copied from `.env.example`
- [ ] `DEBUG=False` (the default in `prod.py`)
- [ ] `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` set
- [ ] `uv run python manage.py check --deploy --settings=config.settings.prod` clean
- [ ] `/api/v1/health/` reachable from the monitor, and its 503 wired to an alert
- [ ] `METRICS_TOKEN` set if something scrapes `/metrics`
- [ ] `SENTRY_DSN` set, if you use Sentry
- [ ] backups of the database, verified by restoring one

## On every deploy

Order matters:

1. `npm run build` — assets
2. `manage.py collectstatic --noinput` — **before** migrate
3. `manage.py migrate`
4. restart gunicorn, then the Celery worker

Collectstatic goes before migrate because the URLconf resolves static URLs at
import time when the manifest storage is in use: with no manifest present, every
management command — including `migrate` — fails to start.

Send Celery `SIGTERM` and give it time to finish in-flight tasks; killing it
mid-task loses the task silently.

## Switching to psycopg 3

The lockfile ships `psycopg2-binary`, which is what this stack has been running.
Django supports psycopg 3 as well and it is the better long-term choice:

```bash
uv remove psycopg2-binary && uv add "psycopg[binary]"
```

No settings change is needed — `env.db()` produces the same
`django.db.backends.postgresql` engine. Run the test suite against Postgres, not
just SQLite, before shipping the change.
