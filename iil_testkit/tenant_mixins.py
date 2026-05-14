"""
iil_testkit/tenant_mixins.py

TenantTestMixin for multi-tenant Django test cases.
ADR-109 requirement: all UI-Hub tenant isolation tests use this mixin.

Usage:
    class MyTest(TenantTestMixin, TestCase):
        def test_isolation(self):
            t1 = self.create_tenant("acme", "ACME")
            t2 = self.create_tenant("globex", "Globex")
            obj = MyModel.objects.create(tenant_id=t1.pk, title="secret")
            self.assert_tenant_isolated(MyModel, obj, t2)
            self.assert_tenant_visible(MyModel, obj, t1)
"""
from __future__ import annotations

from typing import Any

from django.http import HttpRequest
from django.test import RequestFactory


class TenantTestMixin:
    """
    Mixin for Django TestCase / pytest classes.

    Requires django_tenancy.models.Organization to be importable.
    Add 'django_tenancy' to INSTALLED_APPS in your test settings.
    """

    _rf: RequestFactory | None = None

    @property
    def _request_factory(self) -> RequestFactory:
        if self._rf is None:
            self._rf = RequestFactory()
        return self._rf

    def create_tenant(
        self,
        slug: str,
        name: str,
        language: str = "de",
        **kwargs: Any,
    ) -> Any:
        """
        Create and return an Organization (tenant).

        :param slug: Unique slug / subdomain identifier
        :param name: Display name
        :param language: Default language (ADR-110)
        :param kwargs: Extra fields passed to Organization.objects.create()
        """
        from django_tenancy.models import Organization

        return Organization.objects.create(
            slug=slug,
            name=name,
            language=language,
            **kwargs,
        )

    def set_tenant(self, client: Any, tenant: Any) -> None:
        """
        Set the active tenant in the test client session.
        Use this with TENANCY_MODE='session' (default in CI).

        :param client: Django test client
        :param tenant: Organization instance
        """
        session = client.session
        session["tenant_id"] = tenant.pk
        session.save()

    def make_tenant_request(
        self,
        path: str = "/",
        tenant: Any = None,
        method: str = "GET",
        user: Any = None,
        **kwargs: Any,
    ) -> HttpRequest:
        """
        Build a mock HttpRequest pre-populated with tenant context.

        :param path: URL path
        :param tenant: Organization instance (sets request.tenant + request.tenant_id)
        :param method: HTTP method (GET, POST, ...)
        :param user: Optional authenticated user
        :param kwargs: Passed to RequestFactory method
        """
        factory_method = getattr(self._request_factory, method.lower())
        request = factory_method(path, **kwargs)
        request.session = {}

        if tenant is not None:
            request.tenant = tenant
            request.tenant_id = tenant.pk
            request.session["tenant_id"] = tenant.pk
        else:
            request.tenant = None
            request.tenant_id = 0

        if user is not None:
            request.user = user

        return request

    def assert_tenant_isolated(
        self,
        model_class: type[Any],
        obj: Any,
        other_tenant: Any,
    ) -> None:
        """
        Assert that `obj` is NOT visible when querying as `other_tenant`.

        Uses model_class.objects.for_tenant(other_tenant.pk) —
        requires TenantManager on the model.

        :param model_class: Django model class with TenantManager
        :param obj: The object that should NOT be visible
        :param other_tenant: The tenant that should NOT see `obj`
        """
        qs = model_class.objects.for_tenant(other_tenant.pk).filter(pk=obj.pk)
        assert not qs.exists(), (
            f"{model_class.__name__} pk={obj.pk} is visible to tenant "
            f"'{other_tenant.slug}' but should be isolated."
        )

    def assert_tenant_visible(
        self,
        model_class: type[Any],
        obj: Any,
        tenant: Any,
    ) -> None:
        """
        Assert that `obj` IS visible when querying as `tenant`.

        :param model_class: Django model class with TenantManager
        :param obj: The object that should be visible
        :param tenant: The tenant that should see `obj`
        """
        qs = model_class.objects.for_tenant(tenant.pk).filter(pk=obj.pk)
        assert qs.exists(), (
            f"{model_class.__name__} pk={obj.pk} is NOT visible to tenant "
            f"'{tenant.slug}' but should be."
        )
