import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// En desarrollo, /api/* se redirige a Django: mismo origen para el navegador,
// así las cookies de sesión y CSRF funcionan sin configurar CORS.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
