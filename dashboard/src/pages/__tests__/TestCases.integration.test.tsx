import React from 'react'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from 'react-query'
import { BrowserRouter } from 'react-router-dom'
import TestCases from '../TestCases'

// Mock the API service
jest.mock('../../services/api', () => ({
  __esModule: true,
  default: {
    getTests: jest.fn(() => Promise.resolve({
      tests: [
        {
          id: 'test-1',
          name: 'Sample Test',
          description: 'Test description',
          test_type: 'unit',
          target_subsystem: 'kernel/core',
          code_paths: [],
          execution_time_estimate: 30,
          test_script: 'echo "test"',
          metadata: {
            generation_method: 'manual'
          },
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-01-15T10:00:00Z'
        }
      ],
      total: 1
    }))
  }
}))

const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
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

describe('TestCases Integration', () => {
  it('opens modal when view button is clicked', async () => {
    renderWithProviders(<TestCases />)
    
    // Wait for the test data to load
    await waitFor(() => {
      expect(screen.getByText('Sample Test')).toBeInTheDocument()
    })

    // Find and click the view button (eye icon)
    const viewButton = screen.getByRole('button', { name: /view details/i })
    fireEvent.click(viewButton)

    // Check if modal opens
    await waitFor(() => {
      expect(screen.getByText('Test Case Details')).toBeInTheDocument()
    })
  })

  it('switches to edit mode when edit button is clicked in modal', async () => {
    renderWithProviders(<TestCases />)
    
    // Wait for data and open modal
    await waitFor(() => {
      expect(screen.getByText('Sample Test')).toBeInTheDocument()
    })

    const viewButton = screen.getByRole('button', { name: /view details/i })
    fireEvent.click(viewButton)

    await waitFor(() => {
      expect(screen.getByText('Test Case Details')).toBeInTheDocument()
    })

    // Click edit button in modal
    const editButton = screen.getByRole('button', { name: /edit/i })
    fireEvent.click(editButton)

    // Check if modal switches to edit mode
    await waitFor(() => {
      expect(screen.getByText('Edit Test Case')).toBeInTheDocument()
    })
  })
})