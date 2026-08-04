/**
 * fetch() wrapper that carries the CSRF token.
 *
 * It lives in its own module (rather than inside main.js) so it can be unit
 * tested with `node --test` — no bundler, no jsdom.
 */

export function getCsrfToken() {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="))
    ?.split("=")[1];
}

export async function apiFetch(url, options = {}) {
  const headers = {
    // FormData sets its own multipart Content-Type including the boundary —
    // overriding it produces a request the server cannot parse.
    ...(options.body instanceof FormData
      ? {}
      : { "Content-Type": "application/json" }),
    "X-CSRFToken": getCsrfToken(),
    ...options.headers,
  };

  // `headers` goes last on purpose. Spreading `options` after an object that
  // already contains merged headers puts the caller's raw `options.headers`
  // back on top, dropping the CSRF token — every POST from a component that
  // passes its own headers then fails with 403.
  const response = await fetch(url, {
    credentials: "same-origin",
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw Object.assign(new Error(error.detail || "Request failed"), {
      status: response.status,
      data: error,
    });
  }
  return response.json();
}
