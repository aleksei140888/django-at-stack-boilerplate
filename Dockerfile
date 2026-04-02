# ── uv ────────────────────────────────────────────────────────────────────────
FROM ghcr.io/astral-sh/uv:0.5 AS uv

# ── Node / frontend build ─────────────────────────────────────────────────────
FROM node:22-slim AS frontend

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY vite.config.js ./
COPY static/src ./static/src
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

# Install deps with dev extras (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --extra dev

COPY . .
COPY --from=frontend /app/static/dist ./static/dist

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ── Production ────────────────────────────────────────────────────────────────
FROM base AS prod

# Install deps with prod extras only (no dev tools)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    uv sync --frozen --extra prod --no-dev

COPY . .
COPY --from=frontend /app/static/dist ./static/dist

RUN python manage.py collectstatic --noinput --settings=config.settings.prod

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "60"]
