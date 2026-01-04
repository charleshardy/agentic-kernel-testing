/**
 * Unit tests for useErrorHandler hook
 * 
 * **Feature: environment-allocation-ui, Task 14.1: Unit tests for component interactions**
 * **Validates: Requirements 3.2, 7.2, 7.4, 7.5**
 */

import { renderHook, act } from '@testing-library/react'
import { useErrorHandler } from '../useErrorHandler'

// Mock toast notifications
jest.mock('../components/ErrorHandling/ToastNotification', () => ({
  toast: {
    error: jest.fn(),
    networkError: jest.fn(),
    allocationError: jest.fn(),
    environmentError: jest.fn()
  }
}))

describe('useErrorHandler Hook', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    console.error = jest.fn()
  })

  test('should initialize with empty errors array', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    expect(result.current.errors).toEqual([])
    expect(result.current.isRetrying).toBe(false)
  })

  test('should handle network errors correctly', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    const networkError = {
      name: 'NetworkError',
      message: 'Failed to fetch',
      config: { url: '/api/test' },
      response: { status: 500 }
    }

    act(() => {
      result.current.handleError(networkError, { component: 'TestComponent' })
    })

    expect(result.current.errors).toHaveLength(1)
    expect(result.current.errors[0].type).toBe('network')
    expect(result.current.errors[0].severity).toBe('high')
    expect(result.current.errors[0].retryable).toBe(true)
  })

  test('should classify allocation errors correctly', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    const allocationError = {
      message: 'Environment allocation failed',
      code: 'ALLOCATION_ERROR'
    }

    act(() => {
      result.current.handleError(allocationError)
    })

    expect(result.current.errors[0].type).toBe('allocation')
    expect(result.current.errors[0].severity).toBe('high')
  })

  test('should classify environment errors correctly', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    const environmentError = {
      message: 'Environment health check failed',
      code: 'ENVIRONMENT_ERROR'
    }

    act(() => {
      result.current.handleError(environmentError)
    })

    expect(result.current.errors[0].type).toBe('environment')
    expect(result.current.errors[0].severity).toBe('high')
  })

  test('should classify user input errors correctly', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    const validationError = {
      name: 'ValidationError',
      message: 'Invalid input provided'
    }

    act(() => {
      result.current.handleError(validationError)
    })

    expect(result.current.errors[0].type).toBe('user_input')
    expect(result.current.errors[0].severity).toBe('low')
  })

  test('should generate appropriate suggested actions', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    const networkError = {
      name: 'NetworkError',
      message: 'Connection timeout',
      response: { status: 401 }
    }

    act(() => {
      result.current.handleError(networkError)
    })

    const error = result.current.errors[0]
    expect(error.suggestedActions).toContain('Check your internet connection')
    expect(error.suggestedActions).toContain('Re-authenticate your session')
  })

  test('should extract diagnostic information', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    const error = {
      message: 'API Error',
      config: { url: '/api/environments', timeout: 5000 },
      response: { status: 404 }
    }

    const context = {
      environmentId: 'env-123',
      testId: 'test-456'
    }

    act(() => {
      result.current.handleError(error, context)
    })

    const handledError = result.current.errors[0]
    expect(handledError.diagnosticInfo?.endpoint).toBe('/api/environments')
    expect(handledError.diagnosticInfo?.statusCode).toBe(404)
    expect(handledError.diagnosticInfo?.environmentId).toBe('env-123')
    expect(handledError.diagnosticInfo?.testId).toBe('test-456')
  })

  test('should clear specific error', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    act(() => {
      result.current.handleError(new Error('Error 1'))
      result.current.handleError(new Error('Error 2'))
    })

    expect(result.current.errors).toHaveLength(2)
    
    const errorIdToClear = result.current.errors[0].id

    act(() => {
      result.current.clearError(errorIdToClear)
    })

    expect(result.current.errors).toHaveLength(1)
    expect(result.current.errors[0].message).toBe('Error 2')
  })

  test('should clear all errors', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    act(() => {
      result.current.handleError(new Error('Error 1'))
      result.current.handleError(new Error('Error 2'))
      result.current.handleError(new Error('Error 3'))
    })

    expect(result.current.errors).toHaveLength(3)

    act(() => {
      result.current.clearAllErrors()
    })

    expect(result.current.errors).toHaveLength(0)
  })

  test('should filter errors by type', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    act(() => {
      result.current.handleError({ name: 'NetworkError', message: 'Network error' })
      result.current.handleError({ message: 'Allocation error', code: 'ALLOCATION_ERROR' })
      result.current.handleError({ name: 'ValidationError', message: 'Validation error' })
    })

    const networkErrors = result.current.getErrorsByType('network')
    const allocationErrors = result.current.getErrorsByType('allocation')
    const userInputErrors = result.current.getErrorsByType('user_input')

    expect(networkErrors).toHaveLength(1)
    expect(allocationErrors).toHaveLength(1)
    expect(userInputErrors).toHaveLength(1)
  })

  test('should filter errors by severity', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    act(() => {
      result.current.handleError({ name: 'NetworkError', message: 'Network error' }) // high
      result.current.handleError({ name: 'ValidationError', message: 'Validation error' }) // low
      result.current.handleError({ message: 'System error' }) // critical
    })

    const highSeverityErrors = result.current.getErrorsBySeverity('high')
    const lowSeverityErrors = result.current.getErrorsBySeverity('low')
    const criticalErrors = result.current.getErrorsBySeverity('critical')

    expect(highSeverityErrors).toHaveLength(1)
    expect(lowSeverityErrors).toHaveLength(1)
    expect(criticalErrors).toHaveLength(1)
  })

  test('should detect critical errors', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    expect(result.current.hasCriticalErrors()).toBe(false)

    act(() => {
      result.current.handleError({ message: 'System failure' }) // critical
    })

    expect(result.current.hasCriticalErrors()).toBe(true)
  })

  test('should wrap async functions with error handling', async () => {
    const { result } = renderHook(() => useErrorHandler())
    
    const asyncFunction = jest.fn().mockRejectedValue(new Error('Async error'))
    const wrappedFunction = result.current.withErrorHandling(
      asyncFunction,
      { component: 'TestComponent' }
    )

    await expect(wrappedFunction('arg1', 'arg2')).rejects.toThrow('Async error')
    
    expect(asyncFunction).toHaveBeenCalledWith('arg1', 'arg2')
    expect(result.current.errors).toHaveLength(1)
    expect(result.current.errors[0].message).toBe('Async error')
  })

  test('should perform retry with exponential backoff', async () => {
    const { result } = renderHook(() => useErrorHandler())
    
    let attemptCount = 0
    const operation = jest.fn().mockImplementation(() => {
      attemptCount++
      if (attemptCount < 3) {
        throw new Error(`Attempt ${attemptCount} failed`)
      }
      return 'success'
    })

    const retryResult = await act(async () => {
      return result.current.retryWithBackoff(operation, 'test-operation')
    })

    expect(retryResult).toBe('success')
    expect(operation).toHaveBeenCalledTimes(3)
  })

  test('should fail after max retry attempts', async () => {
    const { result } = renderHook(() => useErrorHandler({
      retryPolicy: { maxAttempts: 2, backoffStrategy: 'linear', baseDelay: 10, maxDelay: 100 }
    }))
    
    const operation = jest.fn().mockRejectedValue(new Error('Always fails'))

    await expect(
      act(async () => {
        return result.current.retryWithBackoff(operation, 'test-operation')
      })
    ).rejects.toThrow('Always fails')

    expect(operation).toHaveBeenCalledTimes(2)
  })

  test('should respect configuration options', () => {
    const { result } = renderHook(() => useErrorHandler({
      showToast: false,
      logErrors: false,
      autoRetry: true
    }))
    
    act(() => {
      result.current.handleError(new Error('Test error'))
    })

    // Should still add error to state even with showToast: false
    expect(result.current.errors).toHaveLength(1)
  })

  test('should limit errors to last 10', () => {
    const { result } = renderHook(() => useErrorHandler())
    
    act(() => {
      // Add 15 errors
      for (let i = 0; i < 15; i++) {
        result.current.handleError(new Error(`Error ${i}`))
      }
    })

    // Should only keep the last 10 errors
    expect(result.current.errors).toHaveLength(10)
    expect(result.current.errors[0].message).toBe('Error 14') // Most recent first
    expect(result.current.errors[9].message).toBe('Error 5')
  })
})