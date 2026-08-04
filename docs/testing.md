# Tests

The policy (TDD required for business logic, not required for typos and config)
is in [`../CLAUDE.md`](../CLAUDE.md). This is the mechanics: what counts as
enough, how not to break the parallel run, where factories live.

## Running them

```bash
make test        # Python in parallel + JS unit tests
make test-seq    # sequential, for debugging one failure
make test-cov    # coverage report in htmlcov/
uv run pytest apps/accounts/tests/test_services.py
uv run pytest -k "redirect"
```

Tests use in-memory SQLite (`config.settings.test`) — no Docker, no Redis, no
`.env` file. Celery runs tasks inline, mail goes to `locmem`, and the password
hasher is the fast one.

## Minimum coverage

**A view test** covers: anonymous access → redirect, GET 200 with the expected
template, POST valid → saved, POST invalid → form errors.

**A service test** covers: the happy path, the failure path, and the boundary
that made you write the service in the first place.

**A regression test** names what it protects against. When a bug reaches
production, the fix and the test that would have caught it go in the same commit.

## The parallel run (pytest-xdist)

Tests run with `--dist=loadscope --numprocesses=auto`. Every test in one module
lands on the same worker; different modules get separate processes with their own
in-memory database. That gives four rules, and breaking them produces flaky
failures that never reproduce in isolation:

1. **Unique values come from `factory.Sequence`**, `uuid` or `secrets` — never a
   hardcoded `"test@example.com"` outside a `django_db` test whose transaction is
   always rolled back.

2. **Module-level state needs an `autouse` reset fixture.** Registries,
   singletons, thread-locals. The root `conftest.py` resets the two the framework
   itself leaks: the active language (`LocaleMiddleware` activates one per
   request and never deactivates it) and the local-memory cache. When you add a
   registry, add its reset fixture with it — see `isolated_registry` in
   `apps/core/tests/test_seeding.py` and `only_temporary_checks` in
   `test_health.py`.

3. **`scope="function"` for every fixture that touches the database.** A `module`
   or `session` scoped fixture that writes breaks isolation between the tests
   sharing a worker.

4. **`transaction=True` only when you genuinely need `on_commit`.** Those tests
   flush tables afterwards and are much slower.

## Factories

Factories live in `apps/<app>/factories.py`, not in a `conftest.py` — tests in
other apps import them, and a per-app copy is how the set of required flags
drifts apart. `conftest.py` holds fixtures only.

`UserFactory` / `ModeratorFactory` / `AdminFactory` come from
`apps.accounts.factories`. Do not write a local user factory.

`apps/core/tests/test_factories.py` discovers every factory in the project and
exercises it: a new one is covered automatically, and one broken by a model
change fails under its own name instead of somewhere inside an unrelated test.

## Query budgets

`apps/core/tests/test_seo.py` asserts that rendering a page costs a bounded
number of queries — the count must not grow with the number of objects on the
page. Add a case when you add a list view. Raising a budget is allowed; say in
the pull request why the extra query is unavoidable.

## Documentation drift

`apps/core/tests/test_docs_references.py` walks every `.md` file and checks that
relative links resolve and that referenced `make` targets exist. Rename a doc and
this is what tells you which files pointed at it.

## What tests do not catch

The Django test client sees HTML, not a browser. Nothing in pytest notices a dead
asset bundle, a JS exception, an Alpine component that never initialised, or a
page that scrolls sideways on a phone. That is what `make demo-smoke` is for —
see [`test-environment.md`](test-environment.md).
