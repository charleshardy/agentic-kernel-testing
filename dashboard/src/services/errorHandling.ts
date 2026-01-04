/**
 * Error Handling Service for Environment Allocation UI
 * Provides comprehensive error management, retry logic, and recovery strategies
 */

import { 
  ErrorDetails, 
  ErrorCategory, 
  ErrorSeverity,
  RetryPolicy, 
  FallbackBehavior,
  ErrorRecoveryStrategy,
  NotificationStrategy,
  ERROR_CONFIGS,
  DEFAULT_RETRY_POLICIES,
  AllocationError,
  EnvironmentError,
  NetworkError,
  UserInputError,
  SystemError
} from '../types/errors';

export class ErrorHandlingService {
  private retryAttempts: Map<string, number> = new Map();
  private suppressedErrors: Set<string> = new Set();
  private errorListeners: Set<(error: ErrorDetails) => void> = new Set();
  private recoveryStrategies: Map<string, ErrorRecoveryStrategy> = new Map();

  constructor() {
    this.initializeRecoveryStrategies();
  }

  /**
   * Create a standardized error from various input types
   */
  createError(
    errorInput: Partial<ErrorDetails> | Error | string,
    context?: Record<string, any>
  ): ErrorDetails {
    let baseError: Partial<ErrorDetails>;

    if (typeof errorInput === 'string') {
      // Handle string error messages
      baseError = {
        code: 'GENERIC_ERROR',
        message: errorInput,
        category: ErrorCategory.SYSTEM,
        severity: ErrorSeverity.MEDIUM
      };
    } else if (errorInput instanceof Error) {
      // Handle JavaScript Error objects
      baseError = {
        code: 'JS_ERROR',
        message: errorInput.message,
        category: ErrorCategory.SYSTEM,
        severity: ErrorSeverity.MEDIUM,
        diagnosticInfo: {
          stackTrace: errorInput.stack
        }
      };
    } else {
      // Handle ErrorDetails objects
      baseError = errorInput;
    }

    // Apply predefined configuration if available
    const config = baseError.code ? ERROR_CONFIGS[baseError.code] : {};
    
    const error: ErrorDetails = {
      id: this.generateErrorId(),
      timestamp: new Date(),
      retryable: false,
      userFacing: true,
      ...config,
      ...baseError,
      context: { ...context, ...baseError.context }
    };

    return error;
  }

  /**
   * Create specific allocation error
   */
  createAllocationError(
    code: string,
    message: string,
    allocationRequestId?: string,
    additionalContext?: Record<string, any>
  ): AllocationError {
    const baseError = this.createError({
      code,
      message,
      category: ErrorCategory.ALLOCATION
    }, additionalContext);

    return {
      ...baseError,
      category: ErrorCategory.ALLOCATION,
      allocationRequestId
    } as AllocationError;
  }

  /**
   * Create specific environment error
   */
  createEnvironmentError(
    code: string,
    message: string,
    environmentId: string,
    additionalContext?: Record<string, any>
  ): EnvironmentError {
    const baseError = this.createError({
      code,
      message,
      category: ErrorCategory.ENVIRONMENT
    }, additionalContext);

    return {
      ...baseError,
      category: ErrorCategory.ENVIRONMENT,
      environmentId
    } as EnvironmentError;
  }

  /**
   * Create specific network error
   */
  createNetworkError(
    code: string,
    message: string,
    endpoint?: string,
    httpStatus?: number,
    additionalContext?: Record<string, any>
  ): NetworkError {
    const baseError = this.createError({
      code,
      message,
      category: ErrorCategory.NETWORK
    }, additionalContext);

    return {
      ...baseError,
      category: ErrorCategory.NETWORK,
      endpoint,
      httpStatus
    } as NetworkError;
  }

  /**
   * Handle API errors and convert them to standardized errors
   */
  handleApiError(error: any, endpoint?: string): ErrorDetails {
    if (error.response) {
      // HTTP error response
      const status = error.response.status;
      const data = error.response.data;
      
      let code: string;
      let message: string;
      let severity: ErrorSeverity;

      switch (status) {
        case 400:
          code = 'INVALID_REQUEST';
          message = data?.message || 'Invalid request';
          severity = ErrorSeverity.LOW;
          break;
        case 401:
          code = 'UNAUTHORIZED';
          message = 'Authentication required';
          severity = ErrorSeverity.MEDIUM;
          break;
        case 403:
          code = 'FORBIDDEN';
          message = 'Access denied';
          severity = ErrorSeverity.MEDIUM;
          break;
        case 404:
          code = 'NOT_FOUND';
          message = 'Resource not found';
          severity = ErrorSeverity.LOW;
          break;
        case 408:
          code = 'CONNECTION_TIMEOUT';
          message = 'Request timeout';
          severity = ErrorSeverity.MEDIUM;
          break;
        case 429:
          code = 'RATE_LIMITED';
          message = 'Too many requests';
          severity = ErrorSeverity.MEDIUM;
          break;
        case 500:
          code = 'SERVER_ERROR';
          message = 'Internal server error';
          severity = ErrorSeverity.HIGH;
          break;
        case 502:
        case 503:
        case 504:
          code = 'API_UNAVAILABLE';
          message = 'Service unavailable';
          severity = ErrorSeverity.HIGH;
          break;
        default:
          code = 'HTTP_ERROR';
          message = `HTTP ${status}: ${data?.message || error.message}`;
          severity = ErrorSeverity.MEDIUM;
      }

      return this.createNetworkError(code, message, endpoint, status, {
        responseData: data,
        originalError: error.message
      });
    } else if (error.request) {
      // Network error (no response)
      return this.createNetworkError(
        'CONNECTION_TIMEOUT',
        'Network connection failed',
        endpoint,
        undefined,
        { originalError: error.message }
      );
    } else {
      // Other error
      return this.createError(error, { endpoint });
    }
  }

  /**
   * Handle WebSocket errors
   */
  handleWebSocketError(error: Event | Error, connectionType: 'websocket' | 'sse'): ErrorDetails {
    const message = error instanceof Error ? error.message : 'WebSocket connection error';
    
    return this.createNetworkError(
      'WEBSOCKET_ERROR',
      message,
      undefined,
      undefined,
      { connectionType }
    );
  }

  /**
   * Determine if an error should be retried
   */
  shouldRetry(error: ErrorDetails): boolean {
    if (!error.retryable) {
      return false;
    }

    const attempts = this.retryAttempts.get(error.id) || 0;
    const policy = this.getRetryPolicy(error);
    
    return attempts < policy.maxAttempts && 
           policy.retryableErrors.includes(error.code);
  }

  /**
   * Execute retry logic for an error
   */
  async retry<T>(
    error: ErrorDetails,
    operation: () => Promise<T>
  ): Promise<T> {
    if (!this.shouldRetry(error)) {
      throw new Error(`Error ${error.code} is not retryable or max attempts exceeded`);
    }

    const attempts = this.retryAttempts.get(error.id) || 0;
    this.retryAttempts.set(error.id, attempts + 1);

    const policy = this.getRetryPolicy(error);
    const delay = this.calculateDelay(attempts, policy);

    console.log(`Retrying operation for error ${error.code} (attempt ${attempts + 1}/${policy.maxAttempts}) after ${delay}ms`);

    await this.sleep(delay);

    try {
      const result = await operation();
      // Success - clear retry attempts
      this.retryAttempts.delete(error.id);
      return result;
    } catch (retryError) {
      // If this was the last attempt, don't retry again
      if (attempts + 1 >= policy.maxAttempts) {
        this.retryAttempts.delete(error.id);
      }
      throw retryError;
    }
  }

  /**
   * Apply fallback behavior when an error cannot be resolved
   */
  applyFallback(error: ErrorDetails): any {
    const strategy = this.recoveryStrategies.get(error.code);
    if (!strategy) {
      return null;
    }

    const fallback = strategy.fallbackBehavior;
    
    switch (fallback.type) {
      case 'cache':
        // Return cached data if available
        return this.getCachedData(error.context);
      
      case 'mock_data':
        // Return mock data for development/testing
        return fallback.data || this.generateMockData(error);
      
      case 'degraded_mode':
        // Return limited functionality data
        return this.getDegradedModeData(error);
      
      case 'offline_mode':
        // Return offline-capable data
        return this.getOfflineModeData(error);
      
      default:
        return null;
    }
  }

  /**
   * Get notification strategy for an error
   */
  getNotificationStrategy(error: ErrorDetails): NotificationStrategy {
    const strategy = this.recoveryStrategies.get(error.code);
    if (strategy) {
      return strategy.userNotification;
    }

    // Default notification strategy based on severity
    switch (error.severity) {
      case ErrorSeverity.CRITICAL:
        return {
          type: 'modal',
          persistent: true,
          dismissible: false,
          showDiagnostics: true
        };
      
      case ErrorSeverity.HIGH:
        return {
          type: 'banner',
          persistent: true,
          dismissible: true,
          showDiagnostics: true
        };
      
      case ErrorSeverity.MEDIUM:
        return {
          type: 'toast',
          duration: 8000,
          dismissible: true,
          showDiagnostics: false
        };
      
      case ErrorSeverity.LOW:
      default:
        return {
          type: 'toast',
          duration: 4000,
          dismissible: true,
          showDiagnostics: false
        };
    }
  }

  /**
   * Suppress an error (don't show notifications)
   */
  suppressError(errorId: string): void {
    this.suppressedErrors.add(errorId);
  }

  /**
   * Check if an error is suppressed
   */
  isErrorSuppressed(errorId: string): boolean {
    return this.suppressedErrors.has(errorId);
  }

  /**
   * Clear all suppressed errors
   */
  clearSuppressedErrors(): void {
    this.suppressedErrors.clear();
  }

  /**
   * Add error listener
   */
  addErrorListener(listener: (error: ErrorDetails) => void): () => void {
    this.errorListeners.add(listener);
    return () => this.errorListeners.delete(listener);
  }

  /**
   * Notify all error listeners
   */
  private notifyErrorListeners(error: ErrorDetails): void {
    this.errorListeners.forEach(listener => {
      try {
        listener(error);
      } catch (err) {
        console.error('Error in error listener:', err);
      }
    });
  }

  /**
   * Process and handle an error
   */
  handleError(error: ErrorDetails): void {
    console.error('Handling error:', error);
    
    // Don't process suppressed errors
    if (this.isErrorSuppressed(error.id)) {
      return;
    }

    // Notify listeners
    this.notifyErrorListeners(error);
  }

  // Private helper methods

  private generateErrorId(): string {
    return `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getRetryPolicy(error: ErrorDetails): RetryPolicy {
    const strategy = this.recoveryStrategies.get(error.code);
    if (strategy) {
      return strategy.retryPolicy;
    }
    return DEFAULT_RETRY_POLICIES[error.category];
  }

  private calculateDelay(attempt: number, policy: RetryPolicy): number {
    let delay: number;
    
    if (policy.backoffStrategy === 'exponential') {
      delay = policy.baseDelay * Math.pow(2, attempt);
    } else {
      delay = policy.baseDelay * (attempt + 1);
    }
    
    return Math.min(delay, policy.maxDelay);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private initializeRecoveryStrategies(): void {
    // Initialize recovery strategies for common errors
    Object.entries(ERROR_CONFIGS).forEach(([code, config]) => {
      const category = config.category!;
      const retryPolicy = DEFAULT_RETRY_POLICIES[category];
      
      this.recoveryStrategies.set(code, {
        errorType: code,
        retryPolicy,
        fallbackBehavior: {
          type: 'mock_data',
          message: 'Using fallback data due to error'
        },
        userNotification: {
          type: 'toast',
          duration: 5000,
          dismissible: true
        }
      });
    });
  }

  private getCachedData(context?: Record<string, any>): any {
    // Implementation would depend on caching strategy
    // For now, return null to indicate no cached data
    return null;
  }

  private generateMockData(error: ErrorDetails): any {
    // Generate appropriate mock data based on error context
    switch (error.category) {
      case ErrorCategory.ALLOCATION:
        return {
          environments: [],
          queue: [],
          message: 'Mock data: No environments available'
        };
      
      case ErrorCategory.ENVIRONMENT:
        return {
          status: 'unknown',
          health: 'unknown',
          message: 'Mock data: Environment status unavailable'
        };
      
      default:
        return {
          message: 'Mock data due to error',
          error: error.message
        };
    }
  }

  private getDegradedModeData(error: ErrorDetails): any {
    return {
      degraded: true,
      message: 'Operating in degraded mode',
      limitedFeatures: true
    };
  }

  private getOfflineModeData(error: ErrorDetails): any {
    return {
      offline: true,
      message: 'Operating in offline mode',
      cachedData: true
    };
  }
}

// Singleton instance
export const errorHandlingService = new ErrorHandlingService();
export default errorHandlingService;