/**
 * Unit tests for performance optimization hooks
 * 
 * **Feature: environment-allocation-ui, Task 14.1: Unit tests for component interactions**
 * **Validates: Requirements 1.2, 2.4**
 */

import { renderHook, act } from '@testing-library/react'
import { 
  useDebounce, 
  useThrottle, 
  useMemoWithComparison,
  useBatchedUpdates,
  useIntersectionObserver,
  useMemoryMonitor,
  usePerformanceTiming
} from '../usePerformanceOptimization'

// Mock performance API
const mockPerformance = {
  now: jest.fn(() => Date.now()),
  memory: {
    usedJSHeapSize: 50000000,
    totalJSHeapSize: 100000000,
    jsHeapSizeLimit: 200000000
  }
}

Object.defineProperty(global, 'performance', {
  value: mockPerformance,
  writable: true
})

describe('useDebounce Hook', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  test('should debounce function calls', () => {
    const callback = jest.fn()
    const { result } = renderHook(() => useDebounce(callback, 500))

    // Call the debounced function multiple times
    act(() => {
      result.current('arg1')
      result.current('arg2')
      result.current('arg3')
    })

    // Should not have been called yet
    expect(callback).not.toHaveBeenCalled()

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(500)
    })

    // Should have been called once with the last arguments
    expect(callback).toHaveBeenCalledTimes(1)
    expect(callback).toHaveBeenCalledWith('arg3')
  })

  test('should reset timer on subsequent calls', () => {
    const callback = jest.fn()
    const { result } = renderHook(() => useDebounce(callback, 500))

    act(() => {
      result.current('arg1')
    })

    act(() => {
      jest.advanceTimersByTime(300)
    })

    act(() => {
      result.current('arg2')
    })

    act(() => {
      jest.advanceTimersByTime(300)
    })

    // Should not have been called yet (timer was reset)
    expect(callback).not.toHaveBeenCalled()

    act(() => {
      jest.advanceTimersByTime(200)
    })

    // Now should be called
    expect(callback).toHaveBeenCalledTimes(1)
    expect(callback).toHaveBeenCalledWith('arg2')
  })

  test('should cleanup timeout on unmount', () => {
    const callback = jest.fn()
    const { result, unmount } = renderHook(() => useDebounce(callback, 500))

    act(() => {
      result.current('arg1')
    })

    unmount()

    act(() => {
      jest.advanceTimersByTime(500)
    })

    // Should not have been called after unmount
    expect(callback).not.toHaveBeenCalled()
  })
})

describe('useThrottle Hook', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  test('should throttle function calls', () => {
    const callback = jest.fn()
    const { result } = renderHook(() => useThrottle(callback, 500))

    // First call should execute immediately
    act(() => {
      result.current('arg1')
    })

    expect(callback).toHaveBeenCalledTimes(1)
    expect(callback).toHaveBeenCalledWith('arg1')

    // Subsequent calls within throttle period should be delayed
    act(() => {
      result.current('arg2')
      result.current('arg3')
    })

    expect(callback).toHaveBeenCalledTimes(1)

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(500)
    })

    // Should have been called with the last arguments
    expect(callback).toHaveBeenCalledTimes(2)
    expect(callback).toHaveBeenLastCalledWith('arg3')
  })

  test('should allow immediate execution after throttle period', () => {
    const callback = jest.fn()
    const { result } = renderHook(() => useThrottle(callback, 500))

    act(() => {
      result.current('arg1')
    })

    act(() => {
      jest.advanceTimersByTime(500)
    })

    act(() => {
      result.current('arg2')
    })

    expect(callback).toHaveBeenCalledTimes(2)
    expect(callback).toHaveBeenLastCalledWith('arg2')
  })
})

describe('useMemoWithComparison Hook', () => {
  test('should memoize value with default comparison', () => {
    const factory = jest.fn(() => ({ value: 'test' }))
    const { result, rerender } = renderHook(
      ({ deps }) => useMemoWithComparison(factory, deps),
      { initialProps: { deps: [1, 2, 3] } }
    )

    const firstResult = result.current
    expect(factory).toHaveBeenCalledTimes(1)

    // Rerender with same deps
    rerender({ deps: [1, 2, 3] })
    expect(result.current).toBe(firstResult)
    expect(factory).toHaveBeenCalledTimes(1)

    // Rerender with different deps
    rerender({ deps: [1, 2, 4] })
    expect(result.current).not.toBe(firstResult)
    expect(factory).toHaveBeenCalledTimes(2)
  })

  test('should use custom comparison function', () => {
    const factory = jest.fn(() => ({ value: 'test' }))
    const customCompare = jest.fn((prev, next) => prev[0] === next[0])
    
    const { result, rerender } = renderHook(
      ({ deps }) => useMemoWithComparison(factory, deps, customCompare),
      { initialProps: { deps: [1, 2] } }
    )

    const firstResult = result.current
    expect(factory).toHaveBeenCalledTimes(1)

    // Rerender with different second element but same first
    rerender({ deps: [1, 3] })
    expect(result.current).toBe(firstResult)
    expect(factory).toHaveBeenCalledTimes(1)
    expect(customCompare).toHaveBeenCalledWith([1, 2], [1, 3])

    // Rerender with different first element
    rerender({ deps: [2, 3] })
    expect(result.current).not.toBe(firstResult)
    expect(factory).toHaveBeenCalledTimes(2)
  })
})

describe('useBatchedUpdates Hook', () => {
  beforeEach(() => {
    jest.useFakeTimers()
  })

  afterEach(() => {
    jest.useRealTimers()
  })

  test('should batch multiple updates', () => {
    const update1 = jest.fn()
    const update2 = jest.fn()
    const update3 = jest.fn()
    
    const { result } = renderHook(() => useBatchedUpdates())

    act(() => {
      result.current(update1)
      result.current(update2)
      result.current(update3)
    })

    // Updates should not have been called yet
    expect(update1).not.toHaveBeenCalled()
    expect(update2).not.toHaveBeenCalled()
    expect(update3).not.toHaveBeenCalled()

    // Fast-forward to next tick
    act(() => {
      jest.advanceTimersByTime(0)
    })

    // All updates should have been called
    expect(update1).toHaveBeenCalledTimes(1)
    expect(update2).toHaveBeenCalledTimes(1)
    expect(update3).toHaveBeenCalledTimes(1)
  })
})

describe('useIntersectionObserver Hook', () => {
  const mockIntersectionObserver = jest.fn()
  const mockObserve = jest.fn()
  const mockUnobserve = jest.fn()
  const mockDisconnect = jest.fn()

  beforeEach(() => {
    mockIntersectionObserver.mockImplementation((callback, options) => ({
      observe: mockObserve,
      unobserve: mockUnobserve,
      disconnect: mockDisconnect
    }))

    global.IntersectionObserver = mockIntersectionObserver
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  test('should create intersection observer when observe is called', () => {
    const { result } = renderHook(() => useIntersectionObserver())
    const callback = jest.fn()

    // Set up element ref
    const mockElement = document.createElement('div')
    result.current.elementRef.current = mockElement

    act(() => {
      result.current.observe(callback)
    })

    expect(mockIntersectionObserver).toHaveBeenCalledWith(
      expect.any(Function),
      expect.objectContaining({
        threshold: 0.1,
        rootMargin: '50px'
      })
    )
    expect(mockObserve).toHaveBeenCalledWith(mockElement)
  })

  test('should unobserve element', () => {
    const { result } = renderHook(() => useIntersectionObserver())
    const mockElement = document.createElement('div')
    result.current.elementRef.current = mockElement

    act(() => {
      result.current.observe(jest.fn())
    })

    act(() => {
      result.current.unobserve()
    })

    expect(mockUnobserve).toHaveBeenCalledWith(mockElement)
  })

  test('should disconnect observer on unmount', () => {
    const { result, unmount } = renderHook(() => useIntersectionObserver())
    const mockElement = document.createElement('div')
    result.current.elementRef.current = mockElement

    act(() => {
      result.current.observe(jest.fn())
    })

    unmount()

    expect(mockDisconnect).toHaveBeenCalled()
  })
})

describe('useMemoryMonitor Hook', () => {
  test('should get memory usage when available', () => {
    const { result } = renderHook(() => useMemoryMonitor())

    const memoryUsage = result.current.getMemoryUsage()

    expect(memoryUsage).toEqual({
      usedJSHeapSize: 50000000,
      totalJSHeapSize: 100000000,
      jsHeapSizeLimit: 200000000,
      usagePercentage: 25 // 50MB / 200MB * 100
    })
  })

  test('should return null when memory API is not available', () => {
    const originalMemory = mockPerformance.memory
    delete mockPerformance.memory

    const { result } = renderHook(() => useMemoryMonitor())

    const memoryUsage = result.current.getMemoryUsage()
    expect(memoryUsage).toBeNull()

    mockPerformance.memory = originalMemory
  })

  test('should log memory usage', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
    const { result } = renderHook(() => useMemoryMonitor())

    act(() => {
      result.current.logMemoryUsage('Test Label')
    })

    expect(consoleSpy).toHaveBeenCalledWith(
      'Memory Usage (Test Label):',
      expect.objectContaining({
        used: '47.68 MB',
        total: '95.37 MB',
        limit: '190.73 MB',
        percentage: '25.00%'
      })
    )

    consoleSpy.mockRestore()
  })
})

describe('usePerformanceTiming Hook', () => {
  beforeEach(() => {
    mockPerformance.now.mockClear()
    let time = 1000
    mockPerformance.now.mockImplementation(() => time += 100)
  })

  test('should measure timing between start and end', () => {
    const { result } = renderHook(() => usePerformanceTiming())

    act(() => {
      result.current.startTiming('test-operation')
    })

    const duration = act(() => {
      return result.current.endTiming('test-operation')
    })

    expect(duration).toBe(100)
  })

  test('should return null for unknown timing label', () => {
    const { result } = renderHook(() => usePerformanceTiming())

    const duration = act(() => {
      return result.current.endTiming('unknown-operation')
    })

    expect(duration).toBeNull()
  })

  test('should measure function execution time', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
    const { result } = renderHook(() => usePerformanceTiming())

    const testFunction = jest.fn(() => 'result')

    const functionResult = act(() => {
      return result.current.measureTiming('test-function', testFunction)
    })

    expect(functionResult).toBe('result')
    expect(testFunction).toHaveBeenCalled()
    expect(consoleSpy).toHaveBeenCalledWith(
      'Performance: test-function took 100.00ms'
    )

    consoleSpy.mockRestore()
  })

  test('should not log in production', () => {
    const originalEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'production'

    const consoleSpy = jest.spyOn(console, 'log').mockImplementation()
    const { result } = renderHook(() => usePerformanceTiming())

    act(() => {
      result.current.measureTiming('test-function', () => 'result')
    })

    expect(consoleSpy).not.toHaveBeenCalled()

    process.env.NODE_ENV = originalEnv
    consoleSpy.mockRestore()
  })
})