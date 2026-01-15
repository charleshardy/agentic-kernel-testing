// Performance monitoring and optimization utilities

interface PerformanceMetrics {
  loadTime: number;
  renderTime: number;
  interactionTime: number;
  resourceCount: number;
  memoryUsage?: number;
}

interface PerformanceThresholds {
  loadTime: number; // 2 seconds as per requirements
  renderTime: number;
  interactionTime: number;
}

const DEFAULT_THRESHOLDS: PerformanceThresholds = {
  loadTime: 2000, // 2 seconds
  renderTime: 100, // 100ms
  interactionTime: 50 // 50ms
};

class PerformanceMonitor {
  private static instance: PerformanceMonitor;
  private metrics: Map<string, PerformanceMetrics[]> = new Map();
  private thresholds: PerformanceThresholds = DEFAULT_THRESHOLDS;
  private observers: PerformanceObserver[] = [];

  private constructor() {
    this.initializeObservers();
  }

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor();
    }
    return PerformanceMonitor.instance;
  }

  private initializeObservers(): void {
    if (typeof window === 'undefined' || !window.PerformanceObserver) {
      return;
    }

    // Monitor navigation timing
    try {
      const navObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'navigation') {
            this.recordNavigationMetrics(entry as PerformanceNavigationTiming);
          }
        }
      });
      navObserver.observe({ entryTypes: ['navigation'] });
      this.observers.push(navObserver);
    } catch (e) {
      console.warn('Navigation timing observer not supported');
    }

    // Monitor resource timing
    try {
      const resourceObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (entry.entryType === 'resource') {
            this.recordResourceMetrics(entry as PerformanceResourceTiming);
          }
        }
      });
      resourceObserver.observe({ entryTypes: ['resource'] });
      this.observers.push(resourceObserver);
    } catch (e) {
      console.warn('Resource timing observer not supported');
    }

    // Monitor long tasks
    try {
      const longTaskObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          this.recordLongTask(entry);
        }
      });
      longTaskObserver.observe({ entryTypes: ['longtask'] });
      this.observers.push(longTaskObserver);
    } catch (e) {
      console.warn('Long task observer not supported');
    }
  }

  private recordNavigationMetrics(entry: PerformanceNavigationTiming): void {
    const loadTime = entry.loadEventEnd - entry.fetchStart;
    const renderTime = entry.domContentLoadedEventEnd - entry.domContentLoadedEventStart;

    const metrics: PerformanceMetrics = {
      loadTime,
      renderTime,
      interactionTime: 0,
      resourceCount: performance.getEntriesByType('resource').length
    };

    this.addMetric('navigation', metrics);

    // Check thresholds
    if (loadTime > this.thresholds.loadTime) {
      console.warn(`Page load time (${loadTime}ms) exceeds threshold (${this.thresholds.loadTime}ms)`);
    }
  }

  private recordResourceMetrics(entry: PerformanceResourceTiming): void {
    const duration = entry.duration;
    if (duration > 1000) {
      console.warn(`Slow resource load: ${entry.name} took ${duration}ms`);
    }
  }

  private recordLongTask(entry: PerformanceEntry): void {
    console.warn(`Long task detected: ${entry.duration}ms`);
  }

  private addMetric(key: string, metric: PerformanceMetrics): void {
    if (!this.metrics.has(key)) {
      this.metrics.set(key, []);
    }
    const metrics = this.metrics.get(key)!;
    metrics.push(metric);

    // Keep only last 100 metrics
    if (metrics.length > 100) {
      metrics.shift();
    }
  }

  /**
   * Measure component render time
   */
  measureRender(componentName: string, callback: () => void): void {
    const startTime = performance.now();
    callback();
    const endTime = performance.now();
    const renderTime = endTime - startTime;

    this.addMetric(`render:${componentName}`, {
      loadTime: 0,
      renderTime,
      interactionTime: 0,
      resourceCount: 0
    });

    if (renderTime > this.thresholds.renderTime) {
      console.warn(`Component ${componentName} render time (${renderTime}ms) exceeds threshold`);
    }
  }

  /**
   * Measure async operation time
   */
  async measureAsync<T>(
    operationName: string,
    operation: () => Promise<T>
  ): Promise<T> {
    const startTime = performance.now();
    try {
      const result = await operation();
      const endTime = performance.now();
      const duration = endTime - startTime;

      this.addMetric(`async:${operationName}`, {
        loadTime: duration,
        renderTime: 0,
        interactionTime: 0,
        resourceCount: 0
      });

      return result;
    } catch (error) {
      const endTime = performance.now();
      const duration = endTime - startTime;
      console.error(`Operation ${operationName} failed after ${duration}ms`, error);
      throw error;
    }
  }

  /**
   * Get metrics for a specific key
   */
  getMetrics(key: string): PerformanceMetrics[] {
    return this.metrics.get(key) || [];
  }

  /**
   * Get average metrics for a key
   */
  getAverageMetrics(key: string): PerformanceMetrics | null {
    const metrics = this.getMetrics(key);
    if (metrics.length === 0) return null;

    const sum = metrics.reduce(
      (acc, m) => ({
        loadTime: acc.loadTime + m.loadTime,
        renderTime: acc.renderTime + m.renderTime,
        interactionTime: acc.interactionTime + m.interactionTime,
        resourceCount: acc.resourceCount + m.resourceCount
      }),
      { loadTime: 0, renderTime: 0, interactionTime: 0, resourceCount: 0 }
    );

    return {
      loadTime: sum.loadTime / metrics.length,
      renderTime: sum.renderTime / metrics.length,
      interactionTime: sum.interactionTime / metrics.length,
      resourceCount: sum.resourceCount / metrics.length
    };
  }

  /**
   * Check if current performance meets thresholds
   */
  checkCompliance(): { compliant: boolean; violations: string[] } {
    const violations: string[] = [];
    const navMetrics = this.getAverageMetrics('navigation');

    if (navMetrics) {
      if (navMetrics.loadTime > this.thresholds.loadTime) {
        violations.push(
          `Average load time (${navMetrics.loadTime.toFixed(2)}ms) exceeds threshold (${this.thresholds.loadTime}ms)`
        );
      }
      if (navMetrics.renderTime > this.thresholds.renderTime) {
        violations.push(
          `Average render time (${navMetrics.renderTime.toFixed(2)}ms) exceeds threshold (${this.thresholds.renderTime}ms)`
        );
      }
    }

    return {
      compliant: violations.length === 0,
      violations
    };
  }

  /**
   * Get memory usage if available
   */
  getMemoryUsage(): number | null {
    if ('memory' in performance && (performance as any).memory) {
      return (performance as any).memory.usedJSHeapSize;
    }
    return null;
  }

  /**
   * Clear all metrics
   */
  clearMetrics(): void {
    this.metrics.clear();
  }

  /**
   * Cleanup observers
   */
  cleanup(): void {
    this.observers.forEach(observer => observer.disconnect());
    this.observers = [];
  }
}

// Export singleton instance
export const performanceMonitor = PerformanceMonitor.getInstance();

/**
 * React hook for performance monitoring
 */
export const usePerformanceMonitor = (componentName: string) => {
  return {
    measureRender: (callback: () => void) => {
      performanceMonitor.measureRender(componentName, callback);
    },
    measureAsync: <T,>(operationName: string, operation: () => Promise<T>) => {
      return performanceMonitor.measureAsync(`${componentName}:${operationName}`, operation);
    }
  };
};

/**
 * Debounce function for performance optimization
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout | null = null;

  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null;
      func(...args);
    };

    if (timeout) {
      clearTimeout(timeout);
    }
    timeout = setTimeout(later, wait);
  };
}

/**
 * Throttle function for performance optimization
 */
export function throttle<T extends (...args: any[]) => any>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle: boolean = false;

  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
}

/**
 * Lazy load component with performance tracking
 */
export function lazyLoadWithTracking<T extends React.ComponentType<any>>(
  componentName: string,
  importFunc: () => Promise<{ default: T }>
): React.LazyExoticComponent<T> {
  return React.lazy(async () => {
    const startTime = performance.now();
    try {
      const module = await importFunc();
      const endTime = performance.now();
      const loadTime = endTime - startTime;

      performanceMonitor.measureAsync(`lazy-load:${componentName}`, async () => {
        return { loadTime };
      });

      return module;
    } catch (error) {
      console.error(`Failed to lazy load ${componentName}`, error);
      throw error;
    }
  });
}

// React import for lazy loading
import React from 'react';
