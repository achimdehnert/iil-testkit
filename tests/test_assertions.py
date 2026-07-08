# tests/test_assertions.py
import pytest

from iil_testkit.assertions import (
    assert_form_error,
    assert_htmx_response,
    assert_no_n_plus_one,
    assert_redirects_to_login,
)


# ---------------------------------------------------------------------------
# assert_no_n_plus_one
# ---------------------------------------------------------------------------


def test_should_pass_when_queries_within_threshold():
    assert_no_n_plus_one(list(range(3)), threshold=5)


def test_should_pass_when_queries_equal_threshold():
    assert_no_n_plus_one(list(range(5)), threshold=5)


def test_should_fail_when_queries_exceed_threshold():
    with pytest.raises(AssertionError, match="Possible N\\+1"):
        assert_no_n_plus_one(list(range(10)), threshold=5)


def test_should_include_query_count_in_n_plus_one_message():
    with pytest.raises(AssertionError, match="10 queries"):
        assert_no_n_plus_one(list(range(10)), threshold=5)


def test_should_include_threshold_in_n_plus_one_message():
    with pytest.raises(AssertionError, match="threshold: 5"):
        assert_no_n_plus_one(list(range(10)), threshold=5)


# ---------------------------------------------------------------------------
# assert_htmx_response
# ---------------------------------------------------------------------------


class _Response:
    """Minimal fake response for assertion tests."""

    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self.status_code = status_code


def test_should_pass_for_valid_htmx_fragment():
    assert_htmx_response(_Response(b"<div>fragment</div>"))


def test_should_pass_for_empty_fragment():
    assert_htmx_response(_Response(b""))


def test_should_reject_full_html_page():
    with pytest.raises(AssertionError, match="full <html>"):
        assert_htmx_response(_Response(b"<html><body>Full page</body></html>"))


def test_should_reject_head_tag():
    with pytest.raises(AssertionError, match="full <html>"):
        assert_htmx_response(_Response(b"<head><title>Page</title></head>"))


def test_should_reject_body_tag():
    with pytest.raises(AssertionError, match="full <html>"):
        assert_htmx_response(_Response(b"<body>content</body>"))


def test_should_fail_on_wrong_status_code():
    with pytest.raises(AssertionError, match="Expected status 200, got 404"):
        assert_htmx_response(_Response(b"not found", status_code=404))


def test_should_pass_for_custom_expected_status_code():
    assert_htmx_response(_Response(b"<div>ok</div>", status_code=201), status_code=201)


# ---------------------------------------------------------------------------
# assert_redirects_to_login
# ---------------------------------------------------------------------------


class _RedirectResponse:
    """Minimal fake redirect response."""

    def __init__(self, status_code: int, location: str):
        self.status_code = status_code
        self._location = location

    def get(self, header: str, default: str = "") -> str:
        if header == "Location":
            return self._location
        return default


def test_should_pass_for_302_to_login():
    assert_redirects_to_login(_RedirectResponse(302, "/login/?next=/dashboard/"))


def test_should_pass_for_301_to_accounts_login():
    assert_redirects_to_login(_RedirectResponse(301, "/accounts/login/"))


def test_should_fail_for_200_response():
    with pytest.raises(AssertionError, match="Expected redirect"):
        assert_redirects_to_login(_RedirectResponse(200, "/login/"))


def test_should_fail_when_redirect_not_to_login():
    with pytest.raises(AssertionError, match="Expected redirect to login URL"):
        assert_redirects_to_login(_RedirectResponse(302, "/home/"))


def test_should_pass_when_next_url_matches():
    assert_redirects_to_login(
        _RedirectResponse(302, "/login/?next=%2Fdashboard%2F"),
        next_url="/dashboard/",
    )


def test_should_fail_when_next_url_missing():
    with pytest.raises(AssertionError, match="next="):
        assert_redirects_to_login(
            _RedirectResponse(302, "/login/"),
            next_url="/dashboard/",
        )


# ---------------------------------------------------------------------------
# assert_form_error
# ---------------------------------------------------------------------------


class _FakeForm:
    def __init__(self, errors: dict):
        self.errors = errors


class _FormResponse:
    def __init__(self, form):
        self.context = {"form": form}


def test_should_pass_when_form_has_expected_error():
    resp = _FormResponse(_FakeForm({"email": ["This field is required."]}))
    assert_form_error(resp, "email", "required")


def test_should_fail_when_field_has_no_errors():
    resp = _FormResponse(_FakeForm({}))
    with pytest.raises(AssertionError, match="has no errors"):
        assert_form_error(resp, "email", "required")


def test_should_fail_when_error_message_does_not_match():
    resp = _FormResponse(_FakeForm({"email": ["Enter a valid email."]}))
    with pytest.raises(AssertionError, match="Expected 'required'"):
        assert_form_error(resp, "email", "required")


def test_should_fail_when_response_has_no_context():
    class _NoContext:
        context = None

    with pytest.raises(AssertionError, match="no context"):
        assert_form_error(_NoContext(), "email", "required")


def test_should_fail_when_form_not_in_context():
    class _EmptyContext:
        context = {}

    with pytest.raises(AssertionError, match="No 'form'"):
        assert_form_error(_EmptyContext(), "email", "required")
