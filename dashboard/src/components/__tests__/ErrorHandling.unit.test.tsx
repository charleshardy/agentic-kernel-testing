/**
 * Unit tests for Error Handling components
 * 
 * **Feature: environment-allocation-ui, Task 14.1: Unit tests for component interactions**
 * **Validates: Requirements 3.2, 7.2, 7.4, 7.5**
 */

import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'

import { ErrorBoundary, ErrorAlert, ErrorRecovery } from '../ErrorHandling'
import { ErrorDetails } from '../ErrorHandling/ErrorAlert'
import { RecoveryAction } from '../ErrorHandling/ErrorRecovery'

// Mock console methods to avoid noise in tests
const originalConsoleError = console.error
beforeAll(() => {
  console.error = jest.fn()
})

afterAll(() => {
  console.error = originalConsoleError
})

// Component that throws an error for testing ErrorBoundary
const ThrowError: React.FC<{ shouldThrow: boolean }> = ({ shouldThrow }) => {
  if (shouldThrow) {
    throw new Error('Test error for ErrorBoundary')
  }
  return <div>No error</div>
}

describe('ErrorBoundary Component', () => {
  test('should render children when no error occurs', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )

    expect(screen.getByText('No error')).toBeInTheDocument()
  })

  test('should catch and display error when child component throws', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    expect(screen.getByText('An unexpected error occurred while rendering this component.')).toBeInTheDocument()
  })

  test('should display retry and reload buttons', () => {
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByRole('button', { name: /try again/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /reload page/i })).toBeInTheDocument()
  })

  test('should call onError callback when error occurs', () => {
    const onError = jest.fn()
    
    render(
      <ErrorBoundary onError={onError}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(onError).toHaveBeenCalledWith(
      expect.any(Error),
      expect.objectContaining({
        componentStack: expect.any(String)
      })
    )
  })

  test('should show error details in development mode', () => {
    const originalEnv = process.env.NODE_ENV
    process.env.NODE_ENV = 'development'

    render(
      <ErrorBoundary showDetails={true}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('Error Details')).toBeInTheDocument()
    
    process.env.NODE_ENV = originalEnv
  })

  test('should reset error state when retry button is clicked', async () => {
    const user = userEvent.setup()
    
    const { rerender } = render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    )

    expect(screen.getByText('Something went wrong')).toBeInTheDocument()

    const retryButton = screen.getByRole('button', { name: /try again/i })
    await user.click(retryButton)

    // Re-render with no error
    rerender(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    )

    expect(screen.getByText('No error')).toBeInTheDocument()
  })
})

describe('ErrorAlert Component', () => {
  const mockError: ErrorDetails = {
    id: 'test-error-1',
    message: 'Test error message',
    type: 'network',
    severity: 'high',
    timestamp: new Date(),
    suggestedActions: ['Check network connection', 'Retry the operation'],
    retryable: true,
    diagnosticInfo: {
      endpoint: '/api/test',
      statusCode: 500,
      responseTime: 1500
    }
  }

  test('should render error message and details', () => {
    render(<ErrorAlert error={mockError} />)

    expect(screen.getByText('Network Error')).toBeInTheDocument()
    expect(screen.getByText('Test error message')).toBeInTheDocument()
    expect(screen.getByText('NETWORK')).toBeInTheDocument()
    expect(screen.getByText('HIGH')).toBeInTheDocument()
  })

  test('should display suggested actions', () => {
    render(<ErrorAlert error={mockError} />)

    expect(screen.getByText('Suggested Actions:')).toBeInTheDocument()
    expect(screen.getByText('Check network connection')).toBeInTheDocument()
    expect(screen.getByText('Retry the operation')).toBeInTheDocument()
  })

  test('should show diagnostic information', () => {
    render(<ErrorAlert error={mockError} />)

    expect(screen.getByText('Diagnostic Information:')).toBeInTheDocument()
    expect(screen.getByText('Endpoint: /api/test')).toBeInTheDocument()
    expect(screen.getByText('Status: 500')).toBeInTheDocument()
    expect(screen.getByText('Response Time: 1500ms')).toBeInTheDocument()
  })

  test('should show retry button for retryable errors', () => {
    const onRetry = jest.fn()
    
    render(<ErrorAlert error={mockError} onRetry={onRetry} />)

    const retryButton = screen.getByRole('button', { name: /retry/i })
    expect(retryButton).toBeInTheDocument()
  })

  test('should call onRetry when retry button is clicked', async () => {
    const user = userEvent.setup()
    const onRetry = jest.fn()
    
    render(<ErrorAlert error={mockError} onRetry={onRetry} />)

    const retryButton = screen.getByRole('button', { name: /retry/i })
    await user.click(retryButton)

    expect(onRetry).toHaveBeenCalledWith('test-error-1')
  })

  test('should call onDismiss when dismiss button is clicked', async () => {
    const user = userEvent.setup()
    const onDismiss = jest.fn()
    
    render(<ErrorAlert error={mockError} onDismiss={onDismiss} />)

    const dismissButton = screen.getByRole('button', { name: /dismiss/i })
    await user.click(dismissButton)

    expect(onDismiss).toHaveBeenCalledWith('test-error-1')
  })

  test('should auto-hide after delay for non-critical errors', async () => {
    const onDismiss = jest.fn()
    const lowSeverityError = { ...mockError, severity: 'low' as const }
    
    render(
      <ErrorAlert 
        error={lowSeverityError} 
        onDismiss={onDismiss} 
        autoHide={true}
        autoHideDelay={100}
      />
    )

    await waitFor(() => {
      expect(onDismiss).toHaveBeenCalledWith('test-error-1')
    }, { timeout: 200 })
  })

  test('should not auto-hide critical errors', async () => {
    const onDismiss = jest.fn()
    const criticalError = { ...mockError, severity: 'critical' as const }
    
    render(
      <ErrorAlert 
        error={criticalError} 
        onDismiss={onDismiss} 
        autoHide={true}
        autoHideDelay={100}
      />
    )

    await new Promise(resolve => setTimeout(resolve, 150))
    expect(onDismiss).not.toHaveBeenCalled()
  })

  test('should render in compact mode', () => {
    render(<ErrorAlert error={mockError} compact={true} />)

    // In compact mode, only basic message should be shown
    expect(screen.getByText('Test error message')).toBeInTheDocument()
    expect(screen.queryByText('Suggested Actions:')).not.toBeInTheDocument()
  })

  test('should show technical details when details button is clicked', async () => {
    const user = userEvent.setup()
    const errorWithContext = {
      ...mockError,
      context: { userId: '123', sessionId: 'abc' },
      stack: 'Error stack trace here'
    }
    
    render(<ErrorAlert error={errorWithContext} showDetails={true} />)

    const detailsButton = screen.getByRole('button', { name: /details/i })
    await user.click(detailsButton)

    expect(screen.getByText('Technical Details')).toBeInTheDocument()
  })
})

describe('ErrorRecovery Component', () => {
  const mockError = new Error('Test recovery error')
  
  const mockRecoveryActions: RecoveryAction[] = [
    {
      id: 'refresh',
      label: 'Refresh Data',
      description: 'Reload the data from server',
      action: jest.fn().mockResolvedValue(undefined),
      type: 'primary'
    },
    {
      id: 'reset',
      label: 'Reset Settings',
      description: 'Reset to default settings',
      action: jest.fn().mockResolvedValue(undefined)
    }
  ]

  beforeEach(() => {
    jest.clearAllMocks()
  })

  test('should render error details and recovery options', () => {
    render(
      <ErrorRecovery 
        error={mockError}
        recoveryActions={mockRecoveryActions}
      />
    )

    expect(screen.getByText('Error Recovery')).toBeInTheDocument()
    expect(screen.getByText('Test recovery error')).toBeInTheDocument()
    expect(screen.getByText('Recovery Options:')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /refresh data/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /reset settings/i })).toBeInTheDocument()
  })

  test('should show retry button when onRetry is provided', () => {
    const onRetry = jest.fn()
    
    render(
      <ErrorRecovery 
        error={mockError}
        onRetry={onRetry}
        recoveryActions={mockRecoveryActions}
      />
    )

    expect(screen.getByRole('button', { name: /retry now/i })).toBeInTheDocument()
  })

  test('should call onRetry when retry button is clicked', async () => {
    const user = userEvent.setup()
    const onRetry = jest.fn().mockResolvedValue(undefined)
    
    render(
      <ErrorRecovery 
        error={mockError}
        onRetry={onRetry}
        recoveryActions={mockRecoveryActions}
      />
    )

    const retryButton = screen.getByRole('button', { name: /retry now/i })
    await user.click(retryButton)

    expect(onRetry).toHaveBeenCalled()
  })

  test('should execute recovery action when clicked', async () => {
    const user = userEvent.setup()
    
    render(
      <ErrorRecovery 
        error={mockError}
        recoveryActions={mockRecoveryActions}
      />
    )

    const refreshButton = screen.getByRole('button', { name: /refresh data/i })
    await user.click(refreshButton)

    expect(mockRecoveryActions[0].action).toHaveBeenCalled()
  })

  test('should show loading state during recovery action', async () => {
    const user = userEvent.setup()
    const slowAction = jest.fn(() => new Promise(resolve => setTimeout(resolve, 100)))
    const actionsWithSlowAction = [
      { ...mockRecoveryActions[0], action: slowAction }
    ]
    
    render(
      <ErrorRecovery 
        error={mockError}
        recoveryActions={actionsWithSlowAction}
      />
    )

    const refreshButton = screen.getByRole('button', { name: /refresh data/i })
    
    await user.click(refreshButton)
    
    // Should show loading state
    expect(screen.getByText('Attempting to recover from error...')).toBeInTheDocument()
  })

  test('should call onRecovered when recovery is successful', async () => {
    const user = userEvent.setup()
    const onRecovered = jest.fn()
    
    render(
      <ErrorRecovery 
        error={mockError}
        recoveryActions={mockRecoveryActions}
        onRecovered={onRecovered}
      />
    )

    const refreshButton = screen.getByRole('button', { name: /refresh data/i })
    await user.click(refreshButton)

    await waitFor(() => {
      expect(onRecovered).toHaveBeenCalled()
    })
  })

  test('should show retry policy information', () => {
    const customRetryPolicy = {
      maxAttempts: 5,
      backoffStrategy: 'exponential' as const,
      baseDelay: 2000,
      maxDelay: 30000
    }
    
    render(
      <ErrorRecovery 
        error={mockError}
        retryPolicy={customRetryPolicy}
        recoveryActions={mockRecoveryActions}
      />
    )

    expect(screen.getByText(/Recovery Policy: 5 max attempts/)).toBeInTheDocument()
    expect(screen.getByText(/exponential backoff strategy/)).toBeInTheDocument()
    expect(screen.getByText(/2000ms base delay/)).toBeInTheDocument()
  })

  test('should show reload page button as fallback', () => {
    render(
      <ErrorRecovery 
        error={mockError}
        recoveryActions={mockRecoveryActions}
      />
    )

    expect(screen.getByRole('button', { name: /reload page/i })).toBeInTheDocument()
  })

  test('should perform auto-retry when enabled', async () => {
    const onRetry = jest.fn().mockResolvedValue(undefined)
    
    render(
      <ErrorRecovery 
        error={mockError}
        onRetry={onRetry}
        autoRetry={true}
        recoveryActions={mockRecoveryActions}
      />
    )

    await waitFor(() => {
      expect(onRetry).toHaveBeenCalled()
    })
  })

  test('should show success message when recovered', async () => {
    const user = userEvent.setup()
    const onRecovered = jest.fn()
    
    const { rerender } = render(
      <ErrorRecovery 
        error={mockError}
        recoveryActions={mockRecoveryActions}
        onRecovered={onRecovered}
      />
    )

    const refreshButton = screen.getByRole('button', { name: /refresh data/i })
    await user.click(refreshButton)

    await waitFor(() => {
      expect(onRecovered).toHaveBeenCalled()
    })

    // Simulate recovery success by showing success message
    expect(screen.getByText('Recovery Successful')).toBeInTheDocument()
  })
})