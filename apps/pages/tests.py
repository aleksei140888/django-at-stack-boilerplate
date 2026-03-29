import pytest
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
