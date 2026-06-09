# tests/test_plugin_hooks.py — coverage for the remaining plugin hooks
# (configure / addoption / sessionfinish / _as_bool). ADR-057 + ADR-058.
import warnings
from unittest.mock import MagicMock

import pytest

from iil_testkit.plugin import (
    MANDATORY_MARKERS,
    _as_bool,
    pytest_addoption,
    pytest_configure,
    pytest_sessionfinish,
)


# ---------------------------------------------------------------------------
# pytest_configure
# ---------------------------------------------------------------------------


def test_should_register_markers_on_configure():
    config = MagicMock()
    pytest_configure(config)
    registered = " ".join(str(c) for c in config.addinivalue_line.call_args_list)
    assert "no_naming_convention" in registered
    assert "iil_testkit" in registered


# ---------------------------------------------------------------------------
# pytest_addoption
# ---------------------------------------------------------------------------


def test_should_add_relax_naming_option_and_inis():
    parser = MagicMock()
    pytest_addoption(parser)
    assert parser.addoption.call_args[0][0] == "--relax-naming"
    ini_names = {call.args[0] for call in parser.addini.call_args_list}
    assert {"iil_naming_mode", "iil_repo_type", "iil_marker_enforce"} <= ini_names


def test_should_tolerate_duplicate_ini_registration():
    parser = MagicMock()
    parser.addini.side_effect = ValueError("already registered")
    # Must not raise — each addini is guarded by try/except ValueError.
    pytest_addoption(parser)


# ---------------------------------------------------------------------------
# pytest_sessionfinish (ADR-058 marker enforcement)
# ---------------------------------------------------------------------------


def _marker(name):
    m = MagicMock()
    m.name = name
    return m


def _make_session(repo_type="mcp", enforce="false", marker_names=()):
    session = MagicMock()
    inis = {"iil_repo_type": repo_type, "iil_marker_enforce": enforce}
    session.config.getini.side_effect = lambda key: inis.get(key)
    item = MagicMock()
    item.iter_markers.return_value = [_marker(n) for n in marker_names]
    session.items = [item]
    return session


def test_should_pass_when_all_mandatory_markers_present():
    session = _make_session(repo_type="mcp", marker_names=MANDATORY_MARKERS["mcp"])
    pytest_sessionfinish(session, exitstatus=0)
    tr = session.config.pluginmanager.get_plugin.return_value
    assert any("PASSED" in str(c) for c in tr.write_line.call_args_list)


def test_should_report_missing_markers_without_enforce():
    session = _make_session(repo_type="mcp", enforce="false", marker_names=["f1"])
    session.exitstatus = 0
    pytest_sessionfinish(session, exitstatus=0)
    # enforce off → exit status untouched
    assert session.exitstatus == 0


def test_should_fail_session_when_enforce_and_markers_missing():
    session = _make_session(repo_type="mcp", enforce="true", marker_names=["f1"])
    session.exitstatus = 0
    pytest_sessionfinish(session, exitstatus=0)
    assert session.exitstatus == 1


def test_should_warn_on_unknown_repo_type():
    session = _make_session(repo_type="bogus")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pytest_sessionfinish(session, exitstatus=0)
    assert any("unknown iil_repo_type" in str(w.message) for w in caught)


def test_should_not_crash_when_terminalreporter_absent():
    session = _make_session(repo_type="mcp", marker_names=["f1"])
    session.config.pluginmanager.get_plugin.return_value = None
    pytest_sessionfinish(session, exitstatus=0)  # no terminalreporter → no crash


# ---------------------------------------------------------------------------
# _as_bool
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value,expected",
    [
        (True, True),
        (False, False),
        ("true", True),
        ("1", True),
        ("yes", True),
        ("false", False),
        ("no", False),
        ("", False),
        (1, True),
        (0, False),
    ],
)
def test_should_coerce_value_to_bool(value, expected):
    assert _as_bool(value) is expected
