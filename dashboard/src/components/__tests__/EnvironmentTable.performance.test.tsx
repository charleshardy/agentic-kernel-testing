/**
 * Performance tests for EnvironmentTable component
 * Tests update performance with large numbers of environments
 * and verifies memory usage and rendering efficiency
 * 
 * **Feature: environment-allocation-ui, Performance Tests**
 * **Validates: Requirements 1.2, 2.4**
 */

import React from 'react'
import { render, cleanup, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import '@testing-library/jest-dom'

import EnvironmentTable from '../EnvironmentTable'
import { 
  Environment, 
  EnvironmentType, 
  EnvironmentStatus, 
  EnvironmentHealth,
  EnvironmentFilter
} from '../../types/environment'

// Test wrapper component with required providers
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
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

// Helper function to generate mock environments
const generateMockEnvironments = (count: number): Environment[] => {
  const environments: Environment[] = []
  const types = Object.values(EnvironmentType)
  const statuses = Object.values(EnvironmentStatus)
  const healths = Object.values(EnvironmentHealth)
  const architectures = ['x86_64', 'arm64', 'riscv64']

  for (let i = 0; i < count; i++) {
    environments.push({
      id: `env-${i.toString().padStart(6, '0')}`,
      type: types[i % types.length],
      status: statuses[i % statuses.length],
      architecture: architectures[i % architectures.length],
      assignedTests: Array.from({ length: Math.floor(Math.random() * 5) }, (_, j) => `test-${i}-${j}`),
      resources: {
        cpu: Math.random() * 100,
        memory: Math.random() * 100,
        disk: Math.random() * 100,
        network: {
          bytesIn: Math.floor(Math.random() * 1000000),
          bytesOut: Math.floor(Math.random() * 1000000),
          packetsIn: Math.floor(Math.random() * 10000),
          packetsOut: Math.floor(Math.random() * 10000)
        }
      },
      health: healths[i % healths.length],
      metadata: {
        kernelVersion: `5.${Math.floor(Math.random() * 20)}.${Math.floor(Math.random() * 10)}`,
        ipAddress: `192.168.1.${(i % 254) + 1}`,
        createdAt: new Date(Date.now() - Math.random() * 86400000).toISOString()
      },
      createdAt: new Date(Date.now() - Math.random() * 86400000),
      lastUpdated: new Date()
    })
  }

  return environments
}

// Performance measurement utilities
const measureRenderTime = async (renderFn: () => void): Promise<number> => {
  const start = performance.now()
  await act(async () => {
    renderFn()
  })
  const end = performance.now()
  return end - start
}

const measureMemoryUsage = (): number => {
  if ('memory' in performance) {
    return (performance as any).memory.usedJSHeapSize
  }
  return 0
}

describe('EnvironmentTable Performance Tests', () => {
  let mockOnEnvironmentSelect: jest.Mock
  let mockOnEnvironmentAction: jest.Mock
  let mockOnSelectionChange: jest.Mock

  beforeEach(() => {
    mockOnEnvironmentSelect = jest.fn()
    mockOnEnvironmentAction = jest.fn()
    mockOnSelectionChange = jest.fn()
  })

  afterEach(() => {
    cleanup()
    jest.clearAllMocks()
  })

  describe('Rendering Performance', () => {
    test('should render 100 environments within acceptable time', async () => {
      const environments = generateMockEnvironments(100)
      const filterOptions: EnvironmentFilter = {}

      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <EnvironmentTable
              environments={environments}
              onEnvironmentSelect={mockOnEnvironmentSelect}
              onEnvironmentAction={mockOnEnvironmentAction}
              showResourceUsage={true}
              filterOptions={filterOptions}
              onSelectionChange={mockOnSelectionChange}
              realTimeUpdates={false} // Disable for performance testing
              enableVirtualization={false} // Test without virtualization first
            />
          </TestWrapper>
        )
      })

      // Should render within 1 second for 100 environments
      expect(renderTime).toBeLessThan(1000)
      console.log(`Rendered 100 environments in ${renderTime.toFixed(2)}ms`)
    })

    test('should render 500 environments with virtualization within acceptable time', async () => {
      const environments = generateMockEnvironments(500)
      const filterOptions: EnvironmentFilter = {}

      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <EnvironmentTable
              environments={environments}
              onEnvironmentSelect={mockOnEnvironmentSelect}
              onEnvironmentAction={mockOnEnvironmentAction}
              showResourceUsage={true}
              filterOptions={filterOptions}
              onSelectionChange={mockOnSelectionChange}
              realTimeUpdates={false}
              enableVirtualization={true}
              virtualizationThreshold={50}
            />
          </TestWrapper>
        )
      })

      // Should render within 2 seconds even with 500 environments when virtualized
      expect(renderTime).toBeLessThan(2000)
      console.log(`Rendered 500 environments with virtualization in ${renderTime.toFixed(2)}ms`)
    })

    test('virtualization should improve performance for large datasets', async () => {
      const environments = generateMockEnvironments(200)
      const filterOptions: EnvironmentFilter = {}

      // Measure without virtualization
      const timeWithoutVirtualization = await measureRenderTime(() => {
        const { unmount } = render(
          <TestWrapper>
            <EnvironmentTable
              environments={environments}
              onEnvironmentSelect={mockOnEnvironmentSelect}
              onEnvironmentAction={mockOnEnvironmentAction}
              showResourceUsage={true}
              filterOptions={filterOptions}
              enableVirtualization={false}
            />
          </TestWrapper>
        )
        unmount()
      })

      // Measure with virtualization
      const timeWithVirtualization = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <EnvironmentTable
              environments={environments}
              onEnvironmentSelect={mockOnEnvironmentSelect}
              onEnvironmentAction={mockOnEnvironmentAction}
              showResourceUsage={true}
              filterOptions={filterOptions}
              enableVirtualization={true}
              virtualizationThreshold={50}
            />
          </TestWrapper>
        )
      })

      console.log(`Without virtualization: ${timeWithoutVirtualization.toFixed(2)}ms`)
      console.log(`With virtualization: ${timeWithVirtualization.toFixed(2)}ms`)

      // Virtualization should be faster or at least not significantly slower
      // Allow for some variance in measurements
      expect(timeWithVirtualization).toBeLessThan(timeWithoutVirtualization * 1.5)
    })
  })

  describe('Update Performance', () => {
    test('should handle rapid status updates efficiently', async () => {
      const environments = generateMockEnvironments(50)
      const filterOptions: EnvironmentFilter = {}

      const { rerender } = render(
        <TestWrapper>
          <EnvironmentTable
            environments={environments}
            onEnvironmentSelect={mockOnEnvironmentSelect}
            onEnvironmentAction={mockOnEnvironmentAction}
            showResourceUsage={true}
            filterOptions={filterOptions}
            realTimeUpdates={true}
            lastUpdateTime={new Date()}
          />
        </TestWrapper>
      )

      // Simulate rapid updates
      const updateCount = 10
      const updateTimes: number[] = []

      for (let i = 0; i < updateCount; i++) {
        const updatedEnvironments = environments.map(env => ({
          ...env,
          status: i % 2 === 0 ? EnvironmentStatus.RUNNING : EnvironmentStatus.READY,
          resources: {
            ...env.resources,
            cpu: Math.random() * 100,
            memory: Math.random() * 100,
            disk: Math.random() * 100
          },
          lastUpdated: new Date()
        }))

        const updateTime = await measureRenderTime(() => {
          rerender(
            <TestWrapper>
              <EnvironmentTable
                environments={updatedEnvironments}
                onEnvironmentSelect={mockOnEnvironmentSelect}
                onEnvironmentAction={mockOnEnvironmentAction}
                showResourceUsage={true}
                filterOptions={filterOptions}
                realTimeUpdates={true}
                lastUpdateTime={new Date()}
              />
            </TestWrapper>
          )
        })

        updateTimes.push(updateTime)
      }

      const averageUpdateTime = updateTimes.reduce((sum, time) => sum + time, 0) / updateTimes.length
      const maxUpdateTime = Math.max(...updateTimes)

      console.log(`Average update time: ${averageUpdateTime.toFixed(2)}ms`)
      console.log(`Max update time: ${maxUpdateTime.toFixed(2)}ms`)

      // Updates should be fast
      expect(averageUpdateTime).toBeLessThan(100) // Average under 100ms
      expect(maxUpdateTime).toBeLessThan(500) // No single update over 500ms
    })

    test('should maintain performance with frequent resource usage updates', async () => {
      const environments = generateMockEnvironments(30)
      const filterOptions: EnvironmentFilter = {}

      const { rerender } = render(
        <TestWrapper>
          <EnvironmentTable
            environments={environments}
            onEnvironmentSelect={mockOnEnvironmentSelect}
            onEnvironmentAction={mockOnEnvironmentAction}
            showResourceUsage={true}
            filterOptions={filterOptions}
            realTimeUpdates={true}
          />
        </TestWrapper>
      )

      // Simulate resource usage updates every 100ms for 1 second
      const updateInterval = 100
      const totalDuration = 1000
      const updateCount = totalDuration / updateInterval
      const updateTimes: number[] = []

      for (let i = 0; i < updateCount; i++) {
        const updatedEnvironments = environments.map(env => ({
          ...env,
          resources: {
            ...env.resources,
            cpu: Math.min(100, env.resources.cpu + (Math.random() - 0.5) * 10),
            memory: Math.min(100, env.resources.memory + (Math.random() - 0.5) * 10),
            disk: Math.min(100, env.resources.disk + (Math.random() - 0.5) * 10)
          },
          lastUpdated: new Date()
        }))

        const updateTime = await measureRenderTime(() => {
          rerender(
            <TestWrapper>
              <EnvironmentTable
                environments={updatedEnvironments}
                onEnvironmentSelect={mockOnEnvironmentSelect}
                onEnvironmentAction={mockOnEnvironmentAction}
                showResourceUsage={true}
                filterOptions={filterOptions}
                realTimeUpdates={true}
                lastUpdateTime={new Date()}
              />
            </TestWrapper>
          )
        })

        updateTimes.push(updateTime)
      }

      const averageUpdateTime = updateTimes.reduce((sum, time) => sum + time, 0) / updateTimes.length

      console.log(`Resource update performance: ${averageUpdateTime.toFixed(2)}ms average`)

      // Resource updates should be very fast since they're frequent
      expect(averageUpdateTime).toBeLessThan(50)
    })
  })

  describe('Memory Usage', () => {
    test('should not have significant memory leaks during updates', async () => {
      if (!('memory' in performance)) {
        console.log('Memory measurement not available in this environment')
        return
      }

      const environments = generateMockEnvironments(100)
      const filterOptions: EnvironmentFilter = {}

      const initialMemory = measureMemoryUsage()

      const { rerender, unmount } = render(
        <TestWrapper>
          <EnvironmentTable
            environments={environments}
            onEnvironmentSelect={mockOnEnvironmentSelect}
            onEnvironmentAction={mockOnEnvironmentAction}
            showResourceUsage={true}
            filterOptions={filterOptions}
            realTimeUpdates={true}
          />
        </TestWrapper>
      )

      // Perform many updates to test for memory leaks
      for (let i = 0; i < 50; i++) {
        const updatedEnvironments = environments.map(env => ({
          ...env,
          status: i % 3 === 0 ? EnvironmentStatus.RUNNING : 
                  i % 3 === 1 ? EnvironmentStatus.READY : EnvironmentStatus.ALLOCATING,
          resources: {
            ...env.resources,
            cpu: Math.random() * 100,
            memory: Math.random() * 100,
            disk: Math.random() * 100
          },
          lastUpdated: new Date()
        }))

        await act(async () => {
          rerender(
            <TestWrapper>
              <EnvironmentTable
                environments={updatedEnvironments}
                onEnvironmentSelect={mockOnEnvironmentSelect}
                onEnvironmentAction={mockOnEnvironmentAction}
                showResourceUsage={true}
                filterOptions={filterOptions}
                realTimeUpdates={true}
                lastUpdateTime={new Date()}
              />
            </TestWrapper>
          )
        })
      }

      const finalMemory = measureMemoryUsage()
      unmount()

      const memoryIncrease = finalMemory - initialMemory
      const memoryIncreasePercent = (memoryIncrease / initialMemory) * 100

      console.log(`Memory usage: ${initialMemory} -> ${finalMemory} (${memoryIncreasePercent.toFixed(2)}% increase)`)

      // Memory increase should be reasonable (less than 50% increase)
      expect(memoryIncreasePercent).toBeLessThan(50)
    })
  })

  describe('Accessibility Performance', () => {
    test('should maintain performance with accessibility features enabled', async () => {
      const environments = generateMockEnvironments(100)
      const filterOptions: EnvironmentFilter = {}

      // Measure render time with full accessibility features
      const renderTime = await measureRenderTime(() => {
        render(
          <TestWrapper>
            <EnvironmentTable
              environments={environments}
              onEnvironmentSelect={mockOnEnvironmentSelect}
              onEnvironmentAction={mockOnEnvironmentAction}
              showResourceUsage={true}
              filterOptions={filterOptions}
              realTimeUpdates={true}
              enableVirtualization={true}
            />
          </TestWrapper>
        )
      })

      console.log(`Render time with accessibility features: ${renderTime.toFixed(2)}ms`)

      // Accessibility features should not significantly impact performance
      expect(renderTime).toBeLessThan(1500)
    })

    test('should handle keyboard navigation efficiently', async () => {
      const environments = generateMockEnvironments(50)
      const filterOptions: EnvironmentFilter = {}

      const { container } = render(
        <TestWrapper>
          <EnvironmentTable
            environments={environments}
            onEnvironmentSelect={mockOnEnvironmentSelect}
            onEnvironmentAction={mockOnEnvironmentAction}
            showResourceUsage={true}
            filterOptions={filterOptions}
            realTimeUpdates={true}
          />
        </TestWrapper>
      )

      const tableContainer = container.querySelector('[role="region"]') as HTMLElement
      expect(tableContainer).toBeInTheDocument()

      // Simulate rapid keyboard navigation
      const navigationTime = await measureRenderTime(() => {
        for (let i = 0; i < 20; i++) {
          act(() => {
            tableContainer.dispatchEvent(new KeyboardEvent('keydown', { 
              key: 'ArrowDown',
              bubbles: true 
            }))
          })
        }
      })

      console.log(`Keyboard navigation time for 20 moves: ${navigationTime.toFixed(2)}ms`)

      // Keyboard navigation should be very responsive
      expect(navigationTime).toBeLessThan(100)
    })
  })

  describe('Batch Update Performance', () => {
    test('should efficiently handle batch updates', async () => {
      const environments = generateMockEnvironments(100)
      const filterOptions: EnvironmentFilter = {}

      const { rerender } = render(
        <TestWrapper>
          <EnvironmentTable
            environments={environments}
            onEnvironmentSelect={mockOnEnvironmentSelect}
            onEnvironmentAction={mockOnEnvironmentAction}
            showResourceUsage={true}
            filterOptions={filterOptions}
            realTimeUpdates={true}
          />
        </TestWrapper>
      )

      // Simulate a large batch update (like what might come from WebSocket)
      const batchUpdateTime = await measureRenderTime(() => {
        const batchUpdatedEnvironments = environments.map((env, index) => ({
          ...env,
          status: index % 4 === 0 ? EnvironmentStatus.RUNNING :
                  index % 4 === 1 ? EnvironmentStatus.READY :
                  index % 4 === 2 ? EnvironmentStatus.ALLOCATING : EnvironmentStatus.CLEANUP,
          resources: {
            cpu: Math.random() * 100,
            memory: Math.random() * 100,
            disk: Math.random() * 100,
            network: env.resources.network
          },
          health: index % 3 === 0 ? EnvironmentHealth.HEALTHY :
                  index % 3 === 1 ? EnvironmentHealth.DEGRADED : EnvironmentHealth.UNHEALTHY,
          lastUpdated: new Date()
        }))

        rerender(
          <TestWrapper>
            <EnvironmentTable
              environments={batchUpdatedEnvironments}
              onEnvironmentSelect={mockOnEnvironmentSelect}
              onEnvironmentAction={mockOnEnvironmentAction}
              showResourceUsage={true}
              filterOptions={filterOptions}
              realTimeUpdates={true}
              lastUpdateTime={new Date()}
            />
          </TestWrapper>
        )
      })

      console.log(`Batch update time for 100 environments: ${batchUpdateTime.toFixed(2)}ms`)

      // Batch updates should be efficient
      expect(batchUpdateTime).toBeLessThan(200)
    })
  })
})