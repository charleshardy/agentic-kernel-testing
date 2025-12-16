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
    name: 'Manual Test Case',
    description: 'A manually created test case',
    test_type: 'unit',
    target_subsystem: 'kernel/core',
    code_paths: ['kernel/core/test.c'],
    execution_time_estimate: 30,
    test_script: 'echo "manual test"',
    metadata: {
      generation_method: 'manual',
      execution_status: 'never_run'
    },
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z'
  },
  {
    id: 'test-2',
    name: 'AI Generated from Diff',
    description: 'Test generated from code diff analysis',
    test_type: 'unit',
    target_subsystem: 'kernel/mm',
    code_paths: ['kernel/mm/memory.c'],
    execution_time_estimate: 45,
    test_script: 'test_memory_allocation()',
    metadata: {
      generation_method: 'ai_diff',
      execution_status: 'completed',
      generation_info: {
        method: 'ai_diff',
        source_data: {
          diff_content: 'diff --git a/kernel/mm/memory.c b/kernel/mm/memory.c\n+void test_function() {}',
          ai_model: 'gpt-4',
          generated_at: '2024-01-15T11:00:00Z'
        }
      }
    },
    created_at: '2024-01-15T11:00:00Z',
    updated_at: '2024-01-15T11:00:00Z'
  },
  {
    id: 'test-3',
    name: 'AI Generated from Function',
    description: 'Test generated from function analysis',
    test_type: 'integration',
    target_subsystem: 'kernel/sched',
    code_paths: ['kernel/sched/core.c'],
    execution_time_estimate: 60,
    test_script: 'test_schedule_task()',
    metadata: {
      generation_method: 'ai_function',
      execution_status: 'failed',
      generation_info: {
        method: 'ai_function',
        source_data: {
          function_name: 'schedule_task',
          file_path: 'kernel/sched/core.c',
          subsystem: 'kernel/sched',
          ai_model: 'gpt-4',
          generated_at: '2024-01-15T12:00:00Z'
        }
      }
    },
    created_at: '2024-01-15T12:00:00Z',
    updated_at: '2024-01-15T12:00:00Z'
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

describe('AI Generation Workflow Integration Tests', () => {
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

  describe('Test List Display and Filtering', () => {
    it('displays all test cases with correct metadata', async () => {
      renderWithProviders(<TestCases />)

      // Wait for test cases to load
      await waitFor(() => {
        expect(screen.getByText('Manual Test Case')).toBeInTheDocument()
        expect(screen.getByText('AI Generated from Diff')).toBeInTheDocument()
        expect(screen.getByText('AI Generated from Function')).toBeInTheDocument()
      })

      // Verify statistics are calculated correctly
      expect(screen.getByText('3')).toBeInTheDocument() // Total tests
      expect(screen.getByText('2')).toBeInTheDocument() // AI Generated tests
      expect(screen.getByText('1')).toBeInTheDocument() // Manual tests
    })

    it('filters tests by generation method', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Manual Test Case')).toBeInTheDocument()
      })

      // Filter by AI from Diff
      const generationMethodFilter = screen.getByDisplayValue('Generation Method') || 
                                   screen.getByPlaceholderText('Generation Method')
      await user.click(generationMethodFilter)
      
      const aiDiffOption = screen.getByText('AI from Diff')
      await user.click(aiDiffOption)

      // Should show only AI diff generated tests
      await waitFor(() => {
        expect(screen.getByText('AI Generated from Diff')).toBeInTheDocument()
        expect(screen.queryByText('Manual Test Case')).not.toBeInTheDocument()
        expect(screen.queryByText('AI Generated from Function')).not.toBeInTheDocument()
      })
    })

    it('filters tests by subsystem', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Manual Test Case')).toBeInTheDocument()
      })

      // Filter by kernel/mm subsystem
      const subsystemFilter = screen.getByPlaceholderText('Subsystem')
      await user.click(subsystemFilter)
      
      const mmOption = screen.getByText('Memory Management')
      await user.click(mmOption)

      // Should show only memory management tests
      await waitFor(() => {
        expect(screen.getByText('AI Generated from Diff')).toBeInTheDocument()
        expect(screen.queryByText('Manual Test Case')).not.toBeInTheDocument()
        expect(screen.queryByText('AI Generated from Function')).not.toBeInTheDocument()
      })
    })

    it('searches tests by name and description', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Manual Test Case')).toBeInTheDocument()
      })

      // Search for "diff"
      const searchInput = screen.getByPlaceholderText('Search test cases...')
      await user.type(searchInput, 'diff')

      // Should show only tests containing "diff"
      await waitFor(() => {
        expect(screen.getByText('AI Generated from Diff')).toBeInTheDocument()
        expect(screen.queryByText('Manual Test Case')).not.toBeInTheDocument()
        expect(screen.queryByText('AI Generated from Function')).not.toBeInTheDocument()
      })
    })
  })

  describe('Test Case Detail Modal', () => {
    it('displays generation source information for AI diff tests', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('AI Generated from Diff')).toBeInTheDocument()
      })

      // Find the row with AI Generated from Diff test and click view button
      const testRow = screen.getByText('AI Generated from Diff').closest('tr')
      expect(testRow).toBeInTheDocument()
      
      const viewButton = within(testRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      // Check modal opens and shows generation info
      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
        expect(screen.getByText('AI from Diff')).toBeInTheDocument()
        expect(screen.getByText('gpt-4')).toBeInTheDocument()
      })
    })

    it('displays generation source information for AI function tests', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('AI Generated from Function')).toBeInTheDocument()
      })

      // Find the row with AI Generated from Function test and click view button
      const testRow = screen.getByText('AI Generated from Function').closest('tr')
      expect(testRow).toBeInTheDocument()
      
      const viewButton = within(testRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      // Check modal opens and shows generation info
      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
        expect(screen.getByText('AI from Function')).toBeInTheDocument()
        expect(screen.getByText('schedule_task')).toBeInTheDocument()
        expect(screen.getByText('kernel/sched/core.c')).toBeInTheDocument()
      })
    })

    it('does not show generation info for manual tests', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Manual Test Case')).toBeInTheDocument()
      })

      // Find the row with Manual Test Case and click view button
      const testRow = screen.getByText('Manual Test Case').closest('tr')
      expect(testRow).toBeInTheDocument()
      
      const viewButton = within(testRow!).getByRole('button', { name: /view/i })
      await user.click(viewButton)

      // Check modal opens but doesn't show AI generation info
      await waitFor(() => {
        expect(screen.getByText('Test Case Details')).toBeInTheDocument()
        expect(screen.getByText('Manual')).toBeInTheDocument()
        expect(screen.queryByText('AI from Diff')).not.toBeInTheDocument()
        expect(screen.queryByText('AI from Function')).not.toBeInTheDocument()
      })
    })
  })

  describe('AI Generation Modal Workflow', () => {
    it('opens AI generation modal and shows diff generation form', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Test Cases')).toBeInTheDocument()
      })

      // Click AI Generate Tests button
      const aiGenerateButton = screen.getByRole('button', { name: /ai generate tests/i })
      await user.click(aiGenerateButton)

      // Check modal opens with diff form by default
      await waitFor(() => {
        expect(screen.getByText('AI Test Generation')).toBeInTheDocument()
        expect(screen.getByText('From Code Diff')).toBeInTheDocument()
        expect(screen.getByPlaceholderText(/paste your git diff/i)).toBeInTheDocument()
      })
    })

    it('switches to function generation form', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Test Cases')).toBeInTheDocument()
      })

      // Open AI generation modal
      const aiGenerateButton = screen.getByRole('button', { name: /ai generate tests/i })
      await user.click(aiGenerateButton)

      await waitFor(() => {
        expect(screen.getByText('AI Test Generation')).toBeInTheDocument()
      })

      // Switch to function generation
      const functionButton = screen.getByRole('button', { name: /from function/i })
      await user.click(functionButton)

      // Check function form is shown
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/function name/i)).toBeInTheDocument()
        expect(screen.getByPlaceholderText(/file path/i)).toBeInTheDocument()
      })
    })

    it('validates required fields in diff generation form', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Test Cases')).toBeInTheDocument()
      })

      // Open AI generation modal
      const aiGenerateButton = screen.getByRole('button', { name: /ai generate tests/i })
      await user.click(aiGenerateButton)

      await waitFor(() => {
        expect(screen.getByText('AI Test Generation')).toBeInTheDocument()
      })

      // Try to submit without filling diff content
      const generateButton = screen.getByRole('button', { name: /generate tests/i })
      await user.click(generateButton)

      // Should show validation error
      await waitFor(() => {
        expect(screen.getByText(/please paste your git diff/i)).toBeInTheDocument()
      })
    })

    it('validates required fields in function generation form', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Test Cases')).toBeInTheDocument()
      })

      // Open AI generation modal and switch to function form
      const aiGenerateButton = screen.getByRole('button', { name: /ai generate tests/i })
      await user.click(aiGenerateButton)

      await waitFor(() => {
        expect(screen.getByText('AI Test Generation')).toBeInTheDocument()
      })

      const functionButton = screen.getByRole('button', { name: /from function/i })
      await user.click(functionButton)

      // Try to submit without filling required fields
      const generateButton = screen.getByRole('button', { name: /generate tests/i })
      await user.click(generateButton)

      // Should show validation errors
      await waitFor(() => {
        expect(screen.getByText(/please enter function name/i)).toBeInTheDocument()
        expect(screen.getByText(/please enter file path/i)).toBeInTheDocument()
      })
    })
  })

  describe('Real-time Updates After Generation', () => {
    it('refreshes test list after successful AI generation', async () => {
      const user = userEvent.setup()
      
      // Mock successful generation response
      const newTestCase = {
        id: 'test-4',
        name: 'Newly Generated Test',
        description: 'Test generated from AI',
        test_type: 'unit',
        target_subsystem: 'kernel/core',
        code_paths: ['kernel/core/new.c'],
        execution_time_estimate: 30,
        test_script: 'test_new_function()',
        metadata: {
          generation_method: 'ai_diff',
          execution_status: 'never_run'
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }

      // First call returns original tests, second call includes new test
      mockApiService.getTests
        .mockResolvedValueOnce({
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
        .mockResolvedValueOnce({
          tests: [...mockTestCases, newTestCase],
          pagination: {
            page: 1,
            page_size: 20,
            total_items: mockTestCases.length + 1,
            total_pages: 1,
            has_next: false,
            has_prev: false
          },
          filters_applied: {}
        })

      renderWithProviders(<TestCases />)

      // Wait for initial load
      await waitFor(() => {
        expect(screen.getByText('Manual Test Case')).toBeInTheDocument()
      })

      // Verify initial count
      expect(screen.getByText('3')).toBeInTheDocument() // Total tests

      // Simulate successful AI generation by manually triggering refresh
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)

      // Wait for new test to appear
      await waitFor(() => {
        expect(screen.getByText('Newly Generated Test')).toBeInTheDocument()
      })

      // Verify updated count
      expect(screen.getByText('4')).toBeInTheDocument() // Total tests now 4
    })

    it('preserves filters and pagination after generation', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Manual Test Case')).toBeInTheDocument()
      })

      // Apply a filter
      const generationMethodFilter = screen.getByPlaceholderText('Generation Method')
      await user.click(generationMethodFilter)
      
      const aiDiffOption = screen.getByText('AI from Diff')
      await user.click(aiDiffOption)

      // Verify filter is applied
      await waitFor(() => {
        expect(screen.getByText('AI Generated from Diff')).toBeInTheDocument()
        expect(screen.queryByText('Manual Test Case')).not.toBeInTheDocument()
      })

      // Simulate refresh (which would happen after AI generation)
      const refreshButton = screen.getByRole('button', { name: /refresh/i })
      await user.click(refreshButton)

      // Verify filter is still applied
      await waitFor(() => {
        expect(screen.getByText('AI Generated from Diff')).toBeInTheDocument()
        expect(screen.queryByText('Manual Test Case')).not.toBeInTheDocument()
      })
    })
  })

  describe('Error Handling', () => {
    it('handles API errors gracefully during test loading', async () => {
      mockApiService.getTests.mockRejectedValue(new Error('API Error'))
      
      renderWithProviders(<TestCases />)

      // Should not crash and show loading state
      await waitFor(() => {
        expect(screen.getByText('Test Cases')).toBeInTheDocument()
      })

      // Should handle the error gracefully (component should still render)
      expect(screen.queryByText('Manual Test Case')).not.toBeInTheDocument()
    })

    it('shows appropriate message when no tests match filters', async () => {
      const user = userEvent.setup()
      renderWithProviders(<TestCases />)

      await waitFor(() => {
        expect(screen.getByText('Manual Test Case')).toBeInTheDocument()
      })

      // Apply a filter that matches no tests
      const searchInput = screen.getByPlaceholderText('Search test cases...')
      await user.type(searchInput, 'nonexistent')

      // Should show no results
      await waitFor(() => {
        expect(screen.queryByText('Manual Test Case')).not.toBeInTheDocument()
        expect(screen.queryByText('AI Generated from Diff')).not.toBeInTheDocument()
        expect(screen.queryByText('AI Generated from Function')).not.toBeInTheDocument()
      })

      // Should show 0 in statistics
      expect(screen.getByText('0')).toBeInTheDocument() // Total tests filtered
    })
  })
})