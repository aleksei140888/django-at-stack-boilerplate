import assert from "node:assert/strict";
import test from "node:test";

import { isKnownTheme, resolveTheme, THEMES, THEME_COLORS } from "./theme.js";

test("a stored choice wins over the OS preference", () => {
  assert.equal(resolveTheme(THEMES.light, false), THEMES.light);
  assert.equal(resolveTheme(THEMES.dark, true), THEMES.dark);
});

test("without a stored choice the OS decides", () => {
  assert.equal(resolveTheme(null, true), THEMES.light);
  assert.equal(resolveTheme(null, false), THEMES.dark);
});

test("dark is the fallback when nothing is known", () => {
  assert.equal(resolveTheme(undefined, undefined), THEMES.dark);
});

// Regression: an unknown value used to be written to data-theme verbatim.
// DaisyUI has no rules for it, so the page kept the default palette while
// data-theme claimed something else — and the switcher's `isDark` disagreed with
// what was on screen, making the first click look like it did nothing.
//
// "dark" and "light" are exactly what an earlier build of this template stored,
// so every browser that visited it carries one of them.
test("an unrecognised stored value is ignored, not trusted", () => {
  for (const stale of ["dark", "light", "garbage", "", "cybertribal-dim"]) {
    assert.equal(resolveTheme(stale, false), THEMES.dark, `stale value: ${stale}`);
    assert.equal(resolveTheme(stale, true), THEMES.light, `stale value: ${stale}`);
  }
});

test("isKnownTheme accepts only the declared themes", () => {
  assert.equal(isKnownTheme(THEMES.dark), true);
  assert.equal(isKnownTheme(THEMES.light), true);
  assert.equal(isKnownTheme("dark"), false);
  assert.equal(isKnownTheme(null), false);
});

test("every theme has a browser-chrome colour", () => {
  for (const theme of Object.values(THEMES)) {
    assert.match(THEME_COLORS[theme], /^#[0-9A-F]{6}$/i, `no colour for ${theme}`);
  }
});
