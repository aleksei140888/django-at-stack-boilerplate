"""
Process-wide Prometheus metrics for the web tier.

``prometheus_client`` lives in the ``prod`` extra, so everything here degrades to
a no-op when it is missing and the same code runs in dev, test and CI without it.

Exposed via ``/metrics`` (see apps/core/api_views.py), which stays 404 until
``METRICS_TOKEN`` is configured.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

    _http_requests = Counter(
        "django_http_requests_total",
        "Total HTTP requests handled by Django",
        labelnames=["method", "view", "status"],
    )
    _http_latency = Histogram(
        "django_http_request_duration_seconds",
        "HTTP request latency",
        labelnames=["method", "view"],
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


def record_request(method: str, view: str, status: int, duration_seconds: float) -> None:
    """
    Record one HTTP request.

    *view* must be a bounded label — the resolver's view name, never the raw
    path. Every distinct label value creates a new time series, so a path label
    would let any crawler blow up the registry.
    """
    if not PROMETHEUS_AVAILABLE:
        return
    _http_requests.labels(method=method, view=view, status=str(status)).inc()
    _http_latency.labels(method=method, view=view).observe(duration_seconds)


def render_latest() -> bytes:
    """Render the default Prometheus registry in exposition format."""
    if not PROMETHEUS_AVAILABLE:
        return b""
    return generate_latest()
