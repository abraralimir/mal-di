import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/health': 'http://localhost:8000',
      '/upload': 'http://localhost:8000',
      '/ask': 'http://localhost:8000',
      '/documents': 'http://localhost:8000',
      '/integrations': 'http://localhost:8000',
      '/docs': 'http://localhost:8000',
      '/openapi.json': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
  },
});
