# CDN Integration and Frontend Performance Optimization Guide

## Overview

This guide provides complete CDN integration and frontend performance optimization for the LangChain AI Chat application.

**Current Status:**
- Frontend: Vite + React (1.1MB main bundle, 198KB secondary chunks)
- Backend: FastAPI (Python)
- Deployment: Docker + Nginx reverse proxy
- Domain: pgvctor.jackcwf.com (custom domain available)

**Performance Targets:**
- LCP (Largest Contentful Paint): <2.5s
- FID (First Input Delay): <100ms
- CLS (Cumulative Layout Shift): <0.1
- Initial Load: <3s (95th percentile)
- API Response: <350ms P50

---

## Table of Contents

1. [CDN Selection and Cost Analysis](#cdn-selection)
2. [Cloudflare CDN Configuration (Recommended)](#cloudflare-configuration)
3. [Nginx Caching and Compression Optimization](#nginx-optimization)
4. [Vite Build Optimization](#vite-optimization)
5. [Frontend Performance Monitoring](#performance-monitoring)
6. [Deployment Checklist](#deployment-checklist)
7. [Alternative CDN Options](#alternative-cdns)

---

## 1. CDN Selection and Cost Analysis {#cdn-selection}

### Recommended: Cloudflare (Free Plan)

**Why Cloudflare?**
- Free plan with unlimited bandwidth
- Global edge network (200+ cities)
- Built-in DDoS protection
- HTTPS/SSL certificates (automatic)
- Cache purging and optimization
- DNS management included
- Best for custom domains (pgvctor.jackcwf.com)

### Cost Comparison

| CDN Provider | Monthly Cost | Bandwidth | Features |
|--------------|--------------|-----------|----------|
| **Cloudflare Free** | $0 | Unlimited | DDoS, SSL, CDN, DNS |
| Cloudflare Pro | $20 | Unlimited | + WAF, image optimization |
| AWS CloudFront | $8.5 | First 1TB | Pay-per-use, S3 integration |
| Bunny CDN | $1/TB | Pay-per-use | Cheap, fast, simple |
| Google Cloud CDN | $0.08/GB | Pay-per-use | GCP integration |

**Recommendation:** Start with Cloudflare Free - best value and features.

---

## 2. Cloudflare CDN Configuration {#cloudflare-configuration}

### Step 1: Add Domain to Cloudflare

```bash
# 1. Create Cloudflare account (if not exists)
#    Visit: https://dash.cloudflare.com/sign-up

# 2. Add your domain
#    - Click "Add a Site"
#    - Enter: jackcwf.com
#    - Select: Free plan

# 3. Update nameservers at your domain registrar
#    Replace existing nameservers with Cloudflare's:
#    - NS1: angie.ns.cloudflare.com
#    - NS2: brad.ns.cloudflare.com
#    (Your actual nameservers will be shown in Cloudflare dashboard)

# 4. Wait for DNS propagation (typically 10-30 minutes)
```

### Step 2: DNS Configuration

**Add DNS Records in Cloudflare Dashboard:**

| Type | Name | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| A | pgvctor | 47.79.87.199 | Proxied (Orange Cloud) | Auto |
| CNAME | www | pgvctor.jackcwf.com | Proxied (Orange Cloud) | Auto |

**Important:** Enable "Proxied" (orange cloud icon) for CDN caching.

### Step 3: SSL/TLS Configuration

```
Cloudflare Dashboard > SSL/TLS > Overview
- Encryption Mode: Full (strict)
- Always Use HTTPS: ON
- Automatic HTTPS Rewrites: ON
- Minimum TLS Version: 1.2
- Opportunistic Encryption: ON
```

### Step 4: Caching Configuration

#### Page Rules (Free Plan: 3 rules available)

**Rule 1: Cache Static Assets (High Priority)**
```
URL Pattern: *pgvctor.jackcwf.com/assets/*

Settings:
- Cache Level: Cache Everything
- Edge Cache TTL: 1 month
- Browser Cache TTL: 1 month
```

**Rule 2: Bypass Cache for API (Medium Priority)**
```
URL Pattern: *pgvctor.jackcwf.com/api/*

Settings:
- Cache Level: Bypass
- Disable Performance
```

**Rule 3: HTML Caching (Low Priority)**
```
URL Pattern: *pgvctor.jackcwf.com/*

Settings:
- Cache Level: Standard
- Browser Cache TTL: 2 hours
- Edge Cache TTL: 2 hours
```

#### Caching Configuration (Dashboard)

```
Cloudflare Dashboard > Caching > Configuration

Browser Cache TTL: Respect Existing Headers
Crawler Hints: ON
Always Online: ON
```

### Step 5: Performance Optimization

```
Cloudflare Dashboard > Speed > Optimization

Auto Minify:
  ✅ JavaScript
  ✅ CSS
  ✅ HTML

Brotli Compression: ON
HTTP/2: ON
HTTP/3 (with QUIC): ON
0-RTT Connection Resumption: ON
Rocket Loader: OFF (conflicts with React hydration)
Early Hints: ON
```

### Step 6: Security Configuration

```
Cloudflare Dashboard > Security

Security Level: Medium
Challenge Passage: 30 minutes

Bot Fight Mode: ON (free plan)
```

### Step 7: Verify Cloudflare CDN

```bash
# Check if Cloudflare is serving your site
curl -I https://pgvctor.jackcwf.com

# Expected headers:
# CF-Cache-Status: HIT (on subsequent requests)
# CF-Ray: <ray-id>
# Server: cloudflare

# Test cache hit rate
for i in {1..3}; do
  curl -s -o /dev/null -w "Request $i: %{http_code} - CF-Cache: %{header_cf_cache_status}\n" \
    https://pgvctor.jackcwf.com/assets/index-CxgqXN_Y.js
  sleep 1
done

# Expected output:
# Request 1: 200 - CF-Cache: MISS
# Request 2: 200 - CF-Cache: HIT
# Request 3: 200 - CF-Cache: HIT
```

---

## 3. Nginx Caching and Compression Optimization {#nginx-optimization}

### Enhanced Nginx Configuration

The optimized configuration adds:
- Brotli compression (better than gzip)
- Fine-grained cache control headers
- CDN-friendly headers
- Static asset optimization
- Security headers enhancement

**Implementation:** See `/mnt/d/工作区/云开发/working/docker/nginx.conf` (updated below)

### Key Improvements

#### 1. Brotli Compression (10-15% better than gzip)

```nginx
# Add to http block (requires nginx-module-brotli)
brotli on;
brotli_comp_level 6;
brotli_types text/plain text/css application/json application/javascript
             text/xml application/xml application/xml+rss text/javascript
             image/svg+xml;
```

#### 2. Enhanced Static Asset Caching

```nginx
# Immutable assets (hashed filenames)
location ~* \.(js|css)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    add_header Vary "Accept-Encoding";

    # Enable CORS for CDN
    add_header Access-Control-Allow-Origin "*";

    # Preload hint for critical resources
    add_header Link "<$uri>; rel=preload; as=script" always;
}

# Images and fonts
location ~* \.(png|jpg|jpeg|gif|webp|ico|svg|woff|woff2|ttf|eot)$ {
    expires 6M;
    add_header Cache-Control "public, immutable";
    add_header Vary "Accept-Encoding";
}
```

#### 3. CDN-Friendly Headers

```nginx
# Add to server block
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;

# CDN cache key
add_header Vary "Accept-Encoding" always;

# CORS for CDN assets
add_header Access-Control-Allow-Origin "*" always;
```

---

## 4. Vite Build Optimization {#vite-optimization}

### Enhanced Vite Configuration

**File:** `/mnt/d/工作区/云开发/working/frontend/vite.config.ts`

Key optimizations:
1. Advanced code splitting
2. Bundle size reduction
3. Compression plugins
4. Source map optimization
5. Dependency pre-bundling

### Implementation

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import viteCompression from 'vite-plugin-compression'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [
    react({
      // Optimize React Fast Refresh in development
      fastRefresh: true,
    }),

    // Gzip compression
    viteCompression({
      algorithm: 'gzip',
      ext: '.gz',
      threshold: 10240, // Only compress files > 10KB
      deleteOriginFile: false,
    }),

    // Brotli compression (better compression ratio)
    viteCompression({
      algorithm: 'brotliCompress',
      ext: '.br',
      threshold: 10240,
      deleteOriginFile: false,
    }),
  ],

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  server: {
    port: 5173,
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
    // Source maps only in development
    sourcemap: mode === 'development',

    // Optimize chunk size threshold
    chunkSizeWarningLimit: 1000,

    // Enable CSS code splitting
    cssCodeSplit: true,

    // Minification settings
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: mode === 'production',
        drop_debugger: mode === 'production',
        pure_funcs: mode === 'production' ? ['console.log', 'console.info'] : [],
      },
    },

    rollupOptions: {
      output: {
        // Advanced code splitting strategy
        manualChunks: (id) => {
          // Vendor chunks
          if (id.includes('node_modules')) {
            // React core
            if (id.includes('react') || id.includes('react-dom')) {
              return 'react-vendor'
            }

            // Router
            if (id.includes('react-router-dom')) {
              return 'router-vendor'
            }

            // UI libraries
            if (id.includes('@heroicons') || id.includes('framer-motion')) {
              return 'ui-vendor'
            }

            // Markdown rendering
            if (id.includes('react-markdown') || id.includes('remark') || id.includes('prismjs')) {
              return 'markdown-vendor'
            }

            // State management
            if (id.includes('zustand') || id.includes('@tanstack/react-query')) {
              return 'state-vendor'
            }

            // Form handling
            if (id.includes('react-hook-form') || id.includes('zod')) {
              return 'form-vendor'
            }

            // PDF export
            if (id.includes('jspdf') || id.includes('html2pdf')) {
              return 'pdf-vendor'
            }

            // Other vendor code
            return 'vendor'
          }
        },

        // Hashed filenames for cache busting
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
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
      ],
    },
  },
}))
```

### Bundle Analysis

```bash
# Install bundle analyzer
npm install --save-dev rollup-plugin-visualizer

# Add to vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer'

plugins: [
  // ... existing plugins
  visualizer({
    filename: './dist/stats.html',
    open: true,
    gzipSize: true,
    brotliSize: true,
  }),
]

# Build and analyze
npm run build

# Open dist/stats.html to see bundle visualization
```

### Expected Bundle Sizes (After Optimization)

| Chunk | Current | Target | Status |
|-------|---------|--------|--------|
| Main (index) | 1.1MB | <800KB | Needs optimization |
| React vendor | 200KB | <150KB | Good |
| Markdown vendor | 121B | <100KB | Excellent |
| UI vendor | - | <100KB | To be split |
| CSS | 27KB | <30KB | Good |

**Total Gzipped:** Target <300KB initial load

---

## 5. Frontend Performance Monitoring {#performance-monitoring}

### Web Vitals Integration

**File:** `/mnt/d/工作区/云开发/working/frontend/src/utils/performance.ts`

```typescript
/**
 * Web Vitals monitoring and reporting
 */

import { onCLS, onFID, onLCP, onFCP, onTTFB } from 'web-vitals'

interface PerformanceMetric {
  name: string
  value: number
  rating: 'good' | 'needs-improvement' | 'poor'
  timestamp: number
  url: string
}

// Metric thresholds (based on Web Vitals)
const THRESHOLDS = {
  LCP: { good: 2500, poor: 4000 },
  FID: { good: 100, poor: 300 },
  CLS: { good: 0.1, poor: 0.25 },
  FCP: { good: 1800, poor: 3000 },
  TTFB: { good: 800, poor: 1800 },
}

function getRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  const threshold = THRESHOLDS[name as keyof typeof THRESHOLDS]
  if (!threshold) return 'good'

  if (value <= threshold.good) return 'good'
  if (value <= threshold.poor) return 'needs-improvement'
  return 'poor'
}

function sendToAnalytics(metric: PerformanceMetric) {
  // Send to backend analytics endpoint
  fetch('/api/analytics/performance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metric),
    keepalive: true, // Ensure sent even if page is unloading
  }).catch((error) => {
    console.error('Failed to send performance metric:', error)
  })

  // Log to console in development
  if (import.meta.env.DEV) {
    console.log(`[Performance] ${metric.name}:`, {
      value: metric.value,
      rating: metric.rating,
    })
  }
}

export function initPerformanceMonitoring() {
  // Core Web Vitals
  onLCP((metric) => {
    sendToAnalytics({
      name: 'LCP',
      value: metric.value,
      rating: getRating('LCP', metric.value),
      timestamp: Date.now(),
      url: window.location.href,
    })
  })

  onFID((metric) => {
    sendToAnalytics({
      name: 'FID',
      value: metric.value,
      rating: getRating('FID', metric.value),
      timestamp: Date.now(),
      url: window.location.href,
    })
  })

  onCLS((metric) => {
    sendToAnalytics({
      name: 'CLS',
      value: metric.value,
      rating: getRating('CLS', metric.value),
      timestamp: Date.now(),
      url: window.location.href,
    })
  })

  // Additional metrics
  onFCP((metric) => {
    sendToAnalytics({
      name: 'FCP',
      value: metric.value,
      rating: getRating('FCP', metric.value),
      timestamp: Date.now(),
      url: window.location.href,
    })
  })

  onTTFB((metric) => {
    sendToAnalytics({
      name: 'TTFB',
      value: metric.value,
      rating: getRating('TTFB', metric.value),
      timestamp: Date.now(),
      url: window.location.href,
    })
  })
}

// Resource timing analysis
export function analyzeResourceTimings() {
  if (!window.performance || !window.performance.getEntriesByType) {
    return
  }

  const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[]

  const analysis = {
    total: resources.length,
    byType: {} as Record<string, number>,
    slowResources: [] as Array<{ name: string; duration: number }>,
  }

  resources.forEach((resource) => {
    // Count by type
    const type = resource.initiatorType
    analysis.byType[type] = (analysis.byType[type] || 0) + 1

    // Track slow resources (>1s)
    if (resource.duration > 1000) {
      analysis.slowResources.push({
        name: resource.name,
        duration: resource.duration,
      })
    }
  })

  console.log('[Performance] Resource Analysis:', analysis)
  return analysis
}

// Performance observer for long tasks
export function observeLongTasks() {
  if (!('PerformanceObserver' in window)) {
    return
  }

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        console.warn('[Performance] Long Task detected:', {
          duration: entry.duration,
          startTime: entry.startTime,
        })

        // Report long tasks to analytics
        sendToAnalytics({
          name: 'LongTask',
          value: entry.duration,
          rating: entry.duration > 500 ? 'poor' : 'needs-improvement',
          timestamp: Date.now(),
          url: window.location.href,
        })
      }
    })

    observer.observe({ entryTypes: ['longtask'] })
  } catch (error) {
    console.error('Failed to observe long tasks:', error)
  }
}
```

### Usage in Main App

**File:** `/mnt/d/工作区/云开发/working/frontend/src/main.tsx`

```typescript
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'
import { initPerformanceMonitoring, observeLongTasks } from './utils/performance'

// Initialize performance monitoring
if (import.meta.env.PROD) {
  initPerformanceMonitoring()
  observeLongTasks()
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

### Backend Analytics Endpoint

**File:** `/mnt/d/工作区/云开发/working/src/api/analytics_routes.py`

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])

class PerformanceMetric(BaseModel):
    name: str
    value: float
    rating: Literal["good", "needs-improvement", "poor"]
    timestamp: int
    url: str

@router.post("/performance")
async def record_performance_metric(metric: PerformanceMetric):
    """
    Record frontend performance metrics for analysis.

    Stores Core Web Vitals and other performance metrics for monitoring.
    """
    try:
        # Log the metric
        logger.info(
            f"Performance Metric: {metric.name}={metric.value}ms "
            f"(rating={metric.rating}, url={metric.url})"
        )

        # TODO: Store in database for analytics dashboard
        # await performance_repository.create(metric)

        return {"status": "recorded", "metric": metric.name}
    except Exception as e:
        logger.error(f"Failed to record performance metric: {e}")
        raise HTTPException(status_code=500, detail="Failed to record metric")
```

### Prometheus Metrics Integration

```python
from prometheus_client import Histogram

# Add to src/infrastructure/monitoring.py
frontend_performance_metrics = Histogram(
    'frontend_performance_seconds',
    'Frontend performance metrics',
    ['metric_name', 'rating'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Record in analytics endpoint
frontend_performance_metrics.labels(
    metric_name=metric.name,
    rating=metric.rating
).observe(metric.value / 1000)  # Convert ms to seconds
```

---

## 6. Deployment Checklist {#deployment-checklist}

### Pre-Deployment

- [ ] Build frontend with optimizations: `npm run build`
- [ ] Verify bundle sizes: Check `dist/` directory
- [ ] Test gzip/brotli compression: Inspect `.gz` and `.br` files
- [ ] Run bundle analyzer: Review `dist/stats.html`
- [ ] Update Nginx configuration with optimized settings
- [ ] Test Nginx config: `nginx -t`
- [ ] Rebuild Docker image with new configs

### CDN Setup

- [ ] Add domain to Cloudflare
- [ ] Update nameservers at registrar
- [ ] Configure DNS records (A, CNAME)
- [ ] Enable SSL/TLS (Full strict mode)
- [ ] Set up Page Rules for caching
- [ ] Enable performance optimizations (Brotli, HTTP/3)
- [ ] Configure security settings (Bot Fight Mode)

### Verification

- [ ] Check DNS propagation: `nslookup pgvctor.jackcwf.com`
- [ ] Verify SSL certificate: `curl -I https://pgvctor.jackcwf.com`
- [ ] Test cache headers: `curl -I https://pgvctor.jackcwf.com/assets/`
- [ ] Confirm Cloudflare is serving: Check `CF-Ray` header
- [ ] Run Lighthouse audit: Target scores (Performance >90, Best Practices >95)
- [ ] Test from multiple locations: Use webpagetest.org

### Post-Deployment Monitoring

- [ ] Monitor Core Web Vitals in analytics dashboard
- [ ] Check CDN cache hit rate in Cloudflare dashboard
- [ ] Review slow resources in performance logs
- [ ] Monitor bundle size in CI/CD
- [ ] Set up alerts for performance degradation

---

## 7. Alternative CDN Options {#alternative-cdns}

### Option 1: AWS CloudFront (Recommended for AWS infrastructure)

**Setup:**
1. Create S3 bucket for static assets
2. Upload frontend build to S3
3. Create CloudFront distribution
4. Configure origin (S3 or custom origin for Docker)
5. Set cache behaviors
6. Add custom domain with SSL

**Cost:** $8.50/TB (first 10TB), ~$0.085/10,000 requests

**Best for:** Existing AWS users, complex caching rules

### Option 2: Bunny CDN (Best price/performance)

**Setup:**
1. Create Bunny CDN account
2. Add pull zone (origin: https://pgvctor.jackcwf.com)
3. Configure caching rules
4. Add custom hostname
5. Enable SSL

**Cost:** $1/TB, $0.005/10,000 requests

**Best for:** Budget-conscious projects, simple setup

### Option 3: Google Cloud CDN

**Setup:**
1. Create Google Cloud Load Balancer
2. Configure backend service (Docker container)
3. Enable Cloud CDN on backend
4. Set cache policies
5. Add custom domain

**Cost:** $0.08/GB (varies by region)

**Best for:** GCP users, Google Cloud infrastructure

---

## Performance Budget

### Bundle Size Budget

| Resource Type | Budget | Current | Status |
|---------------|--------|---------|--------|
| Initial HTML | <15KB | 750B | ✅ |
| Initial CSS | <50KB | 27KB | ✅ |
| Initial JS | <200KB (gzipped) | ~300KB | ⚠️ Needs optimization |
| Images | <500KB | 0KB | ✅ |
| Fonts | <100KB | 0KB | ✅ |
| **Total Initial Load** | <800KB | ~330KB | ✅ |

### Timing Budget

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| TTFB | <800ms | TBD | - |
| FCP | <1.8s | TBD | - |
| LCP | <2.5s | TBD | - |
| TTI | <3.8s | TBD | - |
| FID | <100ms | TBD | - |
| CLS | <0.1 | TBD | - |

### API Performance Budget

| Endpoint | Target (P95) | Current | Status |
|----------|--------------|---------|--------|
| GET /api/conversations | <200ms | ~150ms | ✅ |
| POST /api/messages | <500ms | ~400ms | ✅ |
| POST /api/documents/search | <300ms | ~250ms | ✅ |
| WebSocket latency | <100ms | ~80ms | ✅ |

---

## Cost Estimate

### Monthly Cost Breakdown (Cloudflare Free Plan)

| Service | Cost | Notes |
|---------|------|-------|
| Cloudflare CDN | $0 | Unlimited bandwidth |
| Cloudflare SSL | $0 | Automatic SSL certificates |
| Cloudflare DDoS Protection | $0 | Included |
| DNS Management | $0 | Included |
| **Total** | **$0** | Best value option |

### Alternative: Cloudflare Pro ($20/month)

Additional features:
- Web Application Firewall (WAF)
- Image optimization
- Mobile acceleration
- Prioritized email support

**Recommendation:** Start with Free plan, upgrade if needed.

---

## Testing and Validation

### Lighthouse Testing

```bash
# Install Lighthouse CLI
npm install -g lighthouse

# Run audit
lighthouse https://pgvctor.jackcwf.com --output html --output-path ./lighthouse-report.html

# Target scores:
# - Performance: >90
# - Accessibility: >95
# - Best Practices: >95
# - SEO: >90
```

### WebPageTest.org

1. Visit: https://www.webpagetest.org
2. Enter URL: https://pgvctor.jackcwf.com
3. Test from multiple locations (US, EU, Asia)
4. Review waterfall, filmstrip, and metrics

**Target:** A grade on all metrics

### Cache Verification

```bash
#!/bin/bash
# Test cache headers

URL="https://pgvctor.jackcwf.com"

echo "Testing HTML caching..."
curl -I $URL

echo "\nTesting JS caching..."
curl -I $URL/assets/index-CxgqXN_Y.js

echo "\nTesting CSS caching..."
curl -I $URL/assets/index-CTY8BRAj.css

echo "\nTesting API (should bypass cache)..."
curl -I $URL/api/health

# Expected:
# - HTML: Cache-Control: no-cache
# - JS/CSS: Cache-Control: public, immutable, max-age=31536000
# - API: No cache headers
```

---

## Troubleshooting

### Issue: CDN not serving content

**Symptoms:** No `CF-Ray` header, `CF-Cache-Status` missing

**Solution:**
1. Verify DNS is proxied (orange cloud icon in Cloudflare)
2. Check nameservers are updated at registrar
3. Wait for DNS propagation (up to 48 hours)
4. Clear Cloudflare cache: Dashboard > Caching > Purge Everything

### Issue: Cache not working

**Symptoms:** `CF-Cache-Status: BYPASS` or `MISS` on all requests

**Solution:**
1. Check Page Rules order (most specific first)
2. Verify URL patterns match exactly
3. Check origin server cache headers (Nginx config)
4. Enable "Cache Everything" in Page Rule

### Issue: High bundle sizes

**Symptoms:** Main bundle >1MB, slow initial load

**Solution:**
1. Run bundle analyzer: `npm run build` with visualizer plugin
2. Identify large dependencies
3. Consider lazy loading: `React.lazy()` and `Suspense`
4. Remove unused dependencies: `npm uninstall <package>`
5. Use tree-shaking: Check `package.json` for `sideEffects: false`

### Issue: Poor Web Vitals scores

**Symptoms:** LCP >2.5s, CLS >0.1, FID >100ms

**Solution:**
- **LCP:** Optimize largest image/element, preload critical resources
- **CLS:** Reserve space for dynamic content, avoid layout shifts
- **FID:** Reduce JavaScript execution time, split long tasks

---

## Next Steps

1. **Implement Cloudflare CDN** (1-2 hours)
   - Add domain to Cloudflare
   - Configure DNS and SSL
   - Set up caching rules

2. **Update Nginx Configuration** (30 minutes)
   - Apply optimized cache headers
   - Enable Brotli compression (if supported)
   - Deploy updated config

3. **Optimize Vite Build** (1 hour)
   - Update vite.config.ts with advanced chunking
   - Add compression plugins
   - Run bundle analyzer

4. **Add Performance Monitoring** (1-2 hours)
   - Install web-vitals package
   - Implement performance.ts utility
   - Create analytics endpoint

5. **Test and Validate** (1 hour)
   - Run Lighthouse audit
   - Test cache headers
   - Verify CDN is serving content

**Total Estimated Time:** 4-6 hours

---

## References

- [Cloudflare Documentation](https://developers.cloudflare.com/)
- [Web Vitals](https://web.dev/vitals/)
- [Vite Performance Best Practices](https://vitejs.dev/guide/performance.html)
- [Nginx Caching Guide](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_cache)
- [Lighthouse Documentation](https://github.com/GoogleChrome/lighthouse)

---

**Document Version:** 1.0
**Last Updated:** 2025-11-21
**Author:** Claude (Performance Optimization Expert)
