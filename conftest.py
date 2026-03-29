import pytest


@pytest.fixture
def user(db):
    from apps.accounts.models import User

    return User.objects.create_user(
        email="test@example.com",
        password="testpass123",
        first_name="Test",
        last_name="User",
        gdpr_consent=True,
    )


@pytest.fixture
def admin_user(db):
    from apps.accounts.models import User

    return User.objects.create_superuser(
        email="admin@example.com",
        password="adminpass123",
    )


@pytest.fixture
def client_authenticated(client, user):
    client.force_login(user)
    return client
