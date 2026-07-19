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
      '.ngrok-free.dev' // This will allow any sub-domain from ngrok automatically
    ],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});