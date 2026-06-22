# plugin_tests/test_should_plugin_enforce_naming.py
# Uses pytester to test the iil_testkit naming convention plugin
# in a completely isolated subprocess (no Django context).
import pytest


def test_should_pass_for_correctly_named_test(pytester):
    pytester.makepyprojecttoml("""
[tool.pytest.ini_options]
iil_naming_mode = "error"
""")
    pytester.makepyfile("""
def test_should_do_something():
    assert True
""")
    result = pytester.runpytest("-p", "iil_testkit.plugin", "--relax-naming")
    result.assert_outcomes(passed=1)


def test_should_fail_for_non_conforming_name_in_error_mode(pytester):
    pytester.makepyprojecttoml("""
[tool.pytest.ini_options]
iil_naming_mode = "error"
""")
    pytester.makepyfile("""
def test_bad_name():
    assert True
""")
    result = pytester.runpytest("-p", "iil_testkit.plugin")
    # error mode raises pytest.UsageError → the session aborts before any test
    # runs (no per-test outcomes), exiting with USAGE_ERROR.
    assert result.ret == pytest.ExitCode.USAGE_ERROR
    result.stderr.fnmatch_lines(["*Naming convention violations*"])


def test_should_warn_for_non_conforming_name_in_warn_mode(pytester):
    pytester.makepyprojecttoml("""
[tool.pytest.ini_options]
iil_naming_mode = "warn"
""")
    pytester.makepyfile("""
def test_bad_name():
    assert True
""")
    result = pytester.runpytest("-p", "iil_testkit.plugin")
    result.assert_outcomes(passed=1)


def test_should_skip_check_with_relax_naming_flag(pytester):
    pytester.makepyprojecttoml("""
[tool.pytest.ini_options]
iil_naming_mode = "error"
""")
    pytester.makepyfile("""
def test_bad_name():
    assert True
""")
    result = pytester.runpytest("-p", "iil_testkit.plugin", "--relax-naming")
    result.assert_outcomes(passed=1)


def test_should_skip_check_for_marked_test(pytester):
    pytester.makepyprojecttoml("""
[tool.pytest.ini_options]
iil_naming_mode = "error"
""")
    pytester.makepyfile("""
import pytest

@pytest.mark.no_naming_convention
def test_legacy_name():
    assert True
""")
    result = pytester.runpytest("-p", "iil_testkit.plugin")
    result.assert_outcomes(passed=1)
