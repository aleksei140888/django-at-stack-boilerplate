# ── uv ────────────────────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:0.9 AS uv

# ── Node / frontend build ─────────────────────────────────────────────────────
FROM node:22-slim AS frontend

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY vite.config.js ./
COPY static/src ./static/src
# Tailwind scans templates and apps for class names (@source in main.css) — build
# without them and the bundle comes out with no utilities at all.
COPY templates ./templates
COPY apps ./apps
RUN npm run build

# ── Python base ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /usr/local/bin/

# ── Development ───────────────────────────────────────────────────────────────
FROM base AS dev

# The dev dependency group is installed by default; --frozen fails loudly if
# uv.lock is out of date rather than quietly resolving something else.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen

COPY . .
COPY --from=frontend /app/static/dist ./static/dist

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ── Production ────────────────────────────────────────────────────────────────
FROM base AS prod

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --extra prod --no-dev

COPY . .
COPY --from=frontend /app/static/dist ./static/dist

# collectstatic loads the production settings, which read SECRET_KEY from the
# environment and would fail the build without one. This value never reaches a
# running container — it is overwritten by the real environment at runtime.
RUN SECRET_KEY=build-time-placeholder \
    python manage.py collectstatic --noinput --settings=config.settings.prod

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "60"]
