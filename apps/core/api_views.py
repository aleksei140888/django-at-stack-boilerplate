import datetime

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .health import HealthCheck


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """
    System health check endpoint.

    Returns overall status + per-component details.
    HTTP 200 for ok/degraded, 503 for error.

    Response shape:
        {
            "status": "ok" | "degraded" | "error",
            "timestamp": "2024-01-01T00:00:00Z",
            "checks": {
                "database": {"status": "ok", "latency_ms": 3.1, ...},
                "redis":    {"status": "ok", "latency_ms": 0.8},
                "celery":   {"status": "degraded", "detail": "..."},
                ...
            }
        }
    """
    result = HealthCheck.run_all()
    result["timestamp"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    http_status = 503 if result["status"] == "error" else 200
    return Response(result, status=http_status)
