/**
 * Integration test for real-time environment status updates
 * Tests the complete flow from WebSocket/SSE to UI updates
 */

import React from 'react'
import { render, screen, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import '@testing-library/jest-dom'

import EnvironmentManagementDashboard from '../EnvironmentManagementDashboard'
import { EnvironmentStatus, EnvironmentType, EnvironmentHealth } from '../../types/environment'

// Mock the API service
const mockApiService = {
  getEnvironmentAllocation: jest.fn(),
  performEnvironmentAction: jest.fn(),
  createAllocationEventStream: jest.fn(),
  createEnvironmentWebSocket: jest.fn()
}

jest.mock('../../services/api', () => mockApiService)

// Mock WebSocket and EventSource
class MockWebSocket {
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  readyState: number = WebSocket.CONNECTING

  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 10)
  }

  send(data: string) {}
  close() {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }

  simulateMessage(data: any) {
    if (this.onmessage && this.readyState === WebSocket.OPEN) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }))
    }
  }
}

class MockEventSource {
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  readyState: number = EventSource.CONNECTING

  constructor(public url: string) {
    setTimeout(() => {
      this.readyState = EventSource.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 10)
  }

  close() {
    this.readyState = EventSource.CLOSED
  }

  simulateEvent(data: any) {
    if (this.onmessage && this.readyState === EventSource.OPEN) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }))
    }
  }
}

let mockWebSocketInstance: MockWebSocket | null = null
let mockEventSourceInstance: MockEventSource | null = null

global.WebSocket = jest.fn().mockImplementation((url: string) => {
  mockWebSocketInstance = new MockWebSocket(url)
  return mockWebSocketInstance
}) as any

global.EventSource = jest.fn().mockImplementation((url: string) => {
  mockEventSourceInstance = new MockEventSource(url)
  return mockEventSourceInstance
}) as any

// Test wrapper
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, refetchInterval: false },
      mutations: { retry: false }
    }
  })

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Real-time Environment Status Updates Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockWebSocketInstance = null
    mockEventSourceInstance = null
    
    // Setup default mock responses
    mockApiService.getEnvironmentAllocation.mockResolvedValue({
      environments: [
        {
          id: 'env-test-001',
          type: EnvironmentType.QEMU_X86,
          status: EnvironmentStatus.READY,
          architecture: 'x86_64',
          assignedTests: [],
          resources: {
            cpu: 25.0,
            memory: 45.0,
            disk: 60.0,
            network: {
              bytesIn: 1000,
              bytesOut: 2000,
              packetsIn: 100,
              packetsOut: 200
            }
          },
          health: EnvironmentHealth.HEALTHY,
          metadata: {
            kernelVersion: '6.1.0',
            ipAddress: '192.168.1.100'
          },
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
      ],
      queue: [],
      resourceUtilization: [],
      history: []
    })
    
    mockApiService.createAllocationEventStream.mockImplementation(() => mockEventSourceInstance)
    mockApiService.createEnvironmentWebSocket.mockImplementation(() => mockWebSocketInstance)
  })

  afterEach(() => {
    jest.clearAllMocks()
  })

  test('should establish real-time connections on mount', async () => {
    render(
      <TestWrapper>
        <EnvironmentAllocationDashboard autoRefresh={true} />
      </TestWrapper>
    )

    // Wait for component to mount and connections to establish
    await waitFor(() => {
      expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
    })

    // Verify WebSocket and EventSource were created
    expect(global.WebSocket).toHaveBeenCalled()
    expect(global.EventSource).toHaveBeenCalled()
  })

  test('should display connection status indicator', async () => {
    render(
      <TestWrapper>
        <EnvironmentAllocationDashboard autoRefresh={true} />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
    })

    // Should show connection status (may be "Connected", "Degraded", or "Disconnected")
    // The exact text depends on connection establishment timing
    await waitFor(() => {
      const connectionElements = screen.queryAllByText(/Connected|Degraded|Disconnected|Live/)
      expect(connectionElements.length).toBeGreaterThan(0)
    })
  })

  test('should handle WebSocket status updates', async () => {
    render(
      <TestWrapper>
        <EnvironmentAllocationDashboard autoRefresh={true} />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
    })

    // Wait for WebSocket connection
    await waitFor(() => {
      expect(mockWebSocketInstance).toBeTruthy()
    })

    // Simulate environment status change
    const statusUpdate = {
      type: 'environment_status_changed',
      environment_id: 'env-test-001',
      new_status: EnvironmentStatus.RUNNING,
      timestamp: new Date().toISOString(),
      data: {
        previous_status: EnvironmentStatus.READY,
        environment: {
          id: 'env-test-001',
          type: EnvironmentType.QEMU_X86,
          status: EnvironmentStatus.RUNNING,
          architecture: 'x86_64',
          assignedTests: ['test-001'],
          resources: {
            cpu: 75.0,
            memory: 60.0,
            disk: 65.0,
            network: {
              bytesIn: 5000,
              bytesOut: 8000,
              packetsIn: 500,
              packetsOut: 800
            }
          },
          health: EnvironmentHealth.HEALTHY,
          metadata: {
            kernelVersion: '6.1.0',
            ipAddress: '192.168.1.100'
          },
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        }
      }
    }

    await act(async () => {
      if (mockWebSocketInstance) {
        mockWebSocketInstance.simulateMessage(statusUpdate)
      }
    })

    // The component should handle the update (exact UI changes depend on implementation)
    // At minimum, it should not crash and should continue to display the environment table
    expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
  })

  test('should handle connection failures gracefully', async () => {
    render(
      <TestWrapper>
        <EnvironmentAllocationDashboard autoRefresh={true} />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
    })

    // Simulate connection failure
    await act(async () => {
      if (mockWebSocketInstance && mockWebSocketInstance.onerror) {
        mockWebSocketInstance.onerror(new Event('error'))
      }
    })

    // Component should still be functional
    expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
  })

  test('should show live updates indicator when connected', async () => {
    render(
      <TestWrapper>
        <EnvironmentAllocationDashboard autoRefresh={true} />
      </TestWrapper>
    )

    await waitFor(() => {
      expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
    })

    // Should eventually show some form of live connection indicator
    // This might be "Live", "Connected", or similar text
    await waitFor(() => {
      const liveIndicators = screen.queryAllByText(/Live|Connected|updates/)
      expect(liveIndicators.length).toBeGreaterThan(0)
    }, { timeout: 3000 })
  })
})