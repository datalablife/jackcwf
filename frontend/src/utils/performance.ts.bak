/**
 * Web Vitals monitoring and reporting
 *
 * Tracks Core Web Vitals and custom performance metrics:
 * - LCP (Largest Contentful Paint)
 * - FID (First Input Delay)
 * - CLS (Cumulative Layout Shift)
 * - FCP (First Contentful Paint)
 * - TTFB (Time to First Byte)
 * - Long Tasks (tasks taking >50ms)
 *
 * Usage:
 * ```typescript
 * import { initPerformanceMonitoring } from './utils/performance'
 *
 * // In main.tsx
 * if (import.meta.env.PROD) {
 *   initPerformanceMonitoring()
 * }
 * ```
 */

import { onCLS, onFID, onLCP, onFCP, onTTFB } from 'web-vitals'

export interface PerformanceMetric {
  name: string
  value: number
  rating: 'good' | 'needs-improvement' | 'poor'
  timestamp: number
  url: string
  userAgent?: string
}

// Metric thresholds (based on Web Vitals recommendations)
const THRESHOLDS = {
  LCP: { good: 2500, poor: 4000 }, // ms
  FID: { good: 100, poor: 300 }, // ms
  CLS: { good: 0.1, poor: 0.25 }, // score
  FCP: { good: 1800, poor: 3000 }, // ms
  TTFB: { good: 800, poor: 1800 }, // ms
  LongTask: { good: 50, poor: 200 }, // ms
}

/**
 * Determine performance rating based on thresholds
 */
function getRating(name: string, value: number): 'good' | 'needs-improvement' | 'poor' {
  const threshold = THRESHOLDS[name as keyof typeof THRESHOLDS]
  if (!threshold) return 'good'

  if (value <= threshold.good) return 'good'
  if (value <= threshold.poor) return 'needs-improvement'
  return 'poor'
}

/**
 * Send metric to analytics backend
 */
function sendToAnalytics(metric: PerformanceMetric) {
  // Send to backend analytics endpoint
  const endpoint = '/api/analytics/performance'

  fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(metric),
    keepalive: true, // Ensure sent even if page is unloading
  }).catch((error) => {
    console.error('[Performance] Failed to send metric:', error)
  })

  // Log to console in development
  if (import.meta.env.DEV) {
    const emoji = metric.rating === 'good' ? '✅' : metric.rating === 'needs-improvement' ? '⚠️' : '❌'
    console.log(`[Performance] ${emoji} ${metric.name}:`, {
      value: metric.value,
      rating: metric.rating,
    })
  }
}

/**
 * Initialize Core Web Vitals monitoring
 */
export function initPerformanceMonitoring() {
  // LCP (Largest Contentful Paint)
  onLCP((metric) => {
    sendToAnalytics({
      name: 'LCP',
      value: metric.value,
      rating: getRating('LCP', metric.value),
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    })
  })

  // FID (First Input Delay)
  onFID((metric) => {
    sendToAnalytics({
      name: 'FID',
      value: metric.value,
      rating: getRating('FID', metric.value),
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    })
  })

  // CLS (Cumulative Layout Shift)
  onCLS((metric) => {
    sendToAnalytics({
      name: 'CLS',
      value: metric.value,
      rating: getRating('CLS', metric.value),
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    })
  })

  // FCP (First Contentful Paint)
  onFCP((metric) => {
    sendToAnalytics({
      name: 'FCP',
      value: metric.value,
      rating: getRating('FCP', metric.value),
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    })
  })

  // TTFB (Time to First Byte)
  onTTFB((metric) => {
    sendToAnalytics({
      name: 'TTFB',
      value: metric.value,
      rating: getRating('TTFB', metric.value),
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    })
  })
}

/**
 * Analyze resource timing data
 */
export function analyzeResourceTimings() {
  if (!window.performance || !window.performance.getEntriesByType) {
    console.warn('[Performance] Resource Timing API not supported')
    return
  }

  const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[]

  const analysis = {
    total: resources.length,
    byType: {} as Record<string, number>,
    slowResources: [] as Array<{ name: string; duration: number; type: string }>,
    totalSize: 0,
  }

  resources.forEach((resource) => {
    // Count by type
    const type = resource.initiatorType
    analysis.byType[type] = (analysis.byType[type] || 0) + 1

    // Track slow resources (>1s)
    if (resource.duration > 1000) {
      analysis.slowResources.push({
        name: resource.name,
        duration: Math.round(resource.duration),
        type: resource.initiatorType,
      })
    }

    // Sum transfer sizes
    if ('transferSize' in resource) {
      analysis.totalSize += (resource as PerformanceResourceTiming).transferSize
    }
  })

  console.log('[Performance] Resource Analysis:', {
    total: analysis.total,
    byType: analysis.byType,
    slowResources: analysis.slowResources,
    totalSize: `${(analysis.totalSize / 1024 / 1024).toFixed(2)} MB`,
  })

  return analysis
}

/**
 * Observe Long Tasks (tasks blocking main thread for >50ms)
 */
export function observeLongTasks() {
  if (!('PerformanceObserver' in window)) {
    console.warn('[Performance] PerformanceObserver not supported')
    return
  }

  try {
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        console.warn('[Performance] Long Task detected:', {
          duration: Math.round(entry.duration),
          startTime: Math.round(entry.startTime),
        })

        // Report long tasks to analytics
        sendToAnalytics({
          name: 'LongTask',
          value: entry.duration,
          rating: getRating('LongTask', entry.duration),
          timestamp: Date.now(),
          url: window.location.href,
        })
      }
    })

    observer.observe({ entryTypes: ['longtask'] })
  } catch (error) {
    console.error('[Performance] Failed to observe long tasks:', error)
  }
}

/**
 * Measure custom timing (e.g., component render time)
 */
export function measureCustomTiming(name: string, startMark: string, endMark: string) {
  if (!window.performance || !window.performance.measure) {
    return
  }

  try {
    performance.measure(name, startMark, endMark)
    const measure = performance.getEntriesByName(name)[0] as PerformanceMeasure

    console.log(`[Performance] Custom Timing (${name}):`, {
      duration: Math.round(measure.duration),
    })

    // Clean up marks
    performance.clearMarks(startMark)
    performance.clearMarks(endMark)
    performance.clearMeasures(name)

    return measure.duration
  } catch (error) {
    console.error(`[Performance] Failed to measure ${name}:`, error)
  }
}

/**
 * Mark a performance timing point
 */
export function markPerformance(name: string) {
  if (window.performance && window.performance.mark) {
    performance.mark(name)
  }
}

/**
 * Get Navigation Timing metrics
 */
export function getNavigationTimings() {
  if (!window.performance || !window.performance.timing) {
    console.warn('[Performance] Navigation Timing API not supported')
    return
  }

  const timing = performance.timing
  const navigation = {
    // Time to first byte
    ttfb: timing.responseStart - timing.fetchStart,
    // DNS lookup time
    dns: timing.domainLookupEnd - timing.domainLookupStart,
    // TCP connection time
    tcp: timing.connectEnd - timing.connectStart,
    // Request time
    request: timing.responseEnd - timing.requestStart,
    // DOM processing time
    domProcessing: timing.domComplete - timing.domLoading,
    // DOM Content Loaded
    domContentLoaded: timing.domContentLoadedEventEnd - timing.fetchStart,
    // Full page load
    pageLoad: timing.loadEventEnd - timing.fetchStart,
  }

  console.log('[Performance] Navigation Timings:', navigation)
  return navigation
}

/**
 * Create a performance budget checker
 */
export function checkPerformanceBudget(budgets: Record<string, number>) {
  const analysis = analyzeResourceTimings()
  const violations: string[] = []

  if (analysis) {
    // Check total size budget
    if (budgets.totalSize && analysis.totalSize > budgets.totalSize) {
      violations.push(
        `Total size (${(analysis.totalSize / 1024 / 1024).toFixed(2)}MB) exceeds budget (${(budgets.totalSize / 1024 / 1024).toFixed(2)}MB)`
      )
    }

    // Check resource count budgets
    Object.entries(budgets).forEach(([type, budget]) => {
      if (type !== 'totalSize' && analysis.byType[type] > budget) {
        violations.push(`${type} count (${analysis.byType[type]}) exceeds budget (${budget})`)
      }
    })
  }

  if (violations.length > 0) {
    console.warn('[Performance] Budget violations:', violations)
  }

  return violations
}

/**
 * Log all performance metrics (for debugging)
 */
export function logAllMetrics() {
  console.group('[Performance] All Metrics')
  getNavigationTimings()
  analyzeResourceTimings()
  console.groupEnd()
}
