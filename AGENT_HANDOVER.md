# AGENT_HANDOVER.md — iil-testkit

Living handover for the next agent. Keep current-state and next-priorities honest.

## Current state (observed 2026-06-22)

- Test suite is **green**: `make test` → **141 passed**, coverage **~85%**
  (gate 80%). Verified on branch off the freshly-merged `origin/main` (#8).
- `ruff check .` clean.
- `python3 -c "import iil_testkit; iil_testkit.__version__"` resolves the
  version from package metadata; `iil_testkit.TenantTestMixin` still lazily
  re-exports (no eager Django import).
- Build is healthy: `python3 -m build --wheel` → `iil_testkit-0.5.3`.

## Recently landed

- **#8** — `fix(tests): restore plugin_tests collection + make the suite green
  (pytest 9)`. The conftest/pytester fix that turned the suite green; this
  handover is written on top of it.
- **agent-readiness (this PR)** — added `CLAUDE.md` + `AGENT_HANDOVER.md`;
  `__version__` now resolves from metadata (lazy `__getattr__`/`__all__`
  preserved); aligned config with `requires-python>=3.12` (ruff/mypy → py312,
  classifiers drop 3.11); removed the dead `[tool.hatch.version]` block (it was
  inert — `version` is static in `[project]`, no `dynamic`).

## Known issues / TODO

- **3 pre-existing mypy errors** (left untouched — next tier):
  - `iil_testkit/smoke.py:144` — `attr-defined` (`object` has no `.get`)
  - `iil_testkit/contract/verifier.py:140` — `override` signature mismatch
  - `iil_testkit/contract/verifier.py:463` — `return-value` (`Any | None` vs `str`)
- Tracked built wheels under `dist/` (`0.2.0`, `0.3.0`) should be untracked +
  gitignored (separate cleanup PR).

## Next priorities

1. Resolve the 3 mypy errors (Tier 2 typing pass), then consider tightening
   `[tool.mypy] strict`.
2. Untrack `dist/*.whl` / `dist/*.tar.gz` and add `dist/` to `.gitignore`.
3. Raise the self-test naming mode from `warn` toward `error` once the package's
   own legacy test names are migrated to `test_should_*`.

## Pointers

- Operating guide: `CLAUDE.md`
- Public usage / fixtures / assertions: `README.md`
- Architecture: ADR-100 (shared test factory), ADR-057 (naming), ADR-058
  (markers), ADR-155 (contract testing) in the platform repo.
- Tests live in `tests/` and `plugin_tests/`; settings in `tests/settings`.
