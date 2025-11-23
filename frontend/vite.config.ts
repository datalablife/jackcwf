import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    allowedHosts: [
      'localhost',
      '127.0.0.1',
      '10.27.144.246',      // Windows 主机内网IP
      '172.20.84.171',      // WSL2 容器IP
      '10.255.255.254',     // Hyper-V 网关
      '163.125.190.1',      // 公网IP
    ],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@heroicons/react', 'framer-motion'],
          'markdown-vendor': ['react-markdown', 'remark-gfm', 'prismjs'],
        },
      },
    },
  },
})
