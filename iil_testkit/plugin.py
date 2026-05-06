# iil_testkit/plugin.py — ADR-057 + ADR-058
"""pytest plugin for iil-testkit.

Features:
1. ADR-057 — Naming convention enforcement (test_should_*)
2. ADR-058 — Marker minimum enforcement per repo-type

Configuration in pytest.ini / pyproject.toml:
    [tool.pytest.ini_options]
    iil_naming_mode = "warn"        # "warn" (default) | "error"
    iil_repo_type = "mcp"           # django | package | mcp (default: mcp)
    iil_marker_enforce = false      # true = fail session if markers missing

Opt-out naming per test:
    @pytest.mark.no_naming_convention
    def test_legacy_name(): ...

Opt-out naming globally:
    pytest --relax-naming

Note: "error" mode uses pytest.UsageError (not pytest.fail) to avoid
INTERNALERROR in pytest_collection_modifyitems.
"""
from __future__ import annotations

import warnings

import pytest

__all__ = [
    "pytest_addoption",
    "pytest_configure",
    "pytest_collection_modifyitems",
    "pytest_sessionfinish",
]

MANDATORY_MARKERS: dict[str, list[str]] = {
    "django": ["f1", "f3", "a2", "a6", "u3"],
    "package": ["f1", "f2", "f3"],
    "mcp": ["f1", "f3", "m1", "s1", "t1"],
}


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "no_naming_convention: opt out of test_should_* naming check (ADR-057)",
    )
    config.addinivalue_line(
        "markers",
        "iil_testkit: internal marker used by iil-testkit plugin",
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--relax-naming",
        action="store_true",
        default=False,
        help="Disable test_should_* naming convention enforcement (ADR-057)",
    )
    try:
        parser.addini(
            "iil_naming_mode",
            default="warn",
            help="Naming convention mode: 'warn' (default) or 'error'",
        )
    except ValueError:
        pass
    try:
        parser.addini(
            "iil_repo_type",
            default="mcp",
            help="Repo type for ADR-058 taxonomy (django|package|mcp)",
        )
    except ValueError:
        pass
    try:
        parser.addini(
            "iil_marker_enforce",
            default="false",
            help="Fail session if mandatory markers missing (true|false)",
        )
    except ValueError:
        pass


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Enforce test_should_* naming convention (ADR-057)."""
    if config.getoption("--relax-naming", default=False):
        return

    violations = []
    for item in items:
        if not isinstance(item, pytest.Function):
            continue
        if item.get_closest_marker("no_naming_convention"):
            continue
        name = item.originalname or item.name
        if name.startswith("test_") and not name.startswith("test_should_"):
            violations.append(item.nodeid)

    if not violations:
        return

    mode = config.getini("iil_naming_mode") or "warn"
    msg = (
        f"Naming convention violations (ADR-057 \u00a72.3) \u2014 "
        f"{len(violations)} test(s) must start with 'test_should_':\n"
        + "\n".join(f"  {v}" for v in violations)
        + "\n\nFix: rename to test_should_<what_it_does>(...)"
        + "\nOpt-out: @pytest.mark.no_naming_convention or --relax-naming"
    )

    if mode == "error":
        raise pytest.UsageError(msg)
    else:
        warnings.warn(msg, UserWarning, stacklevel=2)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Enforce mandatory markers per repo-type (ADR-058)."""
    repo_type: str = session.config.getini("iil_repo_type") or "mcp"
    enforce: bool = _as_bool(session.config.getini("iil_marker_enforce"))

    mandatory = MANDATORY_MARKERS.get(repo_type)
    if mandatory is None:
        warnings.warn(
            f"iil-testkit: unknown iil_repo_type='{repo_type}'. "
            f"Valid: {list(MANDATORY_MARKERS)}",
            stacklevel=1,
        )
        return

    used_markers: set[str] = set()
    for item in session.items:
        for marker in item.iter_markers():
            used_markers.add(marker.name)

    missing = [m for m in mandatory if m not in used_markers]

    if not missing:
        tr = session.config.pluginmanager.get_plugin("terminalreporter")
        if tr is not None:
            tr.write_line(
                f"\niil-testkit \u2705  ADR-058 Compliance PASSED "
                f"(repo-type={repo_type}): alle Pflicht-Marker vorhanden.",
                green=True,
            )
        return

    msg = (
        f"\niil-testkit ADR-058 Compliance: fehlende Pflicht-Marker "
        f"f\u00fcr repo-type='{repo_type}': "
        + ", ".join(f"@pytest.mark.{m}" for m in missing)
        + "\n  Annotiere Tests gem\u00e4\u00df ADR-058 Taxonomy."
    )

    tr = session.config.pluginmanager.get_plugin("terminalreporter")
    if tr is not None:
        tr.write_line(msg, red=True)

    if enforce and exitstatus == 0:
        session.exitstatus = 1


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    return bool(value)
