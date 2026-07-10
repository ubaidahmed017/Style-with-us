import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/admin/',
  server: {
    // Pin the dev server so its origin stays in the backend CORS allowlist
    // instead of drifting to 5174/5175 when 5173 is taken.
    port: 5173,
    strictPort: true,
  },
})
