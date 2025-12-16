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

// Mock the AI generation hook with more realistic behavior
const mockGenerateFromDiff = jest.fn()
const mockGenerateFromFunction = jest.fn()

jest.mock('../hooks/useAIGeneration', () => ({
  __esModule: true,
  default: jest.fn(() => ({
    generateFromDiff: mockGenerateFromDiff,
    generateFromFunction: mockGenerateFromFunction,
    isGenerating: false,
  })),
}))

const initialTestCases = [
  {
    id: 'existing-test-1',
    name: 'Existing Manual Test',
    description: 'A pre-existing manual test case',
    test_type: 'unit',
    target_subsystem: 'kernel/core',
    code_paths: ['kernel/core/existing.c'],
    execution_time_estimate: 30,
    test_script: 'echo "existing test"',
    metadata: {
      generation_method: 'manual',
      execution_status: 'completed'
    },
    created_at: '2024-01-15T09:00:00Z',
    updated_at: '2024-01-15T09:00:00Z'
  }
]

const aiGeneratedTestCases = [
  {
    id: 'ai-test-1',
    name: 'AI Generated Memory Test',
    description: 'Test generated from memory allocation diff',
    test_type: 'unit',
    target_subsystem: 'kernel/mm',
    code_paths: ['kernel/mm/memory.c'],
    execution_time_estimate: 45,
    test_script: 'test_memory_allocation_boundary()',
    metadata: {
      generation_method: 'ai_diff',
      execution_status: 'never_run',
      generation_info: {
        method: 'ai_diff',
        source_data: {
          diff_content: 'diff --git a/kernel/mm/memory.c b/kernel/mm/memory.c\n+void *allocate_memory(size_t size) { return malloc(size); }',
          ai_model: 'gpt-4',
          generated_at: '2024-01-15T10:30:00Z'
        }
      }
    },
    created_at: '2024-01-15T10:30:00Z',
    updated_at: '2024-01-15T10:30:00Z'
  },
  {
    id: 'ai-test-2',
    name: 'AI Generated Scheduler Test',
    description: 'Test generated from schedule_task function',
    test_type: 'integration',
    target_subsystem: 'kernel/sched',
    code_paths: ['kernel/sched/core.c'],
    execution_time_estimate: 60,
    test_script: 'test_schedule_task_priority()',
    metadata: {
      generation_method: 'ai_function',
      execution_status: 'never_run',
      generation_info: {
        method: 'ai_function',
        source_data: {
          function_name: 'schedule_task',
          file_path: 'kernel/sched/core.c',
          subsystem: 'kernel/sched',
          ai_model: 'gpt-4',
          generated_at: '2024-01-15T11:00:00Z'
        }
      }
    },
    created_at: '2024-01-15T11:00:00Z',
    updated_at: '2024-01-15T11:00:00Z'
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

describe('Complete Workflow Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    
    // Reset mock functions
    mockGenerateFromDiff.mockReset()
    mockGenerateFromFunction.mockReset()
    
    // Default mock implementation - starts with existing tests
    mockApiService.getTests.mockResolvedValue({
      tests: initialTestCases,
      pagination: {
        page: 1,
        page_size: 20,
        total_items: initialTestCases.length,
        total_pages: 1,
        has_next: false,
        has_prev: false
      },
      filters_applied: {}
    })
  })

  describe('End-to-End AI Generation to Execution Flow', () => {
    it('completes full workflow: generate from diff → view → edit → execute', async () => {
      const user = userEvent.setup()
      
      // Mock successful AI generation
      mockApiService.generateTestsFromDiff.mockResolvedValue({
        success: true,
        message: 'Tests generated successfully',
        data: {
          generated_tests: 2,
          test_ids: ['ai-test-1', 'ai-test-2']
        }
      })

      // Mock test update
      mockApiService.updateTest.mockResolvedValue({
        ...aiGeneratedTestCases[0],
        name: 'Updated AI Memory Test',
        description: 'Updated description for memory test'
      })

      // Mock test execution
      mockApiService.executeTest.mockResolvedValue({
        execution_plan_id: 'plan-123',
        estimated_completion: '2024-01-15T12:00:00Z'
      })

      // Set up API responses for different stages
      let callCount = 0
      mockApiService.getTests.mockImplementation(() => {
        callCount++
        if (callCount === 1) {
          // Initial load - only existing tests
          return Promise.resolve({
            tests: initialTestCases,
            pagination: {
              page: 1,
              page_size: 20,
              total_items: initialTestCases.length,
              total_pages: 1,
              has_next: false,
              has_prev: false
            },
            filters_applied: {}
          })
        } else {
          // After AI generation - includes new tests
          return Promise.resolve({
            tests: [...initialTestCases, ...aiGeneratedTestCases],
            pagination: {
              page: 1,
              page_size: 20,
              total_items: initialTestCases.length + aiGeneratedTestCases.length,
              total_pages: 1,
              has_next: false,
              has_prev: false
            },
            filters_applied: {}
          })
        }
      })

      renderWithProviders(<TestCases />)

      // Step 1: Initial state - only existing tests
      await waitFor(() => {
        expect(screen.getByText('Existing Manual Test')).toBeInTheDocument()
        expect(screen.getByText('1')).toBeInTheDocument() // Total tests count
      })

      // Step 2: Generate tests from diff
      const aiGenerateButton = screen.getByRole('button', { name: /ai generate tests/i })
      await user.click(aiGenerateButton)

      await waitFor(() => {
        expect(screen.getByText('AI Test Generation')).toBeInTheDocument()
      })

      // Fill in diff content
      const diffTextarea = screen.getByPlaceholderText(/paste your git diff/i)
      await user.type(diffTextarea, 'diff --git a/kernel/mm/memory.c b/kernel/mm/memory.c\n+void *allocate_memory(size_t size) { return malloc(size); }')

      // Set test parameters
      const maxTestsInput = screen.getByDisplayValue('20')
      await user.clear(maxTestsInput)
      await user.type(maxTestsInput, '2')

      // Generate tests
      const generateButton = screen.getByRole('button', { name: /generate tests/i })
      await user.click(generateButton)

      // Verify API was called
      await waitFor(() => {
        expect(mockApiService.generateTestsFromDiff).toHaveBeenCalledWith(
          expect.stringContaining('allocate_memory'),
          2,
          ['unit']
        )
      })

      // Step 3: Simulate successful generation and refresh
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)

      // Verify new tests appear
      await waitFor(() => {
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
        expect(screen.getByText('AI Generated Scheduler Test')).toBeInTheDocument()
        expect(screen.getByText('3')).toBeInTheDocument() // Updated total count
      })

      // Step 4: View generated test details
      const memoryTestRow = screen.getByText('AI Generated Memory Test').closest('tr')
      const viewButton = within(memoryTestRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
        expect(screen.getByText('AI from Diff')).toBeInTheDocument()
        expect(screen.getByText('gpt-4')).toBeInTheDocument()
      })

      // Step 5: Edit the test case
      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)

      await waitFor(() => {
        expect(screen.getByText('Edit Test Case')).toBeInTheDocument()
      })

      const nameInput = screen.getByDisplayValue('AI Generated Memory Test')
      await user.clear(nameInput)
      await user.type(nameInput, 'Updated AI Memory Test')

      const descriptionInput = screen.getByDisplayValue('Test generated from memory allocation diff')
      await user.clear(descriptionInput)
      await user.type(descriptionInput, 'Updated description for memory test')

      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)

      // Verify update API was called
      await waitFor(() => {
        expect(mockApiService.updateTest).toHaveBeenCalledWith('ai-test-1', {
          name: 'Updated AI Memory Test',
          description: 'Updated description for memory test'
        })
      })

      // Step 6: Close modal and execute the test
      const closeButton = screen.getByRole('button', { name: /close/i }) || 
                         screen.getByLabelText(/close/i)
      await user.click(closeButton)

      await waitFor(() => {
        expect(screen.queryByText('Test Case Details')).not.toBeInTheDocument()
      })

      // Find the updated test and execute it
      const updatedTestRow = screen.getByText('Updated AI Memory Test').closest('tr') ||
                            screen.getByText('AI Generated Memory Test').closest('tr')
      const executeButton = within(updatedTestRow!).getByRole('button', { name: /execute/i })
      await user.click(executeButton)

      // Confirm execution
      await waitFor(() => {
        expect(screen.getByText(/execute.*test case/i)).toBeInTheDocument()
      })

      const confirmExecuteButton = screen.getByRole('button', { name: /yes.*execute/i })
      await user.click(confirmExecuteButton)

      // Verify execution API was called
      await waitFor(() => {
        expect(mockApiService.executeTest).toHaveBeenCalledWith('ai-test-1', expect.any(Object))
      })
    })

    it('completes full workflow: generate from function → filter → bulk execute', async () => {
      const user = userEvent.setup()
      
      // Mock successful function-based generation
      mockApiService.generateTestsFromFunction.mockResolvedValue({
        success: true,
        message: 'Function tests generated successfully',
        data: {
          generated_tests: 1,
          test_ids: ['ai-test-2']
        }
      })

      // Mock bulk execution
      mockApiService.bulkOperations.mockResolvedValue({
        success: true,
        results: [
          { test_id: 'ai-test-2', success: true }
        ],
        summary: {
          total: 1,
          successful: 1,
          failed: 0
        }
      })

      // Set up API responses
      let callCount = 0
      mockApiService.getTests.mockImplementation(() => {
        callCount++
        if (callCount === 1) {
          return Promise.resolve({
            tests: initialTestCases,
            pagination: {
              page: 1, page_size: 20, total_items: 1, total_pages: 1,
              has_next: false, has_prev: false
            },
            filters_applied: {}
          })
        } else {
          return Promise.resolve({
            tests: [...initialTestCases, aiGeneratedTestCases[1]], // Only scheduler test
            pagination: {
              page: 1, page_size: 20, total_items: 2, total_pages: 1,
              has_next: false, has_prev: false
            },
            filters_applied: {}
          })
        }
      })

      renderWithProviders(<TestCases />)

      // Step 1: Generate from function
      await waitFor(() => {
        expect(screen.getByText('Existing Manual Test')).toBeInTheDocument()
      })

      const aiGenerateButton = screen.getByRole('button', { name: /ai generate tests/i })
      await user.click(aiGenerateButton)

      await waitFor(() => {
        expect(screen.getByText('AI Test Generation')).toBeInTheDocument()
      })

      // Switch to function generation
      const functionButton = screen.getByRole('button', { name: /from function/i })
      await user.click(functionButton)

      await waitFor(() => {
        expect(screen.getByPlaceholderText(/function name/i)).toBeInTheDocument()
      })

      // Fill function details
      const functionNameInput = screen.getByPlaceholderText(/function name/i)
      await user.type(functionNameInput, 'schedule_task')

      const filePathInput = screen.getByPlaceholderText(/file path/i)
      await user.type(filePathInput, 'kernel/sched/core.c')

      const subsystemSelect = screen.getByDisplayValue('unknown')
      await user.click(subsystemSelect)
      const schedOption = screen.getByText('kernel/sched')
      await user.click(schedOption)

      const generateButton = screen.getByRole('button', { name: /generate tests/i })
      await user.click(generateButton)

      // Verify API was called
      await waitFor(() => {
        expect(mockApiService.generateTestsFromFunction).toHaveBeenCalledWith(
          'schedule_task',
          'kernel/sched/core.c',
          'kernel/sched',
          10
        )
      })

      // Step 2: Refresh to see new tests
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)

      await waitFor(() => {
        expect(screen.getByText('AI Generated Scheduler Test')).toBeInTheDocument()
        expect(screen.getByText('2')).toBeInTheDocument() // Updated total count
      })

      // Step 3: Filter by AI-generated tests
      const generationMethodFilter = screen.getByPlaceholderText('Generation Method')
      await user.click(generationMethodFilter)
      
      const aiFunctionOption = screen.getByText('AI from Function')
      await user.click(aiFunctionOption)

      // Should show only AI function generated tests
      await waitFor(() => {
        expect(screen.getByText('AI Generated Scheduler Test')).toBeInTheDocument()
        expect(screen.queryByText('Existing Manual Test')).not.toBeInTheDocument()
      })

      // Step 4: Select and bulk execute
      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[1]) // Select the scheduler test

      await waitFor(() => {
        expect(screen.getByText(/1 test case selected/i)).toBeInTheDocument()
      })

      const bulkExecuteButton = screen.getByRole('button', { name: /execute/i })
      await user.click(bulkExecuteButton)

      // Confirm bulk execution
      await waitFor(() => {
        expect(screen.getByText(/execute.*test case/i)).toBeInTheDocument()
      })

      const confirmButton = screen.getByRole('button', { name: /yes.*execute/i })
      await user.click(confirmButton)

      // Verify bulk execution API was called
      await waitFor(() => {
        expect(mockApiService.bulkOperations).toHaveBeenCalledWith({
          operation: 'execute',
          test_ids: ['ai-test-2'],
          data: expect.any(Object)
        })
      })
    })
  })

  describe('Cross-Component Data Consistency', () => {
    it('maintains data consistency across modal operations and table updates', async () => {
      const user = userEvent.setup()
      
      // Mock test update with new data
      const updatedTest = {
        ...aiGeneratedTestCases[0],
        name: 'Consistently Updated Test',
        description: 'Updated through modal',
        updated_at: '2024-01-15T13:00:00Z'
      }
      
      mockApiService.updateTest.mockResolvedValue(updatedTest)

      // Start with AI generated tests
      mockApiService.getTests.mockResolvedValue({
        tests: [...initialTestCases, ...aiGeneratedTestCases],
        pagination: {
          page: 1, page_size: 20, total_items: 3, total_pages: 1,
          has_next: false, has_prev: false
        },
        filters_applied: {}
      })

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
      })

      // Open modal and edit test
      const testRow = screen.getByText('AI Generated Memory Test').closest('tr')
      const viewButton = within(testRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
      })

      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)

      const nameInput = screen.getByDisplayValue('AI Generated Memory Test')
      await user.clear(nameInput)
      await user.type(nameInput, 'Consistently Updated Test')

      const descriptionInput = screen.getByDisplayValue('Test generated from memory allocation diff')
      await user.clear(descriptionInput)
      await user.type(descriptionInput, 'Updated through modal')

      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)

      // Verify update was called
      await waitFor(() => {
        expect(mockApiService.updateTest).toHaveBeenCalled()
      })

      // Close modal
      const closeButton = screen.getByRole('button', { name: /close/i }) || 
                         screen.getByLabelText(/close/i)
      await user.click(closeButton)

      // Mock updated API response for refresh
      mockApiService.getTests.mockResolvedValue({
        tests: [
          ...initialTestCases,
          updatedTest,
          aiGeneratedTestCases[1]
        ],
        pagination: {
          page: 1, page_size: 20, total_items: 3, total_pages: 1,
          has_next: false, has_prev: false
        },
        filters_applied: {}
      })

      // Refresh and verify consistency
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)

      await waitFor(() => {
        expect(screen.getByText('Consistently Updated Test')).toBeInTheDocument()
        expect(screen.queryByText('AI Generated Memory Test')).not.toBeInTheDocument()
      })

      // Verify the updated test shows correct data when viewed again
      const updatedTestRow = screen.getByText('Consistently Updated Test').closest('tr')
      const viewUpdatedButton = within(updatedTestRow!).getByRole('button', { name: /view/i })
      await user.click(viewUpdatedButton)

      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
        expect(screen.getByText('Consistently Updated Test')).toBeInTheDocument()
        expect(screen.getByText('Updated through modal')).toBeInTheDocument()
      })
    })

    it('maintains filter state across operations and refreshes', async () => {
      const user = userEvent.setup()
      
      // Start with mixed test types
      mockApiService.getTests.mockResolvedValue({
        tests: [...initialTestCases, ...aiGeneratedTestCases],
        pagination: {
          page: 1, page_size: 20, total_items: 3, total_pages: 1,
          has_next: false, has_prev: false
        },
        filters_applied: {}
      })

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Existing Manual Test')).toBeInTheDocument()
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
      })

      // Apply subsystem filter
      const subsystemFilter = screen.getByPlaceholderText('Subsystem')
      await user.click(subsystemFilter)
      
      const mmOption = screen.getByText('Memory Management')
      await user.click(mmOption)

      // Should show only memory management tests
      await waitFor(() => {
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
        expect(screen.queryByText('Existing Manual Test')).not.toBeInTheDocument()
        expect(screen.queryByText('AI Generated Scheduler Test')).not.toBeInTheDocument()
      })

      // Perform an operation (like refresh) and verify filter persists
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)

      await waitFor(() => {
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
        expect(screen.queryByText('Existing Manual Test')).not.toBeInTheDocument()
        expect(screen.queryByText('AI Generated Scheduler Test')).not.toBeInTheDocument()
      })

      // Verify filter is still applied in UI
      const activeFilter = screen.getByDisplayValue('Memory Management')
      expect(activeFilter).toBeInTheDocument()
    })
  })

  describe('Error Handling and Recovery Scenarios', () => {
    it('handles AI generation failure gracefully', async () => {
      const user = userEvent.setup()
      
      // Mock generation failure
      mockApiService.generateTestsFromDiff.mockRejectedValue(new Error('AI service unavailable'))

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Existing Manual Test')).toBeInTheDocument()
      })

      // Try to generate tests
      const aiGenerateButton = screen.getByRole('button', { name: /ai generate tests/i })
      await user.click(aiGenerateButton)

      const diffTextarea = screen.getByPlaceholderText(/paste your git diff/i)
      await user.type(diffTextarea, 'diff --git a/test.c b/test.c\n+int test() { return 0; }')

      const generateButton = screen.getByRole('button', { name: /generate tests/i })
      await user.click(generateButton)

      // Should handle error gracefully
      await waitFor(() => {
        expect(mockApiService.generateTestsFromDiff).toHaveBeenCalled()
      })

      // Application should still be functional
      expect(screen.getByText('Existing Manual Test')).toBeInTheDocument()
      expect(screen.getByText('1')).toBeInTheDocument() // Original count unchanged
    })

    it('recovers from network errors during bulk operations', async () => {
      const user = userEvent.setup()
      
      // Start with multiple tests
      mockApiService.getTests.mockResolvedValue({
        tests: [...initialTestCases, ...aiGeneratedTestCases],
        pagination: {
          page: 1, page_size: 20, total_items: 3, total_pages: 1,
          has_next: false, has_prev: false
        },
        filters_applied: {}
      })

      // Mock network error for bulk operation
      mockApiService.bulkOperations.mockRejectedValue(new Error('Network error'))

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
      })

      // Select tests for bulk operation
      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[1]) // First test
      await user.click(checkboxes[2]) // Second test

      await waitFor(() => {
        expect(screen.getByText(/2 test cases? selected/i)).toBeInTheDocument()
      })

      // Try bulk delete
      const deleteButton = screen.getByRole('button', { name: /delete/i })
      await user.click(deleteButton)

      await waitFor(() => {
        expect(screen.getByText(/delete.*test cases?/i)).toBeInTheDocument()
      })

      const confirmButton = screen.getByRole('button', { name: /yes.*delete/i })
      await user.click(confirmButton)

      // Should show error message
      await waitFor(() => {
        expect(screen.getByText(/bulk delete failed/i)).toBeInTheDocument()
      })

      // Tests should still be visible (operation failed)
      expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
      expect(screen.getByText('AI Generated Scheduler Test')).toBeInTheDocument()

      // User should be able to retry or perform other operations
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)

      await waitFor(() => {
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
      })
    })

    it('handles concurrent operations without data corruption', async () => {
      const user = userEvent.setup()
      
      // Mock concurrent update scenario
      let updateCallCount = 0
      mockApiService.updateTest.mockImplementation((testId, updates) => {
        updateCallCount++
        if (updateCallCount === 1) {
          // First update succeeds
          return Promise.resolve({
            ...aiGeneratedTestCases[0],
            ...updates,
            updated_at: '2024-01-15T13:00:00Z'
          })
        } else {
          // Second update fails due to conflict
          return Promise.reject(new Error('Conflict: Test was modified by another user'))
        }
      })

      mockApiService.getTests.mockResolvedValue({
        tests: [...initialTestCases, ...aiGeneratedTestCases],
        pagination: {
          page: 1, page_size: 20, total_items: 3, total_pages: 1,
          has_next: false, has_prev: false
        },
        filters_applied: {}
      })

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
      })

      // First update
      const testRow = screen.getByText('AI Generated Memory Test').closest('tr')
      const viewButton = within(testRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
      })

      const editButton = screen.getByRole('button', { name: /edit/i })
      await user.click(editButton)

      const nameInput = screen.getByDisplayValue('AI Generated Memory Test')
      await user.clear(nameInput)
      await user.type(nameInput, 'First Update')

      const saveButton = screen.getByRole('button', { name: /save/i })
      await user.click(saveButton)

      // First update should succeed
      await waitFor(() => {
        expect(mockApiService.updateTest).toHaveBeenCalledTimes(1)
      })

      // Try second update (simulating concurrent modification)
      await user.clear(nameInput)
      await user.type(nameInput, 'Second Update')
      await user.click(saveButton)

      // Should show conflict error
      await waitFor(() => {
        expect(screen.getByText(/conflict.*modified by another user/i)).toBeInTheDocument()
      })

      // Application should remain stable and functional
      expect(screen.getByText('Edit Test Case')).toBeInTheDocument()
    })

    it('maintains application state during API service interruptions', async () => {
      const user = userEvent.setup()
      
      // Start with successful API calls
      mockApiService.getTests.mockResolvedValue({
        tests: [...initialTestCases, ...aiGeneratedTestCases],
        pagination: {
          page: 1, page_size: 20, total_items: 3, total_pages: 1,
          has_next: false, has_prev: false
        },
        filters_applied: {}
      })

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
      })

      // Apply filters and selections
      const generationMethodFilter = screen.getByPlaceholderText('Generation Method')
      await user.click(generationMethodFilter)
      
      const aiDiffOption = screen.getByText('AI from Diff')
      await user.click(aiDiffOption)

      await waitFor(() => {
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
        expect(screen.queryByText('AI Generated Scheduler Test')).not.toBeInTheDocument()
      })

      // Select test case
      const checkboxes = screen.getAllByRole('checkbox')
      await user.click(checkboxes[1])

      await waitFor(() => {
        expect(screen.getByText(/1 test case selected/i)).toBeInTheDocument()
      })

      // Simulate API service interruption
      mockApiService.getTests.mockRejectedValue(new Error('Service unavailable'))

      // Try to refresh
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)

      // Application should handle the error gracefully
      // UI state should be preserved (filters, selections)
      await waitFor(() => {
        expect(screen.getByDisplayValue('AI from Diff')).toBeInTheDocument()
      })

      // When service recovers, application should work normally
      mockApiService.getTests.mockResolvedValue({
        tests: [...initialTestCases, ...aiGeneratedTestCases],
        pagination: {
          page: 1, page_size: 20, total_items: 3, total_pages: 1,
          has_next: false, has_prev: false
        },
        filters_applied: {}
      })

      await user.click(refreshButton)

      await waitFor(() => {
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
      })
    })
  })

  describe('Performance and Scalability', () => {
    it('handles large numbers of test cases efficiently', async () => {
      const user = userEvent.setup()
      
      // Generate a large number of test cases
      const largeTestSet = Array.from({ length: 100 }, (_, index) => ({
        id: `test-${index}`,
        name: `Test Case ${index}`,
        description: `Description for test case ${index}`,
        test_type: ['unit', 'integration', 'performance'][index % 3],
        target_subsystem: ['kernel/core', 'kernel/mm', 'kernel/sched'][index % 3],
        code_paths: [`kernel/test${index}.c`],
        execution_time_estimate: 30 + (index % 60),
        test_script: `test_function_${index}()`,
        metadata: {
          generation_method: ['manual', 'ai_diff', 'ai_function'][index % 3],
          execution_status: ['never_run', 'completed', 'failed'][index % 3]
        },
        created_at: new Date(2024, 0, 15, 10, index % 60).toISOString(),
        updated_at: new Date(2024, 0, 15, 10, index % 60).toISOString()
      }))

      mockApiService.getTests.mockResolvedValue({
        tests: largeTestSet,
        pagination: {
          page: 1, page_size: 20, total_items: largeTestSet.length, total_pages: 5,
          has_next: true, has_prev: false
        },
        filters_applied: {}
      })

      renderWithProviders(<TestCases />)

      // Should render without performance issues
      await waitFor(() => {
        expect(screen.getByText('Test Case 0')).toBeInTheDocument()
        expect(screen.getByText('100')).toBeInTheDocument() // Total count
      }, { timeout: 5000 })

      // Filtering should work efficiently
      const testTypeFilter = screen.getByPlaceholderText('Test Type')
      await user.click(testTypeFilter)
      
      const unitOption = screen.getByText('Unit Test')
      await user.click(unitOption)

      // Should filter quickly
      await waitFor(() => {
        expect(screen.getByText('Test Case 0')).toBeInTheDocument() // unit test
        expect(screen.queryByText('Test Case 1')).not.toBeInTheDocument() // integration test
      })

      // Search should work efficiently
      const searchInput = screen.getByPlaceholderText('Search test cases...')
      await user.type(searchInput, 'Test Case 5')

      await waitFor(() => {
        expect(screen.getByText('Test Case 5')).toBeInTheDocument()
        expect(screen.getByText('Test Case 50')).toBeInTheDocument()
        expect(screen.queryByText('Test Case 0')).not.toBeInTheDocument()
      })
    })

    it('handles rapid successive operations without conflicts', async () => {
      const user = userEvent.setup()
      
      mockApiService.getTests.mockResolvedValue({
        tests: [...initialTestCases, ...aiGeneratedTestCases],
        pagination: {
          page: 1, page_size: 20, total_items: 3, total_pages: 1,
          has_next: false, has_prev: false
        },
        filters_applied: {}
      })

      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('AI Generated Memory Test')).toBeInTheDocument()
      })

      // Perform rapid successive filter changes
      const testTypeFilter = screen.getByPlaceholderText('Test Type')
      
      // Rapid filter changes
      await user.click(testTypeFilter)
      await user.click(screen.getByText('Unit Test'))
      
      await user.click(testTypeFilter)
      await user.click(screen.getByText('Integration Test'))
      
      await user.click(testTypeFilter)
      await user.click(screen.getByText('Performance Test'))

      // Should handle rapid changes without errors
      await waitFor(() => {
        expect(screen.getByDisplayValue('Performance Test')).toBeInTheDocument()
      })

      // Rapid search changes
      const searchInput = screen.getByPlaceholderText('Search test cases...')
      await user.type(searchInput, 'Memory')
      await user.clear(searchInput)
      await user.type(searchInput, 'Scheduler')
      await user.clear(searchInput)
      await user.type(searchInput, 'AI')

      // Should handle rapid search changes
      await waitFor(() => {
        expect(searchInput).toHaveValue('AI')
      })
    })
  })
})