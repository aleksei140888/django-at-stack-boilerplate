"""
pytest settings — in-memory SQLite, no Docker, no external services.

Extends `base` rather than `dev`: tests should not depend on the debug toolbar
being installed, and DEBUG=False is closer to how the code runs in production.
"""

import os

# Tests must not depend on a .env file: on a fresh clone (CI, a new agent
# session, a new developer) `env("SECRET_KEY")` in base.py would blow up before
# the first test is collected. A real value from .env still wins.
os.environ.setdefault("SECRET_KEY", "test-insecure-key")

from .base import *  # noqa: E402, F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Never send anything anywhere from a test run, whatever .env says — on some
# machines those are real production credentials.
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Celery tasks run inline; no broker needed.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Hashing dominates the runtime of any test that creates users.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Static files: templates call {% static %} everywhere, and the manifest storage
# raises for files that were never collected.
STORAGES = {
    **STORAGES,  # noqa: F405
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# WhiteNoise scans STATIC_ROOT at startup and warns once per test process when it
# does not exist. Nothing in the suite serves static files, so drop the middleware
# instead of teaching everyone to ignore a warning.
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m]  # noqa: F405

# Assets come from the built bundle path, not from a dev server that is not running.
VITE_DEV_SERVER = False
