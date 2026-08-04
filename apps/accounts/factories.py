"""
User factories — the canonical source for every app's tests.

Keep them here rather than in a ``conftest.py``: tests in other apps need to
import them, and a per-app copy is how the set of required flags drifts (a test
built on a user without ``gdpr_consent`` silently exercises a different path than
production does).

Parallel-run rule (pytest-xdist): every unique value comes from
``factory.Sequence`` — no hardcoded emails. See docs/testing.md.
"""

import factory
from factory.django import DjangoModelFactory

from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = "Test"
    last_name = factory.Sequence(lambda n: f"User{n}")
    is_active = True
    gdpr_consent = True
    gdpr_consent_date = factory.LazyFunction(timezone.now)
    password = "testpass123"

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        # create_user() hashes the password; the default _create would store it
        # verbatim and every login test would fail for a non-obvious reason.
        return model_class.objects.create_user(*args, **kwargs)


class ModeratorFactory(UserFactory):
    """Staff user — passes the admin/moderation gates."""

    email = factory.Sequence(lambda n: f"moderator{n}@example.com")
    role = User.Role.MODERATOR
    is_staff = True


class AdminFactory(UserFactory):
    """Superuser — Django admin plus every permission gate."""

    email = factory.Sequence(lambda n: f"admin{n}@example.com")
    role = User.Role.ADMIN
    is_staff = True
    is_superuser = True
