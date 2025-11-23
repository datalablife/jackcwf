# CDN Deployment Checklist

Complete checklist for deploying the application with CDN integration and frontend performance optimizations.

---

## Pre-Deployment Phase

### 1. Frontend Build Optimization

- [ ] **Install compression plugins**
  ```bash
  cd frontend
  npm install --save-dev vite-plugin-compression rollup-plugin-visualizer
  ```

- [ ] **Update Vite configuration**
  ```bash
  # Replace vite.config.ts with optimized version
  cp vite.config.optimized.ts vite.config.ts
  ```

- [ ] **Build frontend with optimizations**
  ```bash
  cd frontend
  npm run build
  ```

- [ ] **Verify build output**
  ```bash
  # Check dist directory
  ls -lh dist/
  ls -lh dist/assets/

  # Expected output:
  # - index.html (~750B)
  # - assets/*.js (with hashes)
  # - assets/*.css (with hashes)
  # - assets/*.js.gz (gzip compressed)
  # - assets/*.js.br (brotli compressed, optional)
  ```

- [ ] **Analyze bundle sizes**
  ```bash
  # Open dist/stats.html in browser (if visualizer plugin enabled)
  # Verify:
  # - Main bundle < 800KB (gzipped < 300KB)
  # - Individual chunks < 500KB
  # - No duplicate dependencies
  ```

### 2. Backend Optimization

- [ ] **Add analytics route**
  ```bash
  # Verify analytics route exists
  cat src/api/analytics_routes.py
  ```

- [ ] **Register analytics router in main.py**
  ```python
  # Add to src/main.py
  from src.api.analytics_routes import router as analytics_router
  app.include_router(analytics_router)
  ```

- [ ] **Test analytics endpoint locally**
  ```bash
  curl -X POST http://localhost:8000/api/analytics/performance \
    -H "Content-Type: application/json" \
    -d '{"name":"LCP","value":2150,"rating":"good","timestamp":1700000000000,"url":"http://localhost:5173/"}'
  ```

### 3. Nginx Configuration

- [ ] **Backup current Nginx config**
  ```bash
  cp docker/nginx.conf docker/nginx.conf.backup
  ```

- [ ] **Update Nginx config with optimizations**
  ```bash
  cp docker/nginx.optimized.conf docker/nginx.conf
  ```

- [ ] **Verify Nginx syntax**
  ```bash
  # If running locally
  nginx -t -c docker/nginx.conf

  # In Docker
  docker run --rm -v $(pwd)/docker/nginx.conf:/etc/nginx/nginx.conf nginx nginx -t
  ```

### 4. Docker Image

- [ ] **Rebuild Docker image**
  ```bash
  docker build -t langchain-ai-chat:cdn-optimized .
  ```

- [ ] **Test Docker image locally**
  ```bash
  docker run --rm -p 80:80 \
    -e DATABASE_URL="$DATABASE_URL" \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    langchain-ai-chat:cdn-optimized
  ```

- [ ] **Verify container health**
  ```bash
  curl http://localhost/health
  # Expected: "healthy"
  ```

---

## CDN Setup Phase

### 1. Cloudflare Account Setup

- [ ] **Create Cloudflare account** (if not exists)
  - Visit: https://dash.cloudflare.com/sign-up
  - Verify email address

- [ ] **Add domain to Cloudflare**
  - Click "Add a Site"
  - Enter domain: `jackcwf.com`
  - Select: Free plan
  - Click "Add Site"

### 2. DNS Configuration

- [ ] **Update nameservers at registrar**
  - Copy Cloudflare nameservers from dashboard
  - Example:
    - `angie.ns.cloudflare.com`
    - `brad.ns.cloudflare.com`
  - Update nameservers at domain registrar
  - Wait 10-30 minutes for propagation

- [ ] **Add DNS records in Cloudflare**

  | Type | Name | Content | Proxy | TTL |
  |------|------|---------|-------|-----|
  | A | pgvctor | 47.79.87.199 | Proxied (🟠) | Auto |
  | CNAME | www | pgvctor.jackcwf.com | Proxied (🟠) | Auto |

  **Important:** Ensure "Proxied" is enabled (orange cloud icon)

- [ ] **Verify DNS propagation**
  ```bash
  # Check nameservers
  nslookup -type=NS jackcwf.com

  # Check A record
  nslookup pgvctor.jackcwf.com

  # Expected output: 47.79.87.199 (or Cloudflare IP if proxied)
  ```

### 3. SSL/TLS Configuration

- [ ] **Configure SSL/TLS**
  - Navigate to: SSL/TLS > Overview
  - Set encryption mode: **Full (strict)**
  - Enable: Always Use HTTPS
  - Enable: Automatic HTTPS Rewrites
  - Set minimum TLS version: **TLS 1.2**
  - Enable: Opportunistic Encryption

- [ ] **Wait for SSL certificate issuance**
  - Usually takes 5-15 minutes
  - Check: SSL/TLS > Edge Certificates
  - Status should show: "Active Certificate"

- [ ] **Test HTTPS access**
  ```bash
  curl -I https://pgvctor.jackcwf.com
  # Expected: 200 OK with proper headers
  ```

### 4. Caching Configuration

- [ ] **Set up Page Rules** (Free plan: 3 rules)

  **Rule 1: Cache Static Assets** (Highest priority)
  ```
  URL: *pgvctor.jackcwf.com/assets/*
  Settings:
    - Cache Level: Cache Everything
    - Edge Cache TTL: 1 month
    - Browser Cache TTL: 1 month
  ```

  **Rule 2: Bypass API Cache** (Medium priority)
  ```
  URL: *pgvctor.jackcwf.com/api/*
  Settings:
    - Cache Level: Bypass
    - Disable Performance
  ```

  **Rule 3: HTML Caching** (Lowest priority)
  ```
  URL: *pgvctor.jackcwf.com/*
  Settings:
    - Cache Level: Standard
    - Browser Cache TTL: 2 hours
    - Edge Cache TTL: 2 hours
  ```

- [ ] **Configure cache settings**
  - Navigate to: Caching > Configuration
  - Browser Cache TTL: Respect Existing Headers
  - Enable: Crawler Hints
  - Enable: Always Online

### 5. Performance Optimization

- [ ] **Enable speed optimizations**
  - Navigate to: Speed > Optimization
  - Enable: Auto Minify (JavaScript, CSS, HTML)
  - Enable: Brotli Compression
  - Enable: HTTP/2
  - Enable: HTTP/3 (with QUIC)
  - Enable: 0-RTT Connection Resumption
  - Enable: Early Hints
  - Disable: Rocket Loader (conflicts with React)

- [ ] **Configure web analytics** (optional)
  - Navigate to: Analytics & Logs > Web Analytics
  - Enable: Cloudflare Web Analytics
  - Copy tracking script to frontend

### 6. Security Configuration

- [ ] **Configure security settings**
  - Navigate to: Security > Settings
  - Security Level: Medium
  - Challenge Passage: 30 minutes
  - Enable: Bot Fight Mode (free plan)
  - Enable: Browser Integrity Check

- [ ] **Set up firewall rules** (optional, Pro plan)
  - Block countries if needed
  - Rate limiting rules
  - Challenge rules

---

## Deployment Phase

### 1. Deploy to Production

- [ ] **Push to production server**
  ```bash
  # If using Docker registry
  docker tag langchain-ai-chat:cdn-optimized registry.example.com/langchain-ai-chat:latest
  docker push registry.example.com/langchain-ai-chat:latest

  # If using Coolify
  git push origin main
  # Coolify will auto-deploy
  ```

- [ ] **Verify deployment**
  ```bash
  # Check container status
  docker ps | grep langchain-ai-chat

  # Check logs
  docker logs <container-id>
  ```

### 2. Verify CDN Integration

- [ ] **Run verification script**
  ```bash
  bash scripts/deploy/verify-cdn-deployment.sh https://pgvctor.jackcwf.com
  ```

- [ ] **Manual verification**
  ```bash
  # Check Cloudflare headers
  curl -I https://pgvctor.jackcwf.com

  # Expected headers:
  # - CF-Ray: <ray-id>
  # - Server: cloudflare
  # - CF-Cache-Status: HIT (on subsequent requests)

  # Check static asset caching
  curl -I https://pgvctor.jackcwf.com/assets/index-<hash>.js

  # Expected headers:
  # - Cache-Control: public, immutable
  # - CF-Cache-Status: HIT
  ```

- [ ] **Test cache hit rate**
  ```bash
  # Make multiple requests
  for i in {1..5}; do
    curl -s -I https://pgvctor.jackcwf.com/assets/index-*.js | grep -i "cf-cache-status"
    sleep 1
  done

  # Expected: MISS on first request, then HIT on subsequent requests
  ```

---

## Verification Phase

### 1. Performance Testing

- [ ] **Run Lighthouse audit**
  ```bash
  # Install Lighthouse CLI
  npm install -g lighthouse

  # Run audit
  lighthouse https://pgvctor.jackcwf.com \
    --output html \
    --output-path ./lighthouse-report.html

  # Target scores:
  # - Performance: >90
  # - Accessibility: >95
  # - Best Practices: >95
  # - SEO: >90
  ```

- [ ] **Test with WebPageTest**
  - Visit: https://www.webpagetest.org
  - Enter URL: https://pgvctor.jackcwf.com
  - Test from multiple locations: US, EU, Asia
  - Review:
    - Waterfall chart
    - Filmstrip view
    - Core Web Vitals

- [ ] **Verify Core Web Vitals**
  - Open Chrome DevTools
  - Navigate to: Lighthouse > Performance
  - Check:
    - LCP < 2.5s
    - FID < 100ms
    - CLS < 0.1

### 2. Functional Testing

- [ ] **Test frontend functionality**
  - [ ] Page loads correctly
  - [ ] Navigation works (React Router)
  - [ ] Chat interface responds
  - [ ] API requests succeed
  - [ ] WebSocket connection works
  - [ ] File uploads work
  - [ ] Export functionality works

- [ ] **Test API endpoints**
  ```bash
  # Health check
  curl https://pgvctor.jackcwf.com/api/health

  # Analytics endpoint
  curl -X POST https://pgvctor.jackcwf.com/api/analytics/performance \
    -H "Content-Type: application/json" \
    -d '{"name":"LCP","value":2150,"rating":"good","timestamp":1700000000000,"url":"https://pgvctor.jackcwf.com/"}'
  ```

### 3. Security Testing

- [ ] **Check SSL/TLS configuration**
  - Visit: https://www.ssllabs.com/ssltest/
  - Enter domain: pgvctor.jackcwf.com
  - Target grade: A or A+

- [ ] **Verify security headers**
  ```bash
  curl -I https://pgvctor.jackcwf.com | grep -i "x-"

  # Expected headers:
  # - X-Content-Type-Options: nosniff
  # - X-Frame-Options: SAMEORIGIN
  # - X-XSS-Protection: 1; mode=block
  ```

- [ ] **Test CORS configuration**
  ```bash
  curl -X OPTIONS https://pgvctor.jackcwf.com/api/conversations \
    -H "Origin: https://pgvctor.jackcwf.com" \
    -H "Access-Control-Request-Method: POST"

  # Should return CORS headers
  ```

---

## Monitoring Phase

### 1. Set Up Monitoring

- [ ] **Enable Cloudflare Analytics**
  - Navigate to: Analytics & Logs
  - Review:
    - Traffic volume
    - Cache hit rate
    - Bandwidth savings
    - Top requests

- [ ] **Set up performance monitoring**
  - Install web-vitals in frontend:
    ```bash
    cd frontend
    npm install web-vitals
    ```
  - Add performance monitoring to main.tsx
  - Verify metrics are being sent to backend

- [ ] **Configure alerts** (optional, Pro plan)
  - High error rate (>5%)
  - Slow response time (>3s)
  - Low cache hit rate (<80%)

### 2. Create Performance Dashboard

- [ ] **Set up Prometheus metrics** (if using)
  - Add frontend performance histogram
  - Track cache hit rate
  - Monitor API response times

- [ ] **Create Grafana dashboard** (if using)
  - Frontend performance panel
  - Backend performance panel
  - Cache statistics panel

---

## Post-Deployment Phase

### 1. Performance Optimization

- [ ] **Review bundle analyzer**
  - Open dist/stats.html
  - Identify large dependencies
  - Consider lazy loading or code splitting

- [ ] **Optimize images** (if any)
  - Convert to WebP format
  - Compress images
  - Use responsive images

- [ ] **Review performance metrics**
  - Check analytics dashboard
  - Identify slow pages
  - Optimize bottlenecks

### 2. Cache Optimization

- [ ] **Review cache hit rate**
  - Target: >80% cache hit rate
  - Identify cache misses
  - Adjust cache rules if needed

- [ ] **Purge cache if needed**
  - Navigate to: Caching > Configuration
  - Click: Purge Everything (only if necessary)

### 3. Documentation

- [ ] **Update deployment documentation**
  - Document CDN configuration
  - Document performance optimizations
  - Document monitoring setup

- [ ] **Create runbook**
  - How to deploy updates
  - How to purge CDN cache
  - How to troubleshoot issues

---

## Troubleshooting Guide

### Issue: CDN not serving content

**Symptoms:** No CF-Ray header, CF-Cache-Status missing

**Solutions:**
1. Verify DNS is proxied (orange cloud icon)
2. Check nameservers are updated at registrar
3. Wait for DNS propagation (up to 48 hours)
4. Clear Cloudflare cache

### Issue: Cache not working

**Symptoms:** CF-Cache-Status: BYPASS on all requests

**Solutions:**
1. Check Page Rules order (most specific first)
2. Verify URL patterns match exactly
3. Check origin server cache headers (Nginx)
4. Enable "Cache Everything" in Page Rule

### Issue: SSL errors

**Symptoms:** NET::ERR_CERT_AUTHORITY_INVALID

**Solutions:**
1. Wait for SSL certificate issuance (5-15 minutes)
2. Check SSL/TLS mode (should be "Full (strict)")
3. Verify origin server has valid SSL certificate

### Issue: High bundle sizes

**Symptoms:** Main bundle >1MB, slow initial load

**Solutions:**
1. Run bundle analyzer
2. Identify large dependencies
3. Consider lazy loading: React.lazy() and Suspense
4. Remove unused dependencies

### Issue: Poor Web Vitals scores

**Symptoms:** LCP >2.5s, CLS >0.1, FID >100ms

**Solutions:**
- **LCP:** Optimize largest image/element, preload critical resources
- **CLS:** Reserve space for dynamic content, avoid layout shifts
- **FID:** Reduce JavaScript execution time, split long tasks

---

## Cost Tracking

### Monthly Cost Estimate (Cloudflare Free Plan)

| Service | Cost | Notes |
|---------|------|-------|
| Cloudflare CDN | $0 | Unlimited bandwidth |
| Cloudflare SSL | $0 | Automatic SSL certificates |
| Cloudflare DDoS Protection | $0 | Included |
| DNS Management | $0 | Included |
| **Total** | **$0** | Best value option |

### When to Upgrade to Pro ($20/month)

Consider upgrading when you need:
- Web Application Firewall (WAF)
- Image optimization
- Mobile acceleration
- Prioritized email support
- Advanced cache analytics

---

## Success Criteria

### Performance Targets

- [ ] **Core Web Vitals**
  - LCP < 2.5s
  - FID < 100ms
  - CLS < 0.1

- [ ] **Load Times**
  - TTFB < 800ms
  - FCP < 1.8s
  - TTI < 3.8s

- [ ] **Lighthouse Scores**
  - Performance: >90
  - Best Practices: >95
  - Accessibility: >95
  - SEO: >90

### CDN Performance

- [ ] **Cache Hit Rate**
  - Target: >80%
  - Static assets: >95%
  - HTML pages: >60%

- [ ] **Bandwidth Savings**
  - Target: >70% reduction
  - Compression: >60% file size reduction

### API Performance

- [ ] **Response Times**
  - P50 < 200ms
  - P95 < 500ms
  - P99 < 1000ms

---

## Next Steps

After successful deployment:

1. **Monitor performance** for 1 week
2. **Collect user feedback** on load times
3. **Review analytics** and identify optimization opportunities
4. **Iterate on performance** improvements
5. **Document lessons learned**

---

**Document Version:** 1.0
**Last Updated:** 2025-11-21
**Estimated Time:** 4-6 hours
