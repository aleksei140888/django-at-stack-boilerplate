"""
Read-only queries for the accounts domain.

Layering rule (docs/architecture.md): every SELECT lives in a ``selectors.py``,
every write in a ``services.py``, and views call those instead of building
querysets inline. The payoff shows up the third time a filter is needed — it is
in one place, tested once, and the N+1 fix lands everywhere at once.
"""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models import QuerySet

User = get_user_model()


def get_user_by_id(user_id: int) -> User | None:
    """Return the user, or None when it does not exist."""
    return User.objects.filter(pk=user_id).first()


def get_user_by_email(email: str) -> User | None:
    """Case-insensitive lookup — emails are stored as typed but compared folded."""
    return User.objects.filter(email__iexact=email).first()


def active_users() -> QuerySet[User]:
    """Users who can still log in."""
    return User.objects.filter(is_active=True)


def staff_users() -> QuerySet[User]:
    """Users with access to the Django admin or moderation surfaces."""
    return User.objects.filter(is_active=True, is_staff=True)
