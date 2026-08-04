import { resolve } from "path";

import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [tailwindcss()],

  root: resolve(import.meta.dirname, "static/src"),

  build: {
    outDir: resolve(import.meta.dirname, "static/dist"),
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        main: resolve(import.meta.dirname, "static/src/js/main.js"),
      },
      // Stable entry filenames so templates can reference dist/main.js and
      // dist/main.css directly. Cache busting is handled by Django's
      // ManifestStaticFilesStorage, which hashes files during collectstatic —
      // adding Vite hashes on top would mean parsing Vite's manifest in the
      // template layer for no additional benefit.
      output: {
        entryFileNames: "[name].js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: (assetInfo) =>
          assetInfo.name?.endsWith(".css")
            ? "[name][extname]"
            : "assets/[name]-[hash][extname]",
      },
    },
  },

  server: {
    host: "0.0.0.0",
    port: 5173,
    // Django templates load these assets cross-origin (:8000 → :5173).
    cors: true,
    hmr: {
      host: "localhost",
    },
    watch: {
      // Docker on macOS does not forward inotify events from the host VM —
      // polling is what makes edits show up inside the container.
      usePolling: true,
      interval: 300,
    },
  },
});
