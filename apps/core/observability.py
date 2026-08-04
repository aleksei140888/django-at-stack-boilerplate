"""
Observability primitives shared across the project.

Three concerns, none of them requiring an optional dependency to be installed:

* **Request correlation** — a contextvar holds the current request id so any log
  line emitted while handling a request can be tied back to it (and to the
  ``X-Request-ID`` response header / Sentry tag).
* **Structured logging** — :class:`JSONFormatter` emits one JSON object per log
  record (including ``request_id`` and any ``extra={...}`` fields), which makes
  shipped logs filterable by field instead of grep-on-strings.
* **Sentry enrichment** — thin wrappers that no-op when ``sentry_sdk`` is not
  installed (it lives in the ``prod`` extra), so call sites stay clean.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:  # Sentry lives in the `prod` extra — degrade gracefully without it.
    import sentry_sdk
except ImportError:  # pragma: no cover - exercised via the no-op tests
    sentry_sdk = None

# ── Request correlation ───────────────────────────────────────────────────────

NO_REQUEST_ID = "-"
_request_id: ContextVar[str] = ContextVar("request_id", default=NO_REQUEST_ID)

# Accept inbound ids but bound their shape — prevents log injection and huge values.
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def get_request_id() -> str:
    """Current request id, or ``"-"`` outside a request."""
    return _request_id.get()


def set_request_id(request_id: str):
    """Bind *request_id* to the current context; returns a reset token."""
    return _request_id.set(request_id)


def reset_request_id(token) -> None:
    """Restore the previous request id using the token from :func:`set_request_id`."""
    _request_id.reset(token)


def coerce_request_id(value: str | None) -> str:
    """Return *value* if it is a safe id, otherwise mint a fresh one."""
    if value and _REQUEST_ID_RE.match(value):
        return value
    return uuid.uuid4().hex


# ── Structured logging ────────────────────────────────────────────────────────

# Standard LogRecord attributes — everything else on a record is a user `extra`.
# request_id is rendered explicitly, so it is excluded from the pass-through.
_STANDARD_ATTRS = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {
    "message",
    "asctime",
    "taskName",
    "request_id",
}


class RequestIDFilter(logging.Filter):
    """Attach the current ``request_id`` to every record (for the formatter)."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True


class JSONFormatter(logging.Formatter):
    """Render a log record as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = getattr(record, "request_id", NO_REQUEST_ID)
        if request_id and request_id != NO_REQUEST_ID:
            payload["request_id"] = request_id

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        # Pass through any structured `extra={...}` fields.
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and key not in payload and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, ensure_ascii=False, default=str)


# ── Sentry enrichment (safe no-ops without sentry_sdk) ────────────────────────


def set_tags(**tags) -> None:
    """Set Sentry tags, skipping ``None`` values. No-op when Sentry is absent."""
    if sentry_sdk is None:
        return
    for key, value in tags.items():
        if value is not None:
            sentry_sdk.set_tag(key, value)


def bind_request_id(request_id: str) -> None:
    """Tag the active Sentry scope with the request id for log↔error correlation."""
    set_tags(request_id=request_id)


def set_sentry_user(user_id: str, email: str | None = None) -> None:
    """Identify the user on the active Sentry scope. No-op when Sentry is absent."""
    if sentry_sdk is None:
        return
    payload: dict = {"id": user_id}
    if email:
        payload["email"] = email
    sentry_sdk.set_user(payload)
