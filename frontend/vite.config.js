import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// If you serve Django on :8000, Vite can proxy /api to it.
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            '/api': 'http://127.0.0.1:8000',
        },
    },
})
