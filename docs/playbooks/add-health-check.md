# Playbook: add a health check

For a dependency whose absence should be visible: a payment provider, a search
cluster, a third-party API the app cannot work without.

## 1. Write it

Anywhere in the codebase, in a module that is imported at startup —
`apps.py`'s `ready()` is the usual place, and `apps/core/health.py` itself for
infrastructure-level checks.

```python
from apps.core.health import HealthCheck


@HealthCheck.register("stripe")
def check_stripe():
    import stripe
    from django.conf import settings

    stripe.api_key = settings.STRIPE_SECRET_KEY
    stripe.Balance.retrieve()          # raises on failure
    return {"status": "ok"}
```

Return a dict with at least `status`. Extra keys pass straight through to the API
response and the dashboard, so include what you would want during an incident:

```python
return {"status": "ok", "version": index_version, "documents": count}
```

Raising is fine — the registry turns any exception into
`{"status": "error", "error": "<message>"}` and records the latency anyway.

## 2. Pick the right severity

This is the only decision that matters here.

| Status | Meaning | HTTP | Consequence |
|---|---|---|---|
| `ok` | working | 200 | — |
| `degraded` | missing, functionality reduced | 200 | visible on the dashboard |
| `error` | the app cannot serve requests | **503** | the monitor pages somebody |

Reserve `error` for things that genuinely break the site. A background worker
that is not running in this environment is `degraded` — the built-in Celery check
does exactly that, because a health endpoint that is red by design gets ignored,
and then it is red for a real reason and still gets ignored.

## 3. Keep it fast and safe

- **Set a timeout on every network call.** The endpoint is polled; a check
  without a timeout turns a slow dependency into a slow health endpoint into a
  monitor that reports the wrong thing.
- **Read, do not write.** `head_bucket`, `SELECT 1`, a ping — never a check that
  creates records.
- **No secrets in the payload.** It is served to whoever can reach the URL.
- **Short-circuit where a check makes no sense.** The Celery check returns early
  under `CELERY_TASK_ALWAYS_EAGER` instead of burning a socket timeout per
  request in tests and the demo environment.

## 4. Test it

```python
def test_stripe_check_reports_error_when_the_api_is_down(monkeypatch):
    ...
```

`apps/core/tests/test_health.py` has the fixtures: `temporary_check` registers
one for a single test, `only_temporary_checks` also removes the built-ins so an
aggregation test does not depend on whether this machine has a database.

Un-register in teardown, or the check leaks into every later test on the same
xdist worker.

## 5. Verify

```bash
curl -s localhost:8000/api/v1/health/ | jq
```

Your check appears in `checks`, and `/health/` shows a card for it with no
template change — the dashboard renders whatever the registry returns.
