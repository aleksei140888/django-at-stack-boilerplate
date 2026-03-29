import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestRegister:
    def test_register_page_loads(self, client):
        response = client.get(reverse("accounts:register"))
        assert response.status_code == 200

    def test_register_creates_user(self, client):
        response = client.post(
            reverse("accounts:register"),
            {
                "email": "new@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "gdpr_consent": True,
            },
        )
        assert response.status_code == 302
        from apps.accounts.models import User

        assert User.objects.filter(email="new@example.com").exists()

    def test_register_redirects_authenticated(self, client_authenticated):
        response = client_authenticated.get(reverse("accounts:register"))
        assert response.status_code == 302


@pytest.mark.django_db
class TestLogin:
    def test_login_page_loads(self, client):
        response = client.get(reverse("accounts:login"))
        assert response.status_code == 200

    def test_login_success(self, client, user):
        response = client.post(
            reverse("accounts:login"),
            {"username": user.email, "password": "testpass123"},
        )
        assert response.status_code == 302

    def test_login_wrong_password(self, client, user):
        response = client.post(
            reverse("accounts:login"),
            {"username": user.email, "password": "wrongpass"},
        )
        assert response.status_code == 200
        assert response.context["form"].errors


@pytest.mark.django_db
class TestProfile:
    def test_profile_requires_login(self, client):
        response = client.get(reverse("accounts:profile"))
        assert response.status_code == 302
        assert "/login/" in response["Location"]

    def test_profile_loads_for_authenticated(self, client_authenticated):
        response = client_authenticated.get(reverse("accounts:profile"))
        assert response.status_code == 200


@pytest.mark.django_db
class TestPasswordReset:
    def test_password_reset_page_loads(self, client):
        response = client.get(reverse("accounts:password_reset"))
        assert response.status_code == 200

    def test_password_reset_post_valid_email(self, client, user):
        response = client.post(
            reverse("accounts:password_reset"),
            {"email": user.email},
        )
        assert response.status_code == 302
