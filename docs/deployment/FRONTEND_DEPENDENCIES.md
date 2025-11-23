# Frontend Performance Optimization Dependencies

This document lists the additional dependencies needed for frontend performance optimization.

## Required Dependencies

### 1. Web Vitals Library

Install the official Web Vitals library for performance monitoring:

```bash
cd frontend
npm install web-vitals
```

**Purpose:** Measure Core Web Vitals (LCP, FID, CLS, FCP, TTFB)

### 2. Vite Compression Plugin (Optional but Recommended)

Install compression plugins for build optimization:

```bash
cd frontend
npm install --save-dev vite-plugin-compression
```

**Purpose:** Generate gzip and brotli compressed assets during build

### 3. Bundle Analyzer (Development Only)

Install bundle analyzer to visualize bundle sizes:

```bash
cd frontend
npm install --save-dev rollup-plugin-visualizer
```

**Purpose:** Analyze bundle sizes and identify optimization opportunities

## Updated package.json

Add these to your `frontend/package.json`:

```json
{
  "dependencies": {
    "web-vitals": "^3.5.0"
  },
  "devDependencies": {
    "vite-plugin-compression": "^0.5.1",
    "rollup-plugin-visualizer": "^5.11.0"
  }
}
```

## Installation Commands

### All at once:

```bash
cd frontend
npm install web-vitals
npm install --save-dev vite-plugin-compression rollup-plugin-visualizer
```

### Verify installation:

```bash
npm list web-vitals vite-plugin-compression rollup-plugin-visualizer
```

## Usage

### 1. Web Vitals

```typescript
// In src/main.tsx
import { initPerformanceMonitoring } from './utils/performance'

if (import.meta.env.PROD) {
  initPerformanceMonitoring()
}
```

### 2. Vite Compression

```typescript
// In vite.config.ts
import viteCompression from 'vite-plugin-compression'

export default defineConfig({
  plugins: [
    // Gzip
    viteCompression({
      algorithm: 'gzip',
      ext: '.gz',
    }),
    // Brotli
    viteCompression({
      algorithm: 'brotliCompress',
      ext: '.br',
    }),
  ],
})
```

### 3. Bundle Analyzer

```typescript
// In vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig({
  plugins: [
    visualizer({
      filename: './dist/stats.html',
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
})
```

Then run:
```bash
npm run build
# Open dist/stats.html in browser
```

## Expected Results

After installing and configuring:

1. **Web Vitals:**
   - Performance metrics sent to `/api/analytics/performance`
   - Console logs in development mode
   - Real user monitoring in production

2. **Compression:**
   - `.gz` files generated in `dist/assets/`
   - `.br` files generated in `dist/assets/`
   - 60-80% file size reduction

3. **Bundle Analyzer:**
   - `dist/stats.html` generated
   - Interactive visualization of bundle composition
   - Identify large dependencies

## Troubleshooting

### Issue: `web-vitals` not found

**Solution:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Issue: Compression files not generated

**Solution:**
1. Verify plugin is in `vite.config.ts`
2. Run `npm run build` (not `npm run dev`)
3. Check `dist/assets/` for `.gz` and `.br` files

### Issue: Bundle analyzer doesn't open

**Solution:**
```bash
# Manually open the file
open dist/stats.html
# Or on Linux:
xdg-open dist/stats.html
```

---

**Note:** These dependencies are optional but highly recommended for production deployments. The application will work without them, but you'll miss out on performance monitoring and optimization opportunities.
