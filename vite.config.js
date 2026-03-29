import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import { resolve } from "path";

export default defineConfig({
  plugins: [tailwindcss()],

  root: resolve(__dirname, "static/src"),

  build: {
    outDir: resolve(__dirname, "static/dist"),
    emptyOutDir: true,
    manifest: true,
    rollupOptions: {
      input: {
        main: resolve(__dirname, "static/src/js/main.js"),
      },
    },
  },

  server: {
    host: "0.0.0.0",
    port: 5173,
    // Allow Django templates to load Vite assets in dev
    cors: true,
    hmr: {
      host: "localhost",
    },
  },
});
