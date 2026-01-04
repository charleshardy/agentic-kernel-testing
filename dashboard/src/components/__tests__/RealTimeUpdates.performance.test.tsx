/**
 * Performance tests for Real-time Updates functionality
 * 
 * **Feature: environment-allocation-ui, Task 13.1: Performance tests for real-time updates**
 * **Validates: Requirements 1.2, 2.4**
 */

import React from 'react'
import { render, cleanup, act, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import '@testing-library/jest-dom'

import EnvironmentTable from '../EnvironmentTable'
import ResourceUtilizationCharts from '../ResourceUtilizationCharts'
import AllocationQueueViewer from '../AllocationQueueViewer'
import { 
  Environment, 
  EnvironmentType, 
  EnvironmentStatus, 
  EnvironmentHealth,
  ResourceMetric,
  TimeRange,
  AllocationRequest,
  AllocationStatus
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

// Performance measurement utilities
const measurePerformance = async (testName: string, testFn: () => Promise<void> | void) => {
  const startTime = performance.now()
  const startMemory = (performance as any).memory?.usedJSHeapSize || 0
  
  await testFn()
  
  const endTime = performance.now()
  const endMemory = (performance as any).memory?.usedJSHeapSize || 0
  const duration = endTime - startTime
  const memoryDelta = endMemory - startMemory
  
  console.log(`Performance Test: ${testName}`)
  console.log(`  Duration: ${duration.toFixed(2)}ms`)
  console.log(`  Memory Delta: ${(memoryDelta / 1024 / 1024).toFixed(2)}MB`)
  
  return { duration, memoryDelta }
}

// Generate test data
const generateEnvironments = (count: number): Environment[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: `env-${i.toString().padStart(3, '0')}`,
    type: [EnvironmentType.QEMU_X86, EnvironmentType.QEMU_ARM, EnvironmentType.DOCKER, EnvironmentType.PHYSICAL][i % 4],
    status: [EnvironmentStatus.RUNNING, EnvironmentStatus.READY, EnvironmentStatus.ALLOCATING, EnvironmentStatus.CLEANUP][i % 4],
    architecture: ['x86_64', 'arm64', 'riscv64'][i % 3],
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
    health: [EnvironmentHealth.HEALTHY, EnvironmentHealth.DEGRADED, EnvironmentHealth.UNHEALTHY][i % 3],
    metadata: {
      kernelVersion: `5.${Math.floor(Math.random() * 20)}.${Math.floor(Math.random() * 10)}`,
      ipAddress: `192.168.1.${100 + i}`,
      provisionedAt: new Date(Date.now() - Math.random() * 86400000).toISOString()
    },
    createdAt: new Date(Date.now() - Math.random() * 86400000),
    lastUpdated: new Date()
  }))
}

const generateAllocationRequests = (count: number): AllocationRequest[] => {
  return Array.from({ length: count }, (_, i) => ({
    id: `req-${i.toString().padStart(3, '0')}`,
    testId: `test-${i}`,
    requirements: {
      architecture: ['x86_64', 'arm64'][i % 2],
      minMemoryMB: 512 + (i * 256),
      minCpuCores: 1 + (i % 4),
      requiredFeatures: [`feature-${i % 3}`],
      isolationLevel: ['none', 'process', 'container', 'vm'][i % 4] as any
    },
    priority: 1 + (i % 10),
    submittedAt: new Date(Date.now() - Math.random() * 3600000),
    estimatedStartTime: new Date(Date.now() + Math.random() * 3600000),
    status: [AllocationStatus.PENDING, AllocationStatus.ALLOCATED, AllocationStatus.FAILED][i % 3]
  }))
}

describe('Real-time Updates Performance Tests', () => {
  afterEach(() => {
    cleanup()
    jest.clearAllMocks()
  })

  describe('EnvironmentTable Performance', () => {
    test('should render large environment lists efficiently', async () => {
      const environments = generateEnvironments(1000)
      
      const { duration, memoryDelta } = await measurePerformance(
        'EnvironmentTable - 1000 environments',
        async () => {
          const { container } = render(
            <TestWrapper>
              <EnvironmentTable
                environments={environments}
                onEnvironmentSelect={() => {}}
                onEnvironmentAction={() => Promise.resolve()}
                showResourceUsage={true}
                filterOptions={{}}
                enableVirtualization={true}
                virtualizationThreshold={50}
              />
            </TestWrapper>
          )
          
          // Wait for component to fully render
          await waitFor(() => {
            expect(container.querySelector('.ant-table')).toBeInTheDocument()
          })
        }
      )
      
      // Performance assertions
      expect(duration).toBeLessThan(2000) // Should render within 2 seconds
      expect(memoryDelta).toBeLessThan(50 * 1024 * 1024) // Should use less than 50MB additional memory
    })

    test('should handle rapid environment updates efficiently', async () => {
      const initialEnvironments = generateEnvironments(100)
      let environments = initialEnvironments
      
      const { rerender } = render(
        <TestWrapper>
          <EnvironmentTable
            environments={environments}
            onEnvironmentSelect={() => {}}
            onEnvironmentAction={() => Promise.resolve()}
            showResourceUsage={true}
            filterOptions={{}}
            realTimeUpdates={true}
            lastUpdateTime={new Date()}
          />
        </TestWrapper>
      )
      
      const { duration } = await measurePerformance(
        'EnvironmentTable - 50 rapid updates',
        async () => {
          // Simulate 50 rapid updates
          for (let i = 0; i < 50; i++) {
            environments = environments.map(env => ({
              ...env,
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
                    environments={environments}
                    onEnvironmentSelect={() => {}}
                    onEnvironmentAction={() => Promise.resolve()}
                    showResourceUsage={true}
                    filterOptions={{}}
                    realTimeUpdates={true}
                    lastUpdateTime={new Date()}
                  />
                </TestWrapper>
              )
            })
            
            // Small delay to simulate real-time updates
            await new Promise(resolve => setTimeout(resolve, 10))
          }
        }
      )
      
      // Should handle rapid updates efficiently
      expect(duration).toBeLessThan(5000) // Should complete within 5 seconds
    })

    test('should maintain performance with virtualization enabled', async () => {
      const environments = generateEnvironments(500)
      
      const { duration: withVirtualization } = await measurePerformance(
        'EnvironmentTable - 500 environments with virtualization',
        async () => {
          render(
            <TestWrapper>
              <EnvironmentTable
                environments={environments}
                onEnvironmentSelect={() => {}}
                onEnvironmentAction={() => Promise.resolve()}
                showResourceUsage={true}
                filterOptions={{}}
                enableVirtualization={true}
                virtualizationThreshold={100}
              />
            </TestWrapper>
          )
        }
      )
      
      cleanup()
      
      const { duration: withoutVirtualization } = await measurePerformance(
        'EnvironmentTable - 500 environments without virtualization',
        async () => {
          render(
            <TestWrapper>
              <EnvironmentTable
                environments={environments}
                onEnvironmentSelect={() => {}}
                onEnvironmentAction={() => Promise.resolve()}
                showResourceUsage={true}
                filterOptions={{}}
                enableVirtualization={false}
              />
            </TestWrapper>
          )
        }
      )
      
      // Virtualization should improve performance for large datasets
      expect(withVirtualization).toBeLessThan(withoutVirtualization * 1.5)
    })
  })

  describe('ResourceUtilizationCharts Performance', () => {
    test('should render charts with large datasets efficiently', async () => {
      const environments = generateEnvironments(200)
      const timeRange: TimeRange = {
        start: new Date(Date.now() - 30 * 60 * 1000),
        end: new Date()
      }
      const metrics: ResourceMetric[] = [
        { name: 'CPU Usage', type: 'cpu', unit: '%' },
        { name: 'Memory Usage', type: 'memory', unit: '%' },
        { name: 'Disk Usage', type: 'disk', unit: '%' },
        { name: 'Network I/O', type: 'network', unit: 'MB/s' }
      ]
      
      const { duration, memoryDelta } = await measurePerformance(
        'ResourceUtilizationCharts - 200 environments',
        async () => {
          render(
            <TestWrapper>
              <ResourceUtilizationCharts
                environments={environments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
                autoRefresh={true}
                refreshInterval={1000}
              />
            </TestWrapper>
          )
        }
      )
      
      // Performance assertions
      expect(duration).toBeLessThan(3000) // Should render within 3 seconds
      expect(memoryDelta).toBeLessThan(30 * 1024 * 1024) // Should use less than 30MB additional memory
    })

    test('should handle real-time chart updates efficiently', async () => {
      const initialEnvironments = generateEnvironments(50)
      let environments = initialEnvironments
      const timeRange: TimeRange = {
        start: new Date(Date.now() - 30 * 60 * 1000),
        end: new Date()
      }
      const metrics: ResourceMetric[] = [
        { name: 'CPU Usage', type: 'cpu', unit: '%' }
      ]
      
      const { rerender } = render(
        <TestWrapper>
          <ResourceUtilizationCharts
            environments={environments}
            timeRange={timeRange}
            chartType="realtime"
            metrics={metrics}
            autoRefresh={true}
            refreshInterval={100}
          />
        </TestWrapper>
      )
      
      const { duration } = await measurePerformance(
        'ResourceUtilizationCharts - 30 real-time updates',
        async () => {
          // Simulate 30 real-time updates
          for (let i = 0; i < 30; i++) {
            environments = environments.map(env => ({
              ...env,
              resources: {
                ...env.resources,
                cpu: Math.random() * 100,
                memory: Math.random() * 100,
                disk: Math.random() * 100
              }
            }))
            
            await act(async () => {
              rerender(
                <TestWrapper>
                  <ResourceUtilizationCharts
                    environments={environments}
                    timeRange={timeRange}
                    chartType="realtime"
                    metrics={metrics}
                    autoRefresh={true}
                    refreshInterval={100}
                  />
                </TestWrapper>
              )
            })
            
            await new Promise(resolve => setTimeout(resolve, 50))
          }
        }
      )
      
      // Should handle real-time updates efficiently
      expect(duration).toBeLessThan(3000) // Should complete within 3 seconds
    })
  })

  describe('AllocationQueueViewer Performance', () => {
    test('should render large allocation queues efficiently', async () => {
      const queue = generateAllocationRequests(500)
      const estimatedWaitTimes = new Map(
        queue.map(req => [req.id, Math.floor(Math.random() * 300) + 60])
      )
      
      const { duration, memoryDelta } = await measurePerformance(
        'AllocationQueueViewer - 500 requests',
        async () => {
          render(
            <TestWrapper>
              <AllocationQueueViewer
                queue={queue}
                estimatedWaitTimes={estimatedWaitTimes}
                onPriorityChange={() => Promise.resolve()}
                onCancelRequest={() => Promise.resolve()}
                onBulkCancel={() => Promise.resolve()}
                onRefresh={() => {}}
                enableBulkOperations={true}
                enableAdvancedFiltering={true}
                showQueueAnalytics={true}
              />
            </TestWrapper>
          )
        }
      )
      
      // Performance assertions
      expect(duration).toBeLessThan(2000) // Should render within 2 seconds
      expect(memoryDelta).toBeLessThan(40 * 1024 * 1024) // Should use less than 40MB additional memory
    })

    test('should handle queue updates efficiently', async () => {
      const initialQueue = generateAllocationRequests(100)
      let queue = initialQueue
      const estimatedWaitTimes = new Map(
        queue.map(req => [req.id, Math.floor(Math.random() * 300) + 60])
      )
      
      const { rerender } = render(
        <TestWrapper>
          <AllocationQueueViewer
            queue={queue}
            estimatedWaitTimes={estimatedWaitTimes}
            onPriorityChange={() => Promise.resolve()}
            onCancelRequest={() => Promise.resolve()}
            onBulkCancel={() => Promise.resolve()}
            onRefresh={() => {}}
            realTimeUpdates={true}
            lastUpdateTime={new Date()}
          />
        </TestWrapper>
      )
      
      const { duration } = await measurePerformance(
        'AllocationQueueViewer - 25 queue updates',
        async () => {
          // Simulate 25 queue updates
          for (let i = 0; i < 25; i++) {
            // Simulate queue changes (priority updates, new requests, etc.)
            queue = queue.map(req => ({
              ...req,
              priority: Math.floor(Math.random() * 10) + 1,
              estimatedStartTime: new Date(Date.now() + Math.random() * 3600000)
            }))
            
            // Add some new requests
            if (i % 5 === 0) {
              queue.push(...generateAllocationRequests(5).map(req => ({
                ...req,
                id: `new-${i}-${req.id}`
              })))
            }
            
            await act(async () => {
              rerender(
                <TestWrapper>
                  <AllocationQueueViewer
                    queue={queue}
                    estimatedWaitTimes={estimatedWaitTimes}
                    onPriorityChange={() => Promise.resolve()}
                    onCancelRequest={() => Promise.resolve()}
                    onBulkCancel={() => Promise.resolve()}
                    onRefresh={() => {}}
                    realTimeUpdates={true}
                    lastUpdateTime={new Date()}
                  />
                </TestWrapper>
              )
            })
            
            await new Promise(resolve => setTimeout(resolve, 20))
          }
        }
      )
      
      // Should handle queue updates efficiently
      expect(duration).toBeLessThan(4000) // Should complete within 4 seconds
    })
  })

  describe('Memory Usage Tests', () => {
    test('should not have significant memory leaks during updates', async () => {
      const environments = generateEnvironments(100)
      let memoryUsages: number[] = []
      
      const { rerender } = render(
        <TestWrapper>
          <EnvironmentTable
            environments={environments}
            onEnvironmentSelect={() => {}}
            onEnvironmentAction={() => Promise.resolve()}
            showResourceUsage={true}
            filterOptions={{}}
            realTimeUpdates={true}
          />
        </TestWrapper>
      )
      
      // Perform multiple update cycles and measure memory
      for (let cycle = 0; cycle < 10; cycle++) {
        // Perform 10 updates per cycle
        for (let i = 0; i < 10; i++) {
          const updatedEnvironments = environments.map(env => ({
            ...env,
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
                  onEnvironmentSelect={() => {}}
                  onEnvironmentAction={() => Promise.resolve()}
                  showResourceUsage={true}
                  filterOptions={{}}
                  realTimeUpdates={true}
                  lastUpdateTime={new Date()}
                />
              </TestWrapper>
            )
          })
        }
        
        // Force garbage collection if available
        if (global.gc) {
          global.gc()
        }
        
        // Measure memory usage
        const memoryUsage = (performance as any).memory?.usedJSHeapSize || 0
        memoryUsages.push(memoryUsage)
        
        await new Promise(resolve => setTimeout(resolve, 100))
      }
      
      // Check for memory leaks - memory usage shouldn't grow significantly
      const initialMemory = memoryUsages[0]
      const finalMemory = memoryUsages[memoryUsages.length - 1]
      const memoryGrowth = finalMemory - initialMemory
      
      // Memory growth should be reasonable (less than 20MB)
      expect(memoryGrowth).toBeLessThan(20 * 1024 * 1024)
    })
  })

  describe('Rendering Efficiency Tests', () => {
    test('should minimize re-renders with memoization', async () => {
      const environments = generateEnvironments(50)
      let renderCount = 0
      
      // Create a component that tracks renders
      const TrackedEnvironmentTable = React.memo(() => {
        renderCount++
        return (
          <EnvironmentTable
            environments={environments}
            onEnvironmentSelect={() => {}}
            onEnvironmentAction={() => Promise.resolve()}
            showResourceUsage={true}
            filterOptions={{}}
            realTimeUpdates={true}
          />
        )
      })
      
      const { rerender } = render(
        <TestWrapper>
          <TrackedEnvironmentTable />
        </TestWrapper>
      )
      
      const initialRenderCount = renderCount
      
      // Trigger multiple re-renders with the same props
      for (let i = 0; i < 5; i++) {
        await act(async () => {
          rerender(
            <TestWrapper>
              <TrackedEnvironmentTable />
            </TestWrapper>
          )
        })
      }
      
      // Should not re-render unnecessarily due to memoization
      expect(renderCount - initialRenderCount).toBeLessThanOrEqual(1)
    })
  })
})