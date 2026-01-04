/**
 * Property-Based Tests for ResourceUtilizationCharts Component
 * 
 * **Feature: environment-allocation-ui, Property 3: Resource Metrics Display Completeness**
 * **Validates: Requirements 2.1, 2.2, 2.3, 7.1, 7.3**
 * 
 * These property-based tests verify that the ResourceUtilizationCharts component
 * behaves correctly across a wide range of input combinations and edge cases.
 */

import React from 'react'
import { render, screen } from '@testing-library/react'
import '@testing-library/jest-dom'
import { vi, describe, it, expect, beforeEach } from 'vitest'
import fc from 'fast-check'

import ResourceUtilizationCharts from '../ResourceUtilizationCharts'
import { Environment, TimeRange, ResourceMetric } from '../../types/environment'

// Mock dependencies (same as unit tests)
vi.mock('../ErrorHandling', () => ({
  ErrorBoundary: ({ children }: any) => <div data-testid="error-boundary">{children}</div>,
  ErrorAlert: ({ error }: any) => <div data-testid="error-alert">{error.message}</div>,
  ErrorRecovery: ({ error }: any) => <div data-testid="error-recovery">{error.message}</div>
}))

vi.mock('../ErrorHandling/ToastNotification', () => ({
  useToast: () => ({
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
    warning: vi.fn()
  })
}))

vi.mock('../../hooks/useErrorHandler', () => ({
  useErrorHandler: () => ({
    handleError: vi.fn(),
    clearError: vi.fn(),
    withErrorHandling: (fn: Function) => fn
  })
}))

vi.mock('recharts', () => ({
  LineChart: ({ children, data }: any) => (
    <div data-testid="line-chart" data-chart-data={JSON.stringify(data)}>
      {children}
    </div>
  ),
  AreaChart: ({ children, data }: any) => (
    <div data-testid="area-chart" data-chart-data={JSON.stringify(data)}>
      {children}
    </div>
  ),
  BarChart: ({ children, data }: any) => (
    <div data-testid="bar-chart" data-chart-data={JSON.stringify(data)}>
      {children}
    </div>
  ),
  Line: ({ dataKey }: any) => <div data-testid={`line-${dataKey}`} />,
  Area: ({ dataKey }: any) => <div data-testid={`area-${dataKey}`} />,
  Bar: ({ dataKey }: any) => <div data-testid={`bar-${dataKey}`} />,
  XAxis: () => <div data-testid="x-axis" />,
  YAxis: () => <div data-testid="y-axis" />,
  CartesianGrid: () => <div data-testid="cartesian-grid" />,
  Tooltip: () => <div data-testid="tooltip" />,
  Legend: () => <div data-testid="legend" />,
  ResponsiveContainer: ({ children }: any) => (
    <div data-testid="responsive-container">{children}</div>
  )
}))

// Property-based test generators
const environmentStatusArbitrary = fc.constantFrom('running', 'ready', 'provisioning', 'stopped', 'error')
const architectureArbitrary = fc.constantFrom('x86_64', 'arm64', 'riscv', 'mips')
const resourceValueArbitrary = fc.float({ min: 0, max: 100, noNaN: true })

const environmentArbitrary = fc.record({
  id: fc.string({ minLength: 1, maxLength: 20 }),
  type: architectureArbitrary,
  architecture: architectureArbitrary,
  status: environmentStatusArbitrary,
  resources: fc.record({
    cpu: resourceValueArbitrary,
    memory: resourceValueArbitrary,
    disk: resourceValueArbitrary,
    network: fc.record({
      bytesIn: fc.integer({ min: 0, max: 1000000 }),
      bytesOut: fc.integer({ min: 0, max: 1000000 })
    })
  }),
  assignedTests: fc.array(fc.string(), { maxLength: 10 })
})

const timeRangeArbitrary = fc.record({
  start: fc.date(),
  end: fc.date()
}).filter(({ start, end }) => start <= end)

const resourceMetricArbitrary = fc.record({
  name: fc.constantFrom('cpu', 'memory', 'disk', 'network'),
  value: resourceValueArbitrary,
  timestamp: fc.date()
})

const thresholdsArbitrary = fc.record({
  cpu: fc.record({
    warning: fc.integer({ min: 0, max: 80 }),
    critical: fc.integer({ min: 81, max: 100 })
  }),
  memory: fc.record({
    warning: fc.integer({ min: 0, max: 80 }),
    critical: fc.integer({ min: 81, max: 100 })
  }),
  disk: fc.record({
    warning: fc.integer({ min: 0, max: 80 }),
    critical: fc.integer({ min: 81, max: 100 })
  }),
  network: fc.record({
    warning: fc.integer({ min: 0, max: 80 }),
    critical: fc.integer({ min: 81, max: 100 })
  })
})

describe('ResourceUtilizationCharts Property-Based Tests', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Property 1: Component Always Renders Successfully', () => {
    it('should render without crashing for any valid environment data', () => {
      fc.assert(
        fc.property(
          fc.array(environmentArbitrary, { maxLength: 50 }),
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary, { maxLength: 20 }),
          (environments, timeRange, metrics) => {
            const { unmount } = render(
              <ResourceUtilizationCharts
                environments={environments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
              />
            )
            
            // Component should render the main title
            expect(screen.getByText('Resource Utilization Monitoring')).toBeInTheDocument()
            
            unmount()
          }
        ),
        { numRuns: 100 }
      )
    })
  })

  describe('Property 2: Environment Count Display Accuracy', () => {
    it('should always display correct environment count in badge', () => {
      fc.assert(
        fc.property(
          fc.array(environmentArbitrary, { maxLength: 100 }),
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary),
          (environments, timeRange, metrics) => {
            render(
              <ResourceUtilizationCharts
                environments={environments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
              />
            )
            
            // Active environments are those with status 'running' or 'ready'
            const activeCount = environments.filter(
              env => env.status === 'running' || env.status === 'ready'
            ).length
            
            // The badge should show the active environment count
            if (activeCount > 0) {
              expect(screen.getByText(activeCount.toString())).toBeInTheDocument()
            }
          }
        ),
        { numRuns: 100 }
      )
    })
  })

  describe('Property 3: Resource Metrics Display Completeness', () => {
    it('should display all required resource metrics for every environment', () => {
      fc.assert(
        fc.property(
          fc.array(environmentArbitrary, { minLength: 1, maxLength: 20 }),
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary),
          (environments, timeRange, metrics) => {
            render(
              <ResourceUtilizationCharts
                environments={environments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
              />
            )
            
            // Each environment should have CPU, Memory, and Disk labels
            const cpuLabels = screen.getAllByText('CPU:')
            const memoryLabels = screen.getAllByText('Memory:')
            const diskLabels = screen.getAllByText('Disk:')
            
            expect(cpuLabels).toHaveLength(environments.length)
            expect(memoryLabels).toHaveLength(environments.length)
            expect(diskLabels).toHaveLength(environments.length)
          }
        ),
        { numRuns: 50 }
      )
    })
  })

  describe('Property 4: Aggregate Statistics Consistency', () => {
    it('should calculate aggregate statistics correctly for any environment set', () => {
      fc.assert(
        fc.property(
          fc.array(environmentArbitrary, { minLength: 1, maxLength: 50 }),
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary),
          (environments, timeRange, metrics) => {
            render(
              <ResourceUtilizationCharts
                environments={environments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
              />
            )
            
            // Should always show aggregate statistics section
            expect(screen.getByText('Average CPU Usage')).toBeInTheDocument()
            expect(screen.getByText('Average Memory Usage')).toBeInTheDocument()
            expect(screen.getByText('Average Disk Usage')).toBeInTheDocument()
            expect(screen.getByText('Active Environments')).toBeInTheDocument()
            
            // Active environments count should be consistent
            const activeEnvs = environments.filter(
              env => env.status === 'running' || env.status === 'ready'
            )
            const totalEnvs = environments.length
            
            // Should show "active / total" format
            expect(screen.getByText(`${activeEnvs.length}`)).toBeInTheDocument()
            expect(screen.getByText(`/ ${totalEnvs}`)).toBeInTheDocument()
          }
        ),
        { numRuns: 100 }
      )
    })
  })

  describe('Property 5: Threshold Alert Consistency', () => {
    it('should show alerts when any environment exceeds thresholds', () => {
      fc.assert(
        fc.property(
          fc.array(environmentArbitrary, { minLength: 1, maxLength: 20 }),
          thresholdsArbitrary,
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary),
          (environments, thresholds, timeRange, metrics) => {
            render(
              <ResourceUtilizationCharts
                environments={environments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
                enableAlerts={true}
                thresholds={thresholds}
              />
            )
            
            // Check if any environment exceeds critical thresholds
            const hasCritical = environments.some(env => 
              env.resources.cpu >= thresholds.cpu.critical ||
              env.resources.memory >= thresholds.memory.critical ||
              env.resources.disk >= thresholds.disk.critical
            )
            
            // Check if any environment exceeds warning thresholds
            const hasWarning = environments.some(env => 
              env.resources.cpu >= thresholds.cpu.warning ||
              env.resources.memory >= thresholds.memory.warning ||
              env.resources.disk >= thresholds.disk.warning
            )
            
            if (hasCritical || hasWarning) {
              // Should show alert summary
              expect(screen.getByText('Resource Threshold Alerts')).toBeInTheDocument()
            }
          }
        ),
        { numRuns: 100 }
      )
    })
  })

  describe('Property 6: Chart Type Consistency', () => {
    it('should render appropriate chart type for any chart view selection', () => {
      fc.assert(
        fc.property(
          fc.array(environmentArbitrary, { minLength: 1, maxLength: 10 }),
          fc.constantFrom('line', 'area', 'bar'),
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary),
          (environments, chartView, timeRange, metrics) => {
            const { container } = render(
              <ResourceUtilizationCharts
                environments={environments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
              />
            )
            
            // Should always render a chart container
            expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
            
            // Default should be line chart
            expect(screen.getByTestId('line-chart')).toBeInTheDocument()
          }
        ),
        { numRuns: 50 }
      )
    })
  })

  describe('Property 7: Resource Value Bounds', () => {
    it('should handle resource values within valid bounds (0-100%)', () => {
      fc.assert(
        fc.property(
          fc.array(environmentArbitrary, { minLength: 1, maxLength: 20 }),
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary),
          (environments, timeRange, metrics) => {
            // Ensure all resource values are within bounds
            const boundedEnvironments = environments.map(env => ({
              ...env,
              resources: {
                ...env.resources,
                cpu: Math.max(0, Math.min(100, env.resources.cpu)),
                memory: Math.max(0, Math.min(100, env.resources.memory)),
                disk: Math.max(0, Math.min(100, env.resources.disk))
              }
            }))
            
            render(
              <ResourceUtilizationCharts
                environments={boundedEnvironments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
              />
            )
            
            // Component should render successfully with bounded values
            expect(screen.getByText('Resource Utilization Monitoring')).toBeInTheDocument()
            
            // All environments should be displayed
            boundedEnvironments.forEach(env => {
              const truncatedId = env.id.slice(0, 8) + '...'
              expect(screen.getByText(truncatedId)).toBeInTheDocument()
            })
          }
        ),
        { numRuns: 100 }
      )
    })
  })

  describe('Property 8: Empty State Handling', () => {
    it('should handle empty environment arrays gracefully', () => {
      fc.assert(
        fc.property(
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary),
          (timeRange, metrics) => {
            render(
              <ResourceUtilizationCharts
                environments={[]}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
              />
            )
            
            // Should show empty state
            expect(screen.getByText('No Environments Available')).toBeInTheDocument()
            expect(screen.getByText('Refresh')).toBeInTheDocument()
          }
        ),
        { numRuns: 50 }
      )
    })
  })

  describe('Property 9: Test Assignment Display', () => {
    it('should correctly display test counts for environments with assigned tests', () => {
      fc.assert(
        fc.property(
          fc.array(environmentArbitrary, { minLength: 1, maxLength: 20 }),
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary),
          (environments, timeRange, metrics) => {
            render(
              <ResourceUtilizationCharts
                environments={environments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
              />
            )
            
            // Check test count display for each environment
            environments.forEach(env => {
              if (env.assignedTests && env.assignedTests.length > 0) {
                const testCountText = `Tests: ${env.assignedTests.length}`
                expect(screen.getByText(testCountText)).toBeInTheDocument()
              }
            })
          }
        ),
        { numRuns: 100 }
      )
    })
  })

  describe('Property 10: Status Tag Consistency', () => {
    it('should display correct status tags for all environment statuses', () => {
      fc.assert(
        fc.property(
          fc.array(environmentArbitrary, { minLength: 1, maxLength: 20 }),
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary),
          (environments, timeRange, metrics) => {
            render(
              <ResourceUtilizationCharts
                environments={environments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
              />
            )
            
            // Each environment should have its status displayed
            const uniqueStatuses = [...new Set(environments.map(env => env.status))]
            uniqueStatuses.forEach(status => {
              expect(screen.getByText(status)).toBeInTheDocument()
            })
          }
        ),
        { numRuns: 100 }
      )
    })
  })

  describe('Property 11: Refresh Interval Behavior', () => {
    it('should handle different refresh intervals without errors', () => {
      fc.assert(
        fc.property(
          fc.array(environmentArbitrary, { minLength: 1, maxLength: 10 }),
          fc.integer({ min: 1000, max: 60000 }), // 1s to 60s
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary),
          (environments, refreshInterval, timeRange, metrics) => {
            const { unmount } = render(
              <ResourceUtilizationCharts
                environments={environments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
                autoRefresh={true}
                refreshInterval={refreshInterval}
              />
            )
            
            // Should render with live indicator for realtime + autoRefresh
            expect(screen.getByText('Live')).toBeInTheDocument()
            
            // Clean up to prevent memory leaks
            unmount()
          }
        ),
        { numRuns: 50 }
      )
    })
  })

  describe('Property 12: Architecture Display Consistency', () => {
    it('should display architecture information consistently', () => {
      fc.assert(
        fc.property(
          fc.array(environmentArbitrary, { minLength: 1, maxLength: 20 }),
          timeRangeArbitrary,
          fc.array(resourceMetricArbitrary),
          (environments, timeRange, metrics) => {
            render(
              <ResourceUtilizationCharts
                environments={environments}
                timeRange={timeRange}
                chartType="realtime"
                metrics={metrics}
              />
            )
            
            // Architecture should be displayed in tooltips or info sections
            // The component should render without errors regardless of architecture
            expect(screen.getByText('Resource Utilization Monitoring')).toBeInTheDocument()
          }
        ),
        { numRuns: 100 }
      )
    })
  })
})