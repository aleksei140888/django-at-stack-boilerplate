import json
import logging

from apps.core import observability


class TestRequestIDCoercion:
    def test_well_formed_id_is_kept(self):
        assert observability.coerce_request_id("req-42_a.b") == "req-42_a.b"

    def test_missing_id_is_generated(self):
        assert len(observability.coerce_request_id(None)) == 32

    def test_generated_ids_differ(self):
        assert observability.coerce_request_id(None) != observability.coerce_request_id(None)


class TestContextVar:
    def test_default_outside_a_request(self):
        assert observability.get_request_id() == observability.NO_REQUEST_ID

    def test_set_and_reset(self):
        token = observability.set_request_id("abc")
        assert observability.get_request_id() == "abc"
        observability.reset_request_id(token)
        assert observability.get_request_id() == observability.NO_REQUEST_ID


def make_record(**extra) -> logging.LogRecord:
    record = logging.LogRecord(
        name="apps.example",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="user %s registered",
        args=("42",),
        exc_info=None,
    )
    for key, value in extra.items():
        setattr(record, key, value)
    return record


class TestJSONFormatter:
    def test_renders_a_single_json_object(self):
        payload = json.loads(observability.JSONFormatter().format(make_record()))

        assert payload["level"] == "INFO"
        assert payload["logger"] == "apps.example"
        assert payload["message"] == "user 42 registered"
        assert payload["timestamp"]

    def test_extra_fields_are_passed_through(self):
        payload = json.loads(observability.JSONFormatter().format(make_record(user_id=7)))
        assert payload["user_id"] == 7

    def test_request_id_is_included_when_set(self):
        record = make_record(request_id="abc123")
        assert json.loads(observability.JSONFormatter().format(record))["request_id"] == "abc123"

    def test_placeholder_request_id_is_omitted(self):
        record = make_record(request_id=observability.NO_REQUEST_ID)
        assert "request_id" not in json.loads(observability.JSONFormatter().format(record))

    def test_exception_is_serialised(self):
        try:
            raise ValueError("boom")
        except ValueError:
            import sys

            record = make_record()
            record.exc_info = sys.exc_info()

        payload = json.loads(observability.JSONFormatter().format(record))
        assert "ValueError: boom" in payload["exception"]

    # json.dumps would raise on a non-serialisable extra, and a logging call must
    # never be the thing that takes down a request.
    def test_unserialisable_extra_does_not_raise(self):
        payload = json.loads(observability.JSONFormatter().format(make_record(obj=object())))
        assert "object object" in payload["obj"]


class TestRequestIDFilter:
    def test_attaches_the_current_id(self):
        token = observability.set_request_id("xyz")
        try:
            record = make_record()
            assert observability.RequestIDFilter().filter(record) is True
            assert record.request_id == "xyz"
        finally:
            observability.reset_request_id(token)


class TestSentryNoOps:
    """Sentry lives in the prod extra; every wrapper must be safe without it."""

    def test_helpers_are_silent_when_sentry_is_absent(self, monkeypatch):
        monkeypatch.setattr(observability, "sentry_sdk", None)

        observability.set_tags(env="test")
        observability.bind_request_id("abc")
        observability.set_sentry_user("1", "user@example.com")
