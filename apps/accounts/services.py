"""
Writes for the accounts domain.

Everything that changes the database (create/update/delete plus its side effects)
lives here, so a view never has to know that registering a user also stamps the
GDPR consent date, and a management command reusing the flow cannot forget it.

Views call these; they do not write querysets themselves.
"""

from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

User = get_user_model()

logger = logging.getLogger(__name__)


@transaction.atomic
def register_user(
    *,
    email: str,
    password: str,
    first_name: str = "",
    last_name: str = "",
    gdpr_consent: bool = True,
) -> User:
    """Create an active account with the consent timestamp recorded."""
    user = User.objects.create_user(
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        role=User.Role.USER,
        gdpr_consent=gdpr_consent,
        gdpr_consent_date=timezone.now() if gdpr_consent else None,
    )
    logger.info("user registered", extra={"user_id": user.pk})
    return user


@transaction.atomic
def update_profile(user: User, **fields) -> User:
    """
    Update the editable profile fields.

    Only whitelisted fields are written: passing a form's ``cleaned_data``
    straight into ``setattr`` is how ``is_staff`` ends up user-editable.
    """
    editable = {"first_name", "last_name", "bio", "avatar", "email_notifications"}
    changed = [name for name, value in fields.items() if name in editable]

    for name in changed:
        setattr(user, name, fields[name])

    if changed:
        user.save(update_fields=changed)
    return user


@transaction.atomic
def deactivate_account(user: User) -> User:
    """
    Soft-delete: the account stops working but its rows stay referenced.

    A hard delete cascades into everything the user ever created, which is rarely
    what "delete my account" is meant to do — and is impossible to undo when it
    turns out it was not. Anonymise or purge on a schedule instead.
    """
    user.is_active = False
    user.save(update_fields=["is_active"])
    logger.info("account deactivated", extra={"user_id": user.pk})
    return user


def touch_last_seen(user: User) -> None:
    """Record activity without bumping any auto_now field on the row."""
    User.objects.filter(pk=user.pk).update(last_seen=timezone.now())
