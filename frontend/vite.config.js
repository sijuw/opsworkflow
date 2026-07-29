import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "node:path";

export default defineConfig({
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
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});