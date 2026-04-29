# iil-testkit

**Shared Test Factory Package for all Platform Django repos** — [ADR-100](https://github.com/achimdehnert/platform/blob/main/docs/adr/ADR-100-iil-testkit-shared-test-factory-package.md)

[![PyPI](https://img.shields.io/pypi/v/iil-testkit)](https://pypi.org/project/iil-testkit/)

## Installation

```bash
pip install iil-testkit
```

In `requirements-test.txt`:
```
iil-testkit>=0.4.0
```

With DRF support:
```
iil-testkit[drf]>=0.4.0
```

## Extras / Optional Dependencies

| Extra | Additional deps | Purpose |
|---|---|---------|
| `drf` | djangorestframework>=3.14 | DRF `APIClient` fixtures (`drf_api_client`, `drf_auth_client`) |
| `django` | django>=4.2, pytest-django>=4.8 | Explicit Django pin (normally pulled transitively) |
| `smoke` | django, beautifulsoup4>=4.12 | HTML smoke assertions |

## Quick Setup

In your `tests/conftest.py`:
```python
pytest_plugins = ["iil_testkit.fixtures"]
```

## Factories

```python
# tests/factories.py — import shared, extend repo-specific
from iil_testkit.factories import UserFactory  # noqa: F401
import factory

class MyModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "myapp.MyModel"
    user = factory.SubFactory(UserFactory)
```

For multi-tenant repos:
```python
from iil_testkit.contrib.tenants import TenantFactory  # noqa: F401
```

## Fixtures

| Fixture | Description |
|---|---|
| `db_user` | Standard active user, saved to DB |
| `staff_user` | User with `is_staff=True` |
| `admin_user` | User with `is_superuser=True` |
| `api_client` | Unauthenticated Django `Client` |
| `auth_client` | Django `Client` logged in as `db_user` |
| `staff_client` | Django `Client` logged in as `staff_user` |
| `drf_api_client` | Unauthenticated DRF `APIClient` (skips if DRF missing) |
| `drf_auth_client` | DRF `APIClient` authenticated as `db_user` (skips if DRF missing) |

```python
def test_should_view_dashboard(auth_client):
    response = auth_client.get("/dashboard/")
    assert response.status_code == 200

def test_should_require_auth(api_client):
    from iil_testkit.assertions import assert_redirects_to_login
    response = api_client.get("/protected/")
    assert_redirects_to_login(response)
```

## Assertion Helpers

```python
from iil_testkit.assertions import (
    assert_redirects_to_login,
    assert_htmx_response,
    assert_no_n_plus_one,
    assert_form_error,
)
```

| Helper | Description |
|---|---|
| `assert_redirects_to_login(response)` | Asserts 301/302 to `/login` or `/accounts/login` |
| `assert_htmx_response(response)` | Asserts no full `<html>` page in HTMX partial |
| `assert_no_n_plus_one(queries, threshold=5)` | Asserts query count within threshold |
| `assert_form_error(response, field, message)` | Asserts form field error in context |

## Naming Convention Plugin (ADR-057)

Auto-registered when installed. All test functions must follow `test_should_*`:

```
Naming convention violations — 1 test(s) must start with 'test_should_':
  tests/test_foo.py::test_login
```

Opt-out per test:
```python
@pytest.mark.no_naming_convention
def test_legacy_name(): ...
```

Opt-out globally: `pytest --relax-naming`

Warn instead of error: `iil_naming_mode = "warn"` in `pyproject.toml`

## Architecture

See [ADR-100](https://github.com/achimdehnert/platform/blob/main/docs/adr/ADR-100-iil-testkit-shared-test-factory-package.md).
