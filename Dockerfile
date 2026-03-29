FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ---- Node stage for frontend build ----
FROM node:22-slim AS frontend

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY vite.config.js ./
COPY static/src ./static/src

RUN npm run build

# ---- Python deps ----
FROM base AS python-deps

COPY requirements/base.txt ./requirements/base.txt
RUN pip install -r requirements/base.txt

# ---- Development ----
FROM python-deps AS dev

COPY requirements/dev.txt ./requirements/dev.txt
RUN pip install -r requirements/dev.txt

COPY . .
COPY --from=frontend /app/static/dist ./static/dist

EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ---- Production ----
FROM python-deps AS prod

COPY requirements/prod.txt ./requirements/prod.txt
RUN pip install -r requirements/prod.txt

COPY . .
COPY --from=frontend /app/static/dist ./static/dist

RUN python manage.py collectstatic --noinput --settings=config.settings.prod

EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "60"]
