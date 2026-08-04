#!/bin/bash
# SessionStart hook — prepares a cloud coding-agent session: dependencies plus a
# demo database with data, so the first thing an agent can do is run the app.
#
# Idempotent: a second run redoes nothing (uv sync compares against uv.lock, the
# demo database is only created when it is missing).
set -euo pipefail

# Local runs are left alone — the developer owns their own environment.
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-$(pwd)}"

export PATH="$HOME/.local/bin:$PATH"

# 1. Python dependencies (uv fetches the interpreter it needs).
uv sync

# 2. Frontend bundle. Without it every page renders unstyled, which reads as a
#    broken app rather than a missing build step.
if [ ! -f static/dist/main.js ]; then
  npm install --no-audit --no-fund
  npm run build
fi

# 3. Demo environment: SQLite with seeded data, no Docker, Redis or API keys.
DEMO_DB="${DEMO_DB_PATH:-db.demo.sqlite3}"
if [ ! -f "$DEMO_DB" ]; then
  uv run python manage.py migrate --settings=config.settings.demo --noinput
  uv run python manage.py seed_demo --settings=config.settings.demo --profile=small --quiet
fi

# 4. PATH for the rest of the session. DJANGO_SETTINGS_MODULE is deliberately NOT
#    exported: in pytest-django an environment variable beats the value in
#    pyproject.toml, and `make test` would quietly run against the demo database
#    instead of config.settings.test. Settings are passed per command instead.
echo 'export PATH="$HOME/.local/bin:$PATH"' >> "${CLAUDE_ENV_FILE:-/dev/null}"

echo "Ready: make demo-run (site), make test (tests), demo login user@demo.local / demo12345"
