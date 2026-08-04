# Observability

Three questions this layer answers: is it up, what happened during one request,
and how much of it is happening.

## Request correlation

`RequestIDMiddleware` gives every request an id. An inbound `X-Request-ID` (from
nginx, a load balancer, a client) is reused when it is well formed; anything
malformed is replaced, because the id ends up in log lines and Sentry tags and an
unbounded value from a client is a log-injection vector.

The id is:

- bound to a contextvar, so every log record during the request carries it,
- tagged on the Sentry scope, which is what links a log line to an error,
- echoed back in the `X-Request-ID` response header.

In application code: `request.request_id`, or
`apps.core.observability.get_request_id()` anywhere below the view.

## Logging

Two formats, one switch:

```env
LOG_FORMAT=console   # human-readable lines, the default
LOG_FORMAT=json      # one JSON object per line; prod.py forces this
LOG_LEVEL=INFO       # applies to the `apps` logger; Django's stays at WARNING
```

JSON output carries `timestamp`, `level`, `logger`, `message`, `request_id`, the
formatted exception, and anything passed as `extra`:

```python
logger.info("user registered", extra={"user_id": user.pk})
```

Structured fields are the point — a log shipper can filter on `user_id` without
anyone writing a regex against a message string. Values that are not JSON
serialisable are stringified rather than raising: a logging call must never be
the thing that takes down a request.

## Health checks

`GET /api/v1/health/` returns the aggregate plus per-component detail, and
`/health/` renders the same data as a live dashboard.

```json
{
  "status": "ok",
  "version": "2026.8.0",
  "timestamp": "2026-08-04T12:00:00+00:00",
  "checks": {
    "database": {"status": "ok", "latency_ms": 3.1, "vendor": "postgresql"},
    "cache":    {"status": "ok", "latency_ms": 0.8},
    "storage":  {"status": "ok", "backend": "s3", "bucket": "assets"},
    "celery":   {"status": "degraded", "detail": "no active workers"}
  }
}
```

HTTP 200 for `ok` and `degraded`, **503 for `error`**.

That distinction is the whole design. `error` means "this instance cannot serve
requests" and will page somebody at 03:00; `degraded` means a component is
missing and functionality is reduced. Plenty of environments run the web tier
without Celery workers — a red health endpoint there teaches everyone to ignore
it.

`version` comes from `pyproject.toml`, so the endpoint identifies the deployed
build without an SSH session.

Adding a check: [`playbooks/add-health-check.md`](playbooks/add-health-check.md).

## Metrics

`GET /metrics` serves the Prometheus registry: request counts and latency
histograms labelled by method, view name and status.

Two conditions, or it returns **404** (not 403 — a 403 confirms the endpoint
exists):

1. `METRICS_TOKEN` is set, and the scraper sends it as `Authorization: Bearer …`
2. `prometheus_client` is installed — it lives in the `prod` extra

Without the package, `apps/core/metrics.py` degrades to no-ops, so the same code
runs in dev, test and CI. Nothing else in the project needs a conditional import.

Labels are bounded on purpose: the view name from the resolver, never the raw
path. Every distinct label value creates a time series, so a path label lets any
crawler blow up the registry.

## Sentry

Enabled when `SENTRY_DSN` is set, in `prod.py` only. The SDK is imported inside
that branch — a stripped image without the `prod` extra still boots. `release` is
set from the app version, so an error report names the build it came from.

`apps.core.observability` wraps the Sentry calls the project makes (`set_tags`,
`bind_request_id`, `set_sentry_user`); each is a no-op without the SDK, so call
sites stay free of `if sentry:` checks.

## During an incident

1. `/api/v1/health/` — which component, and is it `degraded` or `error`.
2. `version` in that payload — is the deployed build the one you think it is.
3. Filter logs by `request_id` from the failing response header — that gives the
   whole request in one query.
4. Sentry, filtered by the same `request_id` tag, for the traceback.
5. `/metrics` — whether it is one view or everything.
