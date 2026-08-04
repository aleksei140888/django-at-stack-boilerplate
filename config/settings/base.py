"""
Shared settings. Never import this module directly — use one of the layers:

    config.settings.dev    local development (DEBUG, debug toolbar, LocMem cache)
    config.settings.test   pytest (in-memory SQLite, eager Celery, no real email)
    config.settings.demo   `make demo-up` — SQLite file + demo data, no Docker
    config.settings.prod   production (Sentry, HSTS, JSON logs)

Secrets are read with `env("VAR")`; every variable is documented in `.env.example`.
"""

import tomllib
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)

environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Single source of truth for the app version: pyproject.toml. Exposed to templates
# through apps.core.context_processors and reported by /api/v1/health/, so a
# deployed build can be identified without shelling into the server.
with open(BASE_DIR / "pyproject.toml", "rb") as _pyproject:
    APP_VERSION = tomllib.load(_pyproject)["project"]["version"]

SITE_URL = env("SITE_URL", default="http://localhost:8000")
SITE_NAME = env("SITE_NAME", default="Django AT Stack")
SITE_ID = 1

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "django.contrib.humanize",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "corsheaders",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "django_filters",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.core",
    "apps.pages",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Before everything that logs: the request id has to exist by the time the
    # first log record of the request is emitted.
    "apps.core.middleware.RequestIDMiddleware",
    "apps.core.middleware.HTTPMetricsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "apps.core.middleware.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                # Without this, {{ LANGUAGE_CODE }} in base.html renders empty and
                # every page claims the fallback language in <html lang="">.
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_settings",
                "apps.core.context_processors.seo_defaults",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Locale defaults are neutral on purpose — set LANGUAGE_CODE / TIME_ZONE in .env
# for your project instead of editing this file. Serving several languages needs
# two more steps (LocaleMiddleware + LANGUAGES); see docs/architecture.md.
LANGUAGE_CODE = env("LANGUAGE_CODE", default="en-us")
TIME_ZONE = env("TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Listed as prefixed directories rather than the whole `static/` tree, so that
# `static/src/` — the Vite build root, not finished assets — never reaches
# STATIC_ROOT. ManifestStaticFilesStorage otherwise fails during collectstatic
# trying to resolve `@import "tailwindcss"` inside the sources.
STATICFILES_DIRS = [
    ("dist", BASE_DIR / "static" / "dist"),
    ("img", BASE_DIR / "static" / "img"),
]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# STORAGES replaces the STATICFILES_STORAGE / DEFAULT_FILE_STORAGE settings that
# Django 5.1 removed. Keeping the old names would not raise — they would just be
# ignored, silently turning off hashed static filenames in production.
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# Serve the compiled bundle from static/dist by default; the Vite dev server is
# opt-in via VITE_DEV_SERVER (dev.py turns it on). Deriving this from DEBUG alone
# means any DEBUG environment without `npm run dev` running renders unstyled HTML.
VITE_DEV_SERVER = env.bool("VITE_DEV_SERVER", default=False)
VITE_DEV_SERVER_URL = env("VITE_DEV_SERVER_URL", default="http://localhost:5173")

# ── AWS S3 (optional) ─────────────────────────────────────────────────────────
# Set AWS_STORAGE_BUCKET_NAME to enable S3 for media files.
# Static files always use WhiteNoise regardless.
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")
AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default="")
# S3-compatible providers (DigitalOcean Spaces, Cloudflare R2, MinIO) — leave
# blank for AWS itself.
AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default="")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None  # use bucket policy
AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
AWS_QUERYSTRING_AUTH = False  # public bucket — no signed URLs by default

if AWS_STORAGE_BUCKET_NAME:
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "bucket_name": AWS_STORAGE_BUCKET_NAME,
                "region_name": AWS_S3_REGION_NAME,
                "endpoint_url": AWS_S3_ENDPOINT_URL or None,
                "custom_domain": AWS_S3_CUSTOM_DOMAIN or None,
                "location": "media",
                "file_overwrite": AWS_S3_FILE_OVERWRITE,
                "object_parameters": AWS_S3_OBJECT_PARAMETERS,
                "querystring_auth": AWS_QUERYSTRING_AUTH,
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    _cdn = (
        AWS_S3_CUSTOM_DOMAIN or f"{AWS_STORAGE_BUCKET_NAME}.s3.{AWS_S3_REGION_NAME}.amazonaws.com"
    )
    MEDIA_URL = f"https://{_cdn}/media/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")
SERVER_EMAIL = env("SERVER_EMAIL", default="noreply@example.com")
# Where contact-form submissions land. Defaults to SERVER_EMAIL so a fresh clone
# still delivers somewhere instead of dropping messages.
CONTACT_EMAIL = env("CONTACT_EMAIL", default=SERVER_EMAIL)

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/hour",
        "user": "1000/hour",
    },
}

# Django Allauth. The pre-65 names (ACCOUNT_AUTHENTICATION_METHOD,
# ACCOUNT_EMAIL_REQUIRED, ACCOUNT_USERNAME_REQUIRED) are gone — allauth no longer
# reads them, so leaving them in place would quietly restore username signup.
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_LOGOUT_ON_PASSWORD_CHANGE = False
ACCOUNT_EMAIL_SUBJECT_PREFIX = f"[{SITE_NAME}] "
ACCOUNT_RATE_LIMITS = {
    "login_failed": "5/5m",
    "signup": "5/h",
}

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Sessions
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days
SESSION_COOKIE_HTTPONLY = True
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

# CSRF
CSRF_COOKIE_HTTPONLY = False  # allow JS to read for Alpine
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Celery
CELERY_BROKER_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# Sitemaps
SITEMAP_INCLUDE_PRIORITIES = True
SITEMAP_INCLUDE_CHANGEFREQ = True

# ── Observability ─────────────────────────────────────────────────────────────
# `/metrics` is served only when a token is configured — an unauthenticated
# metrics endpoint leaks traffic shape and view names to anyone who asks.
METRICS_TOKEN = env("METRICS_TOKEN", default="")
LOG_LEVEL = env("LOG_LEVEL", default="INFO")
# Human-readable lines locally, one JSON object per line in production, where a
# log shipper has to parse them.
LOG_FORMAT = env("LOG_FORMAT", default="console")  # console | json

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {"()": "apps.core.observability.RequestIDFilter"},
    },
    "formatters": {
        "console": {
            "format": "{levelname} {asctime} {name} [{request_id}] {message}",
            "style": "{",
        },
        "json": {"()": "apps.core.observability.JSONFormatter"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": LOG_FORMAT,
            "filters": ["request_id"],
        },
    },
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "apps": {"handlers": ["console"], "level": LOG_LEVEL, "propagate": False},
    },
}
