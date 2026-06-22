# CLAUDE.md — iil-testkit

Operating guide for agents (and humans) working in this repo.

## What this is

`iil-testkit` (dist `iil-testkit`, import `iil_testkit`) is the **shared test
foundation for all Platform Django repos** ([ADR-100](https://github.com/achimdehnert/platform/blob/main/docs/adr/ADR-100-iil-testkit-shared-test-factory-package.md)).
It is a PyPI package that doubles as a **pytest plugin** (registered via the
`pytest11` entry-point), providing:

- **Naming/marker enforcement** — the plugin enforces the **ADR-057** test
  naming convention (`test_should_*`) and **ADR-058** markers. Modes:
  `error` (default for consumers) / `warn` / opt-out (`--relax-naming`,
  `@pytest.mark.no_naming_convention`).
- **Fixtures** (`iil_testkit.fixtures`) — `db_user`, `staff_user`, `admin_user`,
  `api_client`, `auth_client`, `staff_client`, DRF clients.
- **Factories** (`iil_testkit.factories`) — factory-boy base factories.
- **Assertion helpers** (`iil_testkit.assertions`).
- **Contract verifier** (`iil_testkit.contract`, ADR-155) and **smoke** helpers
  (`iil_testkit.smoke`).
- **Tenant helpers** (`iil_testkit.tenant_mixins.TenantTestMixin`,
  `iil_testkit.contrib.tenants`).

`import iil_testkit` is **lazy by design**: the top-level module does NOT eagerly
import Django. `TenantTestMixin` is re-exported via a module-level `__getattr__`
so the `pytest11` entry-point stays safe to load even in non-Django repos (e.g.
MCP packages). Do **not** add eager imports of Django-dependent submodules to
`iil_testkit/__init__.py`.

## Setup

```bash
make install          # pip install -e ".[dev]"
```

Requires Python **>=3.12**.

## Test, lint, types

```bash
make test             # python3 -m pytest (coverage gate >=80%)
make lint             # ruff check .
python3 -m mypy iil_testkit   # type-check (see Known issues)
```

`make test` runs the suite against `tests.settings` with the package's own
plugin in **`warn`** mode (its self-tests predate the `test_should_*`
convention; consumers run in `error`). Coverage gate is **80%** (currently ~85%).

## Architecture / module map

| Module | Purpose |
|---|---|
| `iil_testkit.plugin` | pytest plugin: naming (ADR-057) + marker (ADR-058) enforcement |
| `iil_testkit.fixtures` | shared pytest fixtures (users, clients, DRF) |
| `iil_testkit.factories` | factory-boy base factories |
| `iil_testkit.assertions` | reusable assertion helpers |
| `iil_testkit.contract` | contract-test verifier (ADR-155) |
| `iil_testkit.smoke` | view/HTML smoke-test helpers |
| `iil_testkit.tenant_mixins` | `TenantTestMixin` (Django, lazily re-exported at top level) |
| `iil_testkit.contrib` | optional tenant factories etc. (omitted from coverage) |

`__version__` is resolved from installed package **metadata**
(`importlib.metadata.version("iil-testkit")`), falling back to `"0.0.0.dev0"` in
a bare source checkout. The build version is the static `version` in
`pyproject.toml` `[project]`.

## Conventions

- Test names: `test_should_<expected_behavior>` (ADR-057). The plugin enforces
  this for consumers.
- Commits: `[feat|fix|refactor|docs|test|chore](scope): description`.
- Ruff (`E,F,I,UP`, line-length 100) and mypy both target **py312**.

## Release (GATED — not on-merge)

Publishing to PyPI is a **manual, gated** action. Do **not** publish, tag, or
release as part of routine PRs. Bump the static `version` in `pyproject.toml`
`[project]`, update `CHANGELOG.md`, and only then run the gated release path.

## Known issues

- **3 pre-existing mypy errors** (a later tier — do not fix as part of
  agent-readiness work):
  - `iil_testkit/smoke.py:144` — `"object" has no attribute "get"` [attr-defined]
  - `iil_testkit/contract/verifier.py:140` — `assert_no_param` signature
    incompatible with supertype [override]
  - `iil_testkit/contract/verifier.py:463` — incompatible return value type
    `Any | None` vs `str` [return-value]
- Pre-existing built wheels (`dist/iil_testkit-0.2.0*`, `0.3.0*`) are tracked in
  git — a separate cleanup, not in scope here.
