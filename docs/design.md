# Design system

The visual language is specified in [`../DESIGN.md`](../DESIGN.md) — palette,
typography, motion, component rules, and the do/don't list. That file is the
source of truth; this one explains where each part of it lives in the code and
what to do when you change it.

**Cyber-Tribal**, dark only. Ancient geometry pushed through a digital filter:
hard grids under organic curves, neon on near-black, generous motion.

## Where it lives

| Concern | File |
|---|---|
| Palette, radii, fonts, motion tokens | `static/src/css/main.css` — the `@plugin "daisyui/theme"` and `@theme` blocks |
| Buttons, cards, form fields | the `@layer components` block in the same file |
| Glow, grid, gradient, cascade | the `@layer utilities` block |
| Fixed theme attribute | `templates/base.html` |
| Mechanical rules | `apps/core/tests/test_design.py` |

Templates use semantic classes (`bg-base-200`, `text-primary`, `.btn-tribal`) and
never raw hex. Retheming is one block of CSS, not a sweep through the markup.

## Palette

DaisyUI slots hold the six named colours; the two the framework has no slot for
stay as tokens.

| DESIGN.md | Token | Used for |
|---|---|---|
| Electric Cyan `#00FFFF` | `--color-primary` | links, focus rings, the primary button |
| Jungle Green `#29AB87` | `--color-secondary` / `--color-success` | secondary surfaces, healthy status |
| Blacklight Purple `#BF00FF` | `--color-accent` | decorative accents, glow |
| Deep Indigo `#4B0082` | `--color-neutral`, primary button text | emphasis surfaces |
| Solar Orange `#FF4500` | `--color-warning`, `--color-tribal-solar` | warnings, warm accent |
| Neon Magenta `#FF00FF` | `--color-tribal-magenta` | gradients, neon trails |

Values are stored as `oklch()` because DaisyUI mixes them with `color-mix()`;
each line keeps the original hex in a trailing comment so it stays greppable
against DESIGN.md, and a test asserts all six are still there.

Two deliberate departures from the palette list:

- **Errors are red (`#FF3366`), not Solar Orange.** The palette has no red, and
  an error that reads as a warm accent is an error nobody notices.
- **Surfaces are indigo-tinted near-black, not `#000000`.** Pure black kills the
  glow the whole system depends on, and the do/don't list rules out pure white on
  the other end.

## Typography

`Azonix` is the specified face for display, body and UI labels. It cannot be
redistributed here, so the stack is:

```css
--font-display: "Azonix", "Orbitron", ui-sans-serif, system-ui, sans-serif;
```

**Orbitron** ships self-hosted through `@fontsource/orbitron` (SIL OFL) and does
the same job — geometric, wide, of the same era. Drop Azonix in and it takes over
with no other change:

```css
/* static/src/css/main.css */
@font-face {
  font-family: "Azonix";
  src: url("../fonts/azonix.woff2") format("woff2");
  font-weight: 700;
  font-display: swap;
}
```

**JetBrains Mono** carries code, metadata and technical values, also self-hosted.

Self-hosted rather than loaded from a font CDN because the CSP allows
`font-src 'self'` — and a template whose typography depends on a third-party host
loses its typography the first time that host is blocked.

One judgement call worth knowing about: DESIGN.md specifies the display face for
body copy too, and that is what ships. A wide geometric face at 16px is heavy for
long paragraphs. If you want a neutral body face, change `--font-body` alone —
headings, labels and the display scale keep the design's character.

## Motion

- Entry: fade + 16px rise, 540ms, spring-ish easing. `.animate-enter`.
- Cascades: `.enter-cascade` staggers children 120ms apart, capped at 720ms —
  past that the last card arrives a second late and the page reads as slow.
- Hover: `scale(1.03)` plus a shadow lift over 200ms. `.hover-lift`.
- Only `transform` and `opacity` are animated. Nothing that triggers layout.
- `prefers-reduced-motion` collapses every duration to ~0.

The cascade runs on load, including for cards below the fold. That is why
`make demo-smoke` waits `ANIMATION_SETTLE_MS` before screenshotting — without it
every screenshot catches the later cards mid-fade and looks like a rendering bug.

## Components

Four surfaces are defined once in `@layer components` so a template says what a
thing *is* rather than repeating eight utilities:

| Class | Notes |
|---|---|
| `.btn-tribal` | Primary. Cyan fill, indigo text, 8% darken on hover, 1px press. **No glow** — DESIGN.md is explicit, and a glowing CTA on a page full of glows stops reading as the primary action |
| `.btn-tribal-ghost` | 1.5px outline, primary text, subtle fill on hover |
| `.card-tribal` | 8px radius, 1px stroke, translucent surface, soft shadow |
| `.field-label` / `.field-help` / `.field-error` | Label above, help and error below. No floating labels |

Inputs are styled by element selector, because Django renders widgets without CSS
classes. They are written as plain properties: `@apply` of a DaisyUI component
class inside `@layer base` resolves to an empty rule under Tailwind v4 + DaisyUI 5,
and the fields end up unstyled with nothing logged anywhere.

## Icons

Inline Lucide-style SVG, drawn in the markup. No emoji, no icon font, no request.
A test rejects emoji in any template — including `✓` and `📧`, which were doing an
icon's job in the confirmation pages.

## z-index

Use the named utilities, never an invented number: `z-sticky-nav` (100),
`z-overlay` (200), `z-modal` (300), `z-toast` (500).

## Dark only

`<html data-theme="cybertribal">` is fixed in `base.html` and there is no theme
switcher — DESIGN.md specifies no light mode. To add one:

1. Add a second `@plugin "daisyui/theme"` block with `default: true` and
   `color-scheme: light`.
2. Restore a `themeManager` Alpine component that writes `data-theme` and
   persists the choice, plus the inline pre-paint script in `<head>` that applies
   the saved value before Alpine boots (otherwise the first frame is wrong).
3. Drop the `test_no_light_theme_toggle_remains` guard in
   `apps/core/tests/test_design.py`.

## What the tests check

`apps/core/tests/test_design.py` covers only what a reviewer cannot reliably see:
no emoji, no `h-screen`/`min-h-screen`, no DaisyUI 4 class names that silently
stopped applying, the theme is declared and dark, the radius is 8px, reduced
motion is honoured, and every palette colour is still present.

Whether a layout is genuinely asymmetric, or a page reads as Cyber-Tribal at all,
is a judgement call and stays with the reviewer — plus `make demo-smoke`, which
fails on horizontal overflow at 360 and 390px and leaves screenshots in `var/`.

## Retheming for your own project

1. Replace the `@plugin "daisyui/theme"` block with your palette.
2. Replace `--font-display` / `--font-body` / `--font-mono`.
3. Adjust `--radius-*` and the motion tokens.
4. Regenerate `static/img/` (favicon, apple-touch-icon, og-default).
5. Update `<meta name="theme-color">` in `partials/_meta_seo.html`.
6. Replace `DESIGN.md` with your own spec, and update the guards in
   `test_design.py` that reference the old palette.

Templates should need no changes at all. If they do, a colour leaked into the
markup that belonged in a token.
