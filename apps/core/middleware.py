"""Cross-cutting middleware: request correlation, metrics, security headers."""

from __future__ import annotations

import time
from urllib.parse import urlparse

from django.conf import settings

from apps.core import metrics, observability


def _cdn_origin() -> str:
    """Origin that serves media/static from S3 (or an S3-compatible provider)."""
    custom_domain = getattr(settings, "AWS_S3_CUSTOM_DOMAIN", "")
    if custom_domain:
        return f"https://{custom_domain}"

    bucket = getattr(settings, "AWS_STORAGE_BUCKET_NAME", "")
    if not bucket:
        return ""

    endpoint = getattr(settings, "AWS_S3_ENDPOINT_URL", "")
    if endpoint:
        return f"https://{bucket}.{urlparse(endpoint).netloc}"

    region = getattr(settings, "AWS_S3_REGION_NAME", "us-east-1")
    return f"https://{bucket}.s3.{region}.amazonaws.com"


def _sources(*values) -> str:
    """Join CSP source expressions, dropping the empty ones."""
    parts: list[str] = []
    for value in values:
        if not value:
            continue
        parts.extend(value if isinstance(value, (list, tuple)) else [value])
    return " ".join(parts)


def build_csp() -> str:
    """
    Assemble a Content-Security-Policy from the current settings.

    Sources the project itself needs (an analytics script, a maps tile server, a
    payment iframe) belong in the ``CSP_*_EXTRA`` settings, not in this function:
    a policy edited in code drifts from the deployment that needs the exception,
    and a too-tight policy fails silently in the browser console where nobody is
    looking.
    """
    cdn = _cdn_origin()

    vite = vite_ws = ""
    if getattr(settings, "VITE_DEV_SERVER", False):
        origin = getattr(settings, "VITE_DEV_SERVER_URL", "http://localhost:5173").rstrip("/")
        vite = origin
        vite_ws = origin.replace("http://", "ws://").replace("https://", "wss://")

    directives = {
        "default-src": _sources("'self'"),
        # 'unsafe-inline' is required by Alpine's inline x-data / x-on attributes;
        # dropping it means rewriting every template to external handlers.
        "script-src": _sources(
            "'self'", "'unsafe-inline'", cdn, vite, getattr(settings, "CSP_SCRIPT_SRC_EXTRA", [])
        ),
        "style-src": _sources(
            "'self'", "'unsafe-inline'", cdn, vite, getattr(settings, "CSP_STYLE_SRC_EXTRA", [])
        ),
        "font-src": _sources("'self'", "data:", getattr(settings, "CSP_FONT_SRC_EXTRA", [])),
        # blob: — client-side image previews via URL.createObjectURL.
        "img-src": _sources("'self'", "data:", "blob:", "https:"),
        "connect-src": _sources(
            "'self'", vite, vite_ws, getattr(settings, "CSP_CONNECT_SRC_EXTRA", [])
        ),
        "frame-src": _sources("'self'", getattr(settings, "CSP_FRAME_SRC_EXTRA", [])),
        "frame-ancestors": _sources("'self'"),
        "base-uri": _sources("'self'"),
        "form-action": _sources("'self'"),
        "object-src": _sources("'none'"),
    }
    return "; ".join(f"{name} {value}" for name, value in directives.items())


class RequestIDMiddleware:
    """
    Assign a correlation id to every request.

    Reuses an inbound ``X-Request-ID`` (e.g. set by nginx) when it is well-formed,
    otherwise mints one. The id is bound to the logging contextvar (so every log
    line during the request carries it), tagged on the Sentry scope (log↔error
    correlation), and echoed back in the response header.
    """

    HEADER = "X-Request-ID"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = observability.coerce_request_id(request.headers.get(self.HEADER))
        request.request_id = request_id
        token = observability.set_request_id(request_id)
        observability.bind_request_id(request_id)
        try:
            response = self.get_response(request)
        finally:
            observability.reset_request_id(token)
        response[self.HEADER] = request_id
        return response


class HTTPMetricsMiddleware:
    """Record per-request Prometheus metrics (no-op without prometheus_client)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        match = getattr(request, "resolver_match", None)
        view = match.view_name if match else "unknown"
        metrics.record_request(request.method, view, response.status_code, time.monotonic() - start)
        return response


class SecurityHeadersMiddleware:
    """
    Add the security headers Django does not set on its own.

    ``CONTENT_SECURITY_POLICY`` in settings overrides the built policy; setting it
    to an empty string disables the header entirely (what dev.py does, where the
    Vite HMR socket and the debug toolbar would otherwise be blocked).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response["X-Content-Type-Options"] = "nosniff"
        if not response.has_header("X-Frame-Options"):
            response["X-Frame-Options"] = "SAMEORIGIN"

        policy = getattr(settings, "CONTENT_SECURITY_POLICY", None)
        if policy is None:
            policy = build_csp()
        if policy:
            response["Content-Security-Policy"] = policy

        return response
