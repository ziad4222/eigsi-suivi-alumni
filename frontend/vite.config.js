import { defineConfig } from "vite";

export default defineConfig({
  server: { port: 4173, strictPort: true, proxy: { '/api': process.env.API_TARGET || 'http://127.0.0.1:8000' } },
  preview: { port: 4173, strictPort: true, proxy: { '/api': process.env.API_TARGET || 'http://127.0.0.1:8000' } },
});
