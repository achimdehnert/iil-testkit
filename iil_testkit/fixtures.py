# iil_testkit/fixtures.py — ADR-100
"""pytest fixtures for platform Django repos.

Available fixtures:
    db_user       — standard User, saved to DB
    staff_user    — User with is_staff=True
    admin_user    — User with is_superuser=True
    api_client    — unauthenticated Django test Client
    auth_client   — Django test Client force-logged-in as db_user
    staff_client  — Django test Client force-logged-in as staff_user
    drf_api_client   — unauthenticated DRF APIClient (if djangorestframework installed)
    drf_auth_client  — DRF APIClient authenticated as db_user
"""

import pytest


@pytest.fixture
def db_user(db):
    """A standard active user, saved to DB."""
    from iil_testkit.factories import UserFactory

    return UserFactory()


@pytest.fixture
def staff_user(db):
    """A staff user (is_staff=True), saved to DB."""
    from iil_testkit.factories import StaffUserFactory

    return StaffUserFactory()


@pytest.fixture
def admin_user(db):
    """A superuser (is_staff=True, is_superuser=True), saved to DB."""
    from iil_testkit.factories import AdminUserFactory

    return AdminUserFactory()


@pytest.fixture
def api_client():
    """Unauthenticated Django test Client."""
    from django.test import Client

    return Client()


@pytest.fixture
def auth_client(db_user):
    """Django test Client force-logged-in as db_user."""
    from django.test import Client

    client = Client()
    client.force_login(db_user)
    return client


@pytest.fixture
def staff_client(staff_user):
    """Django test Client force-logged-in as staff_user."""
    from django.test import Client

    client = Client()
    client.force_login(staff_user)
    return client


@pytest.fixture
def drf_api_client():
    """Unauthenticated DRF APIClient.

    Requires djangorestframework to be installed.
    Skip the test automatically if DRF is not available.
    """
    pytest.importorskip("rest_framework", reason="djangorestframework not installed")
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def drf_auth_client(db_user):
    """DRF APIClient authenticated as db_user via force_authenticate.

    Requires djangorestframework to be installed.
    Skip the test automatically if DRF is not available.
    """
    pytest.importorskip("rest_framework", reason="djangorestframework not installed")
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user=db_user)
    return client
