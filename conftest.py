"""
Root pytest fixtures.

Factories live in `apps/<app>/factories.py`, not here — other apps' tests need to
import them. This file holds fixtures and the process-wide state resets that the
parallel runner needs (docs/testing.md).
"""

import pytest

from django.core.cache import cache
from django.utils import translation


@pytest.fixture(autouse=True)
def reset_active_language():
    """
    Django's LocaleMiddleware activates a language per request and never
    deactivates it in process_response — the activated language survives as
    thread-local state for the rest of the process. On a pytest-xdist worker that
    means any test hitting the client with a non-default Accept-Language leaves
    that language active for every later test on the same worker, in any app.
    """
    translation.deactivate_all()
    yield
    translation.deactivate_all()


@pytest.fixture(autouse=True)
def clear_cache():
    """
    LocMemCache is per-process, so values written by one test are visible to the
    next one on the same xdist worker — throttling counters and cached querysets
    leak across unrelated tests otherwise.
    """
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user(db):
    from apps.accounts.factories import UserFactory

    return UserFactory(password="testpass123")


@pytest.fixture
def admin_user(db):
    from apps.accounts.factories import AdminFactory

    return AdminFactory(password="adminpass123")


@pytest.fixture
def client_authenticated(client, user):
    client.force_login(user)
    return client
