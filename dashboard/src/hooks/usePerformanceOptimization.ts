import { useCallback, useRef, useMemo, useEffect } from 'react'

// Debounce hook for performance optimization
export const useDebounce = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T => {
  const timeoutRef = useRef<NodeJS.Timeout>()

  const debouncedCallback = useCallback((...args: Parameters<T>) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      callback(...args)
    }, delay)
  }, [callback, delay]) as T

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return debouncedCallback
}

// Throttle hook for performance optimization
export const useThrottle = <T extends (...args: any[]) => any>(
  callback: T,
  delay: number
): T => {
  const lastCallRef = useRef<number>(0)
  const timeoutRef = useRef<NodeJS.Timeout>()

  const throttledCallback = useCallback((...args: Parameters<T>) => {
    const now = Date.now()
    const timeSinceLastCall = now - lastCallRef.current

    if (timeSinceLastCall >= delay) {
      lastCallRef.current = now
      callback(...args)
    } else {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
      
      timeoutRef.current = setTimeout(() => {
        lastCallRef.current = Date.now()
        callback(...args)
      }, delay - timeSinceLastCall)
    }
  }, [callback, delay]) as T

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return throttledCallback
}

// Memoization with custom equality check
export const useMemoWithComparison = <T>(
  factory: () => T,
  deps: React.DependencyList,
  compare?: (prev: React.DependencyList, next: React.DependencyList) => boolean
): T => {
  const prevDepsRef = useRef<React.DependencyList>()
  const memoizedValueRef = useRef<T>()

  const defaultCompare = (prev: React.DependencyList, next: React.DependencyList) => {
    if (prev.length !== next.length) return false
    return prev.every((item, index) => Object.is(item, next[index]))
  }

  const compareFunction = compare || defaultCompare

  if (!prevDepsRef.current || !compareFunction(prevDepsRef.current, deps)) {
    memoizedValueRef.current = factory()
    prevDepsRef.current = deps
  }

  return memoizedValueRef.current!
}

// Batch updates for better performance
export const useBatchedUpdates = () => {
  const batchRef = useRef<Array<() => void>>([])
  const timeoutRef = useRef<NodeJS.Timeout>()

  const batchUpdate = useCallback((updateFn: () => void) => {
    batchRef.current.push(updateFn)

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      const updates = batchRef.current.splice(0)
      updates.forEach(update => update())
    }, 0)
  }, [])

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return batchUpdate
}

// Intersection Observer hook for lazy loading
export const useIntersectionObserver = (
  options: IntersectionObserverInit = {}
) => {
  const elementRef = useRef<HTMLElement>(null)
  const observerRef = useRef<IntersectionObserver>()
  const callbackRef = useRef<(entry: IntersectionObserverEntry) => void>()

  const observe = useCallback((callback: (entry: IntersectionObserverEntry) => void) => {
    callbackRef.current = callback

    if (elementRef.current && !observerRef.current) {
      observerRef.current = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (callbackRef.current) {
              callbackRef.current(entry)
            }
          })
        },
        {
          threshold: 0.1,
          rootMargin: '50px',
          ...options
        }
      )

      observerRef.current.observe(elementRef.current)
    }
  }, [options])

  const unobserve = useCallback(() => {
    if (observerRef.current && elementRef.current) {
      observerRef.current.unobserve(elementRef.current)
    }
  }, [])

  useEffect(() => {
    return () => {
      if (observerRef.current) {
        observerRef.current.disconnect()
      }
    }
  }, [])

  return { elementRef, observe, unobserve }
}

// Memory usage monitoring
export const useMemoryMonitor = () => {
  const getMemoryUsage = useCallback(() => {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      return {
        usedJSHeapSize: memory.usedJSHeapSize,
        totalJSHeapSize: memory.totalJSHeapSize,
        jsHeapSizeLimit: memory.jsHeapSizeLimit,
        usagePercentage: (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100
      }
    }
    return null
  }, [])

  const logMemoryUsage = useCallback((label?: string) => {
    const usage = getMemoryUsage()
    if (usage) {
      console.log(`Memory Usage${label ? ` (${label})` : ''}:`, {
        used: `${(usage.usedJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
        total: `${(usage.totalJSHeapSize / 1024 / 1024).toFixed(2)} MB`,
        limit: `${(usage.jsHeapSizeLimit / 1024 / 1024).toFixed(2)} MB`,
        percentage: `${usage.usagePercentage.toFixed(2)}%`
      })
    }
  }, [getMemoryUsage])

  return { getMemoryUsage, logMemoryUsage }
}

// Performance timing hook
export const usePerformanceTiming = () => {
  const timingsRef = useRef<Map<string, number>>(new Map())

  const startTiming = useCallback((label: string) => {
    timingsRef.current.set(label, performance.now())
  }, [])

  const endTiming = useCallback((label: string) => {
    const startTime = timingsRef.current.get(label)
    if (startTime) {
      const duration = performance.now() - startTime
      timingsRef.current.delete(label)
      return duration
    }
    return null
  }, [])

  const measureTiming = useCallback(<T>(label: string, fn: () => T): T => {
    startTiming(label)
    const result = fn()
    const duration = endTiming(label)
    
    if (process.env.NODE_ENV === 'development' && duration !== null) {
      console.log(`Performance: ${label} took ${duration.toFixed(2)}ms`)
    }
    
    return result
  }, [startTiming, endTiming])

  return { startTiming, endTiming, measureTiming }
}