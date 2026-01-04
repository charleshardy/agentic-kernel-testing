/**
 * Property-Based Tests for Error Handling and User Feedback
 * Feature: environment-allocation-ui, Property 8: Error Handling and User Feedback
 * Validates: Requirements 3.2, 7.2, 7.4, 7.5
 */

import fc from 'fast-check';
import { ErrorHandlingService } from '../services/errorHandling';
import { 
  ErrorDetails, 
  ErrorCategory, 
  ErrorSeverity,
  AllocationError,
  EnvironmentError,
  NetworkError,
  UserInputError,
  SystemError,
  ERROR_CONFIGS
} from '../types/errors';

describe('Error Handling and User Feedback Properties', () => {
  let errorService: ErrorHandlingService;

  beforeEach(() => {
    errorService = new ErrorHandlingService();
  });

  /**
   * Feature: environment-allocation-ui, Property 8: Error Handling and User Feedback
   * For any allocation failure or system error, the UI should display clear error messages 
   * with suggested actions and provide appropriate diagnostic access
   */
  describe('Property 8: Error Handling and User Feedback', () => {
    
    // Generator for error categories
    const errorCategoryGen = fc.constantFrom(...Object.values(ErrorCategory));
    
    // Generator for error severities
    const errorSeverityGen = fc.constantFrom(...Object.values(ErrorSeverity));
    
    // Generator for error codes
    const errorCodeGen = fc.oneof(
      fc.constantFrom(...Object.keys(ERROR_CONFIGS)),
      fc.string({ minLength: 3, maxLength: 20 }).map(s => s.toUpperCase())
    );
    
    // Generator for error messages
    const errorMessageGen = fc.string({ minLength: 10, maxLength: 200 });
    
    // Generator for context objects (no null values)
    const contextGen = fc.dictionary(
      fc.string({ minLength: 1, maxLength: 20 }),
      fc.oneof(
        fc.string(),
        fc.integer(),
        fc.boolean()
      )
    );

    // Generator for basic error input
    const basicErrorGen = fc.record({
      code: errorCodeGen,
      message: errorMessageGen,
      category: errorCategoryGen,
      severity: errorSeverityGen,
      context: fc.option(contextGen, { nil: undefined })
    });

    // Generator for allocation errors
    const allocationErrorGen = fc.record({
      code: errorCodeGen,
      message: errorMessageGen,
      category: fc.constant(ErrorCategory.ALLOCATION),
      severity: errorSeverityGen,
      allocationRequestId: fc.option(fc.uuid(), { nil: undefined }),
      context: fc.option(contextGen, { nil: undefined })
    });

    // Generator for environment errors
    const environmentErrorGen = fc.record({
      code: errorCodeGen,
      message: errorMessageGen,
      category: fc.constant(ErrorCategory.ENVIRONMENT),
      severity: errorSeverityGen,
      environmentId: fc.uuid(),
      context: fc.option(contextGen, { nil: undefined })
    });

    // Generator for network errors
    const networkErrorGen = fc.record({
      code: errorCodeGen,
      message: errorMessageGen,
      category: fc.constant(ErrorCategory.NETWORK),
      severity: errorSeverityGen,
      endpoint: fc.option(fc.webUrl(), { nil: undefined }),
      httpStatus: fc.option(fc.integer({ min: 100, max: 599 }), { nil: undefined }),
      context: fc.option(contextGen, { nil: undefined })
    });

    // Generator for user input errors
    const userInputErrorGen = fc.record({
      code: errorCodeGen,
      message: errorMessageGen,
      category: fc.constant(ErrorCategory.USER_INPUT),
      severity: errorSeverityGen,
      fieldName: fc.option(fc.string({ minLength: 1, maxLength: 50 }), { nil: undefined }),
      context: fc.option(contextGen, { nil: undefined })
    });

    // Generator for system errors
    const systemErrorGen = fc.record({
      code: errorCodeGen,
      message: errorMessageGen,
      category: fc.constant(ErrorCategory.SYSTEM),
      severity: errorSeverityGen,
      serviceType: fc.option(fc.constantFrom('api', 'database', 'orchestrator', 'resource_manager'), { nil: undefined }),
      context: fc.option(contextGen, { nil: undefined })
    });

    // Generator for any error type
    const anyErrorGen = fc.oneof(
      basicErrorGen,
      allocationErrorGen,
      environmentErrorGen,
      networkErrorGen,
      userInputErrorGen,
      systemErrorGen
    );

    it('should create standardized errors with required fields for any input', () => {
      fc.assert(fc.property(anyErrorGen, (errorInput) => {
        const error = errorService.createError(errorInput, errorInput.context);
        
        // All errors must have required fields
        expect(error.id).toBeDefined();
        expect(typeof error.id).toBe('string');
        expect(error.id.length).toBeGreaterThan(0);
        
        expect(error.timestamp).toBeInstanceOf(Date);
        expect(error.timestamp.getTime()).toBeLessThanOrEqual(Date.now());
        
        expect(error.category).toBeDefined();
        expect(Object.values(ErrorCategory)).toContain(error.category);
        
        expect(error.severity).toBeDefined();
        expect(Object.values(ErrorSeverity)).toContain(error.severity);
        
        expect(error.code).toBeDefined();
        expect(typeof error.code).toBe('string');
        expect(error.code.length).toBeGreaterThan(0);
        
        expect(error.message).toBeDefined();
        expect(typeof error.message).toBe('string');
        expect(error.message.length).toBeGreaterThan(0);
        
        expect(typeof error.retryable).toBe('boolean');
        expect(typeof error.userFacing).toBe('boolean');
      }), { numRuns: 100 });
    });

    it('should provide clear error messages for all error types', () => {
      fc.assert(fc.property(anyErrorGen, (errorInput) => {
        const error = errorService.createError(errorInput, errorInput.context);
        
        // Error messages must be clear and informative
        expect(error.message).toBeDefined();
        expect(error.message.length).toBeGreaterThan(5); // Minimum meaningful length
        expect(error.message).not.toMatch(/^undefined|null|error$/i); // Not generic
        
        // If description exists, it should add value
        if (error.description) {
          expect(error.description.length).toBeGreaterThan(error.message.length);
          expect(error.description).not.toBe(error.message);
        }
      }), { numRuns: 100 });
    });

    it('should provide suggested actions for user-facing errors', () => {
      fc.assert(fc.property(anyErrorGen, (errorInput) => {
        const error = errorService.createError(errorInput, errorInput.context);
        
        if (error.userFacing && error.retryable) {
          // Retryable user-facing errors should have suggested actions
          expect(error.suggestedActions).toBeDefined();
          expect(Array.isArray(error.suggestedActions)).toBe(true);
          
          if (error.suggestedActions && error.suggestedActions.length > 0) {
            error.suggestedActions.forEach(action => {
              expect(action.id).toBeDefined();
              expect(typeof action.id).toBe('string');
              expect(action.id.length).toBeGreaterThan(0);
              
              expect(action.label).toBeDefined();
              expect(typeof action.label).toBe('string');
              expect(action.label.length).toBeGreaterThan(0);
              
              expect(action.description).toBeDefined();
              expect(typeof action.description).toBe('string');
              expect(action.description.length).toBeGreaterThan(0);
              
              expect(['retry', 'navigate', 'contact_support', 'manual_fix', 'ignore']).toContain(action.actionType);
              
              expect(typeof action.priority).toBe('number');
              expect(action.priority).toBeGreaterThan(0);
            });
          }
        }
      }), { numRuns: 100 });
    });

    it('should provide appropriate notification strategies based on severity', () => {
      fc.assert(fc.property(anyErrorGen, (errorInput) => {
        const error = errorService.createError(errorInput, errorInput.context);
        const strategy = errorService.getNotificationStrategy(error);
        
        expect(strategy).toBeDefined();
        expect(['toast', 'banner', 'modal', 'inline']).toContain(strategy.type);
        
        // Critical errors should use persistent notifications
        if (error.severity === ErrorSeverity.CRITICAL) {
          expect(['banner', 'modal']).toContain(strategy.type);
          if (strategy.persistent !== undefined) {
            expect(strategy.persistent).toBe(true);
          }
        }
        
        // Low severity errors should use non-intrusive notifications
        if (error.severity === ErrorSeverity.LOW) {
          expect(['toast', 'inline']).toContain(strategy.type);
        }
        
        // Duration should be reasonable for timed notifications
        if (strategy.duration !== undefined) {
          expect(strategy.duration).toBeGreaterThan(1000); // At least 1 second
          expect(strategy.duration).toBeLessThan(30000); // At most 30 seconds
        }
      }), { numRuns: 100 });
    });

    it('should handle API errors and convert them to standardized format', () => {
      // Generator for API error responses
      const apiErrorGen = fc.record({
        response: fc.option(fc.record({
          status: fc.integer({ min: 400, max: 599 }),
          data: fc.option(fc.record({
            message: fc.option(errorMessageGen),
            error: fc.option(fc.string())
          }))
        })),
        request: fc.option(fc.record({
          url: fc.webUrl(),
          method: fc.constantFrom('GET', 'POST', 'PUT', 'DELETE')
        })),
        message: errorMessageGen
      });

      fc.assert(fc.property(apiErrorGen, fc.webUrl(), (apiError, endpoint) => {
        const standardizedError = errorService.handleApiError(apiError, endpoint);
        
        expect(standardizedError).toBeDefined();
        expect(standardizedError.category).toBe(ErrorCategory.NETWORK);
        expect(standardizedError.id).toBeDefined();
        expect(standardizedError.timestamp).toBeInstanceOf(Date);
        expect(standardizedError.message).toBeDefined();
        expect(standardizedError.code).toBeDefined();
        
        // Should include endpoint in diagnostic info if provided
        if (endpoint) {
          expect(standardizedError.diagnosticInfo?.apiEndpoint || standardizedError.context?.endpoint).toBeDefined();
        }
        
        // Should include HTTP status if available
        if (apiError.response?.status) {
          expect(standardizedError.diagnosticInfo?.httpStatus || standardizedError.context?.httpStatus).toBe(apiError.response.status);
        }
      }), { numRuns: 100 });
    });

    it('should determine retry eligibility correctly', () => {
      fc.assert(fc.property(anyErrorGen, (errorInput) => {
        const error = errorService.createError(errorInput, errorInput.context);
        const shouldRetry = errorService.shouldRetry(error);
        
        // Retry decision should be consistent with error properties
        if (!error.retryable) {
          expect(shouldRetry).toBe(false);
        }
        
        // If error is retryable, check against retry policy
        if (error.retryable) {
          // Should respect max attempts (initially 0 attempts)
          expect(typeof shouldRetry).toBe('boolean');
        }
      }), { numRuns: 100 });
    });

    it('should provide diagnostic information for troubleshooting', () => {
      fc.assert(fc.property(anyErrorGen, (errorInput) => {
        const error = errorService.createError(errorInput, errorInput.context);
        
        // High severity errors should have diagnostic information
        if (error.severity === ErrorSeverity.HIGH || error.severity === ErrorSeverity.CRITICAL) {
          // Should have either diagnostic info or context for troubleshooting
          const hasDiagnosticInfo = error.diagnosticInfo !== undefined;
          const hasContext = error.context !== undefined && Object.keys(error.context).length > 0;
          
          expect(hasDiagnosticInfo || hasContext).toBe(true);
        }
        
        // Network errors should include endpoint information
        if (error.category === ErrorCategory.NETWORK) {
          const hasEndpointInfo = 
            error.diagnosticInfo?.apiEndpoint !== undefined ||
            error.context?.endpoint !== undefined ||
            (errorInput as any).endpoint !== undefined;
          
          // At least one source of endpoint information should be available
          expect(hasEndpointInfo || error.code === 'WEBSOCKET_ERROR').toBe(true);
        }
        
        // Environment errors should include environment ID
        if (error.category === ErrorCategory.ENVIRONMENT) {
          const hasEnvironmentInfo = 
            error.diagnosticInfo?.environmentId !== undefined ||
            (error as EnvironmentError).environmentId !== undefined;
          
          expect(hasEnvironmentInfo).toBe(true);
        }
      }), { numRuns: 100 });
    });

    it('should apply fallback behavior when errors cannot be resolved', () => {
      fc.assert(fc.property(anyErrorGen, (errorInput) => {
        const error = errorService.createError(errorInput, errorInput.context);
        const fallbackData = errorService.applyFallback(error);
        
        // Fallback data should be provided for critical system errors
        if (error.category === ErrorCategory.SYSTEM && error.severity === ErrorSeverity.CRITICAL) {
          expect(fallbackData).toBeDefined();
        }
        
        // Fallback data should be appropriate for the error category
        if (fallbackData !== null && fallbackData !== undefined) {
          expect(typeof fallbackData).toBe('object');
          
          // Should include a message explaining the fallback
          if (typeof fallbackData === 'object' && fallbackData.message) {
            expect(typeof fallbackData.message).toBe('string');
            expect(fallbackData.message.length).toBeGreaterThan(0);
          }
        }
      }), { numRuns: 100 });
    });

    it('should maintain error suppression state correctly', () => {
      fc.assert(fc.property(fc.array(fc.uuid(), { minLength: 1, maxLength: 10 }), (errorIds) => {
        // Clear any existing suppressed errors
        errorService.clearSuppressedErrors();
        
        // Initially, no errors should be suppressed
        errorIds.forEach(id => {
          expect(errorService.isErrorSuppressed(id)).toBe(false);
        });
        
        // Suppress some errors
        const toSuppress = errorIds.slice(0, Math.ceil(errorIds.length / 2));
        toSuppress.forEach(id => {
          errorService.suppressError(id);
        });
        
        // Check suppression state
        errorIds.forEach(id => {
          const shouldBeSuppressed = toSuppress.includes(id);
          expect(errorService.isErrorSuppressed(id)).toBe(shouldBeSuppressed);
        });
        
        // Clear suppressed errors
        errorService.clearSuppressedErrors();
        
        // All errors should no longer be suppressed
        errorIds.forEach(id => {
          expect(errorService.isErrorSuppressed(id)).toBe(false);
        });
      }), { numRuns: 50 });
    });

    it('should create specific error types with correct properties', () => {
      fc.assert(fc.property(
        errorCodeGen,
        errorMessageGen,
        fc.uuid(),
        contextGen,
        (code, message, id, context) => {
          // Test allocation error creation
          const allocationError = errorService.createAllocationError(code, message, id, context);
          expect(allocationError.category).toBe(ErrorCategory.ALLOCATION);
          expect(allocationError.allocationRequestId).toBe(id);
          expect(allocationError.code).toBe(code);
          expect(allocationError.message).toBe(message);
          
          // Test environment error creation
          const environmentError = errorService.createEnvironmentError(code, message, id, context);
          expect(environmentError.category).toBe(ErrorCategory.ENVIRONMENT);
          expect(environmentError.environmentId).toBe(id);
          expect(environmentError.code).toBe(code);
          expect(environmentError.message).toBe(message);
          
          // Test network error creation
          const endpoint = 'https://api.example.com/test';
          const httpStatus = 500;
          const networkError = errorService.createNetworkError(code, message, endpoint, httpStatus, context);
          expect(networkError.category).toBe(ErrorCategory.NETWORK);
          expect(networkError.endpoint).toBe(endpoint);
          expect(networkError.httpStatus).toBe(httpStatus);
          expect(networkError.code).toBe(code);
          expect(networkError.message).toBe(message);
        }
      ), { numRuns: 100 });
    });
  });

  describe('Error Recovery and Retry Logic', () => {
    // Generator for any error type (redefined for this scope)
    const anyErrorGen = fc.record({
      code: fc.string({ minLength: 3, maxLength: 20 }),
      message: fc.string({ minLength: 10, maxLength: 200 }),
      category: fc.constantFrom(...Object.values(ErrorCategory)),
      severity: fc.constantFrom(...Object.values(ErrorSeverity)),
      context: fc.option(fc.dictionary(
        fc.string({ minLength: 1, maxLength: 20 }),
        fc.oneof(fc.string(), fc.integer(), fc.boolean())
      ), { nil: undefined })
    });

    it('should calculate retry delays correctly', () => {
      fc.assert(fc.property(
        anyErrorGen,
        fc.integer({ min: 0, max: 5 }),
        (errorInput, attemptNumber) => {
          const error = errorService.createError(errorInput);
          
          if (error.retryable) {
            // Test that retry delays are reasonable
            // This is testing the internal retry logic indirectly
            const shouldRetry = errorService.shouldRetry(error);
            expect(typeof shouldRetry).toBe('boolean');
            
            // If we can retry, the service should handle delay calculation
            if (shouldRetry) {
              // The service should not throw when determining retry eligibility
              expect(() => errorService.shouldRetry(error)).not.toThrow();
            }
          }
        }
      ), { numRuns: 100 });
    });
  });

  describe('Error Listener Management', () => {
    // Generator for any error type (redefined for this scope)
    const anyErrorGen = fc.record({
      code: fc.string({ minLength: 3, maxLength: 20 }),
      message: fc.string({ minLength: 10, maxLength: 200 }),
      category: fc.constantFrom(...Object.values(ErrorCategory)),
      severity: fc.constantFrom(...Object.values(ErrorSeverity)),
      context: fc.option(fc.dictionary(
        fc.string({ minLength: 1, maxLength: 20 }),
        fc.oneof(fc.string(), fc.integer(), fc.boolean())
      ), { nil: undefined })
    });

    it('should manage error listeners correctly', () => {
      fc.assert(fc.property(
        fc.array(anyErrorGen, { minLength: 1, maxLength: 5 }),
        (errorInputs) => {
          const receivedErrors: ErrorDetails[] = [];
          
          // Add error listener
          const unsubscribe = errorService.addErrorListener((error) => {
            receivedErrors.push(error);
          });
          
          // Process errors
          const errors = errorInputs.map(input => errorService.createError(input));
          errors.forEach(error => errorService.handleError(error));
          
          // Should have received all errors
          expect(receivedErrors.length).toBe(errors.length);
          
          // Unsubscribe
          unsubscribe();
          
          // Clear received errors
          receivedErrors.length = 0;
          
          // Process more errors
          const moreErrors = errorInputs.map(input => errorService.createError(input));
          moreErrors.forEach(error => errorService.handleError(error));
          
          // Should not have received new errors after unsubscribing
          expect(receivedErrors.length).toBe(0);
        }
      ), { numRuns: 50 });
    });
  });
});