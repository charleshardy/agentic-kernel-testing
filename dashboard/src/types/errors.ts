/**
 * TypeScript interfaces for Error Handling
 */

export enum ErrorCategory {
  NETWORK = 'network',
  ALLOCATION = 'allocation',
  ENVIRONMENT = 'environment',
  USER_INPUT = 'user_input',
  SYSTEM = 'system'
}

export enum ErrorSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface ErrorDetails {
  id: string
  code: string
  message: string
  category: ErrorCategory
  severity: ErrorSeverity
  timestamp: Date
  context?: Record<string, any>
  suggestedActions?: SuggestedAction[]
  retryable: boolean
  retryCount: number
  maxRetries: number
  suppressed: boolean
  userFacing?: boolean
  diagnosticInfo?: {
    stackTrace?: string
    [key: string]: any
  }
}

export interface SuggestedAction {
  id: string
  description: string
  action?: () => void | Promise<void>
  priority: number
}

export interface AllocationError extends ErrorDetails {
  category: ErrorCategory.ALLOCATION
  allocationRequestId?: string
}

export interface EnvironmentError extends ErrorDetails {
  category: ErrorCategory.ENVIRONMENT
  environmentId: string
}

export interface NetworkError extends ErrorDetails {
  category: ErrorCategory.NETWORK
  endpoint?: string
  httpStatus?: number
}

export interface UserInputError extends ErrorDetails {
  category: ErrorCategory.USER_INPUT
  fieldName?: string
}

export interface SystemError extends ErrorDetails {
  category: ErrorCategory.SYSTEM
  serviceType?: string
}

export interface ErrorRecoveryStrategy {
  errorType: string
  retryPolicy: RetryPolicy
  fallbackBehavior: FallbackBehavior
  userNotification: NotificationStrategy
}

export interface RetryPolicy {
  maxAttempts: number
  backoffStrategy: 'linear' | 'exponential'
  baseDelay: number
  maxDelay: number
  retryableErrors: string[]
}

export interface FallbackBehavior {
  type: 'none' | 'cache' | 'mock_data' | 'degraded_mode' | 'offline_mode'
  data?: any
  message?: string
}

export interface NotificationStrategy {
  type: 'toast' | 'banner' | 'modal' | 'silent'
  duration?: number
  persistent?: boolean
  dismissible?: boolean
  showDiagnostics?: boolean
}

// Error configuration constants
export const ERROR_CONFIGS: Record<string, Partial<ErrorDetails>> = {
  // Network errors
  CONNECTION_TIMEOUT: {
    code: 'CONNECTION_TIMEOUT',
    message: 'Connection timeout',
    category: ErrorCategory.NETWORK,
    severity: ErrorSeverity.MEDIUM,
    retryable: true,
    retryCount: 0,
    maxRetries: 3,
    suppressed: false
  },
  API_UNAVAILABLE: {
    code: 'API_UNAVAILABLE',
    message: 'API service unavailable',
    category: ErrorCategory.NETWORK,
    severity: ErrorSeverity.HIGH,
    retryable: true,
    retryCount: 0,
    maxRetries: 5,
    suppressed: false
  },
  WEBSOCKET_ERROR: {
    code: 'WEBSOCKET_ERROR',
    message: 'WebSocket connection error',
    category: ErrorCategory.NETWORK,
    severity: ErrorSeverity.MEDIUM,
    retryable: true,
    retryCount: 0,
    maxRetries: 3,
    suppressed: false
  },
  
  // Allocation errors
  ALLOCATION_FAILED: {
    code: 'ALLOCATION_FAILED',
    message: 'Environment allocation failed',
    category: ErrorCategory.ALLOCATION,
    severity: ErrorSeverity.HIGH,
    retryable: true,
    retryCount: 0,
    maxRetries: 2,
    suppressed: false
  },
  QUEUE_FULL: {
    code: 'QUEUE_FULL',
    message: 'Allocation queue is full',
    category: ErrorCategory.ALLOCATION,
    severity: ErrorSeverity.MEDIUM,
    retryable: false,
    retryCount: 0,
    maxRetries: 0,
    suppressed: false
  },
  
  // Environment errors
  ENVIRONMENT_UNAVAILABLE: {
    code: 'ENVIRONMENT_UNAVAILABLE',
    message: 'Environment is unavailable',
    category: ErrorCategory.ENVIRONMENT,
    severity: ErrorSeverity.MEDIUM,
    retryable: true,
    retryCount: 0,
    maxRetries: 3,
    suppressed: false
  },
  RESOURCE_EXHAUSTED: {
    code: 'RESOURCE_EXHAUSTED',
    message: 'Environment resources exhausted',
    category: ErrorCategory.ENVIRONMENT,
    severity: ErrorSeverity.HIGH,
    retryable: false,
    retryCount: 0,
    maxRetries: 0,
    suppressed: false
  },
  
  // User input errors
  INVALID_REQUEST: {
    code: 'INVALID_REQUEST',
    message: 'Invalid request parameters',
    category: ErrorCategory.USER_INPUT,
    severity: ErrorSeverity.LOW,
    retryable: false,
    retryCount: 0,
    maxRetries: 0,
    suppressed: false
  },
  
  // System errors
  GENERIC_ERROR: {
    code: 'GENERIC_ERROR',
    message: 'An unexpected error occurred',
    category: ErrorCategory.SYSTEM,
    severity: ErrorSeverity.MEDIUM,
    retryable: false,
    retryCount: 0,
    maxRetries: 0,
    suppressed: false
  },
  JS_ERROR: {
    code: 'JS_ERROR',
    message: 'JavaScript runtime error',
    category: ErrorCategory.SYSTEM,
    severity: ErrorSeverity.MEDIUM,
    retryable: false,
    retryCount: 0,
    maxRetries: 0,
    suppressed: false
  }
}

// Default retry policies by category
export const DEFAULT_RETRY_POLICIES: Record<ErrorCategory, RetryPolicy> = {
  [ErrorCategory.NETWORK]: {
    maxAttempts: 3,
    backoffStrategy: 'exponential',
    baseDelay: 1000,
    maxDelay: 10000,
    retryableErrors: ['CONNECTION_TIMEOUT', 'API_UNAVAILABLE', 'WEBSOCKET_ERROR', 'HTTP_ERROR']
  },
  [ErrorCategory.ALLOCATION]: {
    maxAttempts: 2,
    backoffStrategy: 'linear',
    baseDelay: 2000,
    maxDelay: 8000,
    retryableErrors: ['ALLOCATION_FAILED', 'ENVIRONMENT_UNAVAILABLE']
  },
  [ErrorCategory.ENVIRONMENT]: {
    maxAttempts: 3,
    backoffStrategy: 'exponential',
    baseDelay: 1500,
    maxDelay: 12000,
    retryableErrors: ['ENVIRONMENT_UNAVAILABLE', 'RESOURCE_EXHAUSTED']
  },
  [ErrorCategory.USER_INPUT]: {
    maxAttempts: 0,
    backoffStrategy: 'linear',
    baseDelay: 0,
    maxDelay: 0,
    retryableErrors: []
  },
  [ErrorCategory.SYSTEM]: {
    maxAttempts: 1,
    backoffStrategy: 'linear',
    baseDelay: 1000,
    maxDelay: 5000,
    retryableErrors: ['GENERIC_ERROR']
  }
}