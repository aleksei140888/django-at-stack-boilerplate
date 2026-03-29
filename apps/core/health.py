"""
Health check registry.

Built-in checks: database, redis, celery.

Adding a custom check anywhere in the codebase:

    from apps.core.health import HealthCheck

    @HealthCheck.register("stripe")
    def check_stripe():
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        stripe.Balance.retrieve()
        return {"status": "ok"}

The check function must return a dict with at least {"status": "ok"|"degraded"|"error"}.
Any extra keys (latency_ms, version, details …) are passed through to the API response.
Raise any exception to automatically mark the check as "error".
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
                if result.get("status") not in ("ok",):
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

    vendor = connection.vendor  # postgresql / sqlite / …
    return {"status": "ok", "vendor": vendor}


@HealthCheck.register("redis")
def _check_redis() -> dict:
    from django.core.cache import cache

    key = "_health_ping"
    cache.set(key, "pong", timeout=5)
    value = cache.get(key)
    if value != "pong":
        return {"status": "error", "error": "unexpected value from cache"}
    return {"status": "ok"}


@HealthCheck.register("storage")
def _check_storage() -> dict:
    """
    When S3 is configured, verifies connectivity by listing the bucket root.
    Falls back to checking that MEDIA_ROOT is writable when using local storage.
    """
    from django.conf import settings

    if getattr(settings, "AWS_STORAGE_BUCKET_NAME", ""):
        import boto3
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            s3 = boto3.client(
                "s3",
                region_name=settings.AWS_S3_REGION_NAME,
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

    # Local storage
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
    Best-effort check: tries to inspect active workers.
    Returns 'degraded' (not 'error') when Celery is not configured —
    so the overall health doesn't go red in envs that don't run workers.
    """
    try:
        from config.celery import app as celery_app

        inspector = celery_app.control.inspect(timeout=1)
        active = inspector.ping()
        if active:
            worker_count = len(active)
            return {"status": "ok", "workers": worker_count}
        return {"status": "degraded", "detail": "no active workers"}
    except Exception as exc:
        return {"status": "degraded", "detail": str(exc)}
