# Changelog

## [0.5.3] — 2026-05-14

- **Fixed**
  - `tests/test_tenant_mixins.py::test_set_tenant_updates_session`: replace bare-dict session mock with `MagicMock.side_effect` so `.save()` is callable. Latent test bug from before 0.5.0 that the naming-mode-error abort had been hiding. Bump version so the publish workflow re-triggers (previous 0.5.2 run failed at the test gate on this same case).

## [0.5.2] — 2026-05-14

- **Fixed**
  - `pyproject.toml` `[tool.pytest.ini_options]`: set `iil_naming_mode = "warn"` (was `"error"`) and `iil_repo_type = "package"` so the testkit's own test suite — which pre-dates the `test_should_*` convention introduced in 0.5.0 — can be collected. Without this, the publish-gate `pytest` step bailed with `no tests ran` (exit 4), blocking the 0.5.1 publish. Downstream consumers are unaffected: they keep their own per-repo `iil_naming_mode` setting.

## [0.5.1] — 2026-05-14

- **Fixed**
  - `__init__.py`: lazy-load `TenantTestMixin` via module-level `__getattr__`. The previous eager `from iil_testkit.tenant_mixins import TenantTestMixin` pulled `django.http.HttpRequest` on plain `import iil_testkit`, which broke pytest startup in non-Django consumers (MCP packages) that load this package via the `pytest11` entry-point. Importing the package no longer requires Django; only accessing `iil_testkit.TenantTestMixin` does.

## [0.4.1] — 2026-04-29

- **Added**
  - Updated version to 0.4.1 in `pyproject.toml`.

- **Changed**
  - Revised workflow documentation files by replacing symlinks with regular files for better manageability and clarity.

- **Fixed**
  - No fixes were made in this version.


## v0.4.1 (2026-04-28)

### Fixed
- `plugin.py`: `iil_naming_mode` ini-Option via `parser.addini()` registrieren — behebt `ValueError: unknown configuration value` INTERNALERROR in pytest (trat auf wenn kein `iil_naming_mode` in pyproject.toml definiert war)

---

## v0.3.0 (2026-04-02)

### Added
- **`iil_testkit.contract` module** — Platform-weiter Contract-Verifier (ADR-155)
  - `ContractVerifier(cls)` — Klassen-API Contracts (Package-APIs, Service-Layer)
  - `CallableContractVerifier(func)` — Freie Funktionen
  - `TaskContractVerifier(task)` — Celery Task Signaturen (korrekte Introspection)
  - `ResponseShapeVerifier(shape)` — REST API Response-Shapes
  - `BaseContractVerifier` — Gemeinsame ABC-Basis
- Factory Methods: `ContractVerifier.for_callable()`, `ContractVerifier.for_task()`
- `assert_init_params(exhaustive=True)` — bidirektionale Parameterprüfung
- `assert_raises()` — Exception-Docstring-Contracts (assert statt warnings.warn)
- `assert_return_keys()` — Return-Shape-Contracts (assert statt warnings.warn)
- `assert_return_origin()` — Generic Return-Type Prüfung
- `assert_is_acks_late()` — Celery Platform-Standard Prüfung
- 53 neue Tests für alle Verifier-Typen

## v0.2.0 (2026-03-10)

### Added
- `drf_api_client` fixture — unauthenticated DRF `APIClient` (auto-skips if DRF not installed)
- `drf_auth_client` fixture — DRF `APIClient` authenticated as `db_user` via `force_authenticate`
- `[drf]` optional dependency group in `pyproject.toml`
- `CHANGELOG.md`

### Fixed
- **BREAKING BUG**: `plugin.py` used `pytest.fail()` in `pytest_collection_modifyitems` which
  caused `INTERNALERROR` (not a normal test failure) when naming violations were found
- Changed default `iil_naming_mode` from `"error"` to `"warn"` — naming convention is now
  advisory by default; opt-in to `"error"` mode explicitly when all tests follow `test_should_*`
- `pytest.fail()` replaced with `pytest.UsageError()` in error-mode to produce a proper
  collection error instead of INTERNALERROR

### Changed
- All Django-Hub repos should now use `iil-testkit>=0.2.0` in `requirements-test.txt`
- Repos with legacy `test_*` naming will get a warning, not a hard failure

## v0.1.0 (2026-03-06)

### Added
- Initial release
- `UserFactory`, `StaffUserFactory`, `AdminUserFactory`
- `db_user`, `staff_user`, `admin_user`, `api_client`, `auth_client`, `staff_client` fixtures
- `assert_redirects_to_login`, `assert_htmx_response`, `assert_no_n_plus_one`, `assert_form_error`
- `iil-testkit` pytest plugin enforcing `test_should_*` naming convention (ADR-057)
- `iil_testkit.contrib.tenants.TenantFactory` for multi-tenant repos
