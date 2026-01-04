import { useState, useCallback, useRef, useEffect } from 'react'
import { ErrorDetails } from '../components/ErrorHandling/ErrorAlert'
import { toast } from '../components/ErrorHandling/ToastNotification'
import { RetryPolicy } from '../components/ErrorHandling/ErrorRecovery'

export interface ErrorHandlerConfig {
  showToast?: boolean
  autoRetry?: boolean
  retryPolicy?: RetryPolicy
  logErrors?: boolean
  reportErrors?: boolean
}

export interface ErrorContext {
  component?: string
  action?: string
  userId?: string
  sessionId?: string
  timestamp?: Date
  userAgent?: string
  url?: string
  [key: string]: any
}

const DEFAULT_CONFIG: ErrorHandlerConfig = {
  showToast: true,
  autoRetry: false,
  logErrors: true,
  reportErrors: false,
  retryPolicy: {
    maxAttempts: 3,
    backoffStrategy: 'exponential',
    baseDelay: 1000,
    maxDelay: 10000
  }
}

export const useErrorHandler = (config: ErrorHandlerConfig = {}) => {
  const [errors, setErrors] = useState<ErrorDetails[]>([])
  const [isRetrying, setIsRetrying] = useState(false)
  const retryAttempts = useRef<Map<string, number>>(new Map())
  const finalConfig = { ...DEFAULT_CONFIG, ...config }

  // Generate unique error ID
  const generateErrorId = useCallback(() => {
    return `error-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
  }, [])

  // Classify error type based on error object
  const classifyError = useCallback((error: any): ErrorDetails['type'] => {
    if (error.name === 'NetworkError' || error.code === 'NETWORK_ERROR') {
      return 'network'
    }
    if (error.message?.includes('allocation') || error.code === 'ALLOCATION_ERROR') {
      return 'allocation'
    }
    if (error.message?.includes('environment') || error.code === 'ENVIRONMENT_ERROR') {
      return 'environment'
    }
    if (error.name === 'ValidationError' || error.code === 'VALIDATION_ERROR') {
      return 'user_input'
    }
    return 'system'
  }, [])

  // Determine error severity
  const determineSeverity = useCallback((error: any, type: ErrorDetails['type']): ErrorDetails['severity'] => {
    if (error.severity) {
      return error.severity
    }
    
    switch (type) {
      case 'network':
        return error.status >= 500 ? 'high' : 'medium'
      case 'allocation':
        return 'high'
      case 'environment':
        return 'high'
      case 'user_input':
        return 'low'
      case 'system':
        return 'critical'
      default:
        return 'medium'
    }
  }, [])

  // Generate suggested actions based on error type
  const generateSuggestedActions = useCallback((error: any, type: ErrorDetails['type']): string[] => {
    const actions: string[] = []
    
    switch (type) {
      case 'network':
        actions.push('Check your internet connection')
        actions.push('Verify the server is accessible')
        actions.push('Try refreshing the page')
        if (error.status === 401) {
          actions.push('Re-authenticate your session')
        }
        break
      case 'allocation':
        actions.push('Check environment availability')
        actions.push('Verify resource requirements')
        actions.push('Try allocating a different environment type')
        break
      case 'environment':
        actions.push('Check environment health status')
        actions.push('Try restarting the environment')
        actions.push('Contact system administrator if issue persists')
        break
      case 'user_input':
        actions.push('Review your input for errors')
        actions.push('Check required fields are filled')
        actions.push('Verify data format is correct')
        break
      case 'system':
        actions.push('Try refreshing the page')
        actions.push('Clear browser cache and cookies')
        actions.push('Contact technical support')
        break
    }
    
    return actions
  }, [])

  // Extract diagnostic information from error
  const extractDiagnosticInfo = useCallback((error: any, context?: ErrorContext) => {
    const diagnosticInfo: ErrorDetails['diagnosticInfo'] = {}
    
    if (error.config?.url) {
      diagnosticInfo.endpoint = error.config.url
    }
    if (error.response?.status) {
      diagnosticInfo.statusCode = error.response.status
    }
    if (error.config?.timeout) {
      diagnosticInfo.responseTime = error.config.timeout
    }
    if (context?.environmentId) {
      diagnosticInfo.environmentId = context.environmentId
    }
    if (context?.testId) {
      diagnosticInfo.testId = context.testId
    }
    
    diagnosticInfo.userAgent = navigator.userAgent
    
    return diagnosticInfo
  }, [])

  // Main error handling function
  const handleError = useCallback((
    error: any,
    context?: ErrorContext,
    options?: Partial<ErrorHandlerConfig>
  ) => {
    const errorConfig = { ...finalConfig, ...options }
    const errorId = generateErrorId()
    const type = classifyError(error)
    const severity = determineSeverity(error, type)
    const suggestedActions = generateSuggestedActions(error, type)
    const diagnosticInfo = extractDiagnosticInfo(error, context)
    
    const errorDetails: ErrorDetails = {
      id: errorId,
      message: error.message || 'An unexpected error occurred',
      type,
      severity,
      timestamp: new Date(),
      context: {
        ...context,
        originalError: error.name,
        stack: error.stack
      },
      stack: error.stack,
      suggestedActions,
      retryable: type === 'network' || type === 'allocation',
      diagnosticInfo
    }

    // Add to errors list
    setErrors(prev => [errorDetails, ...prev.slice(0, 9)]) // Keep last 10 errors

    // Log error if enabled
    if (errorConfig.logErrors) {
      console.error('Error handled:', errorDetails)
    }

    // Show toast notification if enabled
    if (errorConfig.showToast) {
      switch (type) {
        case 'network':
          toast.networkError(
            diagnosticInfo.endpoint || 'Unknown endpoint',
            diagnosticInfo.statusCode
          )
          break
        case 'allocation':
          toast.allocationError(
            diagnosticInfo.environmentId,
            error.message
          )
          break
        case 'environment':
          toast.environmentError(
            diagnosticInfo.environmentId || 'Unknown environment',
            error.message
          )
          break
        default:
          toast.error(errorDetails.message, error.stack?.split('\n')[0])
      }
    }

    // Report error to external service if enabled
    if (errorConfig.reportErrors) {
      // In a real application, you would send this to an error reporting service
      // Example: Sentry.captureException(error, { contexts: { errorDetails } })
      console.log('Would report error to external service:', errorDetails)
    }

    return errorDetails
  }, [
    finalConfig,
    generateErrorId,
    classifyError,
    determineSeverity,
    generateSuggestedActions,
    extractDiagnosticInfo
  ])

  // Retry function with exponential backoff
  const retryWithBackoff = useCallback(async (
    operation: () => Promise<any>,
    errorId?: string,
    customRetryPolicy?: RetryPolicy
  ) => {
    const policy = customRetryPolicy || finalConfig.retryPolicy!
    const attempts = errorId ? (retryAttempts.current.get(errorId) || 0) : 0
    
    if (attempts >= policy.maxAttempts) {
      throw new Error(`Max retry attempts (${policy.maxAttempts}) exceeded`)
    }

    setIsRetrying(true)
    
    try {
      const result = await operation()
      
      // Reset retry count on success
      if (errorId) {
        retryAttempts.current.delete(errorId)
      }
      
      return result
    } catch (error) {
      const newAttempts = attempts + 1
      
      if (errorId) {
        retryAttempts.current.set(errorId, newAttempts)
      }
      
      if (newAttempts < policy.maxAttempts) {
        const delay = policy.backoffStrategy === 'exponential'
          ? Math.min(policy.baseDelay * Math.pow(2, attempts), policy.maxDelay)
          : Math.min(policy.baseDelay * newAttempts, policy.maxDelay)
        
        await new Promise(resolve => setTimeout(resolve, delay))
        return retryWithBackoff(operation, errorId, customRetryPolicy)
      } else {
        throw error
      }
    } finally {
      setIsRetrying(false)
    }
  }, [finalConfig.retryPolicy])

  // Clear specific error
  const clearError = useCallback((errorId: string) => {
    setErrors(prev => prev.filter(error => error.id !== errorId))
    retryAttempts.current.delete(errorId)
  }, [])

  // Clear all errors
  const clearAllErrors = useCallback(() => {
    setErrors([])
    retryAttempts.current.clear()
  }, [])

  // Get errors by type
  const getErrorsByType = useCallback((type: ErrorDetails['type']) => {
    return errors.filter(error => error.type === type)
  }, [errors])

  // Get errors by severity
  const getErrorsBySeverity = useCallback((severity: ErrorDetails['severity']) => {
    return errors.filter(error => error.severity === severity)
  }, [errors])

  // Check if there are critical errors
  const hasCriticalErrors = useCallback(() => {
    return errors.some(error => error.severity === 'critical')
  }, [errors])

  // Async error wrapper
  const withErrorHandling = useCallback(<T extends any[], R>(
    fn: (...args: T) => Promise<R>,
    context?: ErrorContext,
    options?: Partial<ErrorHandlerConfig>
  ) => {
    return async (...args: T): Promise<R> => {
      try {
        return await fn(...args)
      } catch (error) {
        handleError(error, context, options)
        throw error
      }
    }
  }, [handleError])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      retryAttempts.current.clear()
    }
  }, [])

  return {
    errors,
    isRetrying,
    handleError,
    retryWithBackoff,
    clearError,
    clearAllErrors,
    getErrorsByType,
    getErrorsBySeverity,
    hasCriticalErrors,
    withErrorHandling
  }
}