import React from 'react'

/**
 * Monitoring and Analytics Utilities
 * 
 * Provides comprehensive monitoring, error tracking, and analytics
 * for the Environment Allocation UI components.
 */

// Performance monitoring
export interface PerformanceMetrics {
  pageLoadTime: number
  apiResponseTime: number
  renderTime: number
  memoryUsage: number
  errorCount: number
  userInteractions: number
}

// User analytics events
export interface AnalyticsEvent {
  event: string
  category: string
  action: string
  label?: string
  value?: number
  customProperties?: Record<string, any>
}

// Error tracking
export interface ErrorEvent {
  error: Error
  context: {
    component?: string
    action?: string
    userId?: string
    sessionId?: string
    timestamp: Date
    userAgent: string
    url: string
  }
  severity: 'low' | 'medium' | 'high' | 'critical'
}

class MonitoringService {
  private static instance: MonitoringService
  private performanceObserver?: PerformanceObserver
  private errorCount = 0
  private sessionId: string
  private userId?: string

  constructor() {
    this.sessionId = this.generateSessionId()
    this.initializePerformanceMonitoring()
    this.initializeErrorTracking()
  }

  static getInstance(): MonitoringService {
    if (!MonitoringService.instance) {
      MonitoringService.instance = new MonitoringService()
    }
    return MonitoringService.instance
  }

  private generateSessionId(): string {
    return `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }

  setUserId(userId: string): void {
    this.userId = userId
  }

  // Performance Monitoring
  private initializePerformanceMonitoring(): void {
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      this.performanceObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries()
        entries.forEach((entry) => {
          this.handlePerformanceEntry(entry)
        })
      })

      this.performanceObserver.observe({ 
        entryTypes: ['navigation', 'paint', 'measure', 'resource'] 
      })
    }
  }

  private handlePerformanceEntry(entry: PerformanceEntry): void {
    const metrics: Partial<PerformanceMetrics> = {}

    switch (entry.entryType) {
      case 'navigation':
        const navEntry = entry as PerformanceNavigationTiming
        metrics.pageLoadTime = navEntry.loadEventEnd - navEntry.fetchStart
        break

      case 'paint':
        if (entry.name === 'first-contentful-paint') {
          metrics.renderTime = entry.startTime
        }
        break

      case 'measure':
        if (entry.name.startsWith('api-')) {
          metrics.apiResponseTime = entry.duration
        }
        break

      case 'resource':
        // Track resource loading times
        if (entry.duration > 1000) { // Slow resource
          this.trackEvent({
            event: 'slow_resource',
            category: 'performance',
            action: 'resource_load',
            label: entry.name,
            value: entry.duration
          })
        }
        break
    }

    if (Object.keys(metrics).length > 0) {
      this.reportPerformanceMetrics(metrics)
    }
  }

  measureApiCall<T>(
    apiName: string, 
    apiCall: () => Promise<T>
  ): Promise<T> {
    const measureName = `api-${apiName}`
    performance.mark(`${measureName}-start`)

    return apiCall()
      .then((result) => {
        performance.mark(`${measureName}-end`)
        performance.measure(measureName, `${measureName}-start`, `${measureName}-end`)
        return result
      })
      .catch((error) => {
        performance.mark(`${measureName}-end`)
        performance.measure(measureName, `${measureName}-start`, `${measureName}-end`)
        
        this.trackError(error, {
          component: 'API',
          action: apiName,
          userId: this.userId,
          sessionId: this.sessionId,
          timestamp: new Date(),
          userAgent: navigator.userAgent,
          url: window.location.href
        }, 'high')
        
        throw error
      })
  }

  private reportPerformanceMetrics(metrics: Partial<PerformanceMetrics>): void {
    // Send to analytics service
    if (process.env.REACT_APP_ANALYTICS_ENABLED === 'true') {
      this.sendToAnalytics('performance_metrics', {
        ...metrics,
        sessionId: this.sessionId,
        userId: this.userId,
        timestamp: Date.now()
      })
    }

    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.log('Performance Metrics:', metrics)
    }
  }

  // Error Tracking
  private initializeErrorTracking(): void {
    if (typeof window !== 'undefined') {
      window.addEventListener('error', (event) => {
        this.trackError(event.error, {
          component: 'Global',
          action: 'unhandled_error',
          userId: this.userId,
          sessionId: this.sessionId,
          timestamp: new Date(),
          userAgent: navigator.userAgent,
          url: window.location.href
        }, 'critical')
      })

      window.addEventListener('unhandledrejection', (event) => {
        this.trackError(new Error(event.reason), {
          component: 'Global',
          action: 'unhandled_promise_rejection',
          userId: this.userId,
          sessionId: this.sessionId,
          timestamp: new Date(),
          userAgent: navigator.userAgent,
          url: window.location.href
        }, 'high')
      })
    }
  }

  trackError(
    error: Error, 
    context: ErrorEvent['context'], 
    severity: ErrorEvent['severity'] = 'medium'
  ): void {
    this.errorCount++

    const errorEvent: ErrorEvent = {
      error,
      context,
      severity
    }

    // Send to error tracking service (e.g., Sentry)
    if (process.env.REACT_APP_SENTRY_DSN) {
      this.sendToSentry(errorEvent)
    }

    // Send to custom analytics
    this.trackEvent({
      event: 'error',
      category: 'error',
      action: context.action || 'unknown',
      label: error.message,
      customProperties: {
        severity,
        component: context.component,
        stack: error.stack,
        sessionId: this.sessionId,
        userId: this.userId
      }
    })

    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.error('Tracked Error:', errorEvent)
    }
  }

  private sendToSentry(errorEvent: ErrorEvent): void {
    // Integration with Sentry or similar service
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.captureException(errorEvent.error, {
        tags: {
          component: errorEvent.context.component,
          action: errorEvent.context.action,
          severity: errorEvent.severity
        },
        user: {
          id: this.userId,
          session_id: this.sessionId
        },
        extra: errorEvent.context
      })
    }
  }

  // Analytics Tracking
  trackEvent(event: AnalyticsEvent): void {
    // Add session context
    const enrichedEvent = {
      ...event,
      sessionId: this.sessionId,
      userId: this.userId,
      timestamp: Date.now(),
      url: window.location.href
    }

    // Send to analytics service
    this.sendToAnalytics(event.event, enrichedEvent)

    // Log in development
    if (process.env.NODE_ENV === 'development') {
      console.log('Analytics Event:', enrichedEvent)
    }
  }

  trackUserInteraction(
    component: string, 
    action: string, 
    label?: string, 
    value?: number
  ): void {
    this.trackEvent({
      event: 'user_interaction',
      category: 'ui',
      action: `${component}_${action}`,
      label,
      value,
      customProperties: {
        component,
        sessionId: this.sessionId
      }
    })
  }

  trackPageView(page: string, title?: string): void {
    this.trackEvent({
      event: 'page_view',
      category: 'navigation',
      action: 'page_view',
      label: page,
      customProperties: {
        title,
        referrer: document.referrer,
        sessionId: this.sessionId
      }
    })
  }

  trackFeatureUsage(feature: string, details?: Record<string, any>): void {
    this.trackEvent({
      event: 'feature_usage',
      category: 'feature',
      action: feature,
      customProperties: {
        ...details,
        sessionId: this.sessionId
      }
    })
  }

  private sendToAnalytics(eventName: string, data: any): void {
    // Google Analytics 4
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', eventName, data)
    }

    // Custom analytics endpoint
    if (process.env.REACT_APP_ANALYTICS_ENDPOINT) {
      fetch(process.env.REACT_APP_ANALYTICS_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event: eventName,
          data,
          timestamp: Date.now()
        })
      }).catch((error) => {
        console.warn('Failed to send analytics:', error)
      })
    }
  }

  // Health Monitoring
  getHealthMetrics(): {
    errorCount: number
    sessionDuration: number
    memoryUsage?: number
    performanceScore: number
  } {
    const sessionDuration = Date.now() - parseInt(this.sessionId.split('-')[1])
    
    let memoryUsage: number | undefined
    if ('memory' in performance) {
      const memory = (performance as any).memory
      memoryUsage = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
    }

    // Calculate performance score based on various metrics
    let performanceScore = 100
    if (this.errorCount > 0) performanceScore -= this.errorCount * 10
    if (memoryUsage && memoryUsage > 80) performanceScore -= 20
    
    return {
      errorCount: this.errorCount,
      sessionDuration,
      memoryUsage,
      performanceScore: Math.max(0, performanceScore)
    }
  }

  // A/B Testing Support
  trackExperiment(experimentName: string, variant: string, outcome?: string): void {
    this.trackEvent({
      event: 'experiment',
      category: 'ab_test',
      action: experimentName,
      label: variant,
      customProperties: {
        outcome,
        sessionId: this.sessionId
      }
    })
  }

  // Real-time Monitoring
  startRealTimeMonitoring(): void {
    // Monitor every 30 seconds
    setInterval(() => {
      const healthMetrics = this.getHealthMetrics()
      
      if (healthMetrics.performanceScore < 50) {
        this.trackEvent({
          event: 'performance_degradation',
          category: 'performance',
          action: 'health_check',
          value: healthMetrics.performanceScore,
          customProperties: healthMetrics
        })
      }
    }, 30000)
  }

  // Cleanup
  destroy(): void {
    if (this.performanceObserver) {
      this.performanceObserver.disconnect()
    }
  }
}

// Export singleton instance
export const monitoring = MonitoringService.getInstance()

// React hook for easy integration
export const useMonitoring = () => {
  return {
    trackEvent: monitoring.trackEvent.bind(monitoring),
    trackError: monitoring.trackError.bind(monitoring),
    trackUserInteraction: monitoring.trackUserInteraction.bind(monitoring),
    trackPageView: monitoring.trackPageView.bind(monitoring),
    trackFeatureUsage: monitoring.trackFeatureUsage.bind(monitoring),
    measureApiCall: monitoring.measureApiCall.bind(monitoring),
    getHealthMetrics: monitoring.getHealthMetrics.bind(monitoring)
  }
}

// Higher-order component for automatic monitoring
export const withMonitoring = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  componentName: string
) => {
  const MonitoredComponent: React.FC<P> = (props) => {
    React.useEffect(() => {
      monitoring.trackEvent({
        event: 'component_mount',
        category: 'component',
        action: 'mount',
        label: componentName
      })

      return () => {
        monitoring.trackEvent({
          event: 'component_unmount',
          category: 'component',
          action: 'unmount',
          label: componentName
        })
      }
    }, [])

    return React.createElement(WrappedComponent, props)
  }

  MonitoredComponent.displayName = `withMonitoring(${componentName})`
  return MonitoredComponent
}

export default monitoring