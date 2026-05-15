import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const port = Number(process.env.VITE_PORT) || 5171

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Required for Docker: bind all interfaces so host port mapping works.
    host: '0.0.0.0',
    port,
    strictPort: true,
  },
})
