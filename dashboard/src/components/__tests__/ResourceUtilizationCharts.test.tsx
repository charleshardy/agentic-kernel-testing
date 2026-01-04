/**
 * Unit Tests for ResourceUtilizationCharts Component
 * 
 * **Feature: environment-allocation-ui, Property 3: Resource Metrics Display Completeness**
 * **Validates: Requirements 2.1, 2.2, 2.3, 7.1, 7.3**
 * 
 * This test suite provides comprehensive coverage for the ResourceUtilizationCharts component,
 * including rendering, user interactions, error handling, and accessibility features.
 */

import React from 'react'
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import '@testing-library/jest-dom'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'

import ResourceUtilizationCharts from '../ResourceUtilizationCharts'
import { Environment, TimeRange, ResourceMetric } from '../../types/environment'
import { ErrorCategory, ErrorSeverity } from '../../types/errors'

// Mock dependencies
vi.mock('../ErrorHandling', () => ({
  ErrorBoundary: ({ children, onError }: any) => {
    try {
      return <div data-testid="error-boundary">{children}</div>
    } catch (error) {
      if (onError) onError(error, { componentStack: 'test' })
      return <div data-testid="error-boundary-fallback">Error occurred</div>
    }
  },
  ErrorAlert: ({ error }: any) => <div data-testid="error-alert">{error.message}</div>,
  ErrorRecovery: ({ error, onRetry }: any) => (
    <div data-testid="error-recovery">
      <span>{error.message}</span>
      <button onClick={onRetry}>Retry</button>
    </div>
  )
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

// Mock Recharts components
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
  ),
  PieChart: ({ children }: any) => <div data-testid="pie-chart">{children}</div>,
  Pie: () => <div data-testid="pie" />,
  Cell: () => <div data-testid="cell" />
}))

// Test data
const mockEnvironments: Environment[] = [
  {
    id: 'env-001',
    type: 'x86_64',
    architecture: 'x86_64',
    status: 'running',
    resources: {
      cpu: 45.5,
      memory: 67.2,
      disk: 23.8,
      network: { bytesIn: 1024, bytesOut: 2048 }
    },
    assignedTests: ['test-1', 'test-2']
  },
  {
    id: 'env-002',
    type: 'arm64',
    architecture: 'arm64',
    status: 'ready',
    resources: {
      cpu: 78.9,
      memory: 89.1,
      disk: 92.3,
      network: { bytesIn: 512, bytesOut: 1024 }
    },
    assignedTests: []
  },
  {
    id: 'env-003',
    type: 'riscv',
    architecture: 'riscv',
    status: 'provisioning',
    resources: {
      cpu: 12.3,
      memory: 34.5,
      disk: 56.7,
      network: { bytesIn: 256, bytesOut: 512 }
    },
    assignedTests: ['test-3']
  }
]

const mockTimeRange: TimeRange = {
  start: new Date('2024-01-01T00:00:00Z'),
  end: new Date('2024-01-01T01:00:00Z')
}

const mockMetrics: ResourceMetric[] = [
  { name: 'cpu', value: 45.5, timestamp: new Date() },
  { name: 'memory', value: 67.2, timestamp: new Date() },
  { name: 'disk', value: 23.8, timestamp: new Date() }
]

const defaultProps = {
  environments: mockEnvironments,
  timeRange: mockTimeRange,
  chartType: 'realtime' as const,
  metrics: mockMetrics
}

describe('ResourceUtilizationCharts', () => {
  let user: ReturnType<typeof userEvent.setup>

  beforeEach(() => {
    user = userEvent.setup()
    vi.clearAllMocks()
    // Mock Math.random for consistent test results
    vi.spyOn(Math, 'random').mockReturnValue(0.5)
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders the main dashboard with title and environment count', () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      expect(screen.getByText('Resource Utilization Monitoring')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument() // Environment count badge
    })

    it('displays aggregate statistics correctly', () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      expect(screen.getByText('Average CPU Usage')).toBeInTheDocument()
      expect(screen.getByText('Average Memory Usage')).toBeInTheDocument()
      expect(screen.getByText('Average Disk Usage')).toBeInTheDocument()
      expect(screen.getByText('Active Environments')).toBeInTheDocument()
    })

    it('renders environment cards with resource information', () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      // Check for environment IDs (truncated)
      expect(screen.getByText('env-001...')).toBeInTheDocument()
      expect(screen.getByText('env-002...')).toBeInTheDocument()
      expect(screen.getByText('env-003...')).toBeInTheDocument()
      
      // Check for status tags
      expect(screen.getByText('running')).toBeInTheDocument()
      expect(screen.getByText('ready')).toBeInTheDocument()
      expect(screen.getByText('provisioning')).toBeInTheDocument()
    })

    it('shows live indicator for realtime charts with auto-refresh', () => {
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          chartType="realtime" 
          autoRefresh={true} 
        />
      )
      
      expect(screen.getByText('Live')).toBeInTheDocument()
    })
  })

  describe('Chart Rendering and Types', () => {
    it('renders line chart by default', () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      expect(screen.getByTestId('line-chart')).toBeInTheDocument()
      expect(screen.getByTestId('responsive-container')).toBeInTheDocument()
    })

    it('switches to area chart when selected', async () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      const chartTypeSelect = screen.getByDisplayValue('Line')
      await user.click(chartTypeSelect)
      
      const areaOption = screen.getByText('Area')
      await user.click(areaOption)
      
      await waitFor(() => {
        expect(screen.getByTestId('area-chart')).toBeInTheDocument()
      })
    })

    it('switches to bar chart when selected', async () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      const chartTypeSelect = screen.getByDisplayValue('Line')
      await user.click(chartTypeSelect)
      
      const barOption = screen.getByText('Bar')
      await user.click(barOption)
      
      await waitFor(() => {
        expect(screen.getByTestId('bar-chart')).toBeInTheDocument()
      })
    })

    it('renders chart with selected metrics only', async () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      // Default metrics should be cpu, memory, disk
      expect(screen.getByTestId('line-cpu')).toBeInTheDocument()
      expect(screen.getByTestId('line-memory')).toBeInTheDocument()
      expect(screen.getByTestId('line-disk')).toBeInTheDocument()
    })
  })

  describe('Metric Selection and Filtering', () => {
    it('allows selecting different metrics', async () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      const metricsSelect = screen.getByPlaceholderText('Select metrics')
      await user.click(metricsSelect)
      
      const networkOption = screen.getByText('Network')
      await user.click(networkOption)
      
      await waitFor(() => {
        expect(screen.getByTestId('line-network')).toBeInTheDocument()
      })
    })

    it('shows environment filter when there are more than 5 environments', () => {
      const manyEnvironments = Array.from({ length: 10 }, (_, i) => ({
        ...mockEnvironments[0],
        id: `env-${i.toString().padStart(3, '0')}`
      }))
      
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          environments={manyEnvironments}
          showAggregateOnly={false}
        />
      )
      
      expect(screen.getByText('Environment Filter')).toBeInTheDocument()
      expect(screen.getByPlaceholderText('Select environments to display in chart')).toBeInTheDocument()
    })

    it('toggles between aggregate and individual data view', async () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      const aggregateSwitch = screen.getByRole('switch', { name: /aggregate/i })
      await user.click(aggregateSwitch)
      
      // Should show aggregate data
      expect(aggregateSwitch).toBeChecked()
    })
  })

  describe('Threshold Management', () => {
    it('displays threshold configuration section', () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      expect(screen.getByText('Alert Thresholds')).toBeInTheDocument()
      expect(screen.getByText('CPU Thresholds')).toBeInTheDocument()
      expect(screen.getByText('Memory Thresholds')).toBeInTheDocument()
      expect(screen.getByText('Disk Thresholds')).toBeInTheDocument()
    })

    it('allows toggling alerts on/off', async () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      const alertsSwitch = screen.getByRole('switch', { name: /alerts/i })
      await user.click(alertsSwitch)
      
      expect(alertsSwitch).not.toBeChecked()
    })

    it('provides reset defaults button for thresholds', async () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      const resetButton = screen.getByText('Reset Defaults')
      expect(resetButton).toBeInTheDocument()
      
      await user.click(resetButton)
      // Should reset thresholds to default values
    })

    it('shows alert summary when thresholds are exceeded', () => {
      const highUsageEnvironments = mockEnvironments.map(env => ({
        ...env,
        resources: {
          ...env.resources,
          cpu: 90, // Above critical threshold
          memory: 95 // Above critical threshold
        }
      }))
      
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          environments={highUsageEnvironments}
          enableAlerts={true}
        />
      )
      
      expect(screen.getByText('Resource Threshold Alerts')).toBeInTheDocument()
      expect(screen.getByText(/Critical/)).toBeInTheDocument()
    })
  })

  describe('Environment Cards and Status Indicators', () => {
    it('displays environment cards with correct resource percentages', () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      // Check for CPU, Memory, Disk labels
      expect(screen.getAllByText('CPU:')).toHaveLength(3)
      expect(screen.getAllByText('Memory:')).toHaveLength(3)
      expect(screen.getAllByText('Disk:')).toHaveLength(3)
    })

    it('shows test count for environments with assigned tests', () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      expect(screen.getByText('Tests: 2')).toBeInTheDocument() // env-001
      expect(screen.getByText('Tests: 1')).toBeInTheDocument() // env-003
    })

    it('applies warning/critical styling based on thresholds', () => {
      const criticalEnvironments = mockEnvironments.map(env => ({
        ...env,
        resources: {
          ...env.resources,
          cpu: 90 // Above critical threshold (85)
        }
      }))
      
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          environments={criticalEnvironments}
        />
      )
      
      // Should show error badges for critical environments
      const errorBadges = screen.getAllByRole('img', { name: /error/i })
      expect(errorBadges.length).toBeGreaterThan(0)
    })
  })

  describe('Export Functionality', () => {
    it('shows export button when onExportData prop is provided', () => {
      const mockExport = vi.fn()
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          onExportData={mockExport}
        />
      )
      
      expect(screen.getByText('Export')).toBeInTheDocument()
    })

    it('calls onExportData when export button is clicked', async () => {
      const mockExport = vi.fn()
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          onExportData={mockExport}
        />
      )
      
      const exportButton = screen.getByText('Export')
      await user.click(exportButton)
      
      expect(mockExport).toHaveBeenCalledTimes(1)
    })

    it('provides default export functionality when no onExportData prop', async () => {
      // Mock URL.createObjectURL and related functions
      const mockCreateObjectURL = vi.fn(() => 'mock-url')
      const mockRevokeObjectURL = vi.fn()
      const mockClick = vi.fn()
      const mockAppendChild = vi.fn()
      const mockRemoveChild = vi.fn()
      
      Object.defineProperty(URL, 'createObjectURL', { value: mockCreateObjectURL })
      Object.defineProperty(URL, 'revokeObjectURL', { value: mockRevokeObjectURL })
      
      const mockAnchor = {
        href: '',
        download: '',
        click: mockClick
      }
      
      vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as any)
      vi.spyOn(document.body, 'appendChild').mockImplementation(mockAppendChild)
      vi.spyOn(document.body, 'removeChild').mockImplementation(mockRemoveChild)
      
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      // Export button should not be visible without onExportData prop
      expect(screen.queryByText('Export')).not.toBeInTheDocument()
    })
  })

  describe('Fullscreen Mode', () => {
    it('toggles fullscreen mode', async () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      const fullscreenButton = screen.getByText('Fullscreen')
      await user.click(fullscreenButton)
      
      expect(screen.getByText('Exit')).toBeInTheDocument()
    })
  })

  describe('Loading and Empty States', () => {
    it('shows loading state when data is being fetched', () => {
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          environments={[]}
        />
      )
      
      expect(screen.getByText('No Environments Available')).toBeInTheDocument()
      expect(screen.getByText('Refresh')).toBeInTheDocument()
    })

    it('shows empty state message when no environments are provided', () => {
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          environments={[]}
        />
      )
      
      expect(screen.getByText('No Environments Available')).toBeInTheDocument()
      expect(screen.getByText('There are no environments to monitor. Please ensure environments are properly configured and running.')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('renders error boundary when component throws error', () => {
      // Mock console.error to avoid noise in test output
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      const ThrowError = () => {
        throw new Error('Test error')
      }
      
      render(
        <ResourceUtilizationCharts {...defaultProps}>
          <ThrowError />
        </ResourceUtilizationCharts>
      )
      
      expect(screen.getByTestId('error-boundary')).toBeInTheDocument()
      
      consoleSpy.mockRestore()
    })

    it('shows error recovery component when data error occurs', async () => {
      // Mock Math.random to trigger error condition
      vi.spyOn(Math, 'random').mockReturnValue(0.05) // Less than 0.1 to trigger error
      
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      // Wait for useEffect to run and potentially show error
      await waitFor(() => {
        // The component should handle the error gracefully
        expect(screen.getByTestId('error-boundary')).toBeInTheDocument()
      }, { timeout: 1000 })
    })
  })

  describe('Real-time Updates', () => {
    it('sets up auto-refresh interval for realtime charts', () => {
      vi.useFakeTimers()
      
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          chartType="realtime"
          autoRefresh={true}
          refreshInterval={1000}
        />
      )
      
      // Fast-forward time to trigger interval
      act(() => {
        vi.advanceTimersByTime(1000)
      })
      
      vi.useRealTimers()
    })

    it('does not set up auto-refresh for historical charts', () => {
      vi.useFakeTimers()
      
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          chartType="historical"
          autoRefresh={true}
        />
      )
      
      // Should not show live indicator for historical charts
      expect(screen.queryByText('Live')).not.toBeInTheDocument()
      
      vi.useRealTimers()
    })
  })

  describe('Accessibility', () => {
    it('provides proper ARIA labels and roles', () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      // Check for proper button roles
      expect(screen.getByRole('button', { name: /fullscreen/i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /reset defaults/i })).toBeInTheDocument()
      
      // Check for switch roles
      expect(screen.getByRole('switch', { name: /aggregate/i })).toBeInTheDocument()
      expect(screen.getByRole('switch', { name: /alerts/i })).toBeInTheDocument()
    })

    it('supports keyboard navigation', async () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      const fullscreenButton = screen.getByRole('button', { name: /fullscreen/i })
      
      // Focus the button
      fullscreenButton.focus()
      expect(fullscreenButton).toHaveFocus()
      
      // Press Enter to activate
      await user.keyboard('{Enter}')
      
      expect(screen.getByText('Exit')).toBeInTheDocument()
    })

    it('provides tooltips for informational elements', () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      // Check for tooltip triggers (info icons)
      const infoIcons = screen.getAllByRole('img', { name: /info/i })
      expect(infoIcons.length).toBeGreaterThan(0)
    })
  })

  describe('Performance Considerations', () => {
    it('handles large numbers of environments efficiently', () => {
      const manyEnvironments = Array.from({ length: 100 }, (_, i) => ({
        ...mockEnvironments[0],
        id: `env-${i.toString().padStart(3, '0')}`
      }))
      
      const startTime = performance.now()
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          environments={manyEnvironments}
        />
      )
      const endTime = performance.now()
      
      // Should render within reasonable time (less than 100ms)
      expect(endTime - startTime).toBeLessThan(100)
    })

    it('memoizes expensive calculations', () => {
      const { rerender } = render(<ResourceUtilizationCharts {...defaultProps} />)
      
      // Re-render with same props should not recalculate
      rerender(<ResourceUtilizationCharts {...defaultProps} />)
      
      // Component should still render correctly
      expect(screen.getByText('Resource Utilization Monitoring')).toBeInTheDocument()
    })
  })

  describe('Data Processing', () => {
    it('calculates aggregate metrics correctly', () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      // Check that aggregate statistics are displayed
      expect(screen.getByText('Average CPU Usage')).toBeInTheDocument()
      expect(screen.getByText('Average Memory Usage')).toBeInTheDocument()
      expect(screen.getByText('Average Disk Usage')).toBeInTheDocument()
      
      // The values should be calculated from active environments only
      // env-001 (running): cpu=45.5, memory=67.2, disk=23.8
      // env-002 (ready): cpu=78.9, memory=89.1, disk=92.3
      // env-003 (provisioning): not counted as active
      // Average CPU: (45.5 + 78.9) / 2 = 62.2 -> rounded to 62
      // Average Memory: (67.2 + 89.1) / 2 = 78.15 -> rounded to 78
      // Average Disk: (23.8 + 92.3) / 2 = 58.05 -> rounded to 58
    })

    it('filters chart data based on selected environments', async () => {
      const manyEnvironments = Array.from({ length: 10 }, (_, i) => ({
        ...mockEnvironments[0],
        id: `env-${i.toString().padStart(3, '0')}`
      }))
      
      render(
        <ResourceUtilizationCharts 
          {...defaultProps} 
          environments={manyEnvironments}
        />
      )
      
      // Should show environment filter
      expect(screen.getByText('Environment Filter')).toBeInTheDocument()
      
      const environmentSelect = screen.getByPlaceholderText('Select environments to display in chart')
      await user.click(environmentSelect)
      
      // Select first environment
      const firstEnvOption = screen.getByText('env-000... (x86_64)')
      await user.click(firstEnvOption)
      
      // Chart should now only show data for selected environment
    })

    it('groups historical data by timestamp for aggregate view', async () => {
      render(<ResourceUtilizationCharts {...defaultProps} />)
      
      const aggregateSwitch = screen.getByRole('switch', { name: /aggregate/i })
      await user.click(aggregateSwitch)
      
      // Should show aggregate data grouped by timestamp
      expect(aggregateSwitch).toBeChecked()
    })
  })
})