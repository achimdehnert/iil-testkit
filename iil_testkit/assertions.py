# iil_testkit/assertions.py — ADR-100
"""Common assertion helpers for platform Django repos.

All helpers follow the pattern: assert_<what>(response, ...) → None
They raise AssertionError with a descriptive message on failure.

Usage:
    from iil_testkit.assertions import (
        assert_redirects_to_login,
        assert_htmx_response,
        assert_data_testids,
        assert_no_n_plus_one,
        assert_form_error,
    )
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpResponse

__all__ = [
    "assert_redirects_to_login",
    "assert_htmx_response",
    "assert_data_testids",
    "assert_no_n_plus_one",
    "assert_form_error",
]


def assert_redirects_to_login(response: HttpResponse, next_url: str | None = None) -> None:
    """Assert that the response redirects to the login page.

    Args:
        response: Django test client response.
        next_url: Optional URL that should appear as ?next= parameter.

    Example:
        response = client.get("/dashboard/")
        assert_redirects_to_login(response, next_url="/dashboard/")
    """
    assert response.status_code in (301, 302), (
        f"Expected redirect (301/302), got {response.status_code}"
    )
    location = response.get("Location", "")
    assert "/login" in location or "/accounts/login" in location, (
        f"Expected redirect to login URL, got: {location!r}"
    )
    if next_url is not None:
        from urllib.parse import quote
        assert quote(next_url, safe="") in location or next_url in location, (
            f"Expected next={next_url!r} in redirect Location, got: {location!r}"
        )


def assert_htmx_response(response: HttpResponse, status_code: int = 200) -> None:
    """Assert response is a valid HTMX partial (no full HTML page wrapper).

    A valid HTMX partial must not contain <html>, <head>, or <body> tags,
    as those indicate a full page render was returned instead of a fragment.

    Args:
        response: Django test client response.
        status_code: Expected HTTP status code (default: 200).

    Example:
        response = client.get("/items/", HTTP_HX_REQUEST="true")
        assert_htmx_response(response)
    """
    assert response.status_code == status_code, (
        f"Expected status {status_code}, got {response.status_code}"
    )
    content = response.content.decode(errors="replace")
    for forbidden_tag in ("<html", "<head", "<body"):
        assert forbidden_tag not in content, (
            f"HTMX partial must not contain full <html> page \u2014 "
            f"found {forbidden_tag!r} tag, a fragment was expected"
        )


def assert_data_testids(response: HttpResponse, status_code: int = 200) -> None:
    """Assert all HTMX interactive elements have data-testid attributes (ADR-048).

    Parses the response HTML with BeautifulSoup and verifies that every element
    with an hx-* attribute (hx-post, hx-get, hx-delete, hx-put, hx-patch) also
    carries a data-testid attribute, as required by ADR-048.

    Requires: pip install beautifulsoup4

    Args:
        response: Django test client response.
        status_code: Expected HTTP status code (default: 200).

    Example:
        response = auth_client.get("/projects/")
        assert_data_testids(response)
    """
    import pytest
    pytest.importorskip("bs4", reason="beautifulsoup4 not installed — pip install beautifulsoup4")
    from bs4 import BeautifulSoup

    assert response.status_code == status_code, (
        f"Expected status {status_code}, got {response.status_code}"
    )
    content = response.content.decode(errors="replace")
    soup = BeautifulSoup(content, "html.parser")

    _HTMX_ATTRS = ("hx-post", "hx-get", "hx-delete", "hx-put", "hx-patch")
    violations: list[str] = []
    for attr in _HTMX_ATTRS:
        for el in soup.find_all(attrs={attr: True}):
            if not el.get("data-testid"):
                tag_repr = f"<{el.name} {attr}={el[attr]!r}>"
                violations.append(tag_repr)

    assert not violations, (
        f"ADR-048: {len(violations)} HTMX element(s) missing data-testid:\n"
        + "\n".join(f"  {v}" for v in violations)
        + "\n\nFix: add data-testid=\"<name>\" to each listed element."
    )


def assert_no_n_plus_one(queries: list, threshold: int = 5) -> None:
    """Assert query count is within acceptable threshold (N+1 guard).

    Use with django_assert_num_queries or pytest-django's assertNumQueries.

    Args:
        queries: List of recorded queries (e.g. from django.test.utils.CaptureQueriesContext).
        threshold: Maximum allowed query count (default: 5).

    Example:
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        with CaptureQueriesContext(connection) as ctx:
            response = client.get("/items/")
        assert_no_n_plus_one(ctx.captured_queries, threshold=3)
    """
    assert len(queries) <= threshold, (
        f"Possible N+1 query problem: {len(queries)} queries executed "
        f"(threshold: {threshold}). "
        f"Consider select_related() or prefetch_related()."
    )


def assert_form_error(response: HttpResponse, field: str, message: str) -> None:
    """Assert that a form in the response contains a specific field error.

    Args:
        response: Django test client response (must have context with 'form').
        field: Form field name with the error.
        message: Expected error message substring.

    Example:
        response = client.post("/register/", data={})
        assert_form_error(response, "email", "required")
    """
    assert hasattr(response, "context") and response.context is not None, (
        "Response has no context \u2014 ensure the view renders a template"
    )
    form = response.context.get("form")
    assert form is not None, "No 'form' found in response context"
    assert field in form.errors, (
        f"Field {field!r} has no errors. Errors: {dict(form.errors)}"
    )
    error_messages = " ".join(str(e) for e in form.errors[field])
    assert message in error_messages, (
        f"Expected {message!r} in errors for field {field!r}, got: {error_messages!r}"
    )
