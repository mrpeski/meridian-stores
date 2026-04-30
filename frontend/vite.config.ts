import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// Infra: dev server host, port, and API proxy target are all env-driven (see `config/frontend.env.example`).
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const proxyTarget =
    env.VITE_API_PROXY_TARGET || env.VITE_BACKEND_URL || "http://127.0.0.1:8000";
  const host = env.VITE_DEV_HOST || "0.0.0.0";
  const port = Number(env.VITE_DEV_PORT || 5173);

  return {
    plugins: [react()],
    server: {
      host,
      port,
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: env.VITE_PROXY_CHANGE_ORIGIN !== "false",
        },
      },
    },
    preview: {
      host,
      port: Number(env.VITE_PREVIEW_PORT || port),
      proxy: {
        "/api": {
          target: proxyTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
