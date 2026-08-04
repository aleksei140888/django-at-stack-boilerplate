import pytest

from django.test import override_settings
from django.urls import reverse

from apps.core import observability
from apps.core.middleware import build_csp


@pytest.mark.django_db
class TestRequestID:
    def test_response_carries_a_request_id(self, client):
        response = client.get(reverse("pages:home"))
        assert response["X-Request-ID"]

    def test_inbound_id_is_reused(self, client):
        response = client.get(reverse("pages:home"), headers={"x-request-id": "abc-123"})
        assert response["X-Request-ID"] == "abc-123"

    # An id lands in log lines and in Sentry tags, so anything the client sends
    # has to be bounded before it is trusted.
    @pytest.mark.parametrize("hostile", ["with space", "a" * 200, "line\nbreak", "semi;colon"])
    def test_malformed_inbound_id_is_replaced(self, client, hostile):
        response = client.get(reverse("pages:home"), headers={"x-request-id": hostile})
        assert response["X-Request-ID"] != hostile

    def test_context_is_reset_after_the_response(self, client):
        client.get(reverse("pages:home"))
        assert observability.get_request_id() == observability.NO_REQUEST_ID


@pytest.mark.django_db
class TestSecurityHeaders:
    def test_headers_are_present(self, client):
        response = client.get(reverse("pages:home"))

        assert response["X-Content-Type-Options"] == "nosniff"
        assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"
        assert "geolocation=()" in response["Permissions-Policy"]
        assert response["X-Frame-Options"]

    def test_csp_is_sent_by_default(self, client):
        response = client.get(reverse("pages:home"))
        assert "default-src 'self'" in response["Content-Security-Policy"]

    @override_settings(CONTENT_SECURITY_POLICY="")
    def test_empty_policy_setting_disables_the_header(self, client):
        response = client.get(reverse("pages:home"))
        assert not response.has_header("Content-Security-Policy")

    @override_settings(CONTENT_SECURITY_POLICY="default-src 'none'")
    def test_explicit_policy_wins(self, client):
        response = client.get(reverse("pages:home"))
        assert response["Content-Security-Policy"] == "default-src 'none'"


class TestCSPBuilder:
    def test_project_extras_are_included(self):
        with override_settings(CSP_SCRIPT_SRC_EXTRA=["https://plausible.example"]):
            assert "https://plausible.example" in build_csp()

    def test_s3_cdn_origin_is_derived_from_the_bucket(self):
        with override_settings(AWS_STORAGE_BUCKET_NAME="assets", AWS_S3_REGION_NAME="eu-central-1"):
            assert "https://assets.s3.eu-central-1.amazonaws.com" in build_csp()

    def test_custom_domain_wins_over_the_bucket_url(self):
        with override_settings(
            AWS_STORAGE_BUCKET_NAME="assets", AWS_S3_CUSTOM_DOMAIN="cdn.example.com"
        ):
            policy = build_csp()
            assert "https://cdn.example.com" in policy
            assert "amazonaws.com" not in policy

    # Without the websocket origin, HMR is blocked and the dev server looks broken.
    def test_vite_origins_appear_only_with_the_dev_server_on(self):
        with override_settings(VITE_DEV_SERVER=False):
            assert "5173" not in build_csp()

        with override_settings(VITE_DEV_SERVER=True, VITE_DEV_SERVER_URL="http://localhost:5173"):
            policy = build_csp()
            assert "http://localhost:5173" in policy
            assert "ws://localhost:5173" in policy


@pytest.mark.django_db
class TestMetricsEndpoint:
    def test_hidden_without_a_token(self, client):
        assert client.get("/metrics").status_code == 404

    @override_settings(METRICS_TOKEN="s3cret")
    def test_wrong_token_is_a_404_not_a_403(self, client):
        # A 403 would confirm the endpoint exists; a 404 gives nothing away.
        assert client.get("/metrics", headers={"authorization": "Bearer wrong"}).status_code == 404
