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

/**
 * Theme manager — light/dark with system preference detection, persisted to
 * localStorage. The attribute is also written in an inline script in base.html
 * so the correct theme is applied before first paint (no flash of light theme).
 */
Alpine.data("themeManager", () => ({
  theme: "light",

  initTheme() {
    const saved = localStorage.getItem("theme");
    this.theme =
      saved ??
      (window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light");
    document.documentElement.setAttribute("data-theme", this.theme);

    // Follow the OS only while the user has not made an explicit choice.
    window
      .matchMedia("(prefers-color-scheme: dark)")
      .addEventListener("change", (event) => {
        if (!localStorage.getItem("theme")) {
          this.theme = event.matches ? "dark" : "light";
          document.documentElement.setAttribute("data-theme", this.theme);
        }
      });
  },

  toggleTheme() {
    this.theme = this.theme === "dark" ? "light" : "dark";
    localStorage.setItem("theme", this.theme);
    document.documentElement.setAttribute("data-theme", this.theme);
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
