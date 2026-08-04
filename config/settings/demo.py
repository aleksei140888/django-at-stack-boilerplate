"""
Demo environment — a working site with data, without Docker, Redis or API keys.

`make demo-up` has to bring the whole app up on a clean machine, so everything
that needs infrastructure or money (Postgres, Redis, SMTP, S3) is swapped for a
local or offline equivalent here.

Do not use it to measure query performance: SQLite and Postgres pick different
plans, and a query that is slow in production can look fast here.
"""

import os

# Secrets have to be in the environment before base.py is imported, otherwise
# `env("SECRET_KEY")` fails on a machine without .env — and the whole point of
# this layer is that no .env is needed.
os.environ.setdefault("SECRET_KEY", "demo-environment-insecure-key-not-for-production")
os.environ.setdefault("DEBUG", "True")

from .dev import *  # noqa: E402, F401, F403

DEMO_DB_PATH = os.environ.get("DEMO_DB_PATH", str(BASE_DIR / "db.demo.sqlite3"))  # noqa: F405

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DEMO_DB_PATH,
        "OPTIONS": {
            # WAL + relaxed sync: seeding thousands of rows on SQLite is bound by
            # fsync, and durability of a demo database matters to nobody.
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;",
            "transaction_mode": "IMMEDIATE",
        },
    }
}

ALLOWED_HOSTS = ["*"]

# No Vite dev server here — this layer is "one command and a site", so assets
# come from the built bundle in static/dist (`make demo-assets` builds it once).
VITE_DEV_SERVER = os.environ.get("VITE_DEV_SERVER", "False") == "True"

# The debug toolbar is useful while clicking through by hand, but it covers half
# the screen in smoke-run screenshots.
if os.environ.get("DEMO_DEBUG_TOOLBAR", "True") != "True":
    INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]  # noqa: F405
    MIDDLEWARE = [item for item in MIDDLEWARE if "debug_toolbar" not in item]  # noqa: F405

# Seeding creates users in bulk; the default hasher makes that take minutes.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# ── External services disabled ────────────────────────────────────────────────

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = False

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
