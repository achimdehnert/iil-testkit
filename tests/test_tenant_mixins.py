"""
tests/test_tenant_mixins.py

Unit tests for TenantTestMixin.
Requires django_tenancy in INSTALLED_APPS (see tests/settings.py).
"""
import pytest
from unittest.mock import MagicMock
from iil_testkit.tenant_mixins import TenantTestMixin


# ---------------------------------------------------------------------------
# Pure unit tests (no DB) — mock Organization
# ---------------------------------------------------------------------------

class TestTenantTestMixinUnit:
    """Unit tests using mocks — no DB required."""

    def _make_mixin(self) -> TenantTestMixin:
        class Concrete(TenantTestMixin):
            pass
        return Concrete()

    def test_make_tenant_request_no_tenant(self):
        mixin = self._make_mixin()
        request = mixin.make_tenant_request("/", tenant=None)
        assert request.tenant is None
        assert request.tenant_id == 0

    def test_make_tenant_request_with_tenant(self):
        mixin = self._make_mixin()
        tenant = MagicMock()
        tenant.pk = 42
        request = mixin.make_tenant_request("/dashboard/", tenant=tenant)
        assert request.tenant is tenant
        assert request.tenant_id == 42
        assert request.session["tenant_id"] == 42

    def test_make_tenant_request_with_user(self):
        mixin = self._make_mixin()
        user = MagicMock()
        request = mixin.make_tenant_request("/", user=user)
        assert request.user is user

    def test_make_tenant_request_post_method(self):
        mixin = self._make_mixin()
        request = mixin.make_tenant_request("/submit/", method="POST")
        assert request.method == "POST"

    def test_assert_tenant_isolated_passes(self):
        mixin = self._make_mixin()
        tenant = MagicMock()
        tenant.pk = 99
        tenant.slug = "other"
        obj = MagicMock()
        obj.pk = 1
        # Mock model class with manager that returns empty QS for this tenant
        model_class = MagicMock()
        model_class.objects.for_tenant.return_value.filter.return_value.exists.return_value = False
        model_class.__name__ = "FakeModel"
        # Should not raise
        mixin.assert_tenant_isolated(model_class, obj, tenant)

    def test_assert_tenant_isolated_fails(self):
        mixin = self._make_mixin()
        tenant = MagicMock()
        tenant.pk = 99
        tenant.slug = "other"
        obj = MagicMock()
        obj.pk = 1
        model_class = MagicMock()
        model_class.objects.for_tenant.return_value.filter.return_value.exists.return_value = True
        model_class.__name__ = "FakeModel"
        with pytest.raises(AssertionError, match="visible to tenant"):
            mixin.assert_tenant_isolated(model_class, obj, tenant)

    def test_assert_tenant_visible_passes(self):
        mixin = self._make_mixin()
        tenant = MagicMock()
        tenant.pk = 1
        tenant.slug = "acme"
        obj = MagicMock()
        obj.pk = 10
        model_class = MagicMock()
        model_class.objects.for_tenant.return_value.filter.return_value.exists.return_value = True
        model_class.__name__ = "FakeModel"
        mixin.assert_tenant_visible(model_class, obj, tenant)

    def test_assert_tenant_visible_fails(self):
        mixin = self._make_mixin()
        tenant = MagicMock()
        tenant.pk = 1
        tenant.slug = "acme"
        obj = MagicMock()
        obj.pk = 10
        model_class = MagicMock()
        model_class.objects.for_tenant.return_value.filter.return_value.exists.return_value = False
        model_class.__name__ = "FakeModel"
        with pytest.raises(AssertionError, match="NOT visible to tenant"):
            mixin.assert_tenant_visible(model_class, obj, tenant)

    def test_set_tenant_updates_session(self):
        mixin = self._make_mixin()
        tenant = MagicMock()
        tenant.pk = 7
        client = MagicMock()
        captured: dict = {}
        client.session.__setitem__.side_effect = captured.__setitem__
        client.session.__getitem__.side_effect = captured.__getitem__
        mixin.set_tenant(client, tenant)
        assert captured["tenant_id"] == 7
        client.session.save.assert_called_once()

    def test_request_factory_is_lazily_created(self):
        mixin = self._make_mixin()
        rf1 = mixin._request_factory
        rf2 = mixin._request_factory
        assert rf1 is rf2
