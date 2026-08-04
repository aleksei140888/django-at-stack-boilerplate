// The stylesheet is imported here so Vite emits it as part of this entry —
// nothing else pulls main.css into the graph, and without this the build
// produces main.js only while templates keep asking for dist/main.css.
import "../css/main.css";

import Alpine from "alpinejs";

import { apiFetch, getCsrfToken } from "./apiFetch.js";

// Re-exported so templates and other modules have a single import surface.
export { apiFetch, getCsrfToken };

// Every component must be registered before Alpine.start(): a component
// referenced by x-data that was registered afterwards is silently inert.

// Theme names must match the @plugin "daisyui/theme" blocks in main.css. An
// unknown value here leaves data-theme pointing at a theme that does not exist,
// and the page renders with no colours at all.
export const THEMES = { dark: "cybertribal", light: "cybertribal-light" };

// Kept in sync with the browser-chrome colour, which cannot follow data-theme
// from CSS — it is a meta tag and has to be written by hand.
const THEME_COLORS = { [THEMES.dark]: "#08040F", [THEMES.light]: "#F5F2FA" };

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", THEME_COLORS[theme] ?? THEME_COLORS[THEMES.dark]);
}

/**
 * Theme switcher.
 *
 * The stored choice wins; without one, the OS preference decides, and dark is
 * the fallback when the OS expresses none — dark is the design, light is its
 * companion. The same resolution runs in an inline script in <head> before
 * first paint, otherwise the first frame is drawn in the wrong theme.
 */
Alpine.data("themeManager", () => ({
  theme: THEMES.dark,

  initTheme() {
    const saved = localStorage.getItem("theme");
    const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
    this.theme = saved ?? (prefersLight ? THEMES.light : THEMES.dark);
    applyTheme(this.theme);

    // Follow the OS only while the user has not made an explicit choice.
    window.matchMedia("(prefers-color-scheme: light)").addEventListener("change", (event) => {
      if (!localStorage.getItem("theme")) {
        this.theme = event.matches ? THEMES.light : THEMES.dark;
        applyTheme(this.theme);
      }
    });
  },

  get isDark() {
    return this.theme === THEMES.dark;
  },

  toggleTheme() {
    this.theme = this.isDark ? THEMES.light : THEMES.dark;
    localStorage.setItem("theme", this.theme);
    applyTheme(this.theme);
  },
}));


/**
 * Cookie consent banner.
 */
Alpine.data("cookieConsent", () => ({
  accepted: true, // assume accepted until init() proves otherwise — avoids a flash

  init() {
    this.accepted = localStorage.getItem("cookie_consent") === "accepted";
  },

  accept() {
    localStorage.setItem("cookie_consent", "accepted");
    this.accepted = true;
  },
}));

/**
 * Client-side filtering demo (home page).
 */
Alpine.data("searchDemo", (items = []) => ({
  query: "",
  items,

  get filtered() {
    if (!this.query) return this.items;
    const needle = this.query.toLowerCase();
    return this.items.filter((item) => item.toLowerCase().includes(needle));
  },
}));

/**
 * Generic modal. Usage: x-data="modal()"
 */
Alpine.data("modal", () => ({
  open: false,
  show() {
    this.open = true;
    document.body.style.overflow = "hidden";
  },
  hide() {
    this.open = false;
    document.body.style.overflow = "";
  },
}));

/**
 * Auto-dismissing toast.
 */
Alpine.data("toast", (message, type = "info", duration = 4000) => ({
  visible: false,
  message,
  type,

  init() {
    this.$nextTick(() => {
      this.visible = true;
      setTimeout(() => (this.visible = false), duration);
    });
  },
}));

/**
 * System health dashboard — polls /api/v1/health/.
 */
Alpine.data("healthDashboard", (intervalSeconds = 60) => ({
  status: null,
  version: null,
  checks: {},
  lastUpdated: null,
  loading: false,
  fetchError: null,
  countdown: intervalSeconds,
  _timer: null,

  async init() {
    await this.refresh();
    this._timer = setInterval(async () => {
      this.countdown -= 1;
      if (this.countdown <= 0) await this.refresh();
    }, 1000);
    // Alpine calls destroy() when the element leaves the DOM; without it the
    // interval keeps firing (and keeps hitting the API) after navigation.
    this.$el.addEventListener("alpine:destroyed", () => clearInterval(this._timer));
  },

  async refresh() {
    this.loading = true;
    this.fetchError = null;
    this.countdown = intervalSeconds;
    try {
      const data = await apiFetch("/api/v1/health/");
      this.status = data.status;
      this.version = data.version;
      this.checks = data.checks ?? {};
      this.lastUpdated = new Date(data.timestamp).toLocaleTimeString();
    } catch (err) {
      // A 503 is a valid answer here — the endpoint reports unhealthy that way,
      // and its body still holds the per-check detail worth showing.
      this.fetchError = err.message || "Failed to fetch health status";
      if (err.data?.checks) {
        this.status = err.data.status;
        this.checks = err.data.checks;
      }
    } finally {
      this.loading = false;
    }
  },
}));

Alpine.start();
