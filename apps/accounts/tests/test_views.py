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


@pytest.mark.django_db
class TestNextRedirect:
    """
    ?next= is attacker-controlled. Passing it to redirect() unchecked turns every
    auth page into an open redirect — the shape phishing links use to borrow a
    trusted domain.
    """

    def _register(self, client, next_url):
        return client.post(
            f"{reverse('accounts:register')}?next={next_url}",
            {
                "email": "redirect@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "gdpr_consent": True,
            },
        )

    def test_local_next_is_honoured(self, client):
        response = self._register(client, "/privacy/")
        assert response["Location"] == "/privacy/"

    def test_external_next_is_dropped(self, client):
        response = self._register(client, "https://evil.example/phish")
        assert response["Location"] == "/"

    def test_protocol_relative_next_is_dropped(self, client, user):
        response = client.post(
            f"{reverse('accounts:login')}?next=//evil.example",
            {"username": user.email, "password": "testpass123"},
        )
        assert response["Location"] == "/"


@pytest.mark.django_db
class TestLogout:
    def test_get_is_not_enough(self, client_authenticated):
        # A GET logout can be triggered by any <img> tag on another site.
        assert client_authenticated.get(reverse("accounts:logout")).status_code == 405

    def test_post_logs_out(self, client_authenticated):
        response = client_authenticated.post(reverse("accounts:logout"))

        assert response.status_code == 302
        assert not client_authenticated.session.get("_auth_user_id")


@pytest.mark.django_db
class TestProfileUpdate:
    def test_saves_the_submitted_fields(self, client_authenticated, user):
        response = client_authenticated.post(
            reverse("accounts:profile"),
            {"first_name": "Jane", "last_name": "Doe", "bio": "hi", "email_notifications": "on"},
        )
        user.refresh_from_db()

        assert response.status_code == 302
        assert (user.first_name, user.bio) == ("Jane", "hi")

    def test_cannot_grant_itself_staff(self, client_authenticated, user):
        client_authenticated.post(
            reverse("accounts:profile"),
            {"first_name": "Jane", "is_staff": "on", "role": "admin"},
        )
        user.refresh_from_db()

        assert user.is_staff is False


@pytest.mark.django_db
class TestDeleteAccount:
    def test_requires_the_current_password(self, client_authenticated, user):
        response = client_authenticated.post(
            reverse("accounts:delete_account"), {"confirm": "on", "password": "wrong"}
        )
        user.refresh_from_db()

        assert response.status_code == 200
        assert user.is_active

    def test_deactivates_on_the_right_password(self, client_authenticated, user):
        response = client_authenticated.post(
            reverse("accounts:delete_account"), {"confirm": "on", "password": "testpass123"}
        )
        user.refresh_from_db()

        assert response.status_code == 302
        assert not user.is_active
