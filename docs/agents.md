# Project memory

Decisions, edge cases and traps worth remembering between sessions. Not a work
log: routine changes that follow the existing conventions do not go here.

**Read selectively.** Find your area in the index, open only those sections. This
file grows monotonically and reading it end to end is rarely the right move.

**When you add a `##` section, add a line to the index.** An index that lies is
worse than no index.

How and when to write here: [`../.claude/skills/memory/SKILL.md`](../.claude/skills/memory/SKILL.md).

---

## Index

**Design system**
- "Vite `base` has to match where Django serves the bundle" → every font 404s and
  the typography silently falls back
- "DaisyUI 5 removed `form-control`, `label-text`, `input-bordered`" → no error,
  the element just loses its styling

**Frontend / templates / CSS**
- "Multi-line `{# #}` comments leak into the page" → Django's short comment form
  is single-line only
- "Tailwind v4 scans the CSS file's own directory" → `@source` is load-bearing;
  without it the bundle has no utilities at all
- "The entry has to import the stylesheet" → otherwise the build emits no CSS and
  templates ask for a file that was never produced
- "DaisyUI 5: `.label` does not wrap, `@apply` of component classes is empty" →
  what to use instead
- "`x-cloak` on everything visible by default" → and why `x-init="init()"` is a
  double init

**Settings / infrastructure**
- "Django 5.1 removed `STATICFILES_STORAGE` — silently" → the setting is ignored,
  not rejected
- "`STATICFILES_DIRS` with prefixes" → keeping the Vite source tree out of
  `STATIC_ROOT`
- "`VITE_DEV_SERVER` is separate from `DEBUG`" → a DEBUG environment without the
  dev server running renders unstyled HTML

**Auth / security**
- "`login()` needs an explicit backend when allauth is installed"
- "`?next=` is an open redirect until it is validated"

**Testing**
- "Process state that leaks between tests on one xdist worker"
- "black: `force-exclude`, not `extend-exclude`, for pre-commit"

**Incidental observations** (below) — one-liners, no structure required

---

## Incidental observations

Things noticed in passing. Add a line the moment you see one; do not wait for a
better occasion.

- `pytest-django`'s `django_assert_num_queries(0)` counts savepoints, so a
  function wrapped in `@transaction.atomic` never reaches zero. Assert on the
  absence of an `UPDATE` in `CaptureQueriesContext` instead.
- `pre-commit autoupdate` will happily move a hook to a pre-release (it offered
  isort `9.0.0b1`). Check what it wrote before committing.
- Django's password `help_text` is an HTML `<ul>`, not a sentence. Any container
  that does not wrap will overflow because of it.
- `<input type="file">` has an intrinsic width wider than a 360px viewport and is
  the one widget easy to miss when styling form fields by element selector.
- Staggered entry animations make any screenshot taken on `load` look broken —
  the later items are still mid-fade. `make demo-smoke` waits them out.

---

## Multi-line `{# #}` comments leak into the page (2026-08)

**Context.** Comments were added to `base.html`, `_vite_assets.html` and
`_meta_seo.html` explaining non-obvious markup. The rendered page then showed the
comment text as body copy, and one page failed with
`'include' tag takes at least one argument`.

**Decision.** Multi-line explanations use `{% comment %}…{% endcomment %}`.
`{# … #}` is for one line only.

**Reason.** Django's short comment form is line-scoped: an unterminated `{#` does
not comment out the following lines, it emits them as text, and the template tag
that follows can be consumed as part of the leaked run. Nothing warns — the page
renders, it just contains the comment.

```django
{# this is fine #}

{# this leaks
   into the page #}
```

---

## Tailwind v4 scans the CSS file's own directory (2026-08)

**Context.** After the DaisyUI 5 migration, the site rendered as unstyled HTML.
`dist/main.css` was built, was served with HTTP 200, and contained the theme
variables and the base layer — but not a single utility class.

**Decision.** `main.css` declares its sources explicitly:

```css
@source "../../../templates";
@source "../../../apps";
@source "../js";
```

**Reason.** Tailwind v4 dropped the `content` array from a config file and scans
automatically — relative to the CSS file. Here that is `static/src/`, the Vite
root, which contains no templates. Every class name lives in `templates/`, so the
scan found nothing and generated nothing, without an error anywhere. A new
template directory outside those paths needs a line here or its classes silently
vanish from the bundle.

The Docker frontend stage copies `templates/` and `apps/` for the same reason.

---

## The entry has to import the stylesheet (2026-08)

**Context.** `_vite_assets.html` linked `dist/main.css`, and the build never
produced it.

**Decision.** `main.js` starts with `import "../css/main.css";`.

**Reason.** Vite builds a module graph from the entry points. `main.css` was in
the source tree but nothing imported it, so it was not part of any graph and was
never emitted. The template asked for a file that had never existed — a 404 in
the console, and no CSS.

---

## DaisyUI 5: `.label` does not wrap, `@apply` of components is empty (2026-08)

**Context.** After the upgrade from DaisyUI 4, the registration page scrolled
sideways at 360px, and form inputs lost their styling.

**Decision.**

- Help text and errors are plain `<div>`s, not `<label class="label">`.
- A consent checkbox with a sentence next to it uses `flex`, not `label`.
- Base input styling is written as plain CSS properties using DaisyUI's
  `--color-*` variables, not `@apply input`.

**Reason.** DaisyUI 5 sets `white-space: nowrap` on `.label`, so anything longer
than a word refuses to wrap — and Django's password `help_text` is a `<ul>` of
rules. Separately, `@apply` of a DaisyUI component class inside `@layer base`
resolves to an empty rule under Tailwind v4, because the component lives in its
own nested layer: the inputs come out unstyled with nothing logged.

DaisyUI 5 also renamed the CSS variables — `oklch(var(--p))` from v4 is now
`var(--color-primary)`, and the old form silently produces an invalid colour.

---

## `x-cloak` on everything visible by default (2026-08)

**Context.** The cookie banner, flash messages and (while the theme switcher
still existed) both theme icons were visible for a frame before Alpine
initialised.

**Decision.** Every element that is visible by default and hidden by `x-show`
carries `x-cloak`; `[x-cloak] { display: none !important }` lives in `main.css`.

The same class of problem applies to anything decided in JS before first paint. It
is why the theme switcher, while it existed, needed an inline script in `<head>`
to apply the stored value — worth remembering if a second theme is ever added
back (docs/design.md).

**Reason.** `x-show` only takes effect after Alpine boots. Until then the browser
renders the element as written, which is a visible flash and a layout shift.

Related, found in the same pass: `x-data="healthDashboard()" x-init="init()"`
runs `init()` **twice** — Alpine already calls a component's own `init()`. The
dashboard was starting two polling intervals on every page load.

---

## Django 5.1 removed `STATICFILES_STORAGE` — silently (2026-08)

**Context.** The template still set `STATICFILES_STORAGE =
"whitenoise.storage.CompressedManifestStaticFilesStorage"`.

**Decision.** The `STORAGES` dict, with `staticfiles` as a key.

**Reason.** The old setting is not rejected, it is ignored. The project appeared
to have hashed, compressed static files in production and in fact had neither —
plain filenames with far-future cache headers, which is the worst combination
available.

---

## `STATICFILES_DIRS` with prefixes (2026-08)

**Decision.**

```python
STATICFILES_DIRS = [
    ("dist", BASE_DIR / "static" / "dist"),
    ("img", BASE_DIR / "static" / "img"),
]
```

**Reason.** Listing `static/` whole pulls `static/src/` — the Vite build root —
into `STATIC_ROOT`. `ManifestStaticFilesStorage` then walks the collected CSS
looking for referenced assets and fails on `@import "tailwindcss"`, which is not
a file it can resolve. The failure appears at deploy time, during collectstatic.

---

## `VITE_DEV_SERVER` is separate from `DEBUG` (2026-08)

**Context.** Asset loading was branched on `DEBUG`, so any DEBUG environment
without `npm run dev` running rendered with no CSS or JS — including the demo
environment, whose whole purpose is to be a working site in one command.

**Decision.** A dedicated `VITE_DEV_SERVER` setting: `dev.py` turns it on,
`demo.py` and `test.py` leave it off and use the built bundle.

---

## `login()` needs an explicit backend when allauth is installed (2026-08)

**Context.** Registration raised `ValueError: You have multiple authentication
backends configured…`.

**Decision.**

```python
login(request, user, backend="django.contrib.auth.backends.ModelBackend")
```

**Reason.** `login()` can infer the backend only for a user that came out of
`authenticate()`. A freshly created user has no `backend` attribute, and with
both `ModelBackend` and allauth's backend installed Django refuses to guess.

---

## `?next=` is an open redirect until it is validated (2026-08)

**Context.** Login and registration ended with
`redirect(request.GET.get("next", "/"))`.

**Decision.** `_safe_next()` in `apps/accounts/views.py`, built on
`url_has_allowed_host_and_scheme`, with regression tests for an absolute URL and
a protocol-relative `//evil.example`.

**Reason.** The query string is attacker-controlled. Unvalidated, every auth page
becomes a redirector on a trusted domain — the exact shape phishing links use.

---

## Process state that leaks between tests on one xdist worker (2026-08)

**Decision.** Two autouse fixtures in the root `conftest.py`: `deactivate_all()`
for translations, and `cache.clear()` for the local-memory cache. Registries get
their own reset fixture next to the tests that use them.

**Reason.** With `--dist=loadscope`, every test in a module shares a worker
process. `LocaleMiddleware` activates a language per request and never
deactivates it, and `LocMemCache` is per-process — so one test's language or
cached value silently changes the behaviour of a later, unrelated test. The
failures that result do not reproduce when the test is run on its own.

---

## black: `force-exclude`, not `extend-exclude`, for pre-commit (2026-08)

**Context.** `make beautify` left migrations alone; the pre-commit hook
reformatted them. The same files kept coming back dirty.

**Decision.** `[tool.black] force-exclude` with the same pattern.

**Reason.** `extend-exclude` applies only to paths black discovered by walking a
directory. pre-commit passes filenames explicitly, and those bypass it —
`force-exclude` is the flag that applies to explicit paths too.


---

## Vite `base` has to match where Django serves the bundle (2026-08)

**Context.** Self-hosted fonts were added through `@fontsource`. The build emitted
the woff2 files correctly and Django served them correctly, but every page logged
three 404s and rendered in the fallback font.

**Decision.**

```js
base: command === "build" ? "/static/dist/" : "/",
```

**Reason.** Vite writes asset URLs inside the built CSS relative to `base`, which
defaults to `/`. The `@font-face` rules therefore pointed at `/assets/font.woff2`
while the bundle is served from `/static/dist/`. Nothing fails loudly: the CSS
parses, the page renders, and the browser quietly falls back to the next font in
the stack. The dev server keeps `/` because it serves the same files from its own
root.

The same trap applies to any `url()` in the CSS — background images, masks,
cursors — not just fonts.

---

## DaisyUI 5 removed `form-control`, `label-text`, `input-bordered` (2026-08)

**Context.** After the DaisyUI 4 → 5 upgrade, form fields and help text lost their
layout on every auth page.

**Decision.** Project component classes (`.field-label`, `.field-help`,
`.field-error`, `.btn-tribal`, `.card-tribal`) defined once in
`@layer components`, and a test rejecting the removed class names in any template.

**Reason.** Removed utility classes do not error — they stop matching, and the
element keeps rendering with whatever is left. There is no console warning and no
build failure; the only signal is a screenshot that looks slightly wrong. Owning
the handful of component classes the design actually needs also means a retheme
touches one CSS block instead of every template.
