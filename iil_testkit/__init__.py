"""iil-testkit — Shared Test Factory Package for all Platform Django repos.

A pytest plugin + reusable test foundation: it enforces the ADR-057 naming
convention (``test_should_*``) and ADR-058 markers, and ships fixtures,
factories, tenant helpers and contract/smoke utilities.

Public surface (lazily re-exported so ``import iil_testkit`` does NOT eagerly
pull in Django — important for the pytest11 entry-point in non-Django repos):

- ``TenantTestMixin``        — tenant-scoped TestCase mixin (``iil_testkit.tenant_mixins``)
- ``iil_testkit.factories``  — factory-boy base factories
- ``iil_testkit.fixtures``   — shared pytest fixtures
- ``iil_testkit.assertions`` — reusable assertion helpers
- ``iil_testkit.contract``   — contract-test verifier (ADR-155)
- ``iil_testkit.smoke``      — view smoke-test helpers
- ``iil_testkit.plugin``     — the pytest plugin (naming/marker enforcement)

See ADR-100 for architecture decisions.
See ADR-155 for contract testing strategy.

``__version__`` is resolved from the installed package metadata.
"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("iil-testkit")
except PackageNotFoundError:  # source checkout without an install
    __version__ = "0.0.0.dev0"

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
