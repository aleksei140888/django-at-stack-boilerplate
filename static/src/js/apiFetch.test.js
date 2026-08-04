import assert from "node:assert/strict";
import test from "node:test";

import { apiFetch } from "./apiFetch.js";

function withCookieAndFetch(cookie, fetchImpl, run) {
  const originalDocument = globalThis.document;
  const originalFetch = globalThis.fetch;
  globalThis.document = { cookie };
  globalThis.fetch = fetchImpl;
  return run().finally(() => {
    globalThis.document = originalDocument;
    globalThis.fetch = originalFetch;
  });
}

function okJsonResponse(body = {}) {
  return { ok: true, json: async () => body };
}

test("attaches CSRF token header by default", async () => {
  let seenHeaders;
  await withCookieAndFetch(
    "csrftoken=abc123",
    async (_url, options) => {
      seenHeaders = options.headers;
      return okJsonResponse({ ok: true });
    },
    () => apiFetch("/x/"),
  );

  assert.equal(seenHeaders["X-CSRFToken"], "abc123");
});

// Regression: a caller passing its own `headers` (e.g. to override Content-Type
// for a form-encoded body) used to wipe out the CSRF header entirely — headers
// were merged into a `defaults` object, and then `options` was spread over it at
// the top level, putting the caller's raw headers back on top.
test("keeps CSRF token when caller overrides Content-Type", async () => {
  let seenHeaders;
  await withCookieAndFetch(
    "csrftoken=abc123",
    async (_url, options) => {
      seenHeaders = options.headers;
      return okJsonResponse({ ok: true });
    },
    () =>
      apiFetch("/x/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: "id=1",
      }),
  );

  assert.equal(seenHeaders["X-CSRFToken"], "abc123");
  assert.equal(seenHeaders["Content-Type"], "application/x-www-form-urlencoded");
});

// File uploads go as FormData: forcing a JSON content type breaks the multipart
// boundary and Django receives empty request.POST / request.FILES.
test("does not force JSON content type for FormData body", async () => {
  let seenHeaders;
  const body = new FormData();
  body.append("title", "Example");

  await withCookieAndFetch(
    "csrftoken=abc123",
    async (_url, options) => {
      seenHeaders = options.headers;
      return okJsonResponse({ ok: true });
    },
    () => apiFetch("/x/", { method: "POST", body }),
  );

  assert.equal(seenHeaders["Content-Type"], undefined);
  assert.equal(seenHeaders["X-CSRFToken"], "abc123");
});

test("throws with status and parsed body on non-ok response", async () => {
  await withCookieAndFetch(
    "csrftoken=abc123",
    async () => ({
      ok: false,
      status: 403,
      json: async () => ({ detail: "Forbidden" }),
    }),
    async () => {
      await assert.rejects(
        () => apiFetch("/x/"),
        (err) => {
          assert.equal(err.message, "Forbidden");
          assert.equal(err.status, 403);
          return true;
        },
      );
    },
  );
});
