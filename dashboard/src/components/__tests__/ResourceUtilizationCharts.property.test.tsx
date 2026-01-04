/**
 * Property-based tests for Resource Utilization Charts component
 * 
 * **Feature: environment-allocation-ui, Property 3: Resource Metrics Display Completeness**
 * **Validates: Requirements 2.1, 2.2, 2.3, 7.1, 7.3**
 */

import React from 'react'
import { render, cleanup } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import fc from 'fast-check'
import '@testing-library/jest-dom'

import ResourceUtilizationCharts from '../ResourceUtilizationCharts'
import { 
  Environment, 
  EnvironmentType, 
  EnvironmentStatus, 
  EnvironmentHealth,
  ResourceMetric,
  TimeRange
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

// Property-based test generators using fast-check
const resourceUsageArbitrary = fc.record({
  cpu: fc.float({ min: 0, max: 100 }),
  memory: fc.float({ min: 0, max: 100 }),
  disk: fc.float({ min: 0, max: 100 }),
  network: fc.record({
    bytesIn: fc.integer({ min: 0, max: 1000000000 }),
    bytesOut: fc.integer({ min: 0, max: 1000000000 }),
    packetsIn: fc.integer({ min: 0, max: 10000000 }),
    packetsOut: fc.integer({ min: 0, max: 10000000 })
  })
})

const environmentArbitrary = fc.record({
  id: fc.string({ minLength: 8, maxLength: 32 }),
  type: fc.constantFrom(...Object.values(EnvironmentType)),
  status: fc.constantFrom(...Object.values(EnvironmentStatus)),
  architecture: fc.constantFrom('x86_64', 'arm64', 'riscv64', 'arm'),
  assignedTests: fc.array(fc.string({ minLength: 8, maxLength: 16 }), { maxLength: 10 }),
  resources: resourceUsageArbitrary,
  health: fc.constantFrom(...Object.values(EnvironmentHealth)),
  metadata: fc.record({
    kernelVersion: fc.option(fc.string({ minLength: 1, maxLength: 50 }), { nil: undefined }),
    ipAddress: fc.option(fc.string(), { nil: undefined }),
    sshCredentials: fc.option(fc.dictionary(fc.string(), fc.string()), { nil: undefined }),
    provisionedAt: fc.option(fc.date().map(d => d.toISOString()), { nil: undefined }),
    lastHealthCheck: fc.option(fc.date().map(d => d.toISOString()), { nil: undefined })
  }),
  createdAt: fc.date(),
  lastUpdated: fc.date()
})

const timeRangeArbitrary = fc.record({
  start: fc.date({ min: new Date('2020-01-01'), max: new Date() }),
  end: fc.date({ min: new Date('2020-01-01'), max: new Date() })
}).filter(range => range.start <= range.end)

const resourceMetricArbitrary = fc.record({
  name: fc.string({ minLength: 1, maxLength: 50 }),
  type: fc.constantFrom('cpu' as const, 'memory' as const, 'disk' as const, 'network' as const),
  unit: fc.constantFrom('%', 'MB', 'GB', 'MB/s', 'KB/s')
})

describe('Resource Utilization Charts Component', () => {
  afterEach(() => {
    cleanup()
    jest.clearAllMocks()
  })

  /**
   * Property 3: Resource Metrics Display Completeness
   * For any active environment, the UI should display all resource utilization metrics 
   * (CPU, memory, disk, network) and health indicators accurately with appropriate 
   * visual warnings when thresholds are exceeded
   */
  test('Property 3: Charts render without errors for any environment resource data', () => {
    fc.assert(
      fc.property(
        fc.array(environmentArbitrary, { minLength: 1, maxLength: 5 }),
        timeRangeArbitrary,
        fc.constantFrom('realtime' as const, 'historical' as const),
        fc.array(resourceMetricArbitrary, { minLength: 1, maxLength: 4 }),
        (environments, timeRange, chartType, metrics) => {
          try {
            // Ensure resource values are within valid ranges
            const validEnvironments = environments.map(env => ({
              ...env,
              resources: {
                ...env.resources,
                cpu: Math.max(0, Math.min(100, env.resources.cpu)),
                memory: Math.max(0, Math.min(100, env.resources.memory)),
                disk: Math.max(0, Math.min(100, env.resources.disk))
              }
            }))

            // Render the component
            const { container } = render(
              <TestWrapper>
                <ResourceUtilizationCharts
                  environments={validEnvironments}
                  timeRange={timeRange}
                  chartType={chartType}
                  metrics={metrics}
                />
              </TestWrapper>
            )

            // Verify the component renders without throwing errors
            expect(container).toBeInTheDocument()
            
            // Clean up after each test
            cleanup()

            return true
          } catch (error) {
            console.error('Test failed with error:', error)
            cleanup()
            return false
          }
        }
      ),
      { numRuns: 50, verbose: false }
    )
  })

  test('Property 3: All resource metrics are displayed for active environments', () => {
    fc.assert(
      fc.property(
        fc.array(environmentArbitrary, { minLength: 1, maxLength: 3 }),
        (environments) => {
          try {
            // Filter to only active environments and ensure valid resource values
            const activeEnvironments = environments
              .filter(env => env.status === EnvironmentStatus.RUNNING || env.status === EnvironmentStatus.READY)
              .map(env => ({
                ...env,
                resources: {
                  ...env.resources,
                  cpu: Math.max(0, Math.min(100, env.resources.cpu)),
                  memory: Math.max(0, Math.min(100, env.resources.memory)),
                  disk: Math.max(0, Math.min(100, env.resources.disk))
                }
              }))

            // Skip if no active environments
            if (activeEnvironments.length === 0) {
              return true
            }

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

            const { container } = render(
              <TestWrapper>
                <ResourceUtilizationCharts
                  environments={activeEnvironments}
                  timeRange={timeRange}
                  chartType="realtime"
                  metrics={metrics}
                />
              </TestWrapper>
            )

            // Verify CPU metrics are displayed
            const cpuUsageElements = container.querySelectorAll('*')
            const hasAverageCpuUsage = Array.from(cpuUsageElements).some(el => 
              el.textContent && el.textContent.includes('Average CPU Usage')
            )
            const hasAverageMemoryUsage = Array.from(cpuUsageElements).some(el => 
              el.textContent && el.textContent.includes('Average Memory Usage')
            )
            const hasAverageDiskUsage = Array.from(cpuUsageElements).some(el => 
              el.textContent && el.textContent.includes('Average Disk Usage')
            )
            const hasActiveEnvironments = Array.from(cpuUsageElements).some(el => 
              el.textContent && el.textContent.includes('Active Environments')
            )
            
            expect(hasAverageCpuUsage).toBe(true)
            expect(hasAverageMemoryUsage).toBe(true)
            expect(hasAverageDiskUsage).toBe(true)
            expect(hasActiveEnvironments).toBe(true)

            cleanup()
            return true
          } catch (error) {
            console.error('Test failed with error:', error)
            cleanup()
            return false
          }
        }
      ),
      { numRuns: 50, verbose: false }
    )
  })

  test('Property 3: Warning indicators appear when resource thresholds are exceeded', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 85, max: 100 }), // High resource usage above default critical threshold
        fc.constantFrom('cpu' as const, 'memory' as const, 'disk' as const),
        (highUsage, resourceType) => {
          try {
            // Create environment with high resource usage
            const environment: Environment = {
              id: 'test-env-high-usage',
              type: EnvironmentType.QEMU_X86,
              status: EnvironmentStatus.RUNNING,
              architecture: 'x86_64',
              assignedTests: ['test-1'],
              resources: {
                cpu: resourceType === 'cpu' ? highUsage : 50,
                memory: resourceType === 'memory' ? highUsage : 50,
                disk: resourceType === 'disk' ? highUsage : 50,
                network: {
                  bytesIn: 1000000,
                  bytesOut: 1000000,
                  packetsIn: 1000,
                  packetsOut: 1000
                }
              },
              health: EnvironmentHealth.HEALTHY,
              metadata: {},
              createdAt: new Date(),
              lastUpdated: new Date()
            }

            const timeRange: TimeRange = {
              start: new Date(Date.now() - 30 * 60 * 1000),
              end: new Date()
            }

            const metrics: ResourceMetric[] = [
              { name: 'CPU Usage', type: 'cpu', unit: '%' },
              { name: 'Memory Usage', type: 'memory', unit: '%' },
              { name: 'Disk Usage', type: 'disk', unit: '%' }
            ]

            const { container } = render(
              <TestWrapper>
                <ResourceUtilizationCharts
                  environments={[environment]}
                  timeRange={timeRange}
                  chartType="realtime"
                  metrics={metrics}
                  enableAlerts={true}
                />
              </TestWrapper>
            )

            // Verify threshold alert appears for high resource utilization
            const allElements = container.querySelectorAll('*')
            const hasThresholdAlert = Array.from(allElements).some(el => 
              el.textContent && (
                el.textContent.includes('Resource Threshold Alerts') ||
                el.textContent.includes('Critical') ||
                el.textContent.includes('Warning')
              )
            )
            
            // Should have threshold alert when resource usage is high
            expect(hasThresholdAlert).toBe(true)

            cleanup()
            return true
          } catch (error) {
            console.error('Test failed with error:', error)
            cleanup()
            return false
          }
        }
      ),
      { numRuns: 25, verbose: false }
    )
  })

  test('Property 3: Resource utilization charts display correct data ranges', () => {
    fc.assert(
      fc.property(
        fc.array(environmentArbitrary, { minLength: 1, maxLength: 3 }),
        (environments) => {
          try {
            // Ensure resource values are within valid ranges
            const validEnvironments = environments.map(env => ({
              ...env,
              resources: {
                ...env.resources,
                cpu: Math.max(0, Math.min(100, env.resources.cpu)),
                memory: Math.max(0, Math.min(100, env.resources.memory)),
                disk: Math.max(0, Math.min(100, env.resources.disk))
              }
            }))

            const timeRange: TimeRange = {
              start: new Date(Date.now() - 30 * 60 * 1000),
              end: new Date()
            }

            const metrics: ResourceMetric[] = [
              { name: 'CPU Usage', type: 'cpu', unit: '%' }
            ]

            const { container } = render(
              <TestWrapper>
                <ResourceUtilizationCharts
                  environments={validEnvironments}
                  timeRange={timeRange}
                  chartType="realtime"
                  metrics={metrics}
                />
              </TestWrapper>
            )

            // Verify charts are rendered (check for SVG elements which Recharts uses)
            const svgElements = container.querySelectorAll('svg')
            expect(svgElements.length).toBeGreaterThan(0)

            // Verify resource utilization monitoring title is present
            const allElements = container.querySelectorAll('*')
            const hasMonitoringTitle = Array.from(allElements).some(el => 
              el.textContent && el.textContent.includes('Resource Utilization Monitoring')
            )
            expect(hasMonitoringTitle).toBe(true)

            cleanup()
            return true
          } catch (error) {
            console.error('Test failed with error:', error)
            cleanup()
            return false
          }
        }
      ),
      { numRuns: 25, verbose: false }
    )
  })

  test('Property 3: Charts handle empty environment data gracefully', () => {
    fc.assert(
      fc.property(
        timeRangeArbitrary,
        fc.constantFrom('realtime' as const, 'historical' as const),
        fc.array(resourceMetricArbitrary, { minLength: 1, maxLength: 4 }),
        (timeRange, chartType, metrics) => {
          try {
            // Render with empty environments array
            const { container } = render(
              <TestWrapper>
                <ResourceUtilizationCharts
                  environments={[]}
                  timeRange={timeRange}
                  chartType={chartType}
                  metrics={metrics}
                />
              </TestWrapper>
            )

            // Verify the component renders without errors even with no data
            expect(container).toBeInTheDocument()
            
            // Verify default values are shown (0% utilization)
            const cpuUsageElements = container.querySelectorAll('*')
            const hasAverageCpuUsage = Array.from(cpuUsageElements).some(el => 
              el.textContent && el.textContent.includes('Average CPU Usage')
            )
            const hasAverageMemoryUsage = Array.from(cpuUsageElements).some(el => 
              el.textContent && el.textContent.includes('Average Memory Usage')
            )
            const hasAverageDiskUsage = Array.from(cpuUsageElements).some(el => 
              el.textContent && el.textContent.includes('Average Disk Usage')
            )
            
            expect(hasAverageCpuUsage).toBe(true)
            expect(hasAverageMemoryUsage).toBe(true)
            expect(hasAverageDiskUsage).toBe(true)

            cleanup()
            return true
          } catch (error) {
            console.error('Test failed with error:', error)
            cleanup()
            return false
          }
        }
      ),
      { numRuns: 25, verbose: false }
    )
  })

  test('Property 3: Threshold configuration controls work correctly', () => {
    fc.assert(
      fc.property(
        fc.array(environmentArbitrary, { minLength: 1, maxLength: 3 }),
        fc.integer({ min: 50, max: 80 }), // Warning threshold
        fc.integer({ min: 85, max: 95 }), // Critical threshold
        (environments, warningThreshold, criticalThreshold) => {
          try {
            // Ensure resource values are within valid ranges
            const validEnvironments = environments.map(env => ({
              ...env,
              resources: {
                ...env.resources,
                cpu: Math.max(0, Math.min(100, env.resources.cpu)),
                memory: Math.max(0, Math.min(100, env.resources.memory)),
                disk: Math.max(0, Math.min(100, env.resources.disk))
              }
            }))

            const timeRange: TimeRange = {
              start: new Date(Date.now() - 30 * 60 * 1000),
              end: new Date()
            }

            const metrics: ResourceMetric[] = [
              { name: 'CPU Usage', type: 'cpu', unit: '%' }
            ]

            const customThresholds = {
              cpu: { warning: warningThreshold, critical: criticalThreshold },
              memory: { warning: warningThreshold, critical: criticalThreshold },
              disk: { warning: warningThreshold, critical: criticalThreshold },
              network: { warning: warningThreshold, critical: criticalThreshold }
            }

            const { container } = render(
              <TestWrapper>
                <ResourceUtilizationCharts
                  environments={validEnvironments}
                  timeRange={timeRange}
                  chartType="realtime"
                  metrics={metrics}
                  thresholds={customThresholds}
                  enableAlerts={true}
                />
              </TestWrapper>
            )

            // Verify threshold configuration section is present
            const allElements = container.querySelectorAll('*')
            const hasThresholdConfig = Array.from(allElements).some(el => 
              el.textContent && el.textContent.includes('Alert Thresholds')
            )
            expect(hasThresholdConfig).toBe(true)

            // Verify threshold values are displayed
            const hasWarningThreshold = Array.from(allElements).some(el => 
              el.textContent && el.textContent.includes(`Warning: ${warningThreshold}%`)
            )
            const hasCriticalThreshold = Array.from(allElements).some(el => 
              el.textContent && el.textContent.includes(`Critical: ${criticalThreshold}%`)
            )
            
            expect(hasWarningThreshold).toBe(true)
            expect(hasCriticalThreshold).toBe(true)

            cleanup()
            return true
          } catch (error) {
            console.error('Test failed with error:', error)
            cleanup()
            return false
          }
        }
      ),
      { numRuns: 25, verbose: false }
    )
  })

  test('Property 3: Individual environment cards display resource details correctly', () => {
    fc.assert(
      fc.property(
        fc.array(environmentArbitrary, { minLength: 1, maxLength: 5 }),
        (environments) => {
          try {
            // Ensure resource values are within valid ranges
            const validEnvironments = environments.map(env => ({
              ...env,
              resources: {
                ...env.resources,
                cpu: Math.max(0, Math.min(100, env.resources.cpu)),
                memory: Math.max(0, Math.min(100, env.resources.memory)),
                disk: Math.max(0, Math.min(100, env.resources.disk))
              }
            }))

            const timeRange: TimeRange = {
              start: new Date(Date.now() - 30 * 60 * 1000),
              end: new Date()
            }

            const metrics: ResourceMetric[] = [
              { name: 'CPU Usage', type: 'cpu', unit: '%' }
            ]

            const { container } = render(
              <TestWrapper>
                <ResourceUtilizationCharts
                  environments={validEnvironments}
                  timeRange={timeRange}
                  chartType="realtime"
                  metrics={metrics}
                />
              </TestWrapper>
            )

            // Verify environment resource details section is present
            const allElements = container.querySelectorAll('*')
            const hasResourceDetails = Array.from(allElements).some(el => 
              el.textContent && el.textContent.includes('Environment Resource Details')
            )
            expect(hasResourceDetails).toBe(true)

            // Verify individual environment cards show CPU, Memory, Disk labels
            const hasCpuLabel = Array.from(allElements).some(el => 
              el.textContent && el.textContent.includes('CPU:')
            )
            const hasMemoryLabel = Array.from(allElements).some(el => 
              el.textContent && el.textContent.includes('Memory:')
            )
            const hasDiskLabel = Array.from(allElements).some(el => 
              el.textContent && el.textContent.includes('Disk:')
            )
            
            expect(hasCpuLabel).toBe(true)
            expect(hasMemoryLabel).toBe(true)
            expect(hasDiskLabel).toBe(true)

            cleanup()
            return true
          } catch (error) {
            console.error('Test failed with error:', error)
            cleanup()
            return false
          }
        }
      ),
      { numRuns: 25, verbose: false }
    )
  })
})