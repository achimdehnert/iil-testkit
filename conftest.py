# Top-level conftest for the iil-testkit repo.
#
# pytest 9 requires `pytest_plugins` to be declared ONLY in the rootdir
# conftest — it is rejected in any non-top-level conftest (which is what
# aborted collection of plugin_tests/ before). The `pytester` plugin is
# needed by plugin_tests/ to exercise the iil-testkit pytest plugin in
# isolated subprocesses, so it is enabled here for the whole test session.
pytest_plugins = ["pytester"]
