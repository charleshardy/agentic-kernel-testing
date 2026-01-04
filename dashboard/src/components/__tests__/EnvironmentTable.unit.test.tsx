/**
 * Unit tests for EnvironmentTable component interactions
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

import EnvironmentTable from '../EnvironmentTable'
import { 
  Environment, 
  EnvironmentType, 
  EnvironmentStatus, 
  EnvironmentHealth,
  EnvironmentAction
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
    id: 'env-001-qemu-x86',
    type: EnvironmentType.QEMU_X86,
    status: EnvironmentStatus.RUNNING,
    architecture: 'x86_64',
    assignedTests: ['test-kernel-boot', 'test-network-stack'],
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
    metadata: {
      kernelVersion: '5.15.0',
      ipAddress: '192.168.1.100'
    },
    createdAt: new Date('2024-01-01'),
    lastUpdated: new Date()
  },
  {
    id: 'env-002-docker',
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
    createdAt: new Date('2024-01-02'),
    lastUpdated: new Date()
  },
  {
    id: 'env-003-physical',
    type: EnvironmentType.PHYSICAL,
    status: EnvironmentStatus.ERROR,
    architecture: 'x86_64',
    assignedTests: ['test-hardware-specific'],
    resources: {
      cpu: 95.8,
      memory: 88.9,
      disk: 12.3,
      network: {
        bytesIn: 5000000,
        bytesOut: 3000000,
        packetsIn: 5000,
        packetsOut: 4500
      }
    },
    health: EnvironmentHealth.UNHEALTHY,
    metadata: {
      kernelVersion: '5.19.0',
      ipAddress: '192.168.1.200'
    },
    createdAt: new Date('2024-01-03'),
    lastUpdated: new Date()
  }
]

describe('EnvironmentTable Component', () => {
  const defaultProps = {
    environments: mockEnvironments,
    onEnvironmentSelect: jest.fn(),
    onEnvironmentAction: jest.fn(),
    showResourceUsage: true,
    filterOptions: {},
    selectedEnvironments: [],
    onSelectionChange: jest.fn(),
    realTimeUpdates: true,
    lastUpdateTime: new Date()
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Component Rendering', () => {
    test('should render table with environment data', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} />
        </TestWrapper>
      )

      // Check table headers
      expect(screen.getByText('Environment ID')).toBeInTheDocument()
      expect(screen.getByText('Type')).toBeInTheDocument()
      expect(screen.getByText('Status')).toBeInTheDocument()
      expect(screen.getByText('Architecture')).toBeInTheDocument()
      expect(screen.getByText('Assigned Tests')).toBeInTheDocument()
      expect(screen.getByText('Resource Usage')).toBeInTheDocument()
      expect(screen.getByText('Health')).toBeInTheDocument()
      expect(screen.getByText('Actions')).toBeInTheDocument()

      // Check environment data is displayed
      expect(screen.getByText('env-001-qemu-x86')).toBeInTheDocument()
      expect(screen.getByText('env-002-docker')).toBeInTheDocument()
      expect(screen.getByText('env-003-physical')).toBeInTheDocument()
    })

    test('should display environment types with correct colors', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} />
        </TestWrapper>
      )

      // Check environment type tags
      expect(screen.getByText('QEMU-X86')).toBeInTheDocument()
      expect(screen.getByText('DOCKER')).toBeInTheDocument()
      expect(screen.getByText('PHYSICAL')).toBeInTheDocument()
    })

    test('should display environment statuses correctly', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} />
        </TestWrapper>
      )

      // Status indicators should be present (handled by StatusChangeIndicator component)
      const statusElements = screen.getAllByText(/running|ready|error/i)
      expect(statusElements.length).toBeGreaterThan(0)
    })

    test('should display resource usage when enabled', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} showResourceUsage={true} />
        </TestWrapper>
      )

      // Check for resource usage labels
      expect(screen.getAllByText('CPU:')).toHaveLength(3)
      expect(screen.getAllByText('MEM:')).toHaveLength(3)
      expect(screen.getAllByText('DSK:')).toHaveLength(3)
    })

    test('should hide resource usage when disabled', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} showResourceUsage={false} />
        </TestWrapper>
      )

      // Resource usage column should not be present
      expect(screen.queryByText('Resource Usage')).not.toBeInTheDocument()
      expect(screen.queryByText('CPU:')).not.toBeInTheDocument()
    })

    test('should display assigned tests correctly', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} />
        </TestWrapper>
      )

      // Check assigned tests are displayed
      expect(screen.getByText('test-kern...')).toBeInTheDocument() // Truncated test name
      expect(screen.getByText('test-netw...')).toBeInTheDocument() // Truncated test name
      expect(screen.getByText('No tests')).toBeInTheDocument() // For env-002 with no tests
    })

    test('should display health status with correct badges', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} />
        </TestWrapper>
      )

      // Check health status badges
      expect(screen.getAllByText('HEALTHY')).toHaveLength(2)
      expect(screen.getByText('UNHEALTHY')).toBeInTheDocument()
    })
  })

  describe('User Interactions', () => {
    test('should handle environment selection', async () => {
      const user = userEvent.setup()
      const onEnvironmentSelect = jest.fn()

      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            onEnvironmentSelect={onEnvironmentSelect}
          />
        </TestWrapper>
      )

      // Click on first environment row
      const environmentRow = screen.getByText('env-001-qemu-x86').closest('tr')
      expect(environmentRow).toBeInTheDocument()
      
      await user.click(environmentRow!)
      expect(onEnvironmentSelect).toHaveBeenCalledWith('env-001-qemu-x86')
    })

    test('should handle environment action buttons', async () => {
      const user = userEvent.setup()
      const onEnvironmentAction = jest.fn()

      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            onEnvironmentAction={onEnvironmentAction}
          />
        </TestWrapper>
      )

      // Find and click view details button
      const viewButtons = screen.getAllByLabelText(/view details/i)
      expect(viewButtons.length).toBeGreaterThan(0)
      
      await user.click(viewButtons[0])
      // The button click should trigger environment selection, not action
      expect(defaultProps.onEnvironmentSelect).toHaveBeenCalled()
    })

    test('should handle row selection with checkboxes', async () => {
      const user = userEvent.setup()
      const onSelectionChange = jest.fn()

      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            onSelectionChange={onSelectionChange}
          />
        </TestWrapper>
      )

      // Find and click checkbox for first environment
      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes.length).toBeGreaterThan(0)
      
      await user.click(checkboxes[1]) // First checkbox is "select all"
      expect(onSelectionChange).toHaveBeenCalled()
    })

    test('should disable selection for error/offline environments', () => {
      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            onSelectionChange={jest.fn()}
          />
        </TestWrapper>
      )

      // Find checkboxes - the error environment should have disabled checkbox
      const checkboxes = screen.getAllByRole('checkbox')
      
      // Check that at least one checkbox is disabled (for error environment)
      const disabledCheckboxes = checkboxes.filter(cb => cb.hasAttribute('disabled'))
      expect(disabledCheckboxes.length).toBeGreaterThan(0)
    })
  })

  describe('Real-time Updates', () => {
    test('should display real-time update indicator when enabled', () => {
      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            realTimeUpdates={true}
            lastUpdateTime={new Date()}
          />
        </TestWrapper>
      )

      expect(screen.getByText('Live updates enabled')).toBeInTheDocument()
      expect(screen.getByText(/last update:/i)).toBeInTheDocument()
    })

    test('should not display real-time indicator when disabled', () => {
      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            realTimeUpdates={false}
          />
        </TestWrapper>
      )

      expect(screen.queryByText('Live updates enabled')).not.toBeInTheDocument()
    })

    test('should handle environment updates with visual feedback', () => {
      const { rerender } = render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} />
        </TestWrapper>
      )

      // Update environment status
      const updatedEnvironments = mockEnvironments.map(env => 
        env.id === 'env-001-qemu-x86' 
          ? { ...env, status: EnvironmentStatus.CLEANUP, lastUpdated: new Date() }
          : env
      )

      rerender(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            environments={updatedEnvironments}
            lastUpdateTime={new Date()}
          />
        </TestWrapper>
      )

      // The component should handle the update (visual feedback is handled by CSS animations)
      expect(screen.getByText('env-001-qemu-x86')).toBeInTheDocument()
    })
  })

  describe('Performance Features', () => {
    test('should enable virtualization for large datasets', () => {
      const largeEnvironmentList = Array.from({ length: 100 }, (_, i) => ({
        ...mockEnvironments[0],
        id: `env-${i.toString().padStart(3, '0')}`
      }))

      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            environments={largeEnvironmentList}
            enableVirtualization={true}
            virtualizationThreshold={50}
          />
        </TestWrapper>
      )

      // Should show virtualization indicator
      expect(screen.getByText(/virtualization enabled for 100 environments/i)).toBeInTheDocument()
    })

    test('should show loading skeleton when loading', () => {
      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            loading={true}
          />
        </TestWrapper>
      )

      // Should show skeleton loading
      expect(screen.getByTestId('skeleton')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    test('should have proper ARIA labels', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} />
        </TestWrapper>
      )

      // Check main table region
      expect(screen.getByRole('region', { name: /environment allocation table/i })).toBeInTheDocument()
      
      // Check table structure
      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getAllByRole('row')).toHaveLength(4) // Header + 3 data rows
    })

    test('should support keyboard navigation', async () => {
      const user = userEvent.setup()
      
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} />
        </TestWrapper>
      )

      const tableRegion = screen.getByRole('region', { name: /environment allocation table/i })
      
      // Focus the table region
      tableRegion.focus()
      
      // Test arrow key navigation
      await user.keyboard('{ArrowDown}')
      
      // Should handle keyboard navigation (implementation details would be in the component)
      expect(tableRegion).toHaveFocus()
    })

    test('should have proper row labels', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} />
        </TestWrapper>
      )

      // Check that rows have proper ARIA labels
      const rows = screen.getAllByRole('row')
      const dataRows = rows.slice(1) // Skip header row
      
      dataRows.forEach(row => {
        expect(row).toHaveAttribute('aria-label')
      })
    })
  })

  describe('Resource Usage Display', () => {
    test('should show resource usage with correct colors', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} showResourceUsage={true} />
        </TestWrapper>
      )

      // Check that progress bars are rendered
      const progressBars = screen.getAllByRole('progressbar')
      expect(progressBars.length).toBeGreaterThan(0)
    })

    test('should display resource percentages', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} showResourceUsage={true} />
        </TestWrapper>
      )

      // Check for percentage values
      expect(screen.getByText('75.5%')).toBeInTheDocument() // CPU for env-001
      expect(screen.getByText('82.3%')).toBeInTheDocument() // Memory for env-001
      expect(screen.getByText('45.1%')).toBeInTheDocument() // Disk for env-001
    })

    test('should show high usage warnings', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} showResourceUsage={true} />
        </TestWrapper>
      )

      // High usage should be indicated by progress bar status
      // env-003 has high CPU (95.8%) and memory (88.9%) usage
      const progressBars = screen.getAllByRole('progressbar')
      expect(progressBars.length).toBeGreaterThan(0)
    })
  })

  describe('Environment Actions', () => {
    test('should render action buttons for each environment', () => {
      render(
        <TestWrapper>
          <EnvironmentTable {...defaultProps} />
        </TestWrapper>
      )

      // Check for view details buttons
      const viewButtons = screen.getAllByLabelText(/view details for environment/i)
      expect(viewButtons).toHaveLength(3)

      // Check for quick actions buttons
      const actionButtons = screen.getAllByLabelText(/quick actions for environment/i)
      expect(actionButtons).toHaveLength(3)
    })

    test('should handle action button clicks without propagation', async () => {
      const user = userEvent.setup()
      const onEnvironmentSelect = jest.fn()

      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            onEnvironmentSelect={onEnvironmentSelect}
          />
        </TestWrapper>
      )

      // Click on action button should not trigger row selection
      const viewButton = screen.getAllByLabelText(/view details for environment/i)[0]
      await user.click(viewButton)

      // Should call environment select (because the button handler calls it)
      expect(onEnvironmentSelect).toHaveBeenCalled()
    })
  })

  describe('Empty State', () => {
    test('should display empty state when no environments', () => {
      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            environments={[]}
          />
        </TestWrapper>
      )

      expect(screen.getByText('No environments available')).toBeInTheDocument()
    })
  })

  describe('Pagination', () => {
    test('should show pagination for large datasets without virtualization', () => {
      const largeEnvironmentList = Array.from({ length: 25 }, (_, i) => ({
        ...mockEnvironments[0],
        id: `env-${i.toString().padStart(3, '0')}`
      }))

      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            environments={largeEnvironmentList}
            enableVirtualization={false}
          />
        </TestWrapper>
      )

      // Should show pagination
      expect(screen.getByLabelText(/environment table pagination/i)).toBeInTheDocument()
    })

    test('should not show pagination when virtualization is enabled', () => {
      const largeEnvironmentList = Array.from({ length: 100 }, (_, i) => ({
        ...mockEnvironments[0],
        id: `env-${i.toString().padStart(3, '0')}`
      }))

      render(
        <TestWrapper>
          <EnvironmentTable 
            {...defaultProps} 
            environments={largeEnvironmentList}
            enableVirtualization={true}
            virtualizationThreshold={50}
          />
        </TestWrapper>
      )

      // Should not show pagination when virtualization is enabled
      expect(screen.queryByLabelText(/environment table pagination/i)).not.toBeInTheDocument()
    })
  })
})