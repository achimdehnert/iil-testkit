# tests/test_plugin.py — Django-context tests only (no pytester)
import warnings
from unittest.mock import MagicMock

import pytest

from iil_testkit.plugin import pytest_collection_modifyitems


def _make_item(name, marker=None):
    item = MagicMock(spec=pytest.Function)
    item.originalname = name
    item.name = name
    item.nodeid = f"tests/test_fake.py::{name}"
    item.get_closest_marker.return_value = marker
    return item


def _make_config(mode="error", relax=False):
    config = MagicMock()
    config.getoption.return_value = relax
    config.getini.return_value = mode
    return config


# ---------------------------------------------------------------------------
# marker + ini registration (via pytestconfig)
# ---------------------------------------------------------------------------


def test_should_register_no_naming_convention_marker(pytestconfig):
    ini_lines = pytestconfig.getini("markers")
    assert any("no_naming_convention" in line for line in ini_lines)


def test_should_accept_relax_naming_option(pytestconfig):
    val = pytestconfig.getoption("--relax-naming", default=False)
    assert val is False


def test_should_read_iil_naming_mode_ini(pytestconfig):
    mode = pytestconfig.getini("iil_naming_mode")
    assert mode in ("error", "warn")


# ---------------------------------------------------------------------------
# pytest_collection_modifyitems — direct unit tests
# ---------------------------------------------------------------------------


def test_should_pass_for_correctly_named_item():
    config = _make_config(mode="error", relax=False)
    items = [_make_item("test_should_do_something")]
    pytest_collection_modifyitems(config, items)


def test_should_fail_for_bad_name_in_error_mode():
    config = _make_config(mode="error", relax=False)
    items = [_make_item("test_should_bad_name")]
    pytest_collection_modifyitems(config, items)


def test_should_raise_on_violation_in_error_mode():
    config = _make_config(mode="error", relax=False)
    items = [_make_item("test_violating_name")]
    with pytest.raises(BaseException, match="test_should_"):
        pytest_collection_modifyitems(config, items)


def test_should_skip_check_when_relax_naming_flag_set():
    config = _make_config(relax=True)
    items = [_make_item("test_violating_name")]
    pytest_collection_modifyitems(config, items)


def test_should_skip_marked_item():
    marker = MagicMock()
    config = _make_config(mode="error", relax=False)
    items = [_make_item("test_legacy", marker=marker)]
    pytest_collection_modifyitems(config, items)


def test_should_warn_for_bad_name_in_warn_mode():
    config = _make_config(mode="warn", relax=False)
    items = [_make_item("test_violating_name")]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pytest_collection_modifyitems(config, items)
    assert len(caught) == 1
    assert "test_should_" in str(caught[0].message)


def test_should_include_violation_count_in_message():
    config = _make_config(mode="warn", relax=False)
    items = [_make_item("test_violating_one"), _make_item("test_violating_two")]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        pytest_collection_modifyitems(config, items)
    assert "2 test" in str(caught[0].message)
