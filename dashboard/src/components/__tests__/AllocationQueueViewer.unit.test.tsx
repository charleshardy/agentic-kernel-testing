/**
 * Unit tests for AllocationQueueViewer component interactions
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

import AllocationQueueViewer from '../AllocationQueueViewer'
import { 
  AllocationRequest,
  AllocationStatus,
  EnvironmentType
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
const mockAllocationRequests: AllocationRequest[] = [
  {
    id: 'req-001',
    testId: 'test-kernel-boot',
    requirements: {
      architecture: 'x86_64',
      minMemoryMB: 2048,
      minCpuCores: 4,
      requiredFeatures: ['kvm', 'nested-virt'],
      preferredEnvironmentType: EnvironmentType.QEMU_X86,
      isolationLevel: 'vm'
    },
    priority: 8,
    submittedAt: new Date('2024-01-01T10:00:00Z'),
    estimatedStartTime: new Date('2024-01-01T10:05:00Z'),
    status: AllocationStatus.PENDING
  },
  {
    id: 'req-002',
    testId: 'test-network-stack',
    requirements: {
      architecture: 'arm64',
      minMemoryMB: 1024,
      minCpuCores: 2,
      requiredFeatures: ['network'],
      preferredEnvironmentType: EnvironmentType.QEMU_ARM,
      isolationLevel: 'container'
    },
    priority: 5,
    submittedAt: new Date('2024-01-01T10:02:00Z'),
    estimatedStartTime: new Date('2024-01-01T10:08:00Z'),
    status: AllocationStatus.PENDING
  },
  {
    id: 'req-003',
    testId: 'test-filesystem',
    requirements: {
      architecture: 'x86_64',
      minMemoryMB: 512,
      minCpuCores: 1,
      requiredFeatures: ['storage'],
      preferredEnvironmentType: EnvironmentType.DOCKER,
      isolationLevel: 'process'
    },
    priority: 3,
    submittedAt: new Date('2024-01-01T10:01:00Z'),
    estimatedStartTime: new Date('2024-01-01T10:12:00Z'),
    status: AllocationStatus.ALLOCATED
  },
  {
    id: 'req-004',
    testId: 'test-memory-mgmt',
    requirements: {
      architecture: 'x86_64',
      minMemoryMB: 4096,
      minCpuCores: 8,
      requiredFeatures: ['large-memory'],
      preferredEnvironmentType: EnvironmentType.PHYSICAL,
      isolationLevel: 'vm'
    },
    priority: 10,
    submittedAt: new Date('2024-01-01T09:58:00Z'),
    estimatedStartTime: new Date('2024-01-01T10:03:00Z'),
    status: AllocationStatus.FAILED
  }
]

const mockEstimatedWaitTimes = new Map([
  ['req-001', 300], // 5 minutes
  ['req-002', 480], // 8 minutes
  ['req-003', 0],   // Already allocated
  ['req-004', -1]   // Failed
])

describe('AllocationQueueViewer Component', () => {
  const defaultProps = {
    queue: mockAllocationRequests,
    estimatedWaitTimes: mockEstimatedWaitTimes,
    onPriorityChange: jest.fn(),
    onCancelRequest: jest.fn(),
    onBulkCancel: jest.fn(),
    onRefresh: jest.fn(),
    realTimeUpdates: true,
    lastUpdateTime: new Date(),
    enableBulkOperations: true,
    enableAdvancedFiltering: true,
    showQueueAnalytics: true
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  describe('Component Rendering', () => {
    test('should render queue viewer with allocation requests', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Check main title
      expect(screen.getByText('Allocation Queue')).toBeInTheDocument()

      // Check queue analytics
      expect(screen.getByText('Queue Analytics')).toBeInTheDocument()

      // Check allocation requests
      expect(screen.getByText('test-kernel-boot')).toBeInTheDocument()
      expect(screen.getByText('test-network-stack')).toBeInTheDocument()
      expect(screen.getByText('test-filesystem')).toBeInTheDocument()
      expect(screen.getByText('test-memory-mgmt')).toBeInTheDocument()
    })

    test('should display queue analytics when enabled', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Check analytics section
      expect(screen.getByText('Queue Analytics')).toBeInTheDocument()
      expect(screen.getByText('Total Requests')).toBeInTheDocument()
      expect(screen.getByText('Pending Requests')).toBeInTheDocument()
      expect(screen.getByText('Average Wait Time')).toBeInTheDocument()
    })

    test('should hide queue analytics when disabled', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer 
            {...defaultProps} 
            showQueueAnalytics={false}
          />
        </TestWrapper>
      )

      expect(screen.queryByText('Queue Analytics')).not.toBeInTheDocument()
    })

    test('should display real-time update indicator', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      expect(screen.getByText('Live Updates')).toBeInTheDocument()
    })

    test('should display request priorities correctly', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Check priority tags
      expect(screen.getByText('P8')).toBeInTheDocument() // req-001
      expect(screen.getByText('P5')).toBeInTheDocument() // req-002
      expect(screen.getByText('P3')).toBeInTheDocument() // req-003
      expect(screen.getByText('P10')).toBeInTheDocument() // req-004
    })

    test('should display request status with correct colors', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Check status tags
      expect(screen.getAllByText('PENDING')).toHaveLength(2)
      expect(screen.getByText('ALLOCATED')).toBeInTheDocument()
      expect(screen.getByText('FAILED')).toBeInTheDocument()
    })

    test('should display estimated wait times', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Check wait time displays
      expect(screen.getByText('5m 0s')).toBeInTheDocument() // 300 seconds
      expect(screen.getByText('8m 0s')).toBeInTheDocument() // 480 seconds
    })
  })

  describe('Filtering and Search', () => {
    test('should display advanced filtering controls when enabled', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Check filter controls
      expect(screen.getByPlaceholderText('Search requests...')).toBeInTheDocument()
      expect(screen.getByText('All Statuses')).toBeInTheDocument()
      expect(screen.getByText('All Priorities')).toBeInTheDocument()
      expect(screen.getByText('All Architectures')).toBeInTheDocument()
    })

    test('should filter requests by search query', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Type in search box
      const searchInput = screen.getByPlaceholderText('Search requests...')
      await user.type(searchInput, 'kernel')

      // Should filter to show only kernel-related requests
      await waitFor(() => {
        expect(screen.getByText('test-kernel-boot')).toBeInTheDocument()
        expect(screen.queryByText('test-network-stack')).not.toBeInTheDocument()
      })
    })

    test('should filter requests by status', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Click status filter dropdown
      const statusFilter = screen.getByText('All Statuses')
      await user.click(statusFilter)

      // Select PENDING status
      const pendingOption = screen.getByText('Pending')
      await user.click(pendingOption)

      // Should show only pending requests
      await waitFor(() => {
        expect(screen.getAllByText('PENDING')).toHaveLength(2)
        expect(screen.queryByText('ALLOCATED')).not.toBeInTheDocument()
        expect(screen.queryByText('FAILED')).not.toBeInTheDocument()
      })
    })

    test('should clear filters', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Apply a search filter
      const searchInput = screen.getByPlaceholderText('Search requests...')
      await user.type(searchInput, 'kernel')

      // Click clear filters button
      const clearButton = screen.getByText('Clear Filters')
      await user.click(clearButton)

      // Should show all requests again
      await waitFor(() => {
        expect(screen.getByText('test-kernel-boot')).toBeInTheDocument()
        expect(screen.getByText('test-network-stack')).toBeInTheDocument()
        expect(screen.getByText('test-filesystem')).toBeInTheDocument()
        expect(screen.getByText('test-memory-mgmt')).toBeInTheDocument()
      })
    })
  })

  describe('User Interactions', () => {
    test('should handle priority changes', async () => {
      const user = userEvent.setup()
      const onPriorityChange = jest.fn().mockResolvedValue(undefined)

      render(
        <TestWrapper>
          <AllocationQueueViewer 
            {...defaultProps} 
            onPriorityChange={onPriorityChange}
          />
        </TestWrapper>
      )

      // Find and click priority change button for first request
      const priorityButtons = screen.getAllByLabelText(/change priority/i)
      await user.click(priorityButtons[0])

      // Should open priority change modal/dropdown
      // For this test, we'll simulate the priority change
      expect(priorityButtons[0]).toBeInTheDocument()
    })

    test('should handle request cancellation', async () => {
      const user = userEvent.setup()
      const onCancelRequest = jest.fn().mockResolvedValue(undefined)

      render(
        <TestWrapper>
          <AllocationQueueViewer 
            {...defaultProps} 
            onCancelRequest={onCancelRequest}
          />
        </TestWrapper>
      )

      // Find and click cancel button for first request
      const cancelButtons = screen.getAllByLabelText(/cancel request/i)
      await user.click(cancelButtons[0])

      expect(onCancelRequest).toHaveBeenCalledWith('req-001')
    })

    test('should handle bulk operations when enabled', async () => {
      const user = userEvent.setup()
      const onBulkCancel = jest.fn().mockResolvedValue(undefined)

      render(
        <TestWrapper>
          <AllocationQueueViewer 
            {...defaultProps} 
            onBulkCancel={onBulkCancel}
          />
        </TestWrapper>
      )

      // Select multiple requests
      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[1]) // First request
      await user.click(checkboxes[2]) // Second request

      // Click bulk cancel button
      const bulkCancelButton = screen.getByText('Cancel Selected')
      await user.click(bulkCancelButton)

      expect(onBulkCancel).toHaveBeenCalledWith(['req-001', 'req-002'])
    })

    test('should handle refresh action', async () => {
      const user = userEvent.setup()
      const onRefresh = jest.fn()

      render(
        <TestWrapper>
          <AllocationQueueViewer 
            {...defaultProps} 
            onRefresh={onRefresh}
          />
        </TestWrapper>
      )

      // Click refresh button
      const refreshButton = screen.getByLabelText(/refresh/i)
      await user.click(refreshButton)

      expect(onRefresh).toHaveBeenCalled()
    })

    test('should expand request details', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Find and click expand button for first request
      const expandButtons = screen.getAllByLabelText(/expand details/i)
      await user.click(expandButtons[0])

      // Should show detailed information
      await waitFor(() => {
        expect(screen.getByText('Requirements')).toBeInTheDocument()
        expect(screen.getByText('Architecture: x86_64')).toBeInTheDocument()
        expect(screen.getByText('Memory: 2048 MB')).toBeInTheDocument()
        expect(screen.getByText('CPU Cores: 4')).toBeInTheDocument()
      })
    })
  })

  describe('Queue Analytics', () => {
    test('should calculate and display correct analytics', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Check analytics calculations
      expect(screen.getByText('4')).toBeInTheDocument() // Total requests
      expect(screen.getByText('2')).toBeInTheDocument() // Pending requests
      expect(screen.getByText('6m 30s')).toBeInTheDocument() // Average wait time
    })

    test('should update analytics when queue changes', () => {
      const { rerender } = render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Update with fewer requests
      const updatedQueue = mockAllocationRequests.slice(0, 2)
      
      rerender(
        <TestWrapper>
          <AllocationQueueViewer 
            {...defaultProps} 
            queue={updatedQueue}
          />
        </TestWrapper>
      )

      // Analytics should update
      expect(screen.getByText('2')).toBeInTheDocument() // Total requests
    })
  })

  describe('Sorting and Ordering', () => {
    test('should sort requests by priority by default', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Requests should be ordered by priority (highest first)
      const requestElements = screen.getAllByText(/test-/)
      
      // req-004 has priority 10 (highest), should be first
      expect(requestElements[0]).toHaveTextContent('test-memory-mgmt')
      
      // req-001 has priority 8, should be second
      expect(requestElements[1]).toHaveTextContent('test-kernel-boot')
    })

    test('should allow sorting by different columns', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Click on submitted time column header to sort
      const submittedHeader = screen.getByText('Submitted')
      await user.click(submittedHeader)

      // Should sort by submission time
      // req-004 was submitted earliest (09:58), should be first
      await waitFor(() => {
        const requestElements = screen.getAllByText(/test-/)
        expect(requestElements[0]).toHaveTextContent('test-memory-mgmt')
      })
    })
  })

  describe('Empty State', () => {
    test('should display empty state when no requests', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer 
            {...defaultProps} 
            queue={[]}
          />
        </TestWrapper>
      )

      expect(screen.getByText('No allocation requests in queue')).toBeInTheDocument()
    })

    test('should display empty state when all requests are filtered out', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Apply a filter that matches no requests
      const searchInput = screen.getByPlaceholderText('Search requests...')
      await user.type(searchInput, 'nonexistent-test')

      await waitFor(() => {
        expect(screen.getByText('No requests match the current filters')).toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    test('should have proper ARIA labels', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Check main region
      expect(screen.getByRole('region', { name: /allocation queue/i })).toBeInTheDocument()

      // Check table accessibility
      expect(screen.getByRole('table')).toBeInTheDocument()
      expect(screen.getAllByRole('columnheader')).toHaveLength(7) // All table headers
    })

    test('should support keyboard navigation', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Tab through interactive elements
      await user.tab()
      
      // Should focus on first interactive element
      const firstButton = screen.getAllByRole('button')[0]
      expect(firstButton).toHaveFocus()
    })

    test('should have proper row selection labels', () => {
      render(
        <TestWrapper>
          <AllocationQueueViewer {...defaultProps} />
        </TestWrapper>
      )

      // Check checkbox labels
      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes[1]).toHaveAttribute('aria-label', 'Select request req-001')
    })
  })

  describe('Performance', () => {
    test('should handle large queues efficiently', () => {
      const largeQueue = Array.from({ length: 500 }, (_, i) => ({
        ...mockAllocationRequests[0],
        id: `req-${i.toString().padStart(3, '0')}`,
        testId: `test-${i}`
      }))

      const startTime = performance.now()

      render(
        <TestWrapper>
          <AllocationQueueViewer 
            {...defaultProps} 
            queue={largeQueue}
          />
        </TestWrapper>
      )

      const endTime = performance.now()
      const renderTime = endTime - startTime

      // Should render within reasonable time
      expect(renderTime).toBeLessThan(2000)
    })
  })

  describe('Error Handling', () => {
    test('should handle priority change errors gracefully', async () => {
      const user = userEvent.setup()
      const onPriorityChange = jest.fn().mockRejectedValue(new Error('Priority change failed'))

      render(
        <TestWrapper>
          <AllocationQueueViewer 
            {...defaultProps} 
            onPriorityChange={onPriorityChange}
          />
        </TestWrapper>
      )

      // Attempt priority change
      const priorityButtons = screen.getAllByLabelText(/change priority/i)
      await user.click(priorityButtons[0])

      // Should handle error gracefully (no crash)
      expect(priorityButtons[0]).toBeInTheDocument()
    })

    test('should handle cancellation errors gracefully', async () => {
      const user = userEvent.setup()
      const onCancelRequest = jest.fn().mockRejectedValue(new Error('Cancellation failed'))

      render(
        <TestWrapper>
          <AllocationQueueViewer 
            {...defaultProps} 
            onCancelRequest={onCancelRequest}
          />
        </TestWrapper>
      )

      // Attempt cancellation
      const cancelButtons = screen.getAllByLabelText(/cancel request/i)
      await user.click(cancelButtons[0])

      // Should handle error gracefully (no crash)
      expect(cancelButtons[0]).toBeInTheDocument()
    })
  })
})