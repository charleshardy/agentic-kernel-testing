/**
 * Error Context Provider for Environment Allocation UI
 * Provides global error state management and notification system
 */

import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { ErrorDetails, ErrorContextValue } from '../types/errors';
import errorHandlingService from '../services/errorHandling';
import NotificationSystem from '../components/NotificationSystem';

interface ErrorProviderProps {
  children: ReactNode;
  diagnosticMode?: boolean;
  maxErrors?: number;
}

const ErrorContext = createContext<ErrorContextValue | undefined>(undefined);

export const ErrorProvider: React.FC<ErrorProviderProps> = ({
  children,
  diagnosticMode = false,
  maxErrors = 50
}) => {
  const [errors, setErrors] = useState<ErrorDetails[]>([]);
  const [diagnosticModeEnabled, setDiagnosticModeEnabled] = useState(diagnosticMode);

  // Subscribe to global error events
  useEffect(() => {
    const unsubscribe = errorHandlingService.addErrorListener((error: ErrorDetails) => {
      setErrors(prev => [error, ...prev.slice(0, maxErrors - 1)]);
    });

    return unsubscribe;
  }, [maxErrors]);

  const addError = useCallback((errorInput: Omit<ErrorDetails, 'id' | 'timestamp'>) => {
    const error = errorHandlingService.createError(errorInput);
    errorHandlingService.handleError(error);
  }, []);

  const removeError = useCallback((errorId: string) => {
    setErrors(prev => prev.filter(error => error.id !== errorId));
  }, []);

  const clearErrors = useCallback(() => {
    setErrors([]);
    errorHandlingService.clearSuppressedErrors();
  }, []);

  const retryError = useCallback(async (errorId: string) => {
    const error = errors.find(e => e.id === errorId);
    if (!error) {
      throw new Error(`Error with ID ${errorId} not found`);
    }

    if (!errorHandlingService.shouldRetry(error)) {
      throw new Error(`Error ${error.code} is not retryable`);
    }

    // The actual retry operation would be handled by the component that created the error
    // This is just for managing the error state
    console.log(`Retry requested for error: ${error.code}`);
  }, [errors]);

  const suppressError = useCallback((errorId: string) => {
    errorHandlingService.suppressError(errorId);
    removeError(errorId);
  }, [removeError]);

  const toggleDiagnosticMode = useCallback(() => {
    setDiagnosticModeEnabled(prev => !prev);
  }, []);

  const contextValue: ErrorContextValue = {
    errors,
    addError,
    removeError,
    clearErrors,
    retryError,
    suppressError,
    toggleDiagnosticMode,
    diagnosticMode: diagnosticModeEnabled
  };

  return (
    <ErrorContext.Provider value={contextValue}>
      {children}
      <NotificationSystem
        diagnosticMode={diagnosticModeEnabled}
        onDiagnosticModeChange={setDiagnosticModeEnabled}
      />
    </ErrorContext.Provider>
  );
};

export const useErrorContext = (): ErrorContextValue => {
  const context = useContext(ErrorContext);
  if (context === undefined) {
    throw new Error('useErrorContext must be used within an ErrorProvider');
  }
  return context;
};

export default ErrorProvider;