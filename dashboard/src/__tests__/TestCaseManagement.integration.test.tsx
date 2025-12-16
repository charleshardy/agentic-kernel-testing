import React from 'react'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import TestCases from '../pages/TestCases'
import apiService from '../services/api'

// Mock the API service
jest.mock('../services/api')
const mockApiService = apiService as jest.Mocked<typeof apiService>

// Mock the AI generation hook
jest.mock('../hooks/useAIGeneration', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    generateFromDiff: jest.fn(),
    generateFromFunction: jest.fn(),
    isGenerating: false,
  })),
}))

const mockTestCases = [
  {
    id: 'test-1',
    name: 'Editable Test Case',
    description: 'A test case that can be edited',
    test_type: 'unit',
    target_subsystem: 'kernel/core',
    code_paths: ['kernel/core/test.c'],
    execution_time_estimate: 30,
    test_script: 'echo "original test"',
    metadata: {
      generation_method: 'manual',
      execution_status: 'never_run'
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 'test-2',
    name: 'Deletable Test Case',
    description: 'A test case that can be deleted',
    test_type: 'integration',
    target_subsystem: 'kernel/mm',
    code_paths: ['kernel/mm/memory.c'],
    execution_time_estimate: 45,
    test_script: 'test_memory_allocation()',
    metadata: {
      generation_method: 'ai_diff',
      execution_status: 'completed'
    },
    created_at: '2024-01-15T11:00:00Z',
    updated_at: '2024-01-15T11:00:00Z'
  },
  {
    id: 'test-3',
    name: 'Executable Test Case',
    description: 'A test case that can be executed',
    test_type: 'performance',
    target_subsystem: 'kernel/sched',
    code_paths: ['kernel/sched/core.c'],
    execution_time_estimate: 60,
    test_script: 'test_schedule_performance()',
    metadata: {
      generation_method: 'ai_function',
      execution_status: 'failed'
    },
    created_at: '2024-01-15T12:00:00Z',
    updated_at: '2024-01-15T12:00:00Z'
  },
  {
    id: 'test-4',
    name: 'Running Test Case',
    description: 'A test case that is currently running',
    test_type: 'security',
    target_subsystem: 'kernel/net',
    code_paths: ['kernel/net/core.c'],
    execution_time_estimate: 90,
    test_script: 'test_network_security()',
    metadata: {
      generation_method: 'manual',
      execution_status: 'running'
    },
    created_at: '2024-01-15T13:00:00Z',
    updated_at: '2024-01-15T13:00:00Z'
  }
]

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
      },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('Test Case Management Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Default mock implementation
    mockApiService.getTests.mockResolvedValue({
      tests: mockTestCases,
      pagination: {
        page: 1,
        page_size: 20,
        total_items: mockTestCases.length,
        total_pages: 1,
        has_next: false,
        has_prev: false
      },
      filters_applied: {}
    })
  })

  describe('Test Case Viewing', () => {
    it('opens test case detail modal when view button is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
      })

      // Find the row with the test case and click view button
      const testRow = screen.getByText('Editable Test Case').closest('tr')
      expect(testRow).toBeInTheDocument()
      
      const viewButton = within(testRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      // Check modal opens with correct content
      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
        expect(screen.getByText('A test case that can be edited')).toBeInTheDocument()
        expect(screen.getByText('echo "original test"')).toBeInTheDocument()
      })
    })

    it('displays all test case information in detail modal', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
      })

      const testRow = screen.getByText('Editable Test Case').closest('tr')
      const viewButton = within(testRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
      })

      // Check all test case fields are displayed
      expect(screen.getByText('unit')).toBeInTheDocument() // test_type
      expect(screen.getByText('kernel/core')).toBeInTheDocument() // target_subsystem
      expect(screen.getByText('30')).toBeInTheDocument() // execution_time_estimate
      expect(screen.getByText('Manual')).toBeInTheDocument() // generation_method
      expect(screen.getByText('Never Run')).toBeInTheDocument() // execution_status
    })
  })

  describe('Test Case Editing', () => {
    it('switches to edit mode when edit button is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
      })

      // Open test case modal
      const testRow = screen.getByText('Editable Test Case').closest('tr')
      const viewButton = within(testRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
      })

      // Click edit button
      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)

      // Check modal switches to edit mode
      await waitFor(() => {
        expect(screen.getByText('Edit Test Case')).toBeInTheDocument()
        expect(screen.getByDisplayValue('Editable Test Case')).toBeInTheDocument()
        expect(screen.getByDisplayValue('A test case that can be edited')).toBeInTheDocument()
      })
    })

    it('saves test case changes when save button is clicked', async () => {
      const user = userEvent.setup()
      
      // Mock successful update
      mockApiService.updateTest.mockResolvedValue({
        ...mockTestCases[0],
        name: 'Updated Test Case',
        description: 'Updated description',
        updated_at: new Date().toISOString()
      })

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
      })

      // Open and switch to edit mode
      const testRow = screen.getByText('Editable Test Case').closest('tr')
      const viewButton = within(testRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
      })

      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Edit Test Case')).toBeInTheDocument()
      })

      // Edit the test case
      const nameInput = screen.getByDisplayValue('Editable Test Case')
      await user.clear(nameInput)
      await user.type(nameInput, 'Updated Test Case')

      const descriptionInput = screen.getByDisplayValue('A test case that can be edited')
      await user.clear(descriptionInput)
      await user.type(descriptionInput, 'Updated description')

      // Save changes
      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)

      // Verify API was called with correct data
      await waitFor(() => {
        expect(mockApiService.updateTest).toHaveBeenCalledWith('test-1', {
          name: 'Updated Test Case',
          description: 'Updated description',
          // Other fields should be preserved
        })
      })
    })

    it('validates required fields during editing', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
      })

      // Open and switch to edit mode
      const testRow = screen.getByText('Editable Test Case').closest('tr')
      const viewButton = within(testRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
      })

      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Edit Test Case')).toBeInTheDocument()
      })

      // Clear required field
      const nameInput = screen.getByDisplayValue('Editable Test Case')
      await user.clear(nameInput)

      // Try to save
      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/name is required/i)).toBeInTheDocument()
      })

      // API should not be called
      expect(mockApiService.updateTest).not.toHaveBeenCalled()
    })
  })

  describe('Test Case Deletion', () => {
    it('shows confirmation dialog when delete button is clicked', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Deletable Test Case')).toBeInTheDocument()
      })

      // Find the row with the deletable test case and click delete button
      const testRow = screen.getByText('Deletable Test Case').closest('tr')
      expect(testRow).toBeInTheDocument()
      
      const deleteButton = within(testRow!).getByRole('button', { name: /delete/i })
      await user.click(deleteButton)

      // Check confirmation dialog appears
      await waitFor(() => {
        expect(screen.getByText(/are you sure you want to delete/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /yes.*delete/i })).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument()
      })
    })

    it('deletes test case when confirmed', async () => {
      const user = userEvent.setup()
      
      // Mock successful deletion
      mockApiService.deleteTest.mockResolvedValue({
        success: true,
        message: 'Test case deleted successfully'
      })

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Deletable Test Case')).toBeInTheDocument()
      })

      // Click delete button
      const testRow = screen.getByText('Deletable Test Case').closest('tr')
      const deleteButton = within(testRow!).getByRole('button', { name: /delete/i })
      await user.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByText(/are you sure you want to delete/i)).toBeInTheDocument()
      })

      // Confirm deletion
      const confirmButton = screen.getByRole('button', { name: /yes.*delete/i })
      await user.click(confirmButton)

      // Verify API was called
      await waitFor(() => {
        expect(mockApiService.deleteTest).toHaveBeenCalledWith('test-2')
      })
    })

    it('prevents deletion of running tests', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Running Test Case')).toBeInTheDocument()
      })

      // Find the row with the running test case
      const testRow = screen.getByText('Running Test Case').closest('tr')
      expect(testRow).toBeInTheDocument()
      
      // Delete button should be disabled for running tests
      const deleteButton = within(testRow!).getByRole('button', { name: /delete/i })
      expect(deleteButton).toBeDisabled()
    })
  })

  describe('Test Case Execution', () => {
    it('executes single test case when execute button is clicked', async () => {
      const user = userEvent.setup()
      
      // Mock successful execution
      mockApiService.executeTest.mockResolvedValue({
        execution_plan_id: 'plan-123',
        estimated_completion: '2024-01-15T14:00:00Z'
      })

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Executable Test Case')).toBeInTheDocument()
      })

      // Find the row with the executable test case and click execute button
      const testRow = screen.getByText('Executable Test Case').closest('tr')
      expect(testRow).toBeInTheDocument()
      
      const executeButton = within(testRow!).getByRole('button', { name: /execute/i })
      await user.click(executeButton)

      // Verify API was called
      await waitFor(() => {
        expect(mockApiService.executeTest).toHaveBeenCalledWith('test-3', expect.any(Object))
      })
    })

    it('shows execution confirmation for single test', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Executable Test Case')).toBeInTheDocument()
      })

      const testRow = screen.getByText('Executable Test Case').closest('tr')
      const executeButton = within(testRow!).getByRole('button', { name: /execute/i })
      await user.click(executeButton)

      // Should show confirmation dialog
      await waitFor(() => {
        expect(screen.getByText(/execute.*test case/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /yes.*execute/i })).toBeInTheDocument()
      })
    })
  })

  describe('Bulk Operations', () => {
    it('enables bulk actions when tests are selected', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
      })

      // Select multiple test cases
      const checkboxes = screen.getAllByRole('checkbox')
      // Skip the header checkbox (index 0) and select first two test cases
      await user.click(checkboxes[1]) // First test case
      await user.click(checkboxes[2]) // Second test case

      // Bulk action buttons should be enabled
      await waitFor(() => {
        expect(screen.getByText(/2 test cases? selected/i)).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /execute/i })).toBeEnabled()
        expect(screen.getByRole('button', { name: /export/i })).toBeEnabled()
        expect(screen.getByRole('button', { name: /delete/i })).toBeEnabled()
      })
    })

    it('performs bulk execution when confirmed', async () => {
      const user = userEvent.setup()
      
      // Mock successful bulk operation
      mockApiService.bulkOperations.mockResolvedValue({
        success: true,
        results: [
          { test_id: 'test-1', success: true },
          { test_id: 'test-2', success: true }
        ],
        summary: {
          total: 2,
          successful: 2,
          failed: 0
        }
      })

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
      })

      // Select test cases
      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[1])
      await user.click(checkboxes[2])

      await waitFor(() => {
        expect(screen.getByText(/2 test cases? selected/i)).toBeInTheDocument()
      })

      // Click bulk execute
      const executeButton = screen.getByRole('button', { name: /execute/i })
      await user.click(executeButton)

      // Confirm execution
      await waitFor(() => {
        expect(screen.getByText(/execute.*test cases?/i)).toBeInTheDocument()
      })

      const confirmButton = screen.getByRole('button', { name: /yes.*execute/i })
      await user.click(confirmButton)

      // Verify API was called
      await waitFor(() => {
        expect(mockApiService.bulkOperations).toHaveBeenCalledWith({
          operation: 'execute',
          test_ids: ['test-1', 'test-2'],
          data: expect.any(Object)
        })
      })
    })

    it('performs bulk deletion when confirmed', async () => {
      const user = userEvent.setup()
      
      // Mock successful bulk deletion
      mockApiService.bulkOperations.mockResolvedValue({
        success: true,
        results: [
          { test_id: 'test-1', success: true },
          { test_id: 'test-2', success: true }
        ],
        summary: {
          total: 2,
          successful: 2,
          failed: 0
        }
      })

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
      })

      // Select test cases (excluding running test)
      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[1]) // Editable Test Case
      await user.click(checkboxes[2]) // Deletable Test Case

      await waitFor(() => {
        expect(screen.getByText(/2 test cases? selected/i)).toBeInTheDocument()
      })

      // Click bulk delete
      const deleteButton = screen.getByRole('button', { name: /delete/i })
      await user.click(deleteButton)

      // Confirm deletion
      await waitFor(() => {
        expect(screen.getByText(/delete.*test cases?/i)).toBeInTheDocument()
      })

      const confirmButton = screen.getByRole('button', { name: /yes.*delete/i })
      await user.click(confirmButton)

      // Verify API was called
      await waitFor(() => {
        expect(mockApiService.bulkOperations).toHaveBeenCalledWith({
          operation: 'delete',
          test_ids: ['test-1', 'test-2']
        })
      })
    })

    it('exports selected test cases', async () => {
      const user = userEvent.setup()
      
      // Mock URL.createObjectURL and related functions
      global.URL.createObjectURL = jest.fn(() => 'mock-url')
      global.URL.revokeObjectURL = jest.fn()
      
      // Mock document.createElement and related DOM methods
      const mockLink = {
        href: '',
        download: '',
        click: jest.fn(),
      }
      jest.spyOn(document, 'createElement').mockReturnValue(mockLink as any)
      jest.spyOn(document.body, 'appendChild').mockImplementation(() => mockLink as any)
      jest.spyOn(document.body, 'removeChild').mockImplementation(() => mockLink as any)

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
      })

      // Select test cases
      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[1])
      await user.click(checkboxes[2])

      await waitFor(() => {
        expect(screen.getByText(/2 test cases? selected/i)).toBeInTheDocument()
      })

      // Click export
      const exportButton = screen.getByRole('button', { name: /export/i })
      await user.click(exportButton)

      // Confirm export
      await waitFor(() => {
        expect(screen.getByText(/export.*test cases?/i)).toBeInTheDocument()
      })

      const confirmButton = screen.getByRole('button', { name: /yes.*export/i })
      await user.click(confirmButton)

      // Verify download was triggered
      await waitFor(() => {
        expect(mockLink.click).toHaveBeenCalled()
        expect(mockLink.download).toContain('test-cases-export')
      })
    })

    it('excludes running tests from bulk selection', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Running Test Case')).toBeInTheDocument()
      })

      // Try to select all tests
      const selectAllButton = screen.getByRole('button', { name: /all/i })
      await user.click(selectAllButton)

      // Should select only non-running tests
      await waitFor(() => {
        expect(screen.getByText(/3 test cases? selected/i)).toBeInTheDocument() // 4 total - 1 running = 3
      })

      // Running test should not be selected
      const runningTestRow = screen.getByText('Running Test Case').closest('tr')
      const runningTestCheckbox = within(runningTestRow!).getByRole('checkbox')
      expect(runningTestCheckbox).not.toBeChecked()
    })
  })

  describe('Error Handling', () => {
    it('handles test case update errors gracefully', async () => {
      const user = userEvent.setup()
      
      // Mock API error
      mockApiService.updateTest.mockRejectedValue(new Error('Update failed'))

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
      })

      // Open and edit test case
      const testRow = screen.getByText('Editable Test Case').closest('tr')
      const viewButton = within(testRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
      })

      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Edit Test Case')).toBeInTheDocument()
      })

      const nameInput = screen.getByDisplayValue('Editable Test Case')
      await user.clear(nameInput)
      await user.type(nameInput, 'Updated Name')

      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/failed to update test case/i)).toBeInTheDocument()
      })
    })

    it('handles test case deletion errors gracefully', async () => {
      const user = userEvent.setup()
      
      // Mock API error
      mockApiService.deleteTest.mockRejectedValue(new Error('Delete failed'))

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Deletable Test Case')).toBeInTheDocument()
      })

      // Try to delete test case
      const testRow = screen.getByText('Deletable Test Case').closest('tr')
      const deleteButton = within(testRow!).getByRole('button', { name: /delete/i })
      await user.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByText(/are you sure you want to delete/i)).toBeInTheDocument()
      })

      const confirmButton = screen.getByRole('button', { name: /yes.*delete/i })
      await user.click(confirmButton)

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/failed to delete test case/i)).toBeInTheDocument()
      })
    })

    it('handles bulk operation errors gracefully', async () => {
      const user = userEvent.setup()
      
      // Mock partial failure
      mockApiService.bulkOperations.mockResolvedValue({
        success: false,
        results: [
          { test_id: 'test-1', success: true },
          { test_id: 'test-2', success: false, error: 'Execution failed' }
        ],
        summary: {
          total: 2,
          successful: 1,
          failed: 1
        }
      })

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Editable Test Case')).toBeInTheDocument()
      })

      // Select and execute test cases
      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[1])
      await user.click(checkboxes[2])

      const executeButton = screen.getByRole('button', { name: /execute/i })
      await user.click(executeButton)

      await waitFor(() => {
        expect(screen.getByText(/execute.*test cases?/i)).toBeInTheDocument()
      })

      const confirmButton = screen.getByRole('button', { name: /yes.*execute/i })
      await user.click(confirmButton)

      // Should show partial success message
      await waitFor(() => {
        expect(screen.getByText(/1\/2 operations completed successfully/i)).toBeInTheDocument()
        expect(screen.getByText(/1\/2 operations failed/i)).toBeInTheDocument()
      })
    })
  })
})