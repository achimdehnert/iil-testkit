# tests/test_smoke.py — coverage for iil_testkit.smoke (ADR-100)
from unittest.mock import MagicMock, patch

import pytest
from django.urls import include, path, re_path

from iil_testkit.smoke import (
    _collect_patterns,
    _SKIP_NAMESPACES,
    discover_smoke_urls,
    ViewSmokeTester,
)


def _view(request):  # pragma: no cover - never called, only referenced by routes
    return None


def _sample_patterns():
    sub = [path("detail/", _view, name="detail")]
    return [
        path("health/", _view, name="health"),
        path("items/<int:pk>/", _view, name="item"),  # parameterized → skipped
        re_path(r"^admin/$", _view),  # /admin/ prefix → skipped
        path("app/", include((sub, "myapp"))),  # resolver → recurse
        path("dbg/", include((sub, "djdt"))),  # skipped namespace
    ]


# ---------------------------------------------------------------------------
# _collect_patterns
# ---------------------------------------------------------------------------


def test_should_collect_only_parameterless_non_skipped_urls():
    result: list[str] = []
    _collect_patterns(_sample_patterns(), "", result, _SKIP_NAMESPACES)
    assert "/health/" in result
    assert "/app/detail/" in result  # recursed into the myapp resolver


def test_should_skip_parameterized_routes():
    result: list[str] = []
    _collect_patterns(_sample_patterns(), "", result, _SKIP_NAMESPACES)
    assert not any("items" in u for u in result)


def test_should_skip_admin_prefix():
    result: list[str] = []
    _collect_patterns(_sample_patterns(), "", result, _SKIP_NAMESPACES)
    assert "/admin/" not in result


def test_should_skip_blacklisted_namespace():
    result: list[str] = []
    _collect_patterns(_sample_patterns(), "", result, _SKIP_NAMESPACES)
    assert not any(u.startswith("/dbg/") for u in result)


# ---------------------------------------------------------------------------
# discover_smoke_urls
# ---------------------------------------------------------------------------


def test_should_return_sorted_deduplicated_urls():
    resolver = MagicMock()
    resolver.url_patterns = _sample_patterns()
    with patch("django.urls.get_resolver", return_value=resolver):
        urls = discover_smoke_urls()
    assert urls == sorted(set(urls))
    assert "/health/" in urls


def test_should_honor_extra_skip_namespaces():
    resolver = MagicMock()
    resolver.url_patterns = _sample_patterns()
    with patch("django.urls.get_resolver", return_value=resolver):
        urls = discover_smoke_urls(extra_skip_namespaces=frozenset({"myapp"}))
    assert not any(u.startswith("/app/") for u in urls)


# ---------------------------------------------------------------------------
# ViewSmokeTester
# ---------------------------------------------------------------------------


class _FixedTester(ViewSmokeTester):
    urls_to_return: list[str] = ["/a/", "/b/"]

    def discover(self) -> list[str]:
        return self.urls_to_return


def _client_returning(status_by_url):
    client = MagicMock()

    def _get(url):
        resp = MagicMock()
        resp.status_code = status_by_url.get(url, 200)
        return resp

    client.get.side_effect = _get
    return client


def test_should_pass_smoke_when_all_urls_ok():
    tester = _FixedTester()
    tester.run_smoke(_client_returning({"/a/": 200, "/b/": 302}))


def test_should_raise_when_a_url_returns_unexpected_status():
    tester = _FixedTester()
    with pytest.raises(AssertionError, match="500"):
        tester.run_smoke(_client_returning({"/a/": 500, "/b/": 200}))


def test_should_raise_when_no_urls_discovered():
    class _Empty(ViewSmokeTester):
        def discover(self) -> list[str]:
            return []

    with pytest.raises(AssertionError, match="No URLs discovered"):
        _Empty().run_smoke(_client_returning({}))


def test_should_use_default_discover_via_discover_smoke_urls():
    resolver = MagicMock()
    resolver.url_patterns = _sample_patterns()
    with patch("django.urls.get_resolver", return_value=resolver):
        urls = ViewSmokeTester().discover()
    assert "/health/" in urls
