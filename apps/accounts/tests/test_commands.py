import pytest

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestCreateUser:
    def test_creates_a_usable_account(self, client):
        call_command("create_user", "--email=jane@example.com", "--password=StrongPass123!")

        assert client.login(email="jane@example.com", password="StrongPass123!")

    def test_stores_the_optional_names(self):
        call_command(
            "create_user",
            "--email=jane@example.com",
            "--password=StrongPass123!",
            "--first-name=Jane",
            "--last-name=Doe",
        )

        user = User.objects.get(email="jane@example.com")
        assert user.full_name == "Jane Doe"

    def test_duplicate_email_fails_loudly(self):
        call_command("create_user", "--email=jane@example.com", "--password=StrongPass123!")

        with pytest.raises(CommandError, match="already exists"):
            call_command("create_user", "--email=jane@example.com", "--password=StrongPass123!")

    def test_email_comparison_is_case_insensitive(self):
        # Otherwise two accounts differing only in case both exist, and login
        # resolves to whichever the database returns first.
        call_command("create_user", "--email=jane@example.com", "--password=StrongPass123!")

        with pytest.raises(CommandError, match="already exists"):
            call_command("create_user", "--email=JANE@example.com", "--password=StrongPass123!")


class TestCreateAdmin:
    def test_creates_a_superuser_that_can_reach_the_admin(self, client):
        call_command("create_admin", "--email=root@example.com", "--password=StrongPass123!")

        user = User.objects.get(email="root@example.com")
        assert user.is_superuser and user.is_staff
        assert user.role == User.Role.ADMIN

        client.force_login(user)
        assert client.get("/admin/").status_code == 200

    def test_consent_is_recorded_so_the_account_is_immediately_usable(self):
        call_command("create_admin", "--email=root@example.com", "--password=StrongPass123!")

        user = User.objects.get(email="root@example.com")
        assert user.gdpr_consent and user.gdpr_consent_date

    def test_duplicate_email_fails_loudly(self):
        call_command("create_admin", "--email=root@example.com", "--password=StrongPass123!")

        with pytest.raises(CommandError, match="already exists"):
            call_command("create_admin", "--email=root@example.com", "--password=StrongPass123!")
