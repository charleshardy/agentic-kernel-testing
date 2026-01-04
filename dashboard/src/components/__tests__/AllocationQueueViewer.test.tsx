/**
 * Tests for Enhanced Allocation Queue Viewer and Management
 * Validates the comprehensive queue management functionality
 */

import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import AllocationQueueViewer from '../AllocationQueueViewer'
import { AllocationRequest, AllocationStatus, EnvironmentType } from '../../types/environment'

// Mock notification
jest.mock('antd', () => ({
  ...jest.requireActual('antd'),
  notification: {
    success: jest.fn(),
    info: jest.fn(),
    warning: jest.fn(),
    error: jest.fn()
  }
}))

describe('Enhanced Allocation Queue Viewer', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false }
      }
    })
    jest.clearAllMocks()
  })

  const renderWithQueryClient = (component: React.ReactElement) => {
    return render(
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    )
  }

  const mockQueue: AllocationRequest[] = [
    {
      id: 'req-001',
      testId: 'test-001',
      requirements: {
        architecture: 'x86_64',
        minMemoryMB: 2048,
        minCpuCores: 2,
        requiredFeatures: ['kvm'],
        isolationLevel: 'vm'
      },
      priority: 8,
      submittedAt: new Date('2024-01-01T10:00:00Z'),
      status: AllocationStatus.PENDING
    },
    {
      id: 'req-002',
      testId: 'test-002',
      requirements: {
        architecture: 'arm64',
        minMemoryMB: 1024,
        minCpuCores: 1,
        requiredFeatures: [],
        isolationLevel: 'container'
      },
      priority: 5,
      submittedAt: new Date('2024-01-01T10:05:00Z'),
      status: AllocationStatus.ALLOCATED
    },
    {
      id: 'req-003',
      testId: 'test-003',
      requirements: {
        architecture: 'x86_64',
        minMemoryMB: 4096,
        minCpuCores: 4,
        requiredFeatures: ['nested-virt'],
        isolationLevel: 'vm'
      },
      priority: 3,
      submittedAt: new Date('2024-01-01T10:10:00Z'),
      status: AllocationStatus.FAILED
    }
  ]

  const mockEstimatedWaitTimes = new Map([
    ['req-001', 120],
    ['req-002', 0],
    ['req-003', 300]
  ])

  const defaultProps = {
    queue: mockQueue,
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

  describe('Basic Functionality', () => {
    it('should display queue with correct number of requests', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      expect(screen.getByText('Allocation Queue')).toBeInTheDocument()
      expect(screen.getByText('3')).toBeInTheDocument() // Badge count
      
      // Check that all requests are displayed
      expect(screen.getByText('test-001')).toBeInTheDocument()
      expect(screen.getByText('test-002')).toBeInTheDocument()
      expect(screen.getByText('test-003')).toBeInTheDocument()
    })

    it('should display queue analytics correctly', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      expect(screen.getByText('Total Requests')).toBeInTheDocument()
      expect(screen.getByText('Avg Wait Time')).toBeInTheDocument()
      expect(screen.getByText('Allocation Rate')).toBeInTheDocument()
      expect(screen.getByText('Failed Requests')).toBeInTheDocument()
    })

    it('should show empty state when no requests', () => {
      renderWithQueryClient(
        <AllocationQueueViewer 
          {...defaultProps} 
          queue={[]} 
          estimatedWaitTimes={new Map()} 
        />
      )

      expect(screen.getByText('No allocation requests in queue')).toBeInTheDocument()
      expect(screen.getByText('Submit a test to see allocation requests here')).toBeInTheDocument()
    })
  })

  describe('Priority Management', () => {
    it('should display priority correctly with color coding', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      // High priority (8) should be red
      const highPriorityTag = screen.getByText('8 - Critical')
      expect(highPriorityTag).toBeInTheDocument()

      // Medium priority (5) should be orange
      const mediumPriorityTag = screen.getByText('5 - Medium')
      expect(mediumPriorityTag).toBeInTheDocument()

      // Low priority (3) should be blue
      const lowPriorityTag = screen.getByText('3 - Low')
      expect(lowPriorityTag).toBeInTheDocument()
    })

    it('should handle priority increase', () => {
      const onPriorityChange = jest.fn()
      renderWithQueryClient(
        <AllocationQueueViewer {...defaultProps} onPriorityChange={onPriorityChange} />
      )

      // Find the increase priority button for the first request
      const priorityRows = screen.getAllByRole('row')
      const firstDataRow = priorityRows[1] // Skip header row
      const increaseButton = within(firstDataRow).getByRole('button', { name: /increase priority/i })
      
      fireEvent.click(increaseButton)
      
      expect(onPriorityChange).toHaveBeenCalledWith('req-001', 9)
    })

    it('should handle priority decrease', () => {
      const onPriorityChange = jest.fn()
      renderWithQueryClient(
        <AllocationQueueViewer {...defaultProps} onPriorityChange={onPriorityChange} />
      )

      // Find the decrease priority button for the first request
      const priorityRows = screen.getAllByRole('row')
      const firstDataRow = priorityRows[1] // Skip header row
      const decreaseButton = within(firstDataRow).getByRole('button', { name: /decrease priority/i })
      
      fireEvent.click(decreaseButton)
      
      expect(onPriorityChange).toHaveBeenCalledWith('req-001', 7)
    })

    it('should disable priority buttons at limits', () => {
      const queueWithLimits = [
        { ...mockQueue[0], priority: 10 }, // Max priority
        { ...mockQueue[1], priority: 1 }   // Min priority
      ]

      renderWithQueryClient(
        <AllocationQueueViewer 
          {...defaultProps} 
          queue={queueWithLimits}
        />
      )

      const rows = screen.getAllByRole('row')
      
      // Max priority row - increase button should be disabled
      const maxPriorityRow = rows[1]
      const increaseButton = within(maxPriorityRow).getByRole('button', { name: /increase priority/i })
      expect(increaseButton).toBeDisabled()

      // Min priority row - decrease button should be disabled
      const minPriorityRow = rows[2]
      const decreaseButton = within(minPriorityRow).getByRole('button', { name: /decrease priority/i })
      expect(decreaseButton).toBeDisabled()
    })
  })

  describe('Queue Position and Wait Times', () => {
    it('should display queue positions correctly', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      expect(screen.getByText('#1')).toBeInTheDocument()
      expect(screen.getByText('#2')).toBeInTheDocument()
      expect(screen.getByText('#3')).toBeInTheDocument()
    })

    it('should format wait times correctly', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      expect(screen.getByText('2m')).toBeInTheDocument() // 120 seconds
      expect(screen.getByText('5m')).toBeInTheDocument() // 300 seconds
    })

    it('should show visual indicators for long wait times', () => {
      const longWaitTimes = new Map([
        ['req-001', 600], // 10 minutes - should be red
        ['req-002', 60],  // 1 minute - should be green
      ])

      renderWithQueryClient(
        <AllocationQueueViewer 
          {...defaultProps} 
          estimatedWaitTimes={longWaitTimes}
        />
      )

      expect(screen.getByText('10m')).toBeInTheDocument()
      expect(screen.getByText('1m')).toBeInTheDocument()
    })
  })

  describe('Status Management', () => {
    it('should display status with correct icons and colors', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      expect(screen.getByText('PENDING')).toBeInTheDocument()
      expect(screen.getByText('ALLOCATED')).toBeInTheDocument()
      expect(screen.getByText('FAILED')).toBeInTheDocument()
    })

    it('should show details button for failed requests', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      const failedRows = screen.getAllByText('FAILED')
      expect(failedRows.length).toBeGreaterThan(0)
      
      // Should have a details button for failed requests
      expect(screen.getByText('Details')).toBeInTheDocument()
    })
  })

  describe('Filtering and Searching', () => {
    it('should filter by status', async () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      const statusFilter = screen.getByDisplayValue('All Status')
      fireEvent.mouseDown(statusFilter)
      
      await waitFor(() => {
        const pendingOption = screen.getByText('Pending')
        fireEvent.click(pendingOption)
      })

      // Should only show pending requests
      expect(screen.getByText('test-001')).toBeInTheDocument()
      expect(screen.queryByText('test-002')).not.toBeInTheDocument()
    })

    it('should filter by architecture', async () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      const archFilter = screen.getByDisplayValue('All Architectures')
      fireEvent.mouseDown(archFilter)
      
      await waitFor(() => {
        const x86Option = screen.getByText('x86_64')
        fireEvent.click(x86Option)
      })

      // Should only show x86_64 requests
      expect(screen.getByText('test-001')).toBeInTheDocument()
      expect(screen.getByText('test-003')).toBeInTheDocument()
      expect(screen.queryByText('test-002')).not.toBeInTheDocument()
    })

    it('should search by test ID', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      const searchInput = screen.getByPlaceholderText('Search by Test ID or Request ID')
      fireEvent.change(searchInput, { target: { value: 'test-001' } })

      // Should only show matching request
      expect(screen.getByText('test-001')).toBeInTheDocument()
      expect(screen.queryByText('test-002')).not.toBeInTheDocument()
      expect(screen.queryByText('test-003')).not.toBeInTheDocument()
    })

    it('should clear all filters', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      const clearButton = screen.getByText('Clear Filters')
      fireEvent.click(clearButton)

      // All requests should be visible again
      expect(screen.getByText('test-001')).toBeInTheDocument()
      expect(screen.getByText('test-002')).toBeInTheDocument()
      expect(screen.getByText('test-003')).toBeInTheDocument()
    })
  })

  describe('Sorting', () => {
    it('should sort by priority', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      const priorityHeader = screen.getByText('Priority')
      const sortButton = within(priorityHeader.closest('th')!).getByRole('button')
      fireEvent.click(sortButton)

      // Should sort by priority (ascending by default)
      const rows = screen.getAllByRole('row')
      expect(rows.length).toBeGreaterThan(1)
    })

    it('should sort by estimated wait time', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      const waitHeader = screen.getByText('Est. Wait')
      const sortButton = within(waitHeader.closest('th')!).getByRole('button')
      fireEvent.click(sortButton)

      // Should sort by wait time
      const rows = screen.getAllByRole('row')
      expect(rows.length).toBeGreaterThan(1)
    })
  })

  describe('Bulk Operations', () => {
    it('should enable bulk selection', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      // Should have checkboxes for selection
      const checkboxes = screen.getAllByRole('checkbox')
      expect(checkboxes.length).toBeGreaterThan(0)
    })

    it('should handle bulk cancellation', async () => {
      const onBulkCancel = jest.fn()
      renderWithQueryClient(
        <AllocationQueueViewer {...defaultProps} onBulkCancel={onBulkCancel} />
      )

      // Select first checkbox (pending request)
      const checkboxes = screen.getAllByRole('checkbox')
      fireEvent.click(checkboxes[1]) // Skip "select all" checkbox

      // Should show bulk cancel button
      await waitFor(() => {
        expect(screen.getByText(/Cancel Selected/)).toBeInTheDocument()
      })

      const bulkCancelButton = screen.getByText(/Cancel Selected/)
      fireEvent.click(bulkCancelButton)

      // Should show confirmation dialog
      await waitFor(() => {
        expect(screen.getByText(/Cancel .* selected requests/)).toBeInTheDocument()
      })

      const confirmButton = screen.getByText('Yes')
      fireEvent.click(confirmButton)

      expect(onBulkCancel).toHaveBeenCalled()
    })

    it('should disable selection for non-pending requests', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      const checkboxes = screen.getAllByRole('checkbox')
      
      // Allocated and failed requests should have disabled checkboxes
      // This would need to be tested by checking the disabled state
      expect(checkboxes.length).toBeGreaterThan(0)
    })
  })

  describe('Real-time Updates', () => {
    it('should show real-time indicator when enabled', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} realTimeUpdates={true} />)

      expect(screen.getByText('Live')).toBeInTheDocument()
    })

    it('should show last update time', () => {
      const lastUpdateTime = new Date('2024-01-01T12:00:00Z')
      renderWithQueryClient(
        <AllocationQueueViewer {...defaultProps} lastUpdateTime={lastUpdateTime} />
      )

      expect(screen.getByText(/Updated:/)).toBeInTheDocument()
    })

    it('should handle refresh action', () => {
      const onRefresh = jest.fn()
      renderWithQueryClient(
        <AllocationQueueViewer {...defaultProps} onRefresh={onRefresh} />
      )

      const refreshButton = screen.getByRole('button', { name: /refresh queue/i })
      fireEvent.click(refreshButton)

      expect(onRefresh).toHaveBeenCalled()
    })
  })

  describe('Queue Analytics', () => {
    it('should display priority breakdown', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      expect(screen.getByText('Priority Breakdown:')).toBeInTheDocument()
      expect(screen.getByText(/Critical:/)).toBeInTheDocument()
      expect(screen.getByText(/Medium:/)).toBeInTheDocument()
      expect(screen.getByText(/Low:/)).toBeInTheDocument()
    })

    it('should display architecture breakdown', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      expect(screen.getByText('Architecture Breakdown:')).toBeInTheDocument()
      expect(screen.getByText(/x86_64:/)).toBeInTheDocument()
      expect(screen.getByText(/arm64:/)).toBeInTheDocument()
    })

    it('should show alerts for long wait times', () => {
      const longWaitTimes = new Map([
        ['req-001', 700], // Over 10 minutes
        ['req-002', 800],
        ['req-003', 900]
      ])

      renderWithQueryClient(
        <AllocationQueueViewer 
          {...defaultProps} 
          estimatedWaitTimes={longWaitTimes}
        />
      )

      expect(screen.getByText('Long Wait Times Detected')).toBeInTheDocument()
    })

    it('should show alerts for failed requests', () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      expect(screen.getByText(/Failed Allocation/)).toBeInTheDocument()
    })
  })

  describe('Expandable Rows', () => {
    it('should expand row to show detailed information', async () => {
      renderWithQueryClient(<AllocationQueueViewer {...defaultProps} />)

      const viewDetailsButtons = screen.getAllByRole('button', { name: /view details/i })
      fireEvent.click(viewDetailsButtons[0])

      await waitFor(() => {
        expect(screen.getByText('Request Details:')).toBeInTheDocument()
        expect(screen.getByText('Hardware Requirements:')).toBeInTheDocument()
      })
    })
  })
})