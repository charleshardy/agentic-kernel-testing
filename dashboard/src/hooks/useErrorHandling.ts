/**
 * Error Handling Hook for Environment Allocation UI
 * Provides error handling capabilities to React components
 */

import { useState, useCallback, useEffect, useRef } from 'react';
import { 
  ErrorDetails, 
  ErrorCategory, 
  ErrorSeverity,
  AllocationError,
  EnvironmentError,
  NetworkError,
  UserInputError,
  SystemError
} from '../types/errors';
import errorHandlingService from '../services/errorHandling';

interface UseErrorHandlingOptions {
  onError?: (error: ErrorDetails) => void;
  autoRetry?: boolean;
  suppressNotifications?: boolean;
  fallbackData?: any;
}

interface UseErrorHandlingReturn {
  // Error state
  errors: ErrorDetails[];
  hasErrors: boolean;
  lastError?: ErrorDetails;
  
  // Error creation methods
  createError: (error: Partial<ErrorDetails> | Error | string, context?: Record<string, any>) => ErrorDetails;
  createAllocationError: (code: string, message: string, allocationRequestId?: string, context?: Record<string, any>) => AllocationError;
  createEnvironmentError: (code: string, message: string, environmentId: string, context?: Record<string, any>) => EnvironmentError;
  createNetworkError: (code: string, message: string, endpoint?: string, httpStatus?: number, context?: Record<string, any>) => NetworkError;
  createUserInputError: (code: string, message: string, fieldName?: string, context?: Record<string, any>) => UserInputError;
  createSystemError: (code: string, message: string, serviceType?: string, context?: Record<string, any>) => SystemError;
  
  // Error handling methods
  handleError: (error: ErrorDetails) => void;
  handleApiError: (error: any, endpoint?: string) => ErrorDetails;
  handleWebSocketError: (error: Event | Error, connectionType: 'websocket' | 'sse') => ErrorDetails;
  
  // Error management
  clearErrors: () => void;
  removeError: (errorId: string) => void;
  suppressError: (errorId: string) => void;
  
  // Retry functionality
  retry: <T>(error: ErrorDetails, operation: () => Promise<T>) => Promise<T>;
  canRetry: (error: ErrorDetails) => boolean;
  
  // Async operation wrapper with error handling
  withErrorHandling: <T>(
    operation: () => Promise<T>,
    errorContext?: Record<string, any>
  ) => Promise<T | null>;
  
  // Fallback data
  getFallbackData: (error: ErrorDetails) => any;
}

export const useErrorHandling = (options: UseErrorHandlingOptions = {}): UseErrorHandlingReturn => {
  const [errors, setErrors] = useState<ErrorDetails[]>([]);
  const optionsRef = useRef(options);
  
  // Update options ref when options change
  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  // Subscribe to global error events
  useEffect(() => {
    const unsubscribe = errorHandlingService.addErrorListener((error: ErrorDetails) => {
      if (!optionsRef.current.suppressNotifications) {
        setErrors(prev => [error, ...prev.slice(0, 9)]); // Keep last 10 errors
        optionsRef.current.onError?.(error);
      }
    });

    return unsubscribe;
  }, []);

  // Error creation methods
  const createError = useCallback((
    errorInput: Partial<ErrorDetails> | Error | string,
    context?: Record<string, any>
  ): ErrorDetails => {
    return errorHandlingService.createError(errorInput, context);
  }, []);

  const createAllocationError = useCallback((
    code: string,
    message: string,
    allocationRequestId?: string,
    context?: Record<string, any>
  ): AllocationError => {
    return errorHandlingService.createAllocationError(code, message, allocationRequestId, context);
  }, []);

  const createEnvironmentError = useCallback((
    code: string,
    message: string,
    environmentId: string,
    context?: Record<string, any>
  ): EnvironmentError => {
    return errorHandlingService.createEnvironmentError(code, message, environmentId, context);
  }, []);

  const createNetworkError = useCallback((
    code: string,
    message: string,
    endpoint?: string,
    httpStatus?: number,
    context?: Record<string, any>
  ): NetworkError => {
    return errorHandlingService.createNetworkError(code, message, endpoint, httpStatus, context);
  }, []);

  const createUserInputError = useCallback((
    code: string,
    message: string,
    fieldName?: string,
    context?: Record<string, any>
  ): UserInputError => {
    const baseError = errorHandlingService.createError({
      code,
      message,
      category: ErrorCategory.USER_INPUT
    }, context);

    return {
      ...baseError,
      category: ErrorCategory.USER_INPUT,
      fieldName
    } as UserInputError;
  }, []);

  const createSystemError = useCallback((
    code: string,
    message: string,
    serviceType?: string,
    context?: Record<string, any>
  ): SystemError => {
    const baseError = errorHandlingService.createError({
      code,
      message,
      category: ErrorCategory.SYSTEM
    }, context);

    return {
      ...baseError,
      category: ErrorCategory.SYSTEM,
      serviceType
    } as SystemError;
  }, []);

  // Error handling methods
  const handleError = useCallback((error: ErrorDetails) => {
    errorHandlingService.handleError(error);
    
    if (!optionsRef.current.suppressNotifications) {
      setErrors(prev => [error, ...prev.slice(0, 9)]);
      optionsRef.current.onError?.(error);
    }
  }, []);

  const handleApiError = useCallback((error: any, endpoint?: string): ErrorDetails => {
    const standardizedError = errorHandlingService.handleApiError(error, endpoint);
    handleError(standardizedError);
    return standardizedError;
  }, [handleError]);

  const handleWebSocketError = useCallback((
    error: Event | Error,
    connectionType: 'websocket' | 'sse'
  ): ErrorDetails => {
    const standardizedError = errorHandlingService.handleWebSocketError(error, connectionType);
    handleError(standardizedError);
    return standardizedError;
  }, [handleError]);

  // Error management
  const clearErrors = useCallback(() => {
    setErrors([]);
  }, []);

  const removeError = useCallback((errorId: string) => {
    setErrors(prev => prev.filter(error => error.id !== errorId));
  }, []);

  const suppressError = useCallback((errorId: string) => {
    errorHandlingService.suppressError(errorId);
    removeError(errorId);
  }, [removeError]);

  // Retry functionality
  const retry = useCallback(async <T>(
    error: ErrorDetails,
    operation: () => Promise<T>
  ): Promise<T> => {
    try {
      const result = await errorHandlingService.retry(error, operation);
      // Remove error from local state on successful retry
      removeError(error.id);
      return result;
    } catch (retryError) {
      // Handle retry failure
      const newError = createError(retryError as Error, {
        originalErrorId: error.id,
        retryAttempt: true
      });
      handleError(newError);
      throw retryError;
    }
  }, [removeError, createError, handleError]);

  const canRetry = useCallback((error: ErrorDetails): boolean => {
    return errorHandlingService.shouldRetry(error);
  }, []);

  // Async operation wrapper with error handling
  const withErrorHandling = useCallback(async <T>(
    operation: () => Promise<T>,
    errorContext?: Record<string, any>
  ): Promise<T | null> => {
    try {
      return await operation();
    } catch (error) {
      const standardizedError = createError(error as Error, errorContext);
      handleError(standardizedError);
      
      // Try to get fallback data
      if (optionsRef.current.fallbackData !== undefined) {
        return optionsRef.current.fallbackData;
      }
      
      const fallbackData = errorHandlingService.applyFallback(standardizedError);
      return fallbackData;
    }
  }, [createError, handleError]);

  // Get fallback data for an error
  const getFallbackData = useCallback((error: ErrorDetails): any => {
    if (optionsRef.current.fallbackData !== undefined) {
      return optionsRef.current.fallbackData;
    }
    return errorHandlingService.applyFallback(error);
  }, []);

  // Computed values
  const hasErrors = errors.length > 0;
  const lastError = errors[0];

  return {
    // Error state
    errors,
    hasErrors,
    lastError,
    
    // Error creation methods
    createError,
    createAllocationError,
    createEnvironmentError,
    createNetworkError,
    createUserInputError,
    createSystemError,
    
    // Error handling methods
    handleError,
    handleApiError,
    handleWebSocketError,
    
    // Error management
    clearErrors,
    removeError,
    suppressError,
    
    // Retry functionality
    retry,
    canRetry,
    
    // Async operation wrapper
    withErrorHandling,
    
    // Fallback data
    getFallbackData
  };
};

export default useErrorHandling;