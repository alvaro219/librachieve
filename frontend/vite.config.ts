import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The browser only ever talks to the Vite origin; /api and /graphql are proxied to FastAPI.
// This keeps the refresh-token cookie first-party and avoids CORS in development.
const apiTarget = process.env.VITE_API_PROXY ?? "http://localhost:8000";
// Absolute site URL for social previews (index.html og:image). Production builds pass it in.
process.env.VITE_SITE_URL ??= "http://localhost:5173";

const proxy = {
  "/api": { target: apiTarget, changeOrigin: false },
  "/graphql": { target: apiTarget, changeOrigin: false },
};

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    // Bind mounts from Windows/macOS hosts do not deliver file events into Docker; poll there.
    watch: process.env.VITE_USE_POLLING ? { usePolling: true, interval: 300 } : undefined,
    proxy,
  },
  // `npm run build && npm run preview`: the production build (with the service worker),
  // same single origin as dev
  preview: { host: true, port: 4173, proxy },
});
