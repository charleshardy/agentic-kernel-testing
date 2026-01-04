import React from 'react'
import { render, screen, waitFor, cleanup, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { MemoryRouter } from 'react-router-dom'
import ExecutionMonitor from '../pages/ExecutionMonitor'
import apiService from '../services/api'

// Mock timers for better control over async operations
jest.useFakeTimers()

// Mock the API service
jest.mock('../services/api')
const mockApiService = apiService as jest.Mocked<typeof apiService>

// Mock the EnvironmentAllocationDashboard component with proper cleanup
jest.mock('../components/EnvironmentAllocationDashboard', () => {
  return function MockEnvironmentAllocationDashboard({ planId, autoRefresh }: any) {
    const [mounted, setMounted] = React.useState(true)
    
    React.useEffect(() => {
      const cleanup = () => {
        setMounted(false)
      }
      
      return cleanup
    }, [])

    if (!mounted) return null

    return (
      <div data-testid="environment-allocation-dashboard">
        <div>Environment Allocation Dashboard</div>
        <div data-testid="plan-id">Plan ID: {planId || 'none'}</div>
        <div data-testid="auto-refresh">Auto Refresh: {autoRefresh ? 'enabled' : 'disabled'}</div>
      </div>
    )
  }
})

// Mock real-time hooks with proper cleanup
const mockDisconnectAll = jest.fn()
const mockReconnectAll = jest.fn()

jest.mock('../hooks/useRealTimeUpdates', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    isConnected: true,
    connectionHealth: 'healthy' as const,
    lastUpdate: new Date(),
    updateCount: 5,
    errors: [],
    webSocket: { 
      isConnected: true,
      isConnecting: false,
      connectionAttempts: 0,
      lastError: null
    },
    sse: { 
      isConnected: true,
      isConnecting: false,
      connectionAttempts: 0,
      lastError: null
    },
    reconnectAll: mockReconnectAll,
    disconnectAll: mockDisconnectAll
  }))
}))

jest.mock('../hooks/useErrorHandling', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    errors: [],
    hasErrors: false,
    lastError: null,
    handleApiError: jest.fn((error) => ({ 
      id: 'test-error',
      code: 'API_ERROR',
      message: error.message || 'API Error',
      category: 'network' as const,
      severity: 'medium' as const,
      timestamp: new Date(),
      retryable: true,
      retryCount: 0,
      maxRetries: 3,
      suppressed: false,
      suggestedActions: []
    })),
    handleWebSocketError: jest.fn(),
    withErrorHandling: jest.fn(async (fn) => {
      try {
        return await fn()
      } catch (error) {
        console.warn('Mock error handling:', error)
        return null
      }
    }),
    createAllocationError: jest.fn(),
    createEnvironmentError: jest.fn(),
    createNetworkError: jest.fn(),
    clearErrors: jest.fn(),
    removeError: jest.fn()
  }))
}))

// Mock WebSocket and EventSource to prevent real connections
const mockWebSocketClose = jest.fn()
const mockEventSourceClose = jest.fn()

// Create proper WebSocket mock with all required static properties
const MockWebSocket = jest.fn().mockImplementation(() => ({
  close: mockWebSocketClose,
  send: jest.fn(),
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: 1, // OPEN
}))

// Add static properties to the mock
MockWebSocket.CONNECTING = 0
MockWebSocket.OPEN = 1
MockWebSocket.CLOSING = 2
MockWebSocket.CLOSED = 3

global.WebSocket = MockWebSocket as any

// Create proper EventSource mock with all required static properties
const MockEventSource = jest.fn().mockImplementation(() => ({
  close: mockEventSourceClose,
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  readyState: 1, // OPEN
}))

// Add static properties to the mock
MockEventSource.CONNECTING = 0
MockEventSource.OPEN = 1
MockEventSource.CLOSED = 2

global.EventSource = MockEventSource as any

// Mock window.history.pushState and navigate
const mockPushState = jest.fn()
const mockNavigate = jest.fn()

Object.defineProperty(window, 'history', {
  value: { pushState: mockPushState },
  writable: true
})

// Mock react-router-dom navigate
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}))

const mockExecutionData = {
  plan_id: 'test-plan-123',
  submission_id: 'sub-123',
  test_plan_name: 'Integration Test Plan',
  overall_status: 'running' as const,
  progress: 0.65,
  estimated_completion: '2024-01-15T12:30:00Z',
  total_tests: 100,
  completed_tests: 65,
  failed_tests: 5,
  test_statuses: [],
  stages: [
    {
      id: 'validation',
      name: 'Plan Validation',
      status: 'completed' as const,
      progress: 100
    },
    {
      id: 'environment',
      name: 'Environment Allocation',
      status: 'running' as const,
      progress: 65
    },
    {
      id: 'execution',
      name: 'Test Execution',
      status: 'waiting' as const,
      progress: 0
    }
  ]
}

const mockEnvironmentData = {
  environments: [
    {
      id: 'env-qemu-x86-1',
      type: 'QEMU x86_64',
      status: 'ready',
      architecture: 'x86_64',
      assignedTests: ['test-1', 'test-2'],
      resources: { cpu: 45, memory: 60, disk: 30 },
      health: 'healthy'
    }
  ],
  queue: [],
  resourceUtilization: [],
  history: [],
  capacityMetrics: {
    totalCapacity: 10,
    usedCapacity: 6,
    availableCapacity: 4
  }
}

const renderWithProviders = (component: React.ReactElement, initialRoute = '/') => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
        staleTime: 0,
        refetchOnWindowFocus: false,
        refetchOnMount: false,
        refetchOnReconnect: false,
        refetchInterval: false, // Disable automatic refetching
      },
      mutations: {
        retry: false,
      },
    },
  })

  const result = render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        {component}
      </MemoryRouter>
    </QueryClientProvider>
  )

  // Return cleanup function along with render result
  return {
    ...result,
    cleanup: () => {
      // Clear all queries and mutations
      queryClient.clear()
      queryClient.getQueryCache().clear()
      queryClient.getMutationCache().clear()
      
      // Cancel any ongoing queries
      queryClient.cancelQueries()
      
      // Remove the query client
      queryClient.removeQueries()
    }
  }
}

describe('ExecutionMonitor Integration Tests', () => {
  let renderResult: any

  beforeEach(() => {
    // Use fake timers for better control
    jest.useFakeTimers()
    
    jest.clearAllMocks()
    mockPushState.mockClear()
    mockNavigate.mockClear()
    mockDisconnectAll.mockClear()
    mockReconnectAll.mockClear()
    mockWebSocketClose.mockClear()
    mockEventSourceClose.mockClear()
    
    // Default mock implementations
    mockApiService.getExecutionStatus.mockResolvedValue(mockExecutionData)
    mockApiService.getActiveExecutions.mockResolvedValue([mockExecutionData])
    mockApiService.getEnvironmentAllocation.mockResolvedValue(mockEnvironmentData)
  })

  afterEach(async () => {
    // Clean up any render result
    if (renderResult?.cleanup) {
      renderResult.cleanup()
    }
    
    // Ensure all mocked connections are closed
    mockDisconnectAll()
    mockWebSocketClose()
    mockEventSourceClose()
    
    // Fast-forward any remaining timers
    act(() => {
      jest.runOnlyPendingTimers()
    })
    
    // Switch back to real timers
    jest.useRealTimers()
    
    // Clean up DOM
    cleanup()
    
    // Clear all mocks
    jest.clearAllMocks()
    
    // Wait a bit for any remaining async operations
    await act(async () => {
      await new Promise(resolve => setTimeout(resolve, 0))
    })
  })

  describe('Basic Integration', () => {
    it('should render ExecutionMonitor with plan ID', async () => {
      await act(async () => {
        renderResult = renderWithProviders(
          <ExecutionMonitor />, 
          '/execution-monitor?planId=test-plan-123'
        )
      })

      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      await waitFor(() => {
        expect(screen.getByText('Execution Monitor')).toBeInTheDocument()
        expect(screen.getByText('test-plan-123')).toBeInTheDocument()
      }, { timeout: 3000 })
    })

    it('should display environment allocation dashboard in tab', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
      
      await act(async () => {
        renderResult = renderWithProviders(
          <ExecutionMonitor />, 
          '/execution-monitor?planId=test-plan-123'
        )
      })

      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      await waitFor(() => {
        expect(screen.getByText('Execution Monitor')).toBeInTheDocument()
      }, { timeout: 3000 })

      // Find and click environment allocation tab
      const environmentTab = screen.getByRole('tab', { name: /environment allocation/i })
      
      await act(async () => {
        await user.click(environmentTab)
        jest.advanceTimersByTime(100)
      })

      // Verify environment allocation dashboard is rendered
      await waitFor(() => {
        expect(screen.getByTestId('environment-allocation-dashboard')).toBeInTheDocument()
        expect(screen.getByTestId('plan-id')).toHaveTextContent('Plan ID: test-plan-123')
      }, { timeout: 2000 })
    })

    it('should navigate to dedicated environment allocation page', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
      
      await act(async () => {
        renderResult = renderWithProviders(
          <ExecutionMonitor />, 
          '/execution-monitor?planId=test-plan-123'
        )
      })

      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      await waitFor(() => {
        expect(screen.getByText('Execution Monitor')).toBeInTheDocument()
      }, { timeout: 3000 })

      // Click the Environment View button
      const environmentViewButton = screen.getByRole('button', { name: /environment view/i })
      
      await act(async () => {
        await user.click(environmentViewButton)
      })

      // Verify navigation was attempted
      expect(mockNavigate).toHaveBeenCalledWith('/environment-allocation?planId=test-plan-123')
    })

    it('should maintain planId consistency across components', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
      
      await act(async () => {
        renderResult = renderWithProviders(
          <ExecutionMonitor />, 
          '/execution-monitor?planId=test-plan-123'
        )
      })

      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      await waitFor(() => {
        expect(screen.getByText('test-plan-123')).toBeInTheDocument()
      }, { timeout: 3000 })

      // Switch to environment tab
      const environmentTab = screen.getByRole('tab', { name: /environment allocation/i })
      
      await act(async () => {
        await user.click(environmentTab)
        jest.advanceTimersByTime(100)
      })

      // Verify planId is passed to environment dashboard
      await waitFor(() => {
        expect(screen.getByTestId('plan-id')).toHaveTextContent('Plan ID: test-plan-123')
      }, { timeout: 2000 })

      // Verify API calls include the correct planId
      expect(mockApiService.getExecutionStatus).toHaveBeenCalledWith('test-plan-123')
    })

    it('should handle auto-refresh state consistently', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
      
      await act(async () => {
        renderResult = renderWithProviders(
          <ExecutionMonitor />, 
          '/execution-monitor?planId=test-plan-123'
        )
      })

      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      await waitFor(() => {
        expect(screen.getByText('Execution Monitor')).toBeInTheDocument()
      }, { timeout: 3000 })

      // Verify auto-refresh is enabled by default
      const liveButton = screen.getByRole('button', { name: /live/i })
      expect(liveButton).toHaveClass('ant-btn-primary')

      // Switch to environment tab
      const environmentTab = screen.getByRole('tab', { name: /environment allocation/i })
      
      await act(async () => {
        await user.click(environmentTab)
        jest.advanceTimersByTime(100)
      })

      // Verify auto-refresh state is maintained in environment dashboard
      await waitFor(() => {
        expect(screen.getByTestId('auto-refresh')).toHaveTextContent('Auto Refresh: enabled')
      }, { timeout: 2000 })
    })

    it('should handle API errors gracefully', async () => {
      // Mock API error
      mockApiService.getExecutionStatus.mockRejectedValue(new Error('API Error'))
      
      await act(async () => {
        renderResult = renderWithProviders(
          <ExecutionMonitor />, 
          '/execution-monitor?planId=test-plan-123'
        )
      })

      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      // Should still render the basic structure
      await waitFor(() => {
        expect(screen.getByText('Execution Monitor')).toBeInTheDocument()
      }, { timeout: 3000 })

      // Environment tab should still be accessible
      const environmentTab = screen.getByRole('tab', { name: /environment allocation/i })
      expect(environmentTab).toBeInTheDocument()
    })

    it('should switch between tabs correctly', async () => {
      const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime })
      
      await act(async () => {
        renderResult = renderWithProviders(
          <ExecutionMonitor />, 
          '/execution-monitor?planId=test-plan-123'
        )
      })

      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      await waitFor(() => {
        expect(screen.getByText('Execution Monitor')).toBeInTheDocument()
      }, { timeout: 3000 })

      // Verify initial tab state
      const executionTab = screen.getByRole('tab', { name: /execution progress/i })
      const environmentTab = screen.getByRole('tab', { name: /environment allocation/i })
      
      expect(executionTab).toHaveAttribute('aria-selected', 'true')
      expect(environmentTab).toHaveAttribute('aria-selected', 'false')

      // Switch to environment tab
      await act(async () => {
        await user.click(environmentTab)
        jest.advanceTimersByTime(100)
      })

      // Verify tab state changed
      await waitFor(() => {
        expect(environmentTab).toHaveAttribute('aria-selected', 'true')
        expect(executionTab).toHaveAttribute('aria-selected', 'false')
      }, { timeout: 2000 })

      // Switch back to execution tab
      await act(async () => {
        await user.click(executionTab)
        jest.advanceTimersByTime(100)
      })

      // Verify state is restored
      await waitFor(() => {
        expect(executionTab).toHaveAttribute('aria-selected', 'true')
        expect(environmentTab).toHaveAttribute('aria-selected', 'false')
      }, { timeout: 2000 })
    })

    it('should call API endpoints correctly', async () => {
      await act(async () => {
        renderResult = renderWithProviders(
          <ExecutionMonitor />, 
          '/execution-monitor?planId=test-plan-123'
        )
      })

      await act(async () => {
        jest.advanceTimersByTime(100)
      })

      await waitFor(() => {
        expect(screen.getByText('Execution Monitor')).toBeInTheDocument()
      }, { timeout: 3000 })

      // Verify execution API was called
      expect(mockApiService.getExecutionStatus).toHaveBeenCalledWith('test-plan-123')
    })
  })
})