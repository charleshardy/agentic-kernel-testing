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
}

export interface FallbackBehavior {
  type: 'none' | 'cached_data' | 'default_values' | 'graceful_degradation'
  data?: any
}

export interface NotificationStrategy {
  type: 'toast' | 'banner' | 'modal' | 'silent'
  duration?: number
  persistent?: boolean
}