"""iil-testkit — Shared Test Factory Package for all Platform Django repos.

See ADR-100 for architecture decisions.
See ADR-155 for contract testing strategy.
"""
from __future__ import annotations

__version__ = "0.5.1"

__all__ = [
    "__version__",
    "TenantTestMixin",
]


def __getattr__(name: str):
    # Lazy re-export of TenantTestMixin so `import iil_testkit` (e.g. via the
    # pytest11 entry-point in non-Django repos like MCP packages) does not
    # eagerly pull in django via iil_testkit.tenant_mixins.
    if name == "TenantTestMixin":
        from iil_testkit.tenant_mixins import TenantTestMixin
        return TenantTestMixin
    raise AttributeError(f"module 'iil_testkit' has no attribute {name!r}")
