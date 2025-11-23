/**
 * Performance Monitoring Integration Example
 *
 * This file demonstrates how to integrate performance monitoring
 * into your React application.
 *
 * Copy the relevant parts to your src/main.tsx file.
 */

import { StrictMode, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

// Import performance monitoring utilities
import {
  initPerformanceMonitoring,
  observeLongTasks,
  analyzeResourceTimings,
  getNavigationTimings,
  markPerformance,
} from './utils/performance'

/**
 * Initialize performance monitoring in production
 */
if (import.meta.env.PROD) {
  // Core Web Vitals monitoring
  initPerformanceMonitoring()

  // Long task detection
  observeLongTasks()

  // Log navigation timings after page load
  window.addEventListener('load', () => {
    setTimeout(() => {
      getNavigationTimings()
      analyzeResourceTimings()
    }, 1000)
  })
}

/**
 * Mark performance milestones
 */
markPerformance('app-start')

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
)

markPerformance('app-render')

/**
 * Optional: Create a custom hook for component-level performance tracking
 *
 * Usage:
 * ```tsx
 * function MyComponent() {
 *   usePerformanceTracking('MyComponent')
 *   return <div>...</div>
 * }
 * ```
 */
export function usePerformanceTracking(componentName: string) {
  useEffect(() => {
    const startMark = `${componentName}-mount-start`
    const endMark = `${componentName}-mount-end`

    markPerformance(startMark)

    return () => {
      markPerformance(endMark)

      if (window.performance && window.performance.measure) {
        try {
          performance.measure(`${componentName}-mount`, startMark, endMark)
          const measure = performance.getEntriesByName(`${componentName}-mount`)[0]

          if (import.meta.env.DEV) {
            console.log(`[Performance] ${componentName} mount time:`, {
              duration: Math.round(measure.duration),
            })
          }

          // Clean up
          performance.clearMarks(startMark)
          performance.clearMarks(endMark)
          performance.clearMeasures(`${componentName}-mount`)
        } catch (error) {
          // Ignore errors
        }
      }
    }
  }, [componentName])
}

/**
 * Optional: Track API request performance
 *
 * Usage:
 * ```tsx
 * import { trackApiPerformance } from './main'
 *
 * const data = await trackApiPerformance(
 *   'fetchConversations',
 *   fetch('/api/conversations')
 * )
 * ```
 */
export async function trackApiPerformance<T>(
  name: string,
  promise: Promise<T>
): Promise<T> {
  const startMark = `api-${name}-start`
  const endMark = `api-${name}-end`

  markPerformance(startMark)

  try {
    const result = await promise
    markPerformance(endMark)

    if (window.performance && window.performance.measure) {
      try {
        performance.measure(`api-${name}`, startMark, endMark)
        const measure = performance.getEntriesByName(`api-${name}`)[0]

        if (import.meta.env.DEV) {
          console.log(`[Performance] API ${name}:`, {
            duration: Math.round(measure.duration),
          })
        }

        // Send to analytics in production
        if (import.meta.env.PROD && measure.duration > 500) {
          fetch('/api/analytics/performance', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              name: `API_${name}`,
              value: measure.duration,
              rating: measure.duration < 200 ? 'good' : measure.duration < 500 ? 'needs-improvement' : 'poor',
              timestamp: Date.now(),
              url: window.location.href,
            }),
            keepalive: true,
          }).catch(() => {})
        }

        // Clean up
        performance.clearMarks(startMark)
        performance.clearMarks(endMark)
        performance.clearMeasures(`api-${name}`)
      } catch (error) {
        // Ignore errors
      }
    }

    return result
  } catch (error) {
    markPerformance(endMark)
    throw error
  }
}

/**
 * Optional: Add global error tracking
 */
if (import.meta.env.PROD) {
  window.addEventListener('error', (event) => {
    console.error('[Error]', event.error)

    // Send to analytics
    fetch('/api/analytics/error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: event.error?.message || 'Unknown error',
        stack: event.error?.stack,
        url: window.location.href,
        timestamp: Date.now(),
      }),
      keepalive: true,
    }).catch(() => {})
  })

  window.addEventListener('unhandledrejection', (event) => {
    console.error('[Unhandled Promise Rejection]', event.reason)

    // Send to analytics
    fetch('/api/analytics/error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: event.reason?.message || 'Unhandled rejection',
        stack: event.reason?.stack,
        url: window.location.href,
        timestamp: Date.now(),
      }),
      keepalive: true,
    }).catch(() => {})
  })
}

/**
 * Optional: Performance debugging commands for console
 */
if (import.meta.env.DEV) {
  ;(window as any).performanceDebug = {
    // Get navigation timings
    nav: () => {
      const timing = performance.timing
      return {
        dns: timing.domainLookupEnd - timing.domainLookupStart,
        tcp: timing.connectEnd - timing.connectStart,
        ttfb: timing.responseStart - timing.fetchStart,
        download: timing.responseEnd - timing.responseStart,
        domProcessing: timing.domComplete - timing.domLoading,
        total: timing.loadEventEnd - timing.fetchStart,
      }
    },

    // Get all resources
    resources: () => {
      return performance.getEntriesByType('resource').map((r: any) => ({
        name: r.name,
        type: r.initiatorType,
        duration: Math.round(r.duration),
        size: r.transferSize,
      }))
    },

    // Get all marks and measures
    marks: () => {
      return {
        marks: performance.getEntriesByType('mark').map((m) => m.name),
        measures: performance.getEntriesByType('measure').map((m: any) => ({
          name: m.name,
          duration: Math.round(m.duration),
        })),
      }
    },

    // Clear all performance data
    clear: () => {
      performance.clearMarks()
      performance.clearMeasures()
      performance.clearResourceTimings()
      console.log('Performance data cleared')
    },
  }

  console.log(
    '%c[Performance] Debug commands available:',
    'color: #0066cc; font-weight: bold;'
  )
  console.log('  performanceDebug.nav()       - Navigation timings')
  console.log('  performanceDebug.resources() - All resource timings')
  console.log('  performanceDebug.marks()     - All marks and measures')
  console.log('  performanceDebug.clear()     - Clear performance data')
}
