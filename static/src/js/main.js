// Alpine.js
import Alpine from "alpinejs";

// ===== Alpine components =====

/**
 * Theme manager — supports light/dark with system preference detection.
 * Persists user choice to localStorage.
 */
Alpine.data("themeManager", () => ({
  theme: "light",

  initTheme() {
    const saved = localStorage.getItem("theme");
    if (saved) {
      this.theme = saved;
    } else {
      // Auto-detect system preference
      this.theme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
    }
    document.documentElement.setAttribute("data-theme", this.theme);

    // Listen for system preference changes
    window
      .matchMedia("(prefers-color-scheme: dark)")
      .addEventListener("change", (e) => {
        if (!localStorage.getItem("theme")) {
          this.theme = e.matches ? "dark" : "light";
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
  accepted: false,

  init() {
    this.accepted = localStorage.getItem("cookie_consent") === "accepted";
  },

  accept() {
    localStorage.setItem("cookie_consent", "accepted");
    this.accepted = true;
  },
}));

/**
 * Live search demo component (home page).
 */
Alpine.data("searchDemo", () => ({
  query: "",
  items: [
    "Django 5 + DRF",
    "Alpine.js 3",
    "Tailwind CSS 4",
    "DaisyUI components",
    "Vite build tool",
    "PostgreSQL ready",
    "Docker + docker-compose",
    "Full authentication",
    "SEO optimized",
    "Dark / Light themes",
    "Schema.org structured data",
    "Sitemap + robots.txt",
    "Cookie consent",
    "GDPR compliant",
    "WhiteNoise static files",
    "Celery + Redis",
    "Rate limiting",
    "CSRF protection",
  ],

  get filtered() {
    if (!this.query) return this.items;
    return this.items.filter((item) =>
      item.toLowerCase().includes(this.query.toLowerCase())
    );
  },
}));

/**
 * Generic modal component.
 * Usage: x-data="modal()"
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
 * Toast notification component.
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

// Start Alpine
Alpine.start();

// ===== CSRF helper for fetch requests =====
export function getCsrfToken() {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="))
    ?.split("=")[1];
}

/**
 * Wrapper around fetch that includes CSRF token automatically.
 */
export async function apiFetch(url, options = {}) {
  const defaults = {
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCsrfToken(),
      ...options.headers,
    },
    credentials: "same-origin",
  };
  const response = await fetch(url, { ...defaults, ...options });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw Object.assign(new Error(error.detail || "Request failed"), {
      status: response.status,
      data: error,
    });
  }
  return response.json();
}
