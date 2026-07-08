# iil_testkit/factories.py — ADR-100
"""Platform-standard factories for all Django-Hub repos.

Public API:
    UserFactory       — standard user (all repos)
    StaffUserFactory  — is_staff=True
    AdminUserFactory  — is_staff=True + is_superuser=True

For TenantFactory see: iil_testkit.contrib.tenants
(only import if your repo has the 'tenants' app installed)
"""

import factory
from django.contrib.auth import get_user_model

__all__ = ["UserFactory", "StaffUserFactory", "AdminUserFactory"]


class UserFactory(factory.django.DjangoModelFactory):
    """Standard UserFactory — identical across all platform repos.

    Uses skip_postgeneration_save=True to prevent a second save() call
    triggered by PostGenerationMethodCall (set_password). Without this flag,
    factory-boy >= 3.3 emits a deprecation warning and will eventually error.
    The extra save() can also double-trigger post_save signals in some setups.
    """

    class Meta:
        model = get_user_model()
        skip_postgeneration_save = True  # required for factory-boy >= 3.3.x

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True


class StaffUserFactory(UserFactory):
    """Staff user with is_staff=True."""

    is_staff = True


class AdminUserFactory(StaffUserFactory):
    """Superuser factory."""

    is_superuser = True
