"""iil-testkit — Shared Test Factory Package for all Platform Django repos.

See ADR-100 for architecture decisions.
See ADR-155 for contract testing strategy.
"""
__version__ = "0.4.1"

from iil_testkit.tenant_mixins import TenantTestMixin

__all__ = [
    "__version__",
    "TenantTestMixin",
]
