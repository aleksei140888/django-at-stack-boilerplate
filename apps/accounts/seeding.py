"""Demo seeder for user accounts."""

from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from apps.core.seeding import SeedContext, register_seeder
from apps.core.seeding.context import DEMO_EMAIL_DOMAIN
from apps.core.seeding.text import person

User = get_user_model()

#: One password for every demo account, so nobody has to keep a list.
DEMO_PASSWORD = "demo12345"

#: Named accounts for role-specific scenarios.
NAMED_ACCOUNTS = [
    ("admin", "Admin", "Demo", User.Role.ADMIN, {"is_staff": True, "is_superuser": True}),
    ("moderator", "Moderator", "Demo", User.Role.MODERATOR, {"is_staff": True}),
    ("user", "Regular", "User", User.Role.USER, {}),
]


def demo_users_qs():
    """Every user this seeder could have created — the demo marker is the domain."""
    return User.objects.filter(email__endswith=f"@{DEMO_EMAIL_DOMAIN}")


def clear_demo_users() -> int:
    return demo_users_qs().delete()[0]


@register_seeder("accounts", order=10, clear=clear_demo_users)
def seed_users(ctx: SeedContext) -> None:
    """Named role accounts plus a pool of ordinary users."""
    if demo_users_qs().exists():
        ctx.log("  accounts           skipped (demo users already exist)")
        ctx.put("users", list(demo_users_qs().order_by("id")))
        return

    # Hash once for the whole run: password hashing is by far the most expensive
    # part of seeding users (hundreds of ms per row with the default hasher).
    password_hash = make_password(DEMO_PASSWORD)
    now = timezone.now()

    users = [
        _build(email=f"{username}@{DEMO_EMAIL_DOMAIN}", first_name=first, last_name=last,
               role=role, password=password_hash, now=now, **flags)
        for username, first, last, role, flags in NAMED_ACCOUNTS
    ]  # fmt: skip

    for index in range(ctx.count("users")):
        first, last = person(ctx)
        users.append(
            _build(
                email=f"user{index + 1}@{DEMO_EMAIL_DOMAIN}",
                first_name=first,
                last_name=last,
                role=User.Role.USER,
                password=password_hash,
                now=now,
            )
        )

    User.objects.bulk_create(users, batch_size=500)
    created = list(demo_users_qs().order_by("id"))

    ctx.put("users", created)
    ctx.record("users", created)


def _build(*, now, **kwargs) -> User:
    # gdpr_consent is set on purpose: a demo account without it hits the consent
    # flow on first login instead of the page being demonstrated.
    return User(gdpr_consent=True, gdpr_consent_date=now, is_active=True, **kwargs)
