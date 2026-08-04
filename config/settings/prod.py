"""Production: strict security headers, JSON logs, optional Sentry."""

from .base import *  # noqa: F401, F403
from .base import LOGGING, env

DEBUG = False

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)
X_FRAME_OPTIONS = "DENY"

# Behind nginx/a load balancer Django only sees plain HTTP. Without this header
# mapping, SECURE_SSL_REDIRECT sees every request as insecure and redirects
# forever, and request.is_secure() lies to any code that asks.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ACCOUNT_EMAIL_VERIFICATION = "mandatory"

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])

# One JSON object per line — log shippers (BetterStack, Loki, CloudWatch) parse
# it directly and the request id stays queryable as a field.
LOGGING = {
    **LOGGING,
    "handlers": {
        **LOGGING["handlers"],
        "console": {**LOGGING["handlers"]["console"], "formatter": "json"},
    },
}

SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    # Imported lazily: the prod extra may be absent in a stripped image, and a
    # missing Sentry SDK should not stop the site from booting.
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.1),
        send_default_pii=False,
        release=APP_VERSION,  # noqa: F405
        environment=env("SENTRY_ENVIRONMENT", default="production"),
    )
