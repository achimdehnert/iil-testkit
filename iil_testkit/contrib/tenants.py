# iil_testkit/contrib/tenants.py — ADR-100
"""TenantFactory — only for repos with the 'tenants' app installed.

Usage:
    from iil_testkit.contrib.tenants import TenantFactory

This module is intentionally NOT auto-imported by iil_testkit.factories.
Importing it in a repo without 'tenants' in INSTALLED_APPS will raise
a clear RuntimeError at *use time* (not at import time).
"""

import factory

__all__ = ["TenantFactory"]


def _require_tenant_model():
    """Return the Tenant model or raise a clear RuntimeError."""
    from django.apps import apps

    for app_label in ("tenants", "apps.tenants"):
        if apps.is_installed(app_label):
            try:
                return apps.get_model(app_label.split(".")[-1], "Tenant")
            except LookupError:
                pass
    raise RuntimeError(
        "TenantFactory requires the 'tenants' app to be installed. "
        "Add 'tenants' (or 'apps.tenants') to INSTALLED_APPS, "
        "or do not import iil_testkit.contrib.tenants in this repo."
    )


class TenantFactory(factory.django.DjangoModelFactory):
    """TenantFactory — requires tenants app in INSTALLED_APPS.

    Raises RuntimeError at first use (not at import) if tenants is missing.
    """

    class Meta:
        model = "tenants.Tenant"
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Tenant {n}")
    slug = factory.Sequence(lambda n: f"tenant-{n}")
    is_active = True

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        _require_tenant_model()
        return super()._create(model_class, *args, **kwargs)

    @classmethod
    def _build(cls, model_class, *args, **kwargs):
        _require_tenant_model()
        return super()._build(model_class, *args, **kwargs)
