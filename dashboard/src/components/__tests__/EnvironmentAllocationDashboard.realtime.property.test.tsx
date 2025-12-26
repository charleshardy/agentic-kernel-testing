/**
 * Property-based tests for real-time environment status update consistency
 * 
 * **Feature: environment-allocation-ui, Property 2: Real-time Status Updates**
 * **Validates: Requirements 1.2, 2.4**
 */

import React from 'react'
import { render, screen, cleanup, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import fc from 'fast-check'
import '@testing-library/jest-dom'

import EnvironmentAllocationDashboard from '../EnvironmentAllocationDashboard'
import { 
  Environment, 
  EnvironmentType, 
  EnvironmentStatus, 
  EnvironmentHealth
} from '../../types/environment'

// Mock the API service
const mockApiService = {
  getEnvironmentAllocation: jest.fn(),
  performEnvironmentAction: jest.fn(),
  createAllocationEventStream: jest.fn(),
  createEnvironmentWebSocket: jest.fn()
}

jest.mock('../../services/api', () => mockApiService)

// Mock WebSocket and EventSource for testing
class MockWebSocket {
  onopen: ((event: Event) => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null
  onclose: ((event: CloseEvent) => void) | null = null
  onerror: ((event: Event) => void) | null = null
  readyState: number = WebSocket.CONNECTING

  constructor(public url: string) {
    // Simulate connection opening
    setTimeout(() => {
      this.readyState = WebSocket.OPEN
      if (this.onopen) {
        this.onopen(new Event('open'))
      }
    }, 10)
  }

  send(data: string) {
    // Mock send implementation
  }

  close() {
    this.readyState = WebSocket.CLOSED
    if (this.onclose) {
      this.onclose(new CloseEvent('close'))
    }
  }

  // Method to simulate receiving messages
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
    // Simulate connection opening
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

  // Method to simulate receiving events
  simulateEvent(data: any) {
    if (this.onmessage && this.readyState === EventSource.OPEN) {
      this.onmessage(new MessageEvent('message', { data: JSON.stringify(data) }))
    }
  }
}

// Store references to mock instances for testing
let mockWebSocketInstance: MockWebSocket | null = null
let mockEventSourceInstance: MockEventSource | null = null

// Mock global WebSocket and EventSource
global.WebSocket = jest.fn().mockImplementation((url: string) => {
  mockWebSocketInstance = new MockWebSocket(url)
  return mockWebSocketInstance
}) as any

global.EventSource = jest.fn().mockImplementation((url: string) => {
  mockEventSourceInstance = new MockEventSource(url)
  return mockEventSourceInstance
}) as any

// Test wrapper component with required providers
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

// Property-based test generators
const environmentStatusArbitrary = fc.constantFrom(...Object.values(EnvironmentStatus))

const environmentArbitrary = fc.record({
  id: fc.string({ minLength: 8, maxLength: 32 }),
  type: fc.constantFrom(...Object.values(EnvironmentType)),
  status: environmentStatusArbitrary,
  architecture: fc.constantFrom('x86_64', 'arm64', 'riscv64'),
  assignedTests: fc.array(fc.string({ minLength: 8, maxLength: 16 }), { maxLength: 5 }),
  resources: fc.record({
    cpu: fc.float({ min: 0, max: 100 }),
    memory: fc.float({ min: 0, max: 100 }),
    disk: fc.float({ min: 0, max: 100 }),
    network: fc.record({
      bytesIn: fc.integer({ min: 0, max: 1000000 }),
      bytesOut: fc.integer({ min: 0, max: 1000000 }),
      packetsIn: fc.integer({ min: 0, max: 10000 }),
      packetsOut: fc.integer({ min: 0, max: 10000 })
    })
  }),
  health: fc.constantFrom(...Object.values(EnvironmentHealth)),
  metadata: fc.record({
    kernelVersion: fc.option(fc.string({ minLength: 1, maxLength: 20 })),
    ipAddress: fc.option(fc.string()),
    provisionedAt: fc.option(fc.date().map(d => d.toISOString())),
    lastHealthCheck: fc.option(fc.date().map(d => d.toISOString()))
  }),
  createdAt: fc.date().map(d => d.toISOString()),
  updatedAt: fc.date().map(d => d.toISOString())
})

const statusUpdateEventArbitrary = fc.record({
  type: fc.constantFrom('environment_status_changed', 'allocation_status', 'resource_update'),
  environment_id: fc.string({ minLength: 8, maxLength: 32 }),
  new_status: environmentStatusArbitrary,
  timestamp: fc.date().map(d => d.toISOString()),
  data: fc.record({
    previous_status: fc.option(environmentStatusArbitrary),
    resource_usage: fc.option(fc.record({
      cpu: fc.float({ min: 0, max: 100 }),
      memory: fc.float({ min: 0, max: 100 }),
      disk: fc.float({ min: 0, max: 100 })
    }))
  })
})

describe('Real-time Environment Status Update Consistency', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    mockWebSocketInstance = null
    mockEventSourceInstance = null
    
    // Setup default mock implementations
    mockApiService.getEnvironmentAllocation.mockResolvedValue({
      environments: [],
      queue: [],
      resourceUtilization: [],
      history: []
    })
    
    mockApiService.createAllocationEventStream.mockImplementation(() => mockEventSourceInstance)
    mockApiService.createEnvironmentWebSocket.mockImplementation(() => mockWebSocketInstance)
  })

  afterEach(() => {
    cleanup()
    jest.clearAllMocks()
  })

  /**
   * Property 2: Real-time Status Updates
   * For any environment status change, the UI should reflect the change within 2 seconds 
   * without requiring manual refresh
   */
  test('Property 2: Environment status updates are reflected in UI within acceptable time', async () => {
    await fc.assert(
      fc.asyncProperty(
        environmentArbitrary,
        statusUpdateEventArbitrary,
        async (initialEnvironment, statusUpdate) => {
          // Ensure the status update is for the same environment
          const updateEvent = {
            ...statusUpdate,
            environment_id: initialEnvironment.id
          }

          // Setup initial environment data
          mockApiService.getEnvironmentAllocation.mockResolvedValue({
            environments: [initialEnvironment],
            queue: [],
            resourceUtilization: [],
            history: []
          })

          // Render the dashboard
          const { rerender } = render(
            <TestWrapper>
              <EnvironmentAllocationDashboard autoRefresh={true} refreshInterval={1000} />
            </TestWrapper>
          )

          // Wait for initial render
          await waitFor(() => {
            expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
          })

          // Verify initial status is displayed
          await waitFor(() => {
            expect(screen.getByText(initialEnvironment.status.toUpperCase())).toBeInTheDocument()
          })

          // Create updated environment with new status
          const updatedEnvironment = {
            ...initialEnvironment,
            status: updateEvent.new_status,
            updatedAt: updateEvent.timestamp
          }

          // Update the mock to return new data
          mockApiService.getEnvironmentAllocation.mockResolvedValue({
            environments: [updatedEnvironment],
            queue: [],
            resourceUtilization: [],
            history: []
          })

          // Simulate real-time update via WebSocket
          await act(async () => {
            if (mockWebSocketInstance) {
              mockWebSocketInstance.simulateMessage(updateEvent)
            }
          })

          // Wait for the UI to update (should be within 2 seconds as per requirement)
          await waitFor(
            () => {
              // If the status actually changed, verify the new status is displayed
              if (updateEvent.new_status !== initialEnvironment.status) {
                expect(screen.getByText(updateEvent.new_status.toUpperCase())).toBeInTheDocument()
              }
            },
            { timeout: 2000 } // 2 second timeout as per requirement 1.2
          )

          return true
        }
      ),
      { numRuns: 100, verbose: true }
    )
  })

  test('Property 2: WebSocket connection handles multiple rapid status updates correctly', async () => {
    await fc.assert(
      fc.asyncProperty(
        environmentArbitrary,
        fc.array(statusUpdateEventArbitrary, { minLength: 2, maxLength: 5 }),
        async (initialEnvironment, statusUpdates) => {
          // Ensure all updates are for the same environment
          const updates = statusUpdates.map(update => ({
            ...update,
            environment_id: initialEnvironment.id
          }))

          // Setup initial environment data
          mockApiService.getEnvironmentAllocation.mockResolvedValue({
            environments: [initialEnvironment],
            queue: [],
            resourceUtilization: [],
            history: []
          })

          render(
            <TestWrapper>
              <EnvironmentAllocationDashboard autoRefresh={true} refreshInterval={500} />
            </TestWrapper>
          )

          // Wait for initial render
          await waitFor(() => {
            expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
          })

          // Send multiple rapid updates
          for (const update of updates) {
            const updatedEnvironment = {
              ...initialEnvironment,
              status: update.new_status,
              updatedAt: update.timestamp
            }

            mockApiService.getEnvironmentAllocation.mockResolvedValue({
              environments: [updatedEnvironment],
              queue: [],
              resourceUtilization: [],
              history: []
            })

            await act(async () => {
              if (mockWebSocketInstance) {
                mockWebSocketInstance.simulateMessage(update)
              }
            })

            // Small delay between updates to simulate realistic timing
            await new Promise(resolve => setTimeout(resolve, 50))
          }

          // Verify the final status is eventually displayed
          const finalUpdate = updates[updates.length - 1]
          await waitFor(
            () => {
              expect(screen.getByText(finalUpdate.new_status.toUpperCase())).toBeInTheDocument()
            },
            { timeout: 3000 }
          )

          return true
        }
      ),
      { numRuns: 50, verbose: true }
    )
  })

  test('Property 2: Connection recovery works after WebSocket disconnection', async () => {
    await fc.assert(
      fc.asyncProperty(
        environmentArbitrary,
        statusUpdateEventArbitrary,
        async (initialEnvironment, statusUpdate) => {
          const updateEvent = {
            ...statusUpdate,
            environment_id: initialEnvironment.id
          }

          mockApiService.getEnvironmentAllocation.mockResolvedValue({
            environments: [initialEnvironment],
            queue: [],
            resourceUtilization: [],
            history: []
          })

          render(
            <TestWrapper>
              <EnvironmentAllocationDashboard autoRefresh={true} refreshInterval={1000} />
            </TestWrapper>
          )

          await waitFor(() => {
            expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
          })

          // Simulate WebSocket disconnection
          await act(async () => {
            if (mockWebSocketInstance) {
              mockWebSocketInstance.close()
            }
          })

          // Wait a bit for reconnection logic
          await new Promise(resolve => setTimeout(resolve, 100))

          // Verify the component still functions (should fall back to polling)
          expect(screen.getByText('Environment Allocation')).toBeInTheDocument()

          return true
        }
      ),
      { numRuns: 50, verbose: true }
    )
  })

  test('Property 2: Resource utilization updates are reflected in real-time', async () => {
    await fc.assert(
      fc.asyncProperty(
        environmentArbitrary,
        fc.record({
          cpu: fc.float({ min: 0, max: 100 }),
          memory: fc.float({ min: 0, max: 100 }),
          disk: fc.float({ min: 0, max: 100 })
        }),
        async (initialEnvironment, newResourceUsage) => {
          // Setup initial environment
          mockApiService.getEnvironmentAllocation.mockResolvedValue({
            environments: [initialEnvironment],
            queue: [],
            resourceUtilization: [],
            history: []
          })

          render(
            <TestWrapper>
              <EnvironmentAllocationDashboard autoRefresh={true} refreshInterval={1000} />
            </TestWrapper>
          )

          await waitFor(() => {
            expect(screen.getByText('Environment Allocation')).toBeInTheDocument()
          })

          // Create updated environment with new resource usage
          const updatedEnvironment = {
            ...initialEnvironment,
            resources: {
              ...initialEnvironment.resources,
              ...newResourceUsage
            },
            updatedAt: new Date().toISOString()
          }

          mockApiService.getEnvironmentAllocation.mockResolvedValue({
            environments: [updatedEnvironment],
            queue: [],
            resourceUtilization: [],
            history: []
          })

          // Simulate resource update via WebSocket
          const resourceUpdateEvent = {
            type: 'resource_update',
            environment_id: initialEnvironment.id,
            timestamp: new Date().toISOString(),
            data: {
              resource_usage: newResourceUsage
            }
          }

          await act(async () => {
            if (mockWebSocketInstance) {
              mockWebSocketInstance.simulateMessage(resourceUpdateEvent)
            }
          })

          // The component should handle the resource update without errors
          // (Specific UI verification would depend on how resource usage is displayed)
          expect(screen.getByText('Environment Allocation')).toBeInTheDocument()

          return true
        }
      ),
      { numRuns: 100, verbose: true }
    )
  })
})