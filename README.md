# django-at-stack

> Django + Alpine.js + Tailwind CSS + DaisyUI — production-ready boilerplate for SSR web apps.

## Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.1 + Django REST Framework |
| Frontend | Alpine.js 3.x |
| Styling | Tailwind CSS 4.x + DaisyUI 4.x |
| Build | Vite 6 |
| Database | PostgreSQL 16 |
| Cache / Queue | Redis 7 + Celery |
| Infra | Docker + docker-compose |
| Static files | WhiteNoise |
| Auth | django-allauth + custom User model |

## Why this stack?

- **Full SSR** — great for SEO out of the box, no hydration complexity
- **No SPA overhead** — Django templates handle rendering, Alpine.js handles interactivity
- **Alpine.js** — minimal JS footprint, reactive UI without a build step for logic
- **Tailwind 4 purges unused CSS** — tiny bundle in production
- **DaisyUI** — ready-made accessible components with built-in dark/light themes

## Features

- [x] Django 5 + DRF configured with pagination, filtering, throttling
- [x] Tailwind CSS 4 + DaisyUI via Vite
- [x] Alpine.js integrated (theme manager, cookie consent, live search, modal, toast)
- [x] Dark / light theme with **system preference auto-detection** + localStorage persistence
- [x] Custom `User` model — email auth, roles, GDPR consent, avatar
- [x] Full authentication — register, login, logout, password reset/change, profile, account deletion
- [x] Base templates with layout, navbar, footer, breadcrumbs
- [x] SEO-ready — sitemap.xml, robots.txt, Open Graph, Twitter Card, schema.org, canonical URLs
- [x] Cookie consent banner + Privacy Policy, Terms of Use, Cookie Policy pages
- [x] Contact form with email sending
- [x] Docker + docker-compose (dev + prod configs)
- [x] PostgreSQL + Redis + Celery
- [x] Static files via WhiteNoise
- [x] Environment config via django-environ
- [x] Error pages — 404, 403, 500
- [x] Security headers middleware
- [x] Health check API endpoint
- [x] Code quality — black, isort, flake8, pre-commit
- [x] Tests — pytest with fixtures and smoke tests
- [x] Makefile with all common dev commands

## Quick start

### Docker (recommended)

```bash
git clone https://github.com/aleksei140888/django-at-stack-boilerplate
cd django-at-stack-boilerplate
cp .env.example .env       # edit SECRET_KEY and any other values
docker-compose up --build
```

Open http://localhost:8000

### Local development

```bash
# Python
python -m venv .venv && source .venv/bin/activate
make install-dev

# Node
make npm-install

# Environment
cp .env.example .env
# edit .env — set DATABASE_URL, SECRET_KEY

# Database
make migrate
make superuser

# Start servers (two terminals)
make npm-dev               # Vite on :5173
python manage.py runserver # Django on :8000
```

## Project structure

```
apps/
├── accounts/      # Custom User model + full auth flow
├── core/          # Sitemap, robots.txt, middleware, context processors, health API
└── pages/         # Home, contact, privacy, terms, cookies
config/
├── settings/
│   ├── base.py    # Shared settings
│   ├── dev.py     # Development overrides
│   └── prod.py    # Production (Sentry, security headers)
├── urls.py
└── celery.py
templates/
├── base.html                    # Root layout — dark/light theme, SEO head
├── partials/
│   ├── _meta_seo.html           # title, canonical, OG, Twitter Card
│   ├── _schema_org.html         # JSON-LD structured data
│   ├── _navbar.html
│   ├── _footer.html
│   ├── _messages.html           # Flash messages (Alpine auto-dismiss)
│   └── _cookie_consent.html     # GDPR cookie banner
├── accounts/                    # Login, register, profile, password reset templates
├── pages/                       # Content page templates
└── errors/                      # 404, 403, 500
static/src/
├── js/main.js     # Alpine.js components + apiFetch() CSRF helper
└── css/main.css   # Tailwind CSS 4 + DaisyUI
```

## Makefile commands

```bash
make help           # list all commands

# Docker
make up             # start all services
make down           # stop services
make logs           # follow logs

# Django
make migrate        # run migrations
make makemigrations # create new migrations
make superuser      # create admin user
make shell          # Django shell

# Frontend
make npm-dev        # Vite dev server
make npm-build      # build for production

# Code quality
make format         # black + isort
make lint           # flake8
make check          # format + lint

# Tests
make test           # pytest
make test-cov       # pytest with coverage report

# Production
make deploy         # npm build + collectstatic
```

## Environment variables

Copy `.env.example` to `.env` and adjust:

```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgres://postgres:postgres@db:5432/django_at_stack
REDIS_URL=redis://redis:6379/0
SITE_URL=http://localhost:8000
SITE_NAME=My Site
```

See `.env.example` for the full list including email, S3, and Sentry settings.

## Authentication

The `accounts` app provides a complete auth flow out of the box:

| URL | View |
|---|---|
| `/accounts/register/` | Registration with GDPR consent |
| `/accounts/login/` | Login with "remember me" |
| `/accounts/logout/` | POST logout |
| `/accounts/profile/` | Edit profile, avatar |
| `/accounts/password/change/` | Change password |
| `/accounts/password/reset/` | Request reset email |
| `/accounts/password/reset/confirm/<uid>/<token>/` | Set new password |
| `/accounts/profile/delete/` | Deactivate account |

### User model

```python
class User(AbstractBaseUser, PermissionsMixin):
    email           # unique, used as USERNAME_FIELD
    first_name
    last_name
    role            # guest / user / moderator / admin
    avatar
    bio
    gdpr_consent    # required at registration
    email_notifications
```

## SEO

Every page supports:

```python
# In any view:
return render(request, "template.html", {
    "page_title": "My Page",
    "meta_description": "Description for search engines.",
    "schema_type": "Article",   # schema.org type
    "noindex": False,           # set True to exclude from indexing
})
```

This automatically populates:
- `<title>`, `<meta name="description">`, `<link rel="canonical">`
- Open Graph (`og:title`, `og:description`, `og:image`, `og:url`)
- Twitter Card
- schema.org JSON-LD block

Add new public pages to `apps/core/sitemaps.py` to include them in `sitemap.xml`.

## Alpine.js components

Registered globally in `static/src/js/main.js`:

```html
<!-- Dark/light theme -->
<html x-data="themeManager()" x-init="initTheme()" :data-theme="theme">

<!-- Toggle button -->
<button @click="toggleTheme()">...</button>

<!-- Cookie consent -->
<div x-data="cookieConsent()" x-show="!accepted">...</div>

<!-- Live search -->
<div x-data="searchDemo()">
  <input x-model="query">
  <template x-for="item in filtered">...</template>
</div>

<!-- Modal -->
<div x-data="modal()">
  <button @click="show()">Open</button>
  <div x-show="open" @click.outside="hide()">...</div>
</div>
```

### API fetch helper

```js
import { apiFetch } from "/static/src/js/main.js";

// Automatically includes CSRF token
const data = await apiFetch("/api/v1/endpoint/", {
  method: "POST",
  body: JSON.stringify({ key: "value" }),
});
```

## Production deployment

```bash
# Build frontend assets
make npm-build

# Start production stack
docker-compose -f docker-compose.prod.yml up -d
```

Production stack includes:
- Gunicorn (4 workers) as WSGI server
- Nginx for SSL termination and static file serving
- PostgreSQL + Redis
- Celery worker

Set these additional env vars for production:

```env
DEBUG=False
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SENTRY_DSN=https://...
```

## Code quality

```bash
make format    # auto-format with black + isort
make lint      # flake8
make check     # both
```

Pre-commit hooks (installed via `make install-dev`):
- `black` — code formatting (line length 100)
- `isort` — import sorting
- `flake8` + `flake8-django` + `flake8-bugbear`
- Standard hooks: trailing whitespace, end-of-file, merge conflicts

## Running tests

```bash
make test                          # all tests
make test-cov                      # with HTML coverage report
pytest apps/accounts/tests.py      # single module
pytest -k "login"                  # by name
```

Tests use SQLite in memory — no Docker required for running the test suite.

## License

MIT
