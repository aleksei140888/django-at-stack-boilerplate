---
version: "alpha"
name: "Cyber-Tribal"
description: "Cyber-tribal landing page. Ideal for landing pages, saas. AI-ready template."
colors:
  primary: "#00FFFF"
  secondary: "#29AB87"
  tertiary: "#FF00FF"
  neutral: "#4B0082"
  surface: "#FF4500"
  accent: "#BF00FF"
typography:
  h1:
    fontFamily: Azonix
    fontSize: 2.5rem
    fontWeight: 700
  body-md:
    fontFamily: Azonix
    fontSize: 1rem
    fontWeight: 400
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.neutral}"
    padding: 12px
---

## Overview

Cyber-tribal landing page. Ideal for landing pages, saas. AI-ready template. Cyber-Tribal didn't start in a design studio. It crawled out of warehouse raves in the early '90s — body paint meeting laser grids, Maori-inspired tattoos glowing under UV. The aesthetic lives in that collision: ancient geometry forced through a digital filter. Psytrance flyers, Burning Man installations, early Wipeout game art. It was never polite about its references.

The tension is real and unresolved. Tribal patterns carry centuries of meaning — lineage, spirituality, belonging. Slapping them on a neon grid flattens that. The best Cyber-Tribal work acknowledges the source without pretending to own it. The worst treats indigenous culture as texture. There's no clean answer here, only degrees of care.

What persists is the formal power of the combination. Organic curves against hard-edged tech. Symmetry that feels biological rather than mechanical. The style endures because it taps something older than screens — pattern recognition wired into us — then electrifies it. That's not appropriation alone. That's resonance, handled well or badly depending on who's drawing.

- Density: 5/10 — Balanced
- Variance: 8/10 — Expressive
- Motion: 8/10 — Cinematic

- **Style:** Futuristic, Primal, Visionary
- **Keywords:** cyber-tribal, futuristic, primal, visionary, psychedelic, geometric patterns, neon, organic tech, glowing, immersive
- **Era:** Future-Primitivism
- **Light/Dark:** ✗ No / ✓ Full

## Colors

- **Electric Cyan** (#00FFFF) — Accent highlight, links and focus states
- **Jungle Green** (#29AB87) — Secondary surface or text color
- **Neon Magenta** (#FF00FF) — Decorative accent, highlight elements
- **Deep Indigo** (#4B0082) — Accent color, emphasis elements
- **Solar Orange** (#FF4500) — Warm accent, call-to-action secondary
- **Blacklight Purple** (#BF00FF) — Deep contrast surface
- **White** (#FFFFFF) — Secondary surface
- **Black** (#000000) — Deep contrast surface


## Typography

- **Display / Hero:** Azonix — Weight 700, tight tracking, used for headline impact
- **Body:** Azonix — Weight 400, 16px/1.6 line-height, max 72ch per line
- **UI Labels / Captions:** Azonix — 0.875rem, weight 500, slight letter-spacing
- **Monospace:** JetBrains Mono — Used for code, metadata, and technical values

Scale:
- Hero: clamp(2.5rem, 5vw, 4rem)
- H1: 2.25rem
- H2: 1.5rem
- Body: 1rem / 1.6
- Small: 0.875rem


## Layout

- **Grid:** CSS Grid primary. Max-width containment: 1280px centered with 1.5rem side padding.
- **Spacing rhythm:** Balanced. Base unit: 0.5rem (8px).
- **Section vertical gaps:** clamp(4rem, 8vw, 8rem).
- **Hero layout:** Asymmetric composition.
- **Feature sections:** Asymmetric grid with varied card sizes. No 3-equal-columns.
- **Mobile collapse:** All multi-column layouts collapse below 768px. No horizontal overflow.
- **z-index contract:** base (0) / sticky-nav (100) / overlay (200) / modal (300) / toast (500).


## Elevation & Depth

Glowing geometric patterns, psychedelic animations, organic tech interfaces, tribal masks with a cyber twist, neon light trails, immersive 3D environments, holographic elements, pulsating rhythms

- **Physics:** Spring — stiffness 120, damping 20. Confident, weighted transitions.
- **Entry animations:** Fade + translate-Y (16px → 0) over 540ms ease-out. Staggered cascades for lists: 120ms between items.
- **Hover states:** Scale(1.03) + shadow lift over 200ms.
- **Page transitions:** Fade + slide (300ms).
- **Performance:** Only transform and opacity animated. No layout-triggering properties.


## Shapes

Base corner radius: 8px. See rounded tokens in front matter for the full scale.


## Components

- **Primary Button:** Subtly rounded (0.5rem) shape. Accent color fill. Hover: 8% darken + subtle lift shadow. Active: -1px translate tactile press. Font weight 600. No outer glows.
- **Secondary / Ghost Button:** Outline variant. 1.5px border in muted color. Text in primary color. Hover: subtle background fill.
- **Cards:** Subtly rounded (0.5rem) corners. Surface background. Subtle shadow (0 2px 12px rgba(0,0,0,0.06)). 1px border stroke.
- **Inputs:** Label above input. 1px border stroke. Focus ring: 2px accent color offset 2px. Error text below in semantic red. No floating labels.
- **Navigation:** Primary surface background. Active item: accent color indicator. Font weight 500 when active.
- **Skeletons:** Shimmer animation matching component dimensions. No circular spinners.
- **Empty States:** Icon-based composition with descriptive text and action button.


## Do's and Don'ts

- No emojis in UI — use icon system only (Lucide, Heroicons)
- No pure white (#FFFFFF) backgrounds — use off-white or dark surfaces
- No oversaturated accent colors (saturation cap: 80%)
- No 3-column equal-width feature layouts — use zig-zag or asymmetric grid
- No `h-screen` — use `min-h-[100dvh]`
- No AI copywriting clichés: "Elevate", "Seamless", "Unleash", "Next-Gen"
- No broken external image links — use picsum.photos or inline SVG
- No generic lorem ipsum in demos

- Do Glowing geometric patterns
- Do Psychedelic animations
- Do Organic tech interfaces
- Do Cyber-tribal masks
- Do Neon light trails
- Do Immersive 3D environments


## Use Case

Landing pages, SaaS
