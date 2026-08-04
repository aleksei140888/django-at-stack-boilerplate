import datetime
import secrets

from django.conf import settings
from django.http import Http404, HttpResponse

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from . import metrics
from .health import HealthCheck


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    System health check endpoint.

    Returns the overall status plus per-component details.
    HTTP 200 for ok/degraded, 503 for error.

    Response shape:
        {
            "status": "ok" | "degraded" | "error",
            "version": "2026.8.0",
            "timestamp": "2026-08-04T00:00:00+00:00",
            "checks": {
                "database": {"status": "ok", "latency_ms": 3.1, ...},
                "cache":    {"status": "ok", "latency_ms": 0.8},
                "celery":   {"status": "degraded", "detail": "..."},
                ...
            }
        }
    """
    result = HealthCheck.run_all()
    result["version"] = settings.APP_VERSION
    result["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    http_status = 503 if result["status"] == "error" else 200
    return Response(result, status=http_status)


def metrics_view(request):
    """
    Prometheus exposition endpoint.

    Hidden (404, not 403) unless ``METRICS_TOKEN`` is set and matches: view names
    and traffic shape are useful reconnaissance, and a 403 confirms the endpoint
    exists. The scraper sends ``Authorization: Bearer <token>``.
    """
    token = getattr(settings, "METRICS_TOKEN", "")
    if not token or not metrics.PROMETHEUS_AVAILABLE:
        raise Http404

    provided = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not secrets.compare_digest(provided, token):
        raise Http404

    return HttpResponse(metrics.render_latest(), content_type=metrics.CONTENT_TYPE_LATEST)
