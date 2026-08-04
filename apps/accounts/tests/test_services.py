import pytest

from django.contrib.auth import get_user_model

from apps.accounts import selectors, services
from apps.accounts.factories import AdminFactory, ModeratorFactory, UserFactory

User = get_user_model()

pytestmark = pytest.mark.django_db


class TestRegisterUser:
    def test_creates_an_active_user_with_a_usable_password(self):
        user = services.register_user(email="new@example.com", password="StrongPass123!")

        assert user.is_active
        assert user.check_password("StrongPass123!")
        assert user.role == User.Role.USER

    def test_records_the_consent_timestamp(self):
        user = services.register_user(email="a@example.com", password="StrongPass123!")

        assert user.gdpr_consent is True
        assert user.gdpr_consent_date is not None

    def test_without_consent_no_timestamp_is_invented(self):
        user = services.register_user(
            email="b@example.com", password="StrongPass123!", gdpr_consent=False
        )

        assert user.gdpr_consent is False
        assert user.gdpr_consent_date is None

    def test_email_is_required(self):
        with pytest.raises(ValueError):
            services.register_user(email="", password="StrongPass123!")


class TestUpdateProfile:
    def test_updates_the_editable_fields(self):
        user = UserFactory()

        services.update_profile(user, first_name="Jane", bio="hello")
        user.refresh_from_db()

        assert user.first_name == "Jane"
        assert user.bio == "hello"

    # Regression guard: forms grow fields, and passing cleaned_data straight into
    # setattr is how is_staff becomes user-editable.
    def test_ignores_fields_outside_the_whitelist(self):
        user = UserFactory()

        services.update_profile(user, is_staff=True, role=User.Role.ADMIN)
        user.refresh_from_db()

        assert user.is_staff is False
        assert user.role != User.Role.ADMIN

    def test_no_write_when_nothing_editable_was_passed(self, django_capture_on_commit_callbacks):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        user = UserFactory()

        with CaptureQueriesContext(connection) as captured:
            services.update_profile(user, is_superuser=True)

        # Savepoints from @transaction.atomic are expected; an UPDATE is not.
        assert not [q for q in captured.captured_queries if "UPDATE" in q["sql"].upper()]


class TestDeactivateAccount:
    def test_deactivates_without_deleting(self):
        user = UserFactory()

        services.deactivate_account(user)

        assert User.objects.filter(pk=user.pk).exists()
        assert not User.objects.get(pk=user.pk).is_active

    def test_deactivated_user_cannot_log_in(self, client):
        user = UserFactory(password="testpass123")
        services.deactivate_account(user)

        assert not client.login(email=user.email, password="testpass123")


class TestTouchLastSeen:
    def test_records_the_timestamp(self):
        user = UserFactory()
        assert user.last_seen is None

        services.touch_last_seen(user)
        user.refresh_from_db()

        assert user.last_seen is not None


class TestSelectors:
    def test_lookup_by_email_is_case_insensitive(self):
        user = UserFactory(email="Mixed@Example.com")

        assert selectors.get_user_by_email("mixed@example.com") == user

    def test_missing_user_returns_none(self):
        assert selectors.get_user_by_id(999999) is None
        assert selectors.get_user_by_email("nobody@example.com") is None

    def test_active_users_excludes_deactivated(self):
        active = UserFactory()
        inactive = UserFactory(is_active=False)

        assert active in selectors.active_users()
        assert inactive not in selectors.active_users()

    def test_staff_users_covers_moderators_and_admins(self):
        moderator = ModeratorFactory()
        admin = AdminFactory()
        plain = UserFactory()

        staff = set(selectors.staff_users())
        assert {moderator, admin} <= staff
        assert plain not in staff
