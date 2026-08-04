/**
 * Theme resolution.
 *
 * Its own module so the rule can be unit tested with `node --test` — the Alpine
 * component around it needs a DOM and a browser, this does not.
 *
 * Names must match the `@plugin "daisyui/theme"` blocks in main.css. A value
 * that does not is not a theme: DaisyUI has no rules for it, so the page falls
 * back to the default palette while `data-theme` claims otherwise, and the
 * switcher's idea of the current theme no longer matches what is on screen.
 */

export const THEMES = { dark: "cybertribal", light: "cybertribal-light" };

export const THEME_COLORS = {
  [THEMES.dark]: "#08040F",
  [THEMES.light]: "#F5F2FA",
};

export function isKnownTheme(value) {
  return value === THEMES.dark || value === THEMES.light;
}

/**
 * Decide which theme to show.
 *
 * The stored choice wins, the OS preference decides in its absence, and dark is
 * the fallback when the OS expresses none — dark is the design, light is its
 * companion.
 *
 * An unrecognised stored value is ignored rather than trusted. It is not a
 * hypothetical: an earlier build of this template stored "dark" and "light",
 * so every browser that visited it still has one of those in localStorage.
 */
export function resolveTheme(saved, prefersLight) {
  if (isKnownTheme(saved)) return saved;
  return prefersLight ? THEMES.light : THEMES.dark;
}
