# iil_testkit/smoke.py — ADR-100
"""Generic view smoke tester for Django repos.

Auto-discovers all parameterless URL routes and tests HTTP 200/302
using the Django test client — no manual URL lists required.

Usage (pytest parametrize — recommended):

    from iil_testkit.smoke import discover_smoke_urls

    @pytest.mark.parametrize("url", discover_smoke_urls())
    @pytest.mark.django_db
    def test_should_view_return_200(url, auth_client):
        response = auth_client.get(url)
        assert response.status_code in (200, 302)

Usage (ViewSmokeTester mixin):

    from iil_testkit.smoke import ViewSmokeTester

    class TestAppSmoke(ViewSmokeTester):
        namespaces = ["projects"]

    def test_should_all_views_load(self, auth_client):
        self.run_smoke(auth_client)
"""
from __future__ import annotations

import re

__all__ = ["discover_smoke_urls", "ViewSmokeTester"]

_SKIP_NAMESPACES: frozenset[str] = frozenset(
    {"admin", "djdt", "silk", "debug", "media", "prometheus"}
)
_SKIP_URL_PREFIXES: tuple[str, ...] = (
    "/admin/",
    "/static/",
    "/media/",
    "/__debug__/",
    "/metrics",
)
_PARAM_RE = re.compile(r"[<{]")


def _collect_patterns(
    patterns: list,
    prefix: str,
    result: list[str],
    skip_ns: frozenset[str],
) -> None:
    from django.urls import URLPattern, URLResolver

    for pattern in patterns:
        if isinstance(pattern, URLResolver):
            if pattern.namespace and pattern.namespace in skip_ns:
                continue
            _collect_patterns(
                pattern.url_patterns,
                prefix + str(pattern.pattern),
                result,
                skip_ns,
            )
        elif isinstance(pattern, URLPattern):
            full = prefix + str(pattern.pattern)
            if _PARAM_RE.search(full):
                continue
            url = "/" + full.lstrip("^").rstrip("$").lstrip("/")
            if not url.endswith("/"):
                url += "/"
            if not any(url.startswith(s) for s in _SKIP_URL_PREFIXES):
                result.append(url)


def discover_smoke_urls(
    extra_skip_namespaces: frozenset[str] | None = None,
) -> list[str]:
    """Return all parameterless GET URLs discoverable from Django's URL conf.

    Skips: admin, debug toolbar, static/media, Prometheus.
    Skips: parameterized routes that require a PK, slug, or UUID.

    Args:
        extra_skip_namespaces: Additional namespaces to exclude.

    Returns:
        Sorted, deduplicated list of URL paths ready for pytest.mark.parametrize.

    Example:
        @pytest.mark.parametrize("url", discover_smoke_urls())
        @pytest.mark.django_db
        def test_should_view_return_200(url, auth_client):
            response = auth_client.get(url)
            assert response.status_code in (200, 302)
    """
    from django.urls import get_resolver

    skip_ns = _SKIP_NAMESPACES | (extra_skip_namespaces or frozenset())
    result: list[str] = []
    _collect_patterns(get_resolver().url_patterns, "", result, skip_ns)
    return sorted(set(result))


class ViewSmokeTester:
    """Mixin for smoke-testing all auto-discovered views in a test class.

    Subclass and override `namespaces` to restrict to specific apps.
    Call `run_smoke(client)` from a test method.

    Attributes:
        namespaces: If set, only test URLs whose path starts with the
            URL prefix of these namespaces. Empty = all parameterless URLs.
        expected_statuses: Accepted HTTP status codes (default: 200, 302).
        extra_skip_namespaces: Additional namespaces to exclude.

    Example:
        class TestProjectSmoke(ViewSmokeTester):
            expected_statuses = (200, 302, 404)  # 404 OK for empty DB

        def test_should_all_views_load(self, auth_client):
            self.run_smoke(auth_client)
    """

    expected_statuses: tuple[int, ...] = (200, 302)
    extra_skip_namespaces: frozenset[str] = frozenset()

    def discover(self) -> list[str]:
        return discover_smoke_urls(self.extra_skip_namespaces)

    def run_smoke(self, client: object) -> None:
        """Run smoke tests for all discovered URLs.

        Args:
            client: Authenticated Django test Client fixture (e.g. auth_client).

        Raises:
            AssertionError: If any URL returns an unexpected status code.
        """
        urls = self.discover()
        assert urls, "No URLs discovered — check URL configuration"

        failures: list[str] = []
        for url in urls:
            response = client.get(url)  # type: ignore[union-attr]
            if response.status_code not in self.expected_statuses:
                failures.append(f"  {url}  → HTTP {response.status_code}")

        assert not failures, (
            f"Smoke test failures ({len(failures)}/{len(urls)} URLs):\n"
            + "\n".join(failures)
        )
