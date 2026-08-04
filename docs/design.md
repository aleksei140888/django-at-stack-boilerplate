# Design system

The visual language is specified in [`../DESIGN.md`](../DESIGN.md) — palette,
typography, motion, component rules, and the do/don't list. That file is the
source of truth; this one explains where each part of it lives in the code and
what to do when you change it.

**Cyber-Tribal**, dark by default with a light companion. Ancient geometry pushed
through a digital filter:
hard grids under organic curves, neon on near-black, generous motion.

## Where it lives

| Concern | File |
|---|---|
| Palette, radii, fonts, motion tokens | `static/src/css/main.css` — the `@plugin "daisyui/theme"` and `@theme` blocks |
| Buttons, cards, form fields | the `@layer components` block in the same file |
| Glow, grid, gradient, cascade | the `@layer utilities` block |
| Theme resolution before first paint | `templates/base.html` (inline script) |
| Theme switcher | `themeManager` in `static/src/js/main.js`, button in `partials/_navbar.html` |
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

## Two themes

DESIGN.md specifies dark only. The template ships a light companion anyway,
because a boilerplate that cannot follow a user's OS preference is a boilerplate
people patch on day one. **Dark stays the design**: it is the default, it is what
the palette was drawn for, and light is derived from it rather than the reverse.

| Theme | When |
|---|---|
| `cybertribal` | default; used when no choice is stored and the OS expresses no preference |
| `cybertribal-light` | stored choice, or `prefers-color-scheme: light` |

Resolution order is the same in two places — `themeManager` in `main.js` and an
inline script in `<head>`. The duplication is deliberate: Alpine boots after
first paint, so without the inline copy the page renders once in the wrong theme
and visibly corrects itself. A guard asserts the inline script comes before the
bundle.

`themeManager` also rewrites `<meta name="theme-color">`, which cannot follow
`data-theme` from CSS.

### What the light theme drops

Every colour keeps its hue and loses lightness until it clears 4.5:1 on the
off-white base — `#00FFFF` on `#F5F2FA` is 1.2:1, which is not a colour, it is a
suggestion of one. Electric Cyan becomes `#007A8C`, Blacklight Purple `#8A00BA`,
Neon Magenta `#B8009E`, and Deep Indigo is unchanged because it was already the
darkest of the six.

The glows come off entirely rather than being dimmed, because a glow needs
darkness to read as light — on pale surfaces the same effect is grey haze:

- the blacklight wash behind `<body>` → nothing
- `.glow-primary` / `.glow-accent` → a hairline border plus a soft neutral shadow
- `.text-glow` → no text shadow
- `.hover-lift` → a plain shadow instead of a coloured halo

What stays is the structure: the tribal grid (geometry, not light, redrawn in
dark ink at 6%), the radii, the type, the motion, the asymmetric layouts.

Surfaces are off-white with a violet cast, never `#FFFFFF` — DESIGN.md's do-not
list, and a guard checks it.

To go back to dark-only: delete the light `@plugin` block and its
`[data-theme="cybertribal-light"]` overrides, remove the toggle from the navbar,
and fix up the theme tests in `apps/core/tests/test_design.py`.

## What the tests check

`apps/core/tests/test_design.py` covers only what a reviewer cannot reliably see:
no emoji, no `h-screen`/`min-h-screen`, no DaisyUI 4 class names that silently
stopped applying, both themes declared with dark as the default, the light theme
free of glows and of pure white, the radius 8px, reduced motion honoured, every
palette colour present, and the switcher wired up before first paint.

Whether a layout is genuinely asymmetric, or a page reads as Cyber-Tribal at all,
is a judgement call and stays with the reviewer — plus `make demo-smoke`, which
fails on horizontal overflow at 360 and 390px and leaves screenshots in `var/`.

## Retheming for your own project

1. Replace the `@plugin "daisyui/theme"` block with your palette.
2. Replace `--font-display` / `--font-body` / `--font-mono`.
3. Adjust `--radius-*` and the motion tokens.
4. Regenerate `static/img/` (favicon, apple-touch-icon, og-default).
5. Update `<meta name="theme-color">` in `partials/_meta_seo.html` and the
   `THEME_COLORS` map in `main.js`.
6. Replace `DESIGN.md` with your own spec, and update the guards in
   `test_design.py` that reference the old palette.

Templates should need no changes at all. If they do, a colour leaked into the
markup that belonged in a token.
