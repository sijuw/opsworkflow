import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig(({ mode }) => {
  // Loaded without a prefix filter so API_TOKEN is readable here in Node,
  // but never exposed to client code the way a VITE_ variable would be.
  const env = loadEnv(mode, process.cwd(), "");

  return {
    plugins: [
      react(),
      tailwindcss(),
    ],
    server: {
      host: '0.0.0.0',
      allowedHosts: [
        'remodeler-open-companion.ngrok-free.dev',
        'localhost',
        '.ngrok-free.dev'
      ],
      proxy: {
        // Intercept all requests starting with /api
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
          // This removes the '/api' prefix before sending it to FastAPI
          rewrite: (path) => path.replace(/^\/api/, ''),
          // Dev mirror of what nginx does in production: attach the token
          // at the proxy so it stays out of the browser.
          headers: env.API_TOKEN
            ? { Authorization: `Bearer ${env.API_TOKEN}` }
            : {},
        }
      }
    },
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
  };
});
