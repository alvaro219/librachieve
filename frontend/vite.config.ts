import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// The browser only ever talks to the Vite origin; /api and /graphql are proxied to FastAPI.
// This keeps the refresh-token cookie first-party and avoids CORS in development.
const apiTarget = process.env.VITE_API_PROXY ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": { target: apiTarget, changeOrigin: false },
      "/graphql": { target: apiTarget, changeOrigin: false },
    },
  },
});
