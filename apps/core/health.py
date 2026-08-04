"""
Health check registry.

Built-in checks: database, cache, storage, celery.

Adding a custom check anywhere in the codebase — put it in a module that is
imported at startup (``apps.py``'s ``ready()`` is the usual place)::

    from apps.core.health import HealthCheck

    @HealthCheck.register("stripe")
    def check_stripe():
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Balance.retrieve()
        return {"status": "ok"}

The check function must return a dict with at least
``{"status": "ok"|"degraded"|"error"}``. Any extra keys (latency_ms, version,
details …) are passed through to the API response. Raising any exception marks
the check as ``"error"``.

Distinguish the two failure levels deliberately: ``error`` makes
``/api/v1/health/`` answer 503, which an uptime monitor turns into a page at
03:00. Reserve it for "the site cannot serve requests"; use ``degraded`` for a
component whose absence merely reduces functionality.
"""

import time


class HealthCheck:
    _checks: dict = {}

    @classmethod
    def register(cls, name: str):
        """Decorator — register a health check function under *name*."""

        def decorator(fn):
            cls._checks[name] = fn
            return fn

        return decorator

    @classmethod
    def unregister(cls, name: str) -> None:
        """Drop a check. Used by tests that register a temporary one."""
        cls._checks.pop(name, None)

    @classmethod
    def names(cls) -> list[str]:
        return sorted(cls._checks)

    @classmethod
    def run_all(cls) -> dict:
        """Run every registered check and return an aggregated result."""
        results = {}
        overall = "ok"

        for name, fn in cls._checks.items():
            t0 = time.monotonic()
            try:
                result = fn()
                result.setdefault("latency_ms", round((time.monotonic() - t0) * 1000, 1))
                results[name] = result
                # A check that *returns* {"status": "error"} is as fatal as one
                # that raises; a degraded one never downgrades an error already
                # recorded by an earlier check.
                if result.get("status") == "error":
                    overall = "error"
                elif result.get("status") != "ok" and overall == "ok":
                    overall = "degraded"
            except Exception as exc:
                results[name] = {
                    "status": "error",
                    "error": str(exc),
                    "latency_ms": round((time.monotonic() - t0) * 1000, 1),
                }
                overall = "error"

        return {"status": overall, "checks": results}


# ── Built-in checks ────────────────────────────────────────────────────────────


@HealthCheck.register("database")
def _check_database() -> dict:
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()

    return {"status": "ok", "vendor": connection.vendor}


@HealthCheck.register("cache")
def _check_cache() -> dict:
    """Round-trips a value through the configured cache backend (Redis in prod)."""
    from django.core.cache import cache

    key = "_health_ping"
    cache.set(key, "pong", timeout=5)
    if cache.get(key) != "pong":
        return {"status": "error", "error": "unexpected value from cache"}
    return {"status": "ok", "backend": cache.__class__.__name__}


@HealthCheck.register("storage")
def _check_storage() -> dict:
    """
    When S3 is configured, verifies connectivity by heading the bucket.
    Falls back to checking that MEDIA_ROOT is writable for local storage.
    """
    from django.conf import settings

    if getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""):
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            s3 = boto3.client(
                "s3",
                region_name=settings.AWS_S3_REGION_NAME,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL or None,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            s3.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            return {
                "status": "ok",
                "backend": "s3",
                "bucket": settings.AWS_STORAGE_BUCKET_NAME,
            }
        except (BotoCoreError, ClientError) as exc:
            return {"status": "error", "backend": "s3", "error": str(exc)}

    import os

    media_root = str(settings.MEDIA_ROOT)
    os.makedirs(media_root, exist_ok=True)
    writable = os.access(media_root, os.W_OK)
    return {
        "status": "ok" if writable else "error",
        "backend": "local",
        "path": media_root,
        **({"error": "not writable"} if not writable else {}),
    }


@HealthCheck.register("celery")
def _check_celery() -> dict:
    """
    Best-effort worker check.

    Returns 'degraded' rather than 'error' when Celery is unreachable: plenty of
    environments run the web tier without workers, and a red health endpoint
    there would train everyone to ignore it.
    """
    from django.conf import settings

    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        # Tests and the demo environment run tasks inline; there is no broker to
        # ping, and trying to reach one costs a socket timeout per request.
        return {"status": "ok", "detail": "eager mode — tasks run inline"}

    try:
        from config.celery import app as celery_app

        workers = celery_app.control.inspect(timeout=1).ping()
        if workers:
            return {"status": "ok", "workers": len(workers)}
        return {"status": "degraded", "detail": "no active workers"}
    except Exception as exc:
        return {"status": "degraded", "detail": str(exc)}
