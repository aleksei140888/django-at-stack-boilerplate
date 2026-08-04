import pytest

from django.core import mail
from django.urls import reverse


@pytest.mark.django_db
class TestPages:
    def test_home_loads(self, client):
        response = client.get(reverse("pages:home"))
        assert response.status_code == 200

    def test_privacy_loads(self, client):
        response = client.get(reverse("pages:privacy"))
        assert response.status_code == 200

    def test_terms_loads(self, client):
        response = client.get(reverse("pages:terms"))
        assert response.status_code == 200

    def test_cookies_loads(self, client):
        response = client.get(reverse("pages:cookies"))
        assert response.status_code == 200

    def test_contact_loads(self, client):
        response = client.get(reverse("pages:contact"))
        assert response.status_code == 200

    def test_sitemap_loads(self, client):
        response = client.get("/sitemap.xml")
        assert response.status_code == 200

    def test_robots_txt(self, client):
        response = client.get("/robots.txt")
        assert response.status_code == 200
        assert b"User-agent" in response.content


@pytest.mark.django_db
class TestContactForm:
    def test_valid_submission_sends_mail_and_redirects(self, client, settings):
        response = client.post(
            reverse("pages:contact"),
            {"name": "Jane", "email": "jane@example.com", "message": "Hello there"},
        )

        assert response.status_code == 302
        assert response["Location"] == reverse("pages:contact_done")
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [settings.CONTACT_EMAIL]

    def test_message_body_carries_the_sender(self, client):
        client.post(
            reverse("pages:contact"),
            {"name": "Jane", "email": "jane@example.com", "message": "Hello there"},
        )

        assert "jane@example.com" in mail.outbox[0].body

    def test_invalid_submission_re_renders_with_errors(self, client):
        response = client.post(
            reverse("pages:contact"), {"name": "", "email": "not-an-email", "message": ""}
        )

        assert response.status_code == 200
        assert response.context["form"].errors
        assert not mail.outbox
