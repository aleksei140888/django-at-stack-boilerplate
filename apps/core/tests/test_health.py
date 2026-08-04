import pytest

from django.urls import reverse

from apps.core.health import HealthCheck


@pytest.fixture
def temporary_check():
    """Register a check for one test and take it back out again."""
    registered: list[str] = []

    def register(name, fn):
        HealthCheck.register(name)(fn)
        registered.append(name)

    yield register

    for name in registered:
        HealthCheck.unregister(name)


@pytest.fixture
def only_temporary_checks(temporary_check):
    """
    Same, but with the built-in checks taken out for the duration.

    Aggregation tests are about how statuses combine, not about whether this
    machine has a database — leaving the built-ins in makes the result depend on
    the fixtures a test happens to request.
    """
    saved = dict(HealthCheck._checks)
    HealthCheck._checks.clear()
    yield temporary_check
    HealthCheck._checks.clear()
    HealthCheck._checks.update(saved)


class TestRegistry:
    def test_builtin_checks_are_registered(self):
        assert {"database", "cache", "storage", "celery"} <= set(HealthCheck.names())

    @pytest.mark.django_db
    def test_all_builtin_checks_pass_in_test_settings(self):
        result = HealthCheck.run_all()
        assert result["status"] == "ok", result["checks"]

    def test_latency_is_recorded_for_every_check(self, only_temporary_checks):
        only_temporary_checks("quick", lambda: {"status": "ok"})
        assert HealthCheck.run_all()["checks"]["quick"]["latency_ms"] >= 0

    def test_check_may_report_its_own_latency(self, only_temporary_checks):
        only_temporary_checks("fixed", lambda: {"status": "ok", "latency_ms": 42})
        assert HealthCheck.run_all()["checks"]["fixed"]["latency_ms"] == 42


class TestOverallStatus:
    def test_degraded_check_degrades_the_whole(self, only_temporary_checks):
        only_temporary_checks("flaky", lambda: {"status": "degraded", "detail": "no workers"})
        assert HealthCheck.run_all()["status"] == "degraded"

    # Regression: a check that *returned* an error used to only mark the system
    # degraded, so /api/v1/health/ answered 200 and no monitor ever noticed.
    def test_returned_error_is_as_fatal_as_a_raised_one(self, only_temporary_checks):
        only_temporary_checks("broken", lambda: {"status": "error", "error": "boom"})
        assert HealthCheck.run_all()["status"] == "error"

    def test_raised_exception_becomes_an_error_check(self, only_temporary_checks):
        def explode():
            raise RuntimeError("connection refused")

        only_temporary_checks("explodes", explode)
        result = HealthCheck.run_all()

        assert result["status"] == "error"
        assert result["checks"]["explodes"]["error"] == "connection refused"

    def test_degraded_does_not_downgrade_an_earlier_error(self, only_temporary_checks):
        only_temporary_checks("a_broken", lambda: {"status": "error"})
        only_temporary_checks("b_degraded", lambda: {"status": "degraded"})
        assert HealthCheck.run_all()["status"] == "error"


@pytest.mark.django_db
class TestEndpoint:
    def test_returns_200_and_the_app_version(self, client, settings):
        response = client.get(reverse("api:health"))

        assert response.status_code == 200
        assert response.json()["version"] == settings.APP_VERSION
        assert response.json()["status"] == "ok"

    def test_returns_503_when_a_component_is_down(self, client, temporary_check):
        temporary_check("broken", lambda: {"status": "error", "error": "boom"})

        response = client.get(reverse("api:health"))

        assert response.status_code == 503
        assert response.json()["checks"]["broken"]["status"] == "error"

    def test_page_renders_for_anonymous_users(self, client):
        response = client.get(reverse("health"))

        assert response.status_code == 200
        assert "core/health.html" in [t.name for t in response.templates]
