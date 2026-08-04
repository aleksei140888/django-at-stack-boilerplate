# Conventions

Style, commits, versioning, and the gates that enforce them.

## Code style

Black + isort + flake8, line length 100, configured in `pyproject.toml` and
`.flake8`. `make beautify` formats, `make lint` checks, `make ci` does everything
including tests.

The set of paths the formatter owns lives in one place — `PY_PATHS` in the
Makefile — so the Makefile, pre-commit and CI cannot drift apart. Black is
configured with `force-exclude` rather than `extend-exclude`: pre-commit passes
file paths explicitly, and black only applies `extend-exclude` to paths it
discovered itself, so migrations would be reformatted by the hook and left alone
by `make beautify`, and the same files would keep coming back dirty.

`# noqa` is allowed with a reason worth reading next to it.

## Comments

Comment the *why*: the constraint, the alternative rejected, the failure this
line prevents. What the code does is already in the code. A comment that will be
wrong after the next refactor is worse than none.

## Commits

```
<type>(<scope>): <short description>

Body after a blank line when it earns its place.
```

Types: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`.
Scope is the app or area (`accounts`, `core`, `frontend`, `deps`).

The body explains why the change is the way it is. A reviewer can read the diff;
they cannot read the three approaches you discarded.

## Versioning

`YYYY.M.PATCH` — for example `2026.8.0`. The same string appears in three files:

- `pyproject.toml` → `[project] version`
- `package.json` → `version`
- `package-lock.json` → `version` **and** `packages."".version`

Bump it in the same commit as the code. `auto-tag.yml` reads the version from
`pyproject.toml` after a push to main and creates `v<version>`; a bump that
arrives in a later commit produces no tag for the change.

`scripts/check_version_sync.py` verifies all three (plus the format) and runs as
a pre-commit hook, as a CI step, and again inside the tagging workflow. The npm
lockfile is the copy that lags, because it only updates on `npm install`.

## Dependencies

Python dependencies live in `pyproject.toml`; `uv.lock` is committed. Never edit
`uv.lock` by hand — `uv add`, `uv lock`, or `make lock-upgrade`.

```bash
uv add requests                 # runtime dependency
uv add --group dev pytest-mock  # development only
uv add --optional prod newrelic # production extra
```

The dev group installs by default with `uv sync`; `uv sync --no-dev` (what the
production image runs) leaves it out.

Node dependencies: `package.json` + `package-lock.json`, both committed.

## Gates

Three checks stand between a mistake and the main branch. Two are on by default.

| Gate | Where | Default |
|---|---|---|
| Format, lint, tests, missing migrations | pre-commit + CI | on |
| Version sync across the three files | pre-commit + CI + tagging | on |
| No AI authorship in commit messages | pre-commit (commit-msg) + CI | **off** |

### The AI-attribution gate

`scripts/check_no_ai_attribution.py` rejects authorship trailers and footers —
`Co-Authored-By: <assistant>`, "Generated with …", a vendor `noreply@` address, a
link to the assistant's product page.

It is **off by default**: whether AI attribution belongs in your history is your
call, not the template's. Turn it on by uncommenting the `no-ai-attribution` hook
in `.pre-commit-config.yaml` and the matching step in `.github/workflows/ci.yml`.

Why a script rather than a line in the contributing guide: coding agents are
routinely instructed by their own harness to append those trailers to every
commit. A written rule competes with that instruction and loses eventually.

What it deliberately does not flag: `CLAUDE.md`, `AGENTS.md`, `.claude/` paths, a
`docs(claude)` scope, or a model identifier in the subject of a commit that
integrates it. A gate that fails on ordinary messages gets bypassed with the
first `--no-verify`, and then it protects nothing. Its own tests
(`apps/core/tests/test_attribution_gate.py`) hold both halves of that line.

Two surfaces the gate cannot reach, if you enable it: the pull request body and
review comments, where a footer may be appended by the platform after creation.
Those stay a manual step.

## Documentation

Update docs in the same commit as the change:

| Changed | Update |
|---|---|
| Architecture, app boundaries, domain model | the matching file in `docs/` |
| Project structure, stack, setup steps | `README.md` |
| A convention | `CLAUDE.md` and this file |
| A decision or an edge case that cost time | `docs/agents.md` |

`apps/core/tests/test_docs_references.py` fails when a relative link in any
markdown file points at a path that does not exist, or when the docs mention a
`make` target the Makefile does not have. Renaming a file otherwise breaks the
map with no signal anywhere.
