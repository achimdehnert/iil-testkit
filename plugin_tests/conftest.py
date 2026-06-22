# plugin_tests/conftest.py
# The `pytester` plugin these tests rely on is enabled in the rootdir
# conftest.py (../conftest.py): pytest 9 forbids `pytest_plugins` in a
# non-top-level conftest.
import pytest


@pytest.fixture(autouse=True)
def _hermetic_inner_pytest(monkeypatch):
    """Make the inner pytester sessions hermetic.

    The naming-convention plugin under test is pure pytest (no Django, no
    third-party plugins). Without this, each inner `runpytest` autoloads the
    full installed plugin set — pytest-django (which then errors on the
    inherited DJANGO_SETTINGS_MODULE), playwright, schemathesis, randomly … —
    which misbehaves nested and makes these tests fail. Disable autoload and
    drop the leaked Django settings; each test explicitly loads only
    `-p iil_testkit.plugin`.
    """
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.delenv("DJANGO_SETTINGS_MODULE", raising=False)
