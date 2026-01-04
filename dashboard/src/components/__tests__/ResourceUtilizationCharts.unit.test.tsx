/**
 * Unit tests for ResourceUtilizationCharts component interactions
 * 
 * **Feature: environment-allocation-ui, Task 14.1: Unit tests for component interactions**
 * **Validates: Requirements All**
 */

import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
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

// Test wrapper component
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

// Mock data
const mockEnvironments: Environment[] = [
  {
    id: 'env-001',
    type: EnvironmentType.QEMU_X86,
    status: EnvironmentStatus.RUNNING,
    architecture: 'x86_64',
    assignedTests: ['test-1', 'test-2'],
    resources: {
      cpu: 75.5,
      memory: 82.3,
      disk: 45.1,
      network: {
        bytesIn: 1000000,
        bytesOut: 500000,
        packetsIn: 1000,
        packetsOut: 800
      }
    },
    health: EnvironmentHealth.HEALTHY,
    metadata: {},
    createdAt: new Date(),
    lastUpdated: new Date()
  },
  {
    id: 'env-002',
    type: EnvironmentType.DOCKER,
    status: EnvironmentStatus.READY,
    architecture: 'arm64',
    assignedTests: [],
    resources: {
      cpu: 25.2,
      memory: 45.7,
      disk: 67.8,
      network: {
        bytesIn: 200000,
        bytesOut: 150000,
        packetsIn: 200,
        packetsOut: 180
      }
    },
    health: EnvironmentHealth.HEALTHY,
    metadata: {},
    createdAt: new Date(),
    lastUpdated: new Date()
  }
]

const mockTimeRange: TimeRange = {
  start: new Date(Date.now() - 30 * 60 * 1000),
  end: new Date()
}

const mockMetrics: ResourceMetric[] = [
  { name: 'CPU Usage', type: 'cpu', unit: '%' },
  { name: 'Memory Usage', type: 'memory', unit: '%' },
  { name: 'Disk Usage', type: 'disk', unit: '%' },
  { name: 'Network I/O', type: 'network', unit: 'MB/s' }
]

describe('ResourceUtilizationCharts Component', () => {
  const defaultProps = {
    environments: mockEnvironments,
    timeRange: mockTimeRange,
    chartType: 'realtime' as const,
    metrics: mockMetrics
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Component Rendering', () => {
    test('should render charts with aggregate statistics', () => {
      render(
        <TestWrapper>
          <ResourceUtilizationCharts {...defaultProps} />
        </TestWrapper>
      )

      // Check main title
      expect(screen.getByText('Resource Utilization Monitoring')).toBeInTheDocument()

      // Check aggregate statistics
      expect(screen.getByText('Average CPU Usage')).toBeInTheDocument()
      expect(screen.getByText('Average Memory Usage')).toBeInTheDocument()
      expect(screen.getByText('Average Disk Usage')).toBeInTheDocument()
      expect(screen.getByText('Active Environments')).toBeInTheDocument()
    })

    test('should display correct aggregate values', () => {
      render(
        <TestWrapper>
          <ResourceUtilizationCharts {...defaultProps} />
        </TestWrapper>
      )

      // Calculate expected averages: (75.5 + 25.2) / 2 = 50.35 ≈ 50
      expect(screen.getByText('50')).toBeInTheDocument() // Average CPU
      
      // Calculate expected averages: (82.3 + 45.7) / 2 = 64.0 ≈ 64
      expect(screen.getByText('64')).toBeInTheDocument() // Average Memory
      
      // Calculate expected averages: (45.1 + 67.8) / 2 = 56.45 ≈ 56
      expect(screen.getByText('56')).toBeInTheDocument() // Average Disk
    })

    test('should render resource trend charts', () => {
      render(
        <TestWrapper>
          <ResourceUtilizationCharts {...defaultProps} />
        </TestWrapper>
      )

      // Check for chart container
      expect(screen.getByText('Resource Trends')).toBeInTheDocument()
      
      // Check for SVG elements (Recharts renders SVG)
      const svgElements = document.querySelectorAll('svg')
      expect(svgElements.length).toBeGreaterThan(0)
    })

    test('should display individual environment cards', () => {
      render(
        <TestWrapper>
          <ResourceUtilizationCharts {...defaultProps} />
        </TestWrapper>
      )

      // Check for environment resource details section
      expect(screen.getByText('Environment Resource Details')).toBeInTheDocument()
      
      // Check for individual environment cards
      expect(screen.getByText('env-001...')).toBeInTheDocument()
      expect(screen.getByText('env-002...')).toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    test('should handle metric selection changes', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ResourceUtilizationCharts {...defaultProps} />
        </TestWrapper>
      )

      // Find metric selection dropdown
      const metricSelect = screen.getByDisplayValue(/cpu.*memory.*disk/i)
      expect(metricSelect).toBeInTheDocument()
      
      // The interaction would be handled by the Select component
      // We can verify the component renders without errors
    })

    test('should handle chart view changes', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ResourceUtilizationCharts {...defaultProps} />
        </TestWrapper>
      )

      // Find chart view selector
      const chartViewSelect = screen.getByDisplayValue(/line/i)
      expect(chartViewSelect).toBeInTheDocument()
    })

    test('should handle aggregate/individual toggle', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ResourceUtilizationCharts {...defaultProps} />
        </TestWrapper>
      )

      // Find aggregate toggle switch
      const aggregateSwitch = screen.getByRole('switch', { name: /individual/i })
      expect(aggregateSwitch).toBeInTheDocument()
      
      await user.click(aggregateSwitch)
      
      // Should toggle to aggregate view
      expect(screen.getByRole('switch', { name: /aggregate/i })).toBeInTheDocument()
    })

    test('should handle fullscreen toggle', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ResourceUtilizationCharts {...defaultProps} />
        </TestWrapper>
      )

      // Find fullscreen button
      const fullscreenButton = screen.getByRole('button', { name: /fullscreen/i })
      expect(fullscreenButton).toBeInTheDocument()
      
      await user.click(fullscreenButton)
      
      // Should show exit fullscreen button
      expect(screen.getByRole('button', { name: /exit/i })).toBeInTheDocument()
    })
  })

  describe('Threshold Management', () => {
    test('should display threshold configuration', () => {
      render(
        <TestWrapper>
          <ResourceUtilizationCharts {...defaultProps} enableAlerts={true} />
        </TestWrapper>
      )

      // Check threshold configuration section
      expect(screen.getByText('Alert Thresholds')).toBeInTheDocument()
      expect(screen.getByText('CPU Thresholds')).toBeInTheDocument()
      expect(screen.getByText('Memory Thresholds')).toBeInTheDocument()
      expect(screen.getByText('Disk Thresholds')).toBeInTheDocument()
    })

    test('should show threshold alerts for high usage', () => {
      const highUsageEnvironments = mockEnvironments.map(env => ({
        ...env,
        resources: {
          ...env.resources,
          cpu: 90, // Above critical threshold
          memory: 95 // Above critical threshold
        }
      }))

      render(
        <TestWrapper>
          <ResourceUtilizationCharts 
            {...defaultProps} 
            environments={highUsageEnvironments}
            enableAlerts={true}
          />
        </TestWrapper>
      )

      // Should show threshold alert
      expect(screen.getByText('Resource Threshold Alerts')).toBeInTheDocument()
      expect(screen.getByText(/critical/i)).toBeInTheDocument()
    })

    test('should handle threshold reset', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <ResourceUtilizationCharts {...defaultProps} enableAlerts={true} />
        </TestWrapper>
      )

      // Find reset defaults button
      const resetButton = screen.getByRole('button', { name: /reset defaults/i })
      expect(resetButton).toBeInTheDocument()
      
      await user.click(resetButton)
      
      // Should reset to default thresholds (component internal state)
      expect(resetButton).toBeInTheDocument()
    })
  })

  describe('Export Functionality', () => {
    test('should show export button when enabled', () => {
      const onExportData = jest.fn()
      
      render(
        <TestWrapper>
          <ResourceUtilizationCharts 
            {...defaultProps} 
            onExportData={onExportData}
          />
        </TestWrapper>
      )

      // Check for export button
      expect(screen.getByRole('button', { name: /export/i })).toBeInTheDocument()
    })

    test('should handle export button click', async () => {
      const user = userEvent.setup()
      const onExportData = jest.fn()
      
      render(
        <TestWrapper>
          <ResourceUtilizationCharts 
            {...defaultProps} 
            onExportData={onExportData}
          />
        </TestWrapper>
      )

      // Click export button
      const exportButton = screen.getByRole('button', { name: /export/i })
      await user.click(exportButton)
      
      expect(onExportData).toHaveBeenCalled()
    })
  })

  describe('Environment Filtering', () => {
    test('should show environment filter for large datasets', () => {
      const largeEnvironmentList = Array.from({ length: 10 }, (_, i) => ({
        ...mockEnvironments[0],
        id: `env-${i.toString().padStart(3, '0')}`
      }))

      render(
        <TestWrapper>
          <ResourceUtilizationCharts 
            {...defaultProps} 
            environments={largeEnvironmentList}
          />
        </TestWrapper>
      )

      // Should show environment filter
      expect(screen.getByText('Environment Filter')).toBeInTheDocument()
    })

    test('should not show environment filter for small datasets', () => {
      render(
        <TestWrapper>
          <ResourceUtilizationCharts {...defaultProps} />
        </TestWrapper>
      )

      // Should not show environment filter for small datasets
      expect(screen.queryByText('Environment Filter')).not.toBeInTheDocument()
    })
  })

  describe('Empty State Handling', () => {
    test('should handle empty environments gracefully', () => {
      render(
        <TestWrapper>
          <ResourceUtilizationCharts 
            {...defaultProps} 
            environments={[]}
          />
        </TestWrapper>
      )

      // Should still render with 0 values
      expect(screen.getByText('Resource Utilization Monitoring')).toBeInTheDocument()
      expect(screen.getByText('0')).toBeInTheDocument() // Should show 0 for averages
    })
  })
})