import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
// Uncomment if you want to add compression plugins
// npm install --save-dev vite-plugin-compression
// import viteCompression from 'vite-plugin-compression'

// Uncomment if you want to analyze bundle sizes
// npm install --save-dev rollup-plugin-visualizer
// import { visualizer } from 'rollup-plugin-visualizer'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    react({
      // Optimize React Fast Refresh in development
      fastRefresh: true,
      // Remove React DevTools in production
      babel: {
        plugins: mode === 'production' ? ['babel-plugin-react-remove-properties'] : [],
      },
    }),

    // Gzip compression (uncomment to enable)
    // viteCompression({
    //   algorithm: 'gzip',
    //   ext: '.gz',
    //   threshold: 10240, // Only compress files > 10KB
    //   deleteOriginFile: false,
    // }),

    // Brotli compression (better compression ratio)
    // viteCompression({
    //   algorithm: 'brotliCompress',
    //   ext: '.br',
    //   threshold: 10240,
    //   deleteOriginFile: false,
    // }),

    // Bundle analyzer (uncomment to enable)
    // visualizer({
    //   filename: './dist/stats.html',
    //   open: false,
    //   gzipSize: true,
    //   brotliSize: true,
    // }),
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 5173,
    host: true, // Listen on all addresses
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
    // Source maps only in development (reduces bundle size in production)
    sourcemap: mode === 'development',

    // Optimize chunk size threshold (warn if chunk > 1MB)
    chunkSizeWarningLimit: 1000,

    // Enable CSS code splitting (separate CSS files per chunk)
    cssCodeSplit: true,

    // Target modern browsers for smaller bundles
    target: 'es2015',

    // Minification settings
    minify: 'terser',
    terserOptions: {
      compress: {
        // Remove console.log in production
        drop_console: mode === 'production',
        drop_debugger: mode === 'production',
        pure_funcs: mode === 'production' ? ['console.log', 'console.info'] : [],
        // Remove dead code
        dead_code: true,
        // Remove unused function parameters
        unused: true,
      },
      format: {
        // Remove comments
        comments: false,
      },
    },

    rollupOptions: {
      output: {
        // Advanced code splitting strategy
        manualChunks: (id) => {
          // Vendor chunks (third-party libraries)
          if (id.includes('node_modules')) {
            // React core (critical, load first)
            if (id.includes('react') || id.includes('react-dom')) {
              return 'react-vendor'
            }

            // Router (critical for navigation)
            if (id.includes('react-router-dom')) {
              return 'router-vendor'
            }

            // UI libraries (lazy loadable)
            if (id.includes('@heroicons') || id.includes('framer-motion')) {
              return 'ui-vendor'
            }

            // Markdown rendering (lazy loadable - only needed in chat)
            if (id.includes('react-markdown') || id.includes('remark') || id.includes('prismjs')) {
              return 'markdown-vendor'
            }

            // State management (critical)
            if (id.includes('zustand') || id.includes('@tanstack/react-query')) {
              return 'state-vendor'
            }

            // Form handling (lazy loadable)
            if (id.includes('react-hook-form') || id.includes('zod') || id.includes('@hookform')) {
              return 'form-vendor'
            }

            // PDF export (lazy loadable - only needed on export)
            if (id.includes('jspdf') || id.includes('html2pdf') || id.includes('html2canvas')) {
              return 'pdf-vendor'
            }

            // Date utilities (small, can be in main)
            if (id.includes('date-fns')) {
              return 'date-vendor'
            }

            // HTTP client (critical)
            if (id.includes('axios')) {
              return 'http-vendor'
            }

            // Other vendor code (group together)
            return 'vendor'
          }

          // App chunks (split by feature)
          // Example: Split large features into separate chunks
          // if (id.includes('src/components/Chat')) {
          //   return 'chat-feature'
          // }
        },

        // Hashed filenames for cache busting
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: (assetInfo) => {
          // Separate CSS files
          if (assetInfo.name?.endsWith('.css')) {
            return 'assets/[name]-[hash][extname]'
          }
          // Other assets (images, fonts, etc.)
          return 'assets/[name]-[hash][extname]'
        },
      },

      // External dependencies (if using CDN for some libraries)
      // external: ['react', 'react-dom'], // Example: Load from CDN
      // Note: If using external, you need to add <script> tags in index.html
    },
  },

  // Optimize dependencies
  optimizeDeps: {
    include: [
      'react',
      'react-dom',
      'react-router-dom',
      '@tanstack/react-query',
      'zustand',
      'axios',
    ],
    // Exclude large dependencies that should be lazy-loaded
    exclude: [
      'jspdf',
      'html2pdf.js',
    ],
  },

  // Preview server configuration (for testing production build)
  preview: {
    port: 4173,
    host: true,
  },
}))
