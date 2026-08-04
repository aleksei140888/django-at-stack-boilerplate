"""Local development: DEBUG, debug toolbar, in-process cache, Vite dev server."""

from .base import *  # noqa: F401, F403

DEBUG = True

INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
] + MIDDLEWARE  # noqa: F405

INTERNAL_IPS = ["127.0.0.1", "localhost"]

# Simple cache in dev — no Redis required to run `manage.py runserver`.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Emails to console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Allow all CORS in dev
CORS_ALLOW_ALL_ORIGINS = True

# `npm run dev` is the expected local workflow, so assets come from the Vite dev
# server (HMR). Set VITE_DEV_SERVER=False in .env to test the built bundle.
VITE_DEV_SERVER = env.bool("VITE_DEV_SERVER", default=True)  # noqa: F405

# CSP off in dev: the Vite HMR websocket and the debug toolbar both need a
# policy loose enough that enforcing one here only produces noise.
CONTENT_SECURITY_POLICY = ""
